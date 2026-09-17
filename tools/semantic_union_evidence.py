#!/usr/bin/env python3
"""True-golden evidence pack generator (per top-6 PR). Read-only; NOT a frozen instrument.

For each semantic-union cluster (a distinct real bug found by the campaign), produce a
HUMAN-VERIFIABLE card:
  - title, file:startline-endline (post-PR line numbers)
  - why_real: cites the offending code and explains the defect mechanism
  - replication: concrete steps to observe the bug
  - severity, confidence, distinct (cluster sanity flag)
plus coverage: which models/frameworks/efforts found it.

Grounding: the cluster's deduplicated member reports + the actual PR patch for the
concerned file (harnesseval.dataset.pr_diff, gh-cached).

Usage:
  .venv/bin/python tools/semantic_union_evidence.py --pr https://github.com/calcom/cal.com/pull/11059
"""
from __future__ import annotations
import argparse, asyncio, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.model_router import call_model_json

_LOC_RE = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4})(?::(\d+)(?:-(\d+))?)?")

SYSTEM = "You are a precise code-review bug verifier. Always respond with valid JSON."
PROMPT = """You are verifying that a reported issue in a pull request is a REAL, distinct bug, for a benchmark's \
"true golden set" evidence pack. Multiple automated reviewers (different tools/models) reported this same \
underlying issue; their deduplicated reports are below.

PR: {pr}

Reports (clustered as one underlying issue):
{reports}

The PR's patch for {fileloc}:
{patch}

Produce a verification card a human engineer could use to confirm this bug by reading the code. Respond with ONLY a JSON object:
{{
 "title": "one-line bug title",
 "file": "path from the reports (post-PR tree)",
 "startline": <int, post-PR line number where the bug lives — from the reports' line refs, cross-checked with the patch hunk headers>,
 "endline": <int>,
 "why_real": "2-4 sentences quoting the offending lines and explaining the defect mechanism — why this is a genuine bug, not a style nit or a hallucination",
 "replication": "concrete steps to observe the bug: trigger conditions, inputs or request sequence, expected vs actual behavior",
 "severity": "critical|high|medium|low",
 "distinct": true|false,
 "confidence": 0.0-1.0
}}
Rules:
- distinct=false ONLY if the reports clearly describe two different bugs (the cluster is wrong).
- If the patch is empty, rely on the reports alone and say so in why_real.
- Line numbers refer to the NEW side of the diff (post-PR code)."""


def majority_file(texts):
    c = Counter()
    for t in texts:
        for m in _LOC_RE.finditer(t):
            f = m.group(1)
            if "." in f and len(f) < 120:
                c[f.split("/")[-1]] += 1
                c[f] += 1
    return c.most_common(1)[0][0] if c else None


def patch_for(files, fname):
    if not fname:
        return ""
    short = fname.split("/")[-1]
    for f in files or []:
        if f.get("filename", "").endswith(short) or f.get("filename") == fname:
            return (f.get("patch") or "")[:6000]
    return ""


async def run(pr: str, judge: str):
    slug = pr.rstrip("/").split("/")[-1]
    pil = json.load(open(ROOT / f"analysis/exp_union_semantic_pilot_{slug}.json"))
    f2c = {int(k): v for k, v in pil["finding_to_cluster"].items()}
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    runs = [r for r in D["all_healthy_runs"] if r["url"] == pr]
    per_run = {r["run_id"]: (r.get("bugtexts") or [], r) for r in runs}

    # rebuild flat order exactly as the pilot did (dict insertion order = runs order)
    flat = []  # (rid, text)
    for rid, (ts, _r) in per_run.items():
        for t in ts:
            flat.append((rid, t))

    # cluster -> member unique texts + finder cells
    mem_texts = defaultdict(list)
    finders = defaultdict(set)   # (model, fw, eff) sets
    n_find = Counter()
    for i, (rid, t) in enumerate(flat):
        k = f2c[i]
        mem_texts[k].append(t)
        n_find[k] += 1
        _, r = per_run[rid]
        finders[k].add((r["model"], r["framework"], r["effort"]))

    uniq_texts = {k: sorted(set(v), key=len) for k, v in mem_texts.items()}

    diff = fetch_diff(pr)
    files = diff.get("files") or []

    sem = asyncio.Semaphore(8)
    calls = {"n": 0, "tin": 0, "tout": 0}

    async def card(k):
        texts = uniq_texts[k][:8]
        fname = majority_file(texts)
        patch = patch_for(files, fname)
        reports = "\n".join(f"- {t[:500]}" for t in texts)
        async with sem:
            parsed, tin, tout, _ = await call_model_json(
                judge, SYSTEM,
                PROMPT.format(pr=pr, reports=reports, fileloc=fname or "(no file reference in reports)",
                              patch=patch or "(file not part of this PR's diff — rely on the reports)"),
                effort="medium", max_tokens=1500)
        calls["n"] += 1; calls["tin"] += tin; calls["tout"] += tout
        if not isinstance(parsed, dict):
            parsed = {"title": texts[0][:120], "file": fname or "?", "startline": 0, "endline": 0,
                      "why_real": "(judge call failed; see member reports)", "replication": "",
                      "severity": "unknown", "distinct": True, "confidence": 0.0}
        parsed["n_reports"] = len(mem_texts[k])
        parsed["n_findings"] = n_find[k]
        parsed["n_cells"] = len(finders[k])
        parsed["found_by"] = sorted("|".join(x) for x in finders[k])
        parsed["cluster"] = k
        return parsed

    t0 = time.time()
    cards = await asyncio.gather(*[card(k) for k in sorted(uniq_texts)])
    cards = sorted(cards, key=lambda c: (-c["n_cells"], -c["n_findings"]))

    out = {"pr": pr, "judge_model": judge, "judge_calls": calls["n"],
           "tokens_in": calls["tin"], "tokens_out": calls["tout"],
           "n_clusters": len(cards), "cards": cards}
    path = ROOT / f"analysis/semantic_true_golden_{slug}.json"
    json.dump(out, open(path, "w"), indent=1)
    print(f"wrote {path} ({len(cards)} cards, {calls['n']} calls, {time.time()-t0:.0f}s)")
    nd = sum(1 for c in cards if not c.get("distinct", True))
    print(f"clusters flagged NOT distinct: {nd}/{len(cards)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True)
    ap.add_argument("--judge", default="gpt-5.2")
    a = ap.parse_args()
    asyncio.run(run(a.pr, a.judge))


if __name__ == "__main__":
    main()
