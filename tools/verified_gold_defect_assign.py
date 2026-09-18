#!/usr/bin/env python3
"""Assign every finding to a DEFECT id, so per-run matching can be done per defect (not per bundle).

The registry (DEFECT_REGISTRY.json) splits each verified bundle into its distinct defects. This pass
maps each *finding* to one of its bundle's defects — or to JSON null when it describes none of them.
For single-defect bundles the mapping is trivial; for multi-concern bundles the judge assigns each
finding to one of the audit labels, in CHUNK-sized calls so EVERY finding is considered (the 2026-09-17
version silently dropped texts beyond the first 60 of a bundle — 276 findings were never scored).

A verification pass then re-checks low-signal assignments (word-overlap suspects) with the judge and
applies KEEP / REASSIGN / NULL corrections. A validated mis-assignment (a finding about
`embed_by_username.downcase` crashing on nil credited to the queue-flooding defect 4-D04) motivated
this pass; see WITHDRAWALS_AND_DEDUP_2026-09-18.md and the external review of 2026-09-18.

Outputs:
  analysis/verified_gold/DEFECT_ASSIGN.json        {"<pr>": {"<sha16>": "<defect id>" | null}, ...}
    — every finding appears; null means "no clear match" (the scorer skips falsy values).
  analysis/verified_gold/DEFECT_ASSIGN_AUDIT.json  per-bundle chunk/null/suspect/correction counts.
  analysis/verified_gold/DEFECT_ASSIGN.md           human coverage report.

Read-only w.r.t. verdicts. Usage: .venv/bin/python tools/verified_gold_defect_assign.py
"""
from __future__ import annotations
import asyncio, glob, hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402
sys.path.insert(0, str(ROOT / "tools"))
from verified_gold_driver import AUTHOR_MODEL  # single source of truth for the authoring/judge model

VG = ROOT / "analysis" / "verified_gold"
CHUNK = 50
SUSPECT_OVERLAP = 0.10
SYSTEM = "You are a precise code-review deduplicator. Respond with ONLY valid JSON."
PROMPT = """A cluster of automated-review findings was audited. Its cluster's own DISTINCT defects are listed
first; other verified defects of the same PR follow, marked as "other PR defect" (the validated
2026-09-18 review showed clusters leak findings across defect boundaries, so a finding may
legitimately describe a defect outside its own cluster):

{labels}

Below are the findings in the cluster (numbered). Assign EACH finding to the ONE defect it is about —
normally one of the cluster's own defects; use an "other PR defect" only when the finding clearly
describes it and none of the cluster's own defects — or to null if it does not clearly describe any
listed defect. Answer for every finding.

Findings:
{items}

Respond with ONLY a JSON object mapping each finding index to a defect number (0-based) or null:
{{"0": 0, "1": 2, "2": null, ...}}"""
VERIFY_PROMPT = """A cluster of automated-review findings was audited and found to contain {n} DISTINCT defects:

{labels}

Below are SUSPECT findings (numbered) with their currently assigned defect. For each finding decide:
- KEEP  — the finding text does describe the assigned defect.
- REASSIGN:<defect number> — it describes a DIFFERENT listed defect instead.
- NULL  — it does not clearly describe any listed defect.

Answer for every finding.

Findings:
{items}

Respond with ONLY a JSON object mapping each finding index to "KEEP", "REASSIGN:<n>" or "NULL":
{{"0": "KEEP", "1": "REASSIGN:2", "2": "NULL", ...}}"""


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


def label_lines(ds):
    return "\n".join(f"{i}. {d['label'][:180]} [{d.get('anchor_file') or 'n/a'}]" for i, d in enumerate(ds))  # (used for single-defect path docs; multi-defect path builds its own candidate list)


def defect_index(v, n):
    """Coerce a judge answer to a 0-based defect index, or None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if 0 <= v < n else None
    if isinstance(v, str):
        s = v.strip()
        if s.lower() in ("null", "none", ""):
            return None
        if s.lstrip("-").isdigit():
            iv = int(s)
            return iv if 0 <= iv < n else None
    return None


def label_overlap(text, label):
    """Fraction of the defect label's significant words (len>3) present in the finding text."""
    sig = set(re.findall(r"[a-z_0-9]{4,}", label.lower()))
    if not sig:
        return 1.0
    ft = text.lower()
    return sum(1 for w in sig if w in ft) / len(sig)


async def main():
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    by_bundle = defaultdict(list)
    for d in reg["defects"]:
        by_bundle[d["bundle"]].append(d)
    # other verified defects of the same PR: multi-defect bundles may legitimately contain findings
    # that describe a defect outside the bundle (validated case: a 4-B02-clustered finding that
    # describes 4-D56). Withdrawn/duplicate-tier defects never receive new credit.
    pr_verified = defaultdict(list)
    for d in reg["defects"]:
        if d["tier"] == "D-verified":
            pr_verified[d["pr"]].append(d)
    # every verified bundle (including duplicates) contributes its findings to its defects
    bundles = []
    for f in sorted(glob.glob(str(VG / "*/*/meta.json"))):
        m = json.load(open(f))
        if m.get("verdict") in ("confirmed_regression", "behavior_change_not_regression", "duplicate_of"):
            bundles.append(m["bug_id"])
    sem = asyncio.Semaphore(6)
    calls = {"n": 0, "vcalls": 0, "unparseable": 0}
    out = defaultdict(dict)
    audit = []          # per-bundle audit records
    corrections = []    # all verification corrections

    # NOTE: deepseek-4.1-flash rejects effort="medium" (LunarRoute allows low/high/xhigh/max or an
    # integer in [1,100]); "high" is the deliberate step above the old "low" — the validated
    # mis-assignment (3090239f -> 4-D04) is what this pass exists to fix, so signal beats speed.
    async def call_json(prompt, sem, calls, key):
        async with sem:
            p, _, _, _ = await call_model_json(AUTHOR_MODEL, SYSTEM, prompt,
                                               effort="high", max_tokens=8000)
        calls[key] += 1
        if isinstance(p, dict):
            return p
        # unparseable: one tool-level retry, then the caller records nulls (never silent)
        async with sem:
            p, _, _, _ = await call_model_json(AUTHOR_MODEL, SYSTEM, prompt,
                                               effort="high", max_tokens=8000)
        calls[key] += 1
        if isinstance(p, dict):
            return p
        calls["unparseable"] += 1
        return None

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
            audit.append({"bundle": bid, "n_texts": len(texts), "n_defects": 1,
                          "chunks": 0, "judge_nulls": 0, "suspects": 0, "corrections": []})
            return
        # multi-defect bundle: judge maps each finding (ALL of them, chunked) to one defect or null.
        # Candidates: the bundle's own defects, then the PR's other D-verified defects (marked).
        own_ids = {d["id"] for d in ds}
        others = [d for d in pr_verified.get(pr, []) if d["id"] not in own_ids]
        cands = list(ds) + others
        nown = len(ds)
        labels = "\n".join(
            f"{i}. {d['label'][:180]} [{d.get('anchor_file') or 'n/a'}]"
            + ("" if i < nown else "  (other PR defect — choose only if the finding clearly describes it "
               "and none of this cluster's defects)")
            for i, d in enumerate(cands))
        assign = {}   # text -> candidate index or None
        nchunks = 0
        for c0 in range(0, len(texts), CHUNK):
            chunk = texts[c0:c0 + CHUNK]
            body = "\n".join(f"{j}. {t[:300]}" for j, t in enumerate(chunk))
            p = await call_json(PROMPT.format(own=nown, labels=labels, items=body), sem, calls, "n")
            nchunks += 1
            for j, t in enumerate(chunk):
                assign[t] = defect_index((p or {}).get(str(j)), len(cands))
        judge_nulls = sum(1 for k in assign.values() if k is None)
        # verification pass: low word-overlap pairs get a second look
        suspects = [(t, k) for t, k in assign.items()
                    if k is not None and label_overlap(t, cands[k]["label"]) < SUSPECT_OVERLAP]
        bcorr = []
        for c0 in range(0, len(suspects), CHUNK):
            batch = suspects[c0:c0 + CHUNK]
            body = "\n".join(f"{j}. [currently assigned: {cands[k]['id']}] {t[:300]}" for j, (t, k) in enumerate(batch))
            p = await call_json(VERIFY_PROMPT.format(n=len(cands), labels=labels, items=body), sem, calls, "vcalls")
            for j, (t, k) in enumerate(batch):
                v = (p or {}).get(str(j))
                s = str(v).strip().upper() if v is not None else ""
                old = cands[k]["id"]
                if s.startswith("REASSIGN:"):
                    nk = defect_index(s.split(":", 1)[1], len(cands))
                    if nk is not None and nk != k:
                        assign[t] = nk
                        bcorr.append({"sha": sha(t), "old": old, "new": cands[nk]["id"]})
                elif s == "NULL":
                    assign[t] = None
                    bcorr.append({"sha": sha(t), "old": old, "new": None})
                # KEEP (or no parseable verdict): leave as assigned
        cross = sum(1 for k in assign.values() if k is not None and k >= nown)
        for t, k in assign.items():
            out[pr][sha(t)] = cands[k]["id"] if k is not None else None
        corrections.extend({"bundle": bid, **c} for c in bcorr)
        audit.append({"bundle": bid, "n_texts": len(texts), "n_defects": len(ds),
                      "n_candidates": len(cands), "cross_bundle_assignments": cross,
                      "chunks": nchunks, "judge_nulls": judge_nulls,
                      "suspects": len(suspects), "corrections": bcorr})

    await asyncio.gather(*[do_bundle(b) for b in bundles])
    (VG / "DEFECT_ASSIGN.json").write_text(json.dumps(out, indent=1))
    (VG / "DEFECT_ASSIGN_AUDIT.json").write_text(json.dumps(
        {"chunk": CHUNK, "suspect_overlap": SUSPECT_OVERLAP,
         "bundles": audit,
         "totals": {"judge_calls": calls["n"], "verify_calls": calls["vcalls"],
                    "unparseable_after_retry": calls["unparseable"],
                    "corrections": len(corrections)}}, indent=1))

    mapped = {pr: sum(1 for v in m.values() if v) for pr, m in out.items()}
    nulls = {pr: sum(1 for v in m.values() if not v) for pr, m in out.items()}
    total = sum(len(m) for m in out.values())
    print(f"judge calls: {calls['n']} | verify calls: {calls['vcalls']} | "
          f"unparseable chunks (nulled after retry): {calls['unparseable']}")
    print(f"findings considered: {total} | mapped: {sum(mapped.values())} | null (no clear match): {sum(nulls.values())}")
    print("per PR (considered / mapped / null):",
          {pr: (len(out[pr]), mapped[pr], nulls[pr]) for pr in sorted(out)})
    print(f"verification corrections applied: {len(corrections)}")
    for c in corrections:
        print(f"   {c['bundle']} {c['sha']}: {c['old']} -> {c['new']}")
    L = ["# Finding -> defect assignment", "",
         "Every finding in every verified bundle is considered. Multi-defect bundles are judged in "
         f"{CHUNK}-finding calls (the pre-2026-09-18 version dropped texts past the first 60); findings "
         "that describe no listed defect are recorded as `null` and skipped by the scorer, never silently "
         "dropped. Low word-overlap assignments are re-checked by a verification judge pass.", "",
         f"Judge calls: {calls['n']} assignment + {calls['vcalls']} verification "
         f"(unparseable-after-retry chunks: {calls['unparseable']}).", "",
         f"Findings considered: {total}; mapped: {sum(mapped.values())}; null (no clear match): {sum(nulls.values())}.", "",
         f"Verification corrections: {len(corrections)} (see DEFECT_ASSIGN_AUDIT.json).", "",
         "| PR | considered | mapped | null |", "|---|---|---|---|"]
    L += [f"| {pr} | {len(out[pr])} | {mapped[pr]} | {nulls[pr]} |" for pr in sorted(out)]
    L += ["", "Per-bundle detail (chunks, nulls, suspects, corrections): DEFECT_ASSIGN_AUDIT.json", ""]
    (VG / "DEFECT_ASSIGN.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
