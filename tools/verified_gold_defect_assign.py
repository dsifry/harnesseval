#!/usr/bin/env python3
"""Assign every finding to a DEFECT id, so per-run matching can be done per defect (not per bundle).

The registry (DEFECT_REGISTRY.json) splits each verified bundle into its distinct defects. This pass
maps each *finding* to one of its bundle's defects: for single-defect bundles that is trivial; for the
multi-concern bundles the judge assigns each finding to one of the audit labels (one call per bundle).

Output: analysis/verified_gold/DEFECT_ASSIGN.json  {"<pr>": {"<finding_sha1>": "<defect id>"}, ...}
plus a coverage summary. Read-only w.r.t. verdicts.

Usage: .venv/bin/python tools/verified_gold_defect_assign.py
"""
from __future__ import annotations
import asyncio, glob, hashlib, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))
from verified_gold_driver import AUTHOR_MODEL  # single source of truth for the authoring/judge model

VG = ROOT / "analysis/verified_gold"
SYSTEM = "You are a precise code-review deduplicator. Respond with ONLY valid JSON."
PROMPT = """A cluster of automated-review findings was audited and found to contain {n} DISTINCT defects:

{labels}

Below are the findings in the cluster (numbered). Assign EACH finding to the ONE defect it is about.

Findings:
{items}

Respond with ONLY a JSON object mapping each finding index to a defect number (0-based):
{{"0": 0, "1": 2, "2": 1, ...}}"""


def sha(t):
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def load_members(pr, idx):
    v = json.load(open(f"analysis/semantic_true_golden_verify_{pr}.json"))
    pil = json.load(open(f"analysis/exp_union_semantic_pilot_{pr}.json"))
    D = json.load(open("analysis/final_report_dataset.json"))
    f2c = {int(a): b for a, b in pil["finding_to_cluster"].items()}
    runs = [r for r in D["all_healthy_runs"] if r["url"] == pil["pr"]]
    flat = [t for r in runs for t in (r.get("bugtexts") or [])]
    mem = defaultdict(list)
    for i, t in enumerate(flat):
        mem[f2c[i]].append(t)
    out = []
    for g in v["clusters"][idx]["merge_group"]:
        for t in mem[g]:
            if t not in out:
                out.append(t)
    return out


async def main():
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    by_bundle = defaultdict(list)
    for d in reg["defects"]:
        by_bundle[d["bundle"]].append(d)
    # every verified bundle (including duplicates) contributes its findings to its defects
    bundles = []
    for f in sorted(glob.glob(str(VG / "*/*/meta.json"))):
        m = json.load(open(f))
        if m.get("verdict") in ("confirmed_regression", "behavior_change_not_regression", "duplicate_of"):
            bundles.append(m["bug_id"])
    sem = asyncio.Semaphore(8)
    calls = {"n": 0}
    out = defaultdict(dict)
    summary = []

    async def do_bundle(bid):
        pr = bid.split("-")[0]
        idx = int(bid.split("B")[1])
        ds = by_bundle.get(bid) or []
        if not ds:
            return
        texts = load_members(pr, idx)
        if not texts:
            return
        if len(ds) == 1:
            for t in texts:
                out[pr][sha(t)] = ds[0]["id"]
            summary.append((bid, len(texts), 1, len(texts)))
            return
        # multi-defect bundle: one judge call maps each finding to a defect
        labels = "\n".join(f"{i}. {d['label'][:180]}" for i, d in enumerate(ds))
        items = texts[:60]
        body = "\n".join(f"{j}. {t[:300]}" for j, t in enumerate(items))
        async with sem:
            p, _, _, _ = await call_model_json(AUTHOR_MODEL, SYSTEM,
                                              PROMPT.format(n=len(ds), labels=labels, items=body),
                                              effort="low", max_tokens=4000)
        calls["n"] += 1
        p = p if isinstance(p, dict) else {}
        hit = 0
        for j, t in enumerate(items):
            v = p.get(str(j))
            k = int(v) if isinstance(v, (int, str)) and str(v).isdigit() and int(v) < len(ds) else None
            if k is None:
                continue
            out[pr][sha(t)] = ds[k]["id"]
            hit += 1
        summary.append((bid, len(texts), len(ds), hit))

    await asyncio.gather(*[do_bundle(b) for b in bundles])
    (VG / "DEFECT_ASSIGN.json").write_text(json.dumps(out, indent=1))
    cov = {pr: len(m) for pr, m in out.items()}
    print(f"judge calls: {calls['n']}")
    print("findings mapped per PR:", cov, "| total:", sum(cov.values()))
    multi = [s for s in summary if s[2] > 1]
    print(f"multi-defect bundles: {len(multi)} (judged); assigned {sum(s[3] for s in multi)} findings")
    Path(VG / "DEFECT_ASSIGN.md").write_text(
        "# Finding -> defect assignment\n\n"
        f"Judge calls: {calls['n']} (one per multi-defect bundle; single-defect bundles map trivially).\n\n"
        f"Findings mapped: {sum(cov.values())} across {len(cov)} PRs.\n\n"
        "| PR | findings mapped |\n|---|---|\n" + "\n".join(f"| {pr} | {n} |" for pr, n in sorted(cov.items())) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
