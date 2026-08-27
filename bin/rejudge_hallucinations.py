#!/usr/bin/env -S uv run python
"""Re-adjudicate gpt-5.2's stored "hallucinations" with stronger judges (opus-5, gpt-5.6-sol).

WHY: gpt-5.2 has been the adjudicator for the entire eval (384-cell batch 083 + SDLC runs).
If it systematically misclassifies real bugs as "hallucinations," we UNDERCOUNT hidden gold
(and understate the harness advantage). This script validates that assumption by re-judging
the SAME candidates gpt-5.2 called "hallucination" against opus-5 and gpt-5.6-sol.

METHOD (uses STORED data — no re-discovery needed):
  The batch-083 runs store `adjudication_records` with the candidate text + gpt-5.2's verdict
  (matched / real_but_ungold / hallucination). We:
  1. Load all stored adjudication_records where verdict == "hallucination" (deduped to one
     canonical run per cell — ~4,472 across 450 cells).
  2. Sample N (default 200, stratified by framework × model for a representative mix).
  3. Re-adjudicate each sampled candidate with opus-5 AND gpt-5.6-sol using the SAME
     ADJUDICATE_PROMPT + the PR's diff (re-materialized once per PR, cached).
  4. Report the flip rate — how many "hallucinations" the stronger judges call "real."
     A high flip rate means gpt-5.2 is too aggressive (undercounting hidden gold).

This does NOT modify any existing results. Writes to results/hallucination_rejudge.json.

Usage:
  uv run python bin/rejudge_hallucinations.py                      # default: sample 200
  uv run python bin/rejudge_hallucinations.py --sample 500        # larger sample
  uv run python bin/rejudge_hallucinations.py --framework metareview-realistic  # filter
"""
from __future__ import annotations
import asyncio, json, random, argparse, time, glob
from pathlib import Path
from collections import defaultdict

from harnesseval.sdlc_loop import _log
from harnesseval.run_model_matrix import _pr_sample
from harnesseval.adjudicate import ADJUDICATE_PROMPT, ADJUDICATE_SYSTEM
from harnesseval.model_router import call_model_json

STRONG_JUDGES = ["claude-opus-5", "gpt-5.6-sol"]
REAL_THRESHOLD = 0.7  # same as the eval's adjudication threshold


def load_hallucinations(framework_filter: str | None = None) -> list[dict]:
    """Load stored hallucination candidates from batch-083 runs, DEDUPED to one canonical run per cell.

    Duplicate runs (retries for quota/crashes) inflate the count, so we keep one run per
    (url, framework, model, effort) cell — preferring 'pass' status, most findings, latest run_id.
    Returns list of {url, framework, model, effort, issue_text, ...} dicts.
    """
    # collect all runs grouped by cell
    from collections import defaultdict
    by_cell = defaultdict(list)  # cell -> [(run_id, summary_path, n_findings, status)]
    for f in glob.glob("runs/*/summary.json"):
        s = json.load(open(f))
        if "adjudication_records" not in s:
            continue
        fw = s.get("framework", "")
        if framework_filter and fw != framework_filter:
            continue
        cell = (s.get("url", ""), fw, s.get("model", ""), s.get("effort", ""))
        n_f = s.get("n_findings", 0)
        by_cell[cell].append((f.split("/")[-2], f, n_f, s.get("status", "")))
    # pick canonical run per cell: pass first, then most findings, then latest run_id
    rows = []
    n_dup_runs = 0
    for cell, runs in by_cell.items():
        n_dup_runs += len(runs) - 1
        runs.sort(key=lambda x: (x[3] != "pass", -x[2], x[0]))
        canonical_path = runs[0][1]
        s = json.load(open(canonical_path))
        url, fw, model, effort = cell
        for ar in s["adjudication_records"]:
            if ar.get("adjudication", {}).get("verdict") == "hallucination":
                rows.append({"url": url, "framework": fw, "model": model, "effort": effort,
                             "issue_text": ar["issue_text"], "source_lens": ar.get("source_lens"),
                             "gpt52_reasoning": ar.get("adjudication", {}).get("rationale", "")})
    print(f"  (dedup: {sum(len(r) for r in by_cell.values())} runs -> {len(by_cell)} cells, dropped {n_dup_runs} duplicate runs)", flush=True)
    return rows


def stratified_sample(rows: list[dict], n: int) -> list[dict]:
    """Sample n rows, stratified by framework (proportional representation)."""
    if len(rows) <= n:
        return rows
    by_fw = defaultdict(list)
    for r in rows:
        by_fw[r["framework"]].append(r)
    # proportional allocation per framework, min 1 each
    out = []
    for fw, items in by_fw.items():
        k = max(1, round(n * len(items) / len(rows)))
        k = min(k, len(items))
        out.extend(random.sample(items, k))
    # trim to n if over
    return out[:n] if len(out) > n else out + random.sample(rows, n - len(out))


async def readjudicate(candidates: list[dict], diff: str, judge_model: str) -> list[dict]:
    """Re-adjudicate candidates with a specific judge. Returns per-candidate verdicts."""
    sem = asyncio.Semaphore(10)
    async def adj(c: dict) -> dict:
        async with sem:
            parsed, _, _, _ = await call_model_json(judge_model, ADJUDICATE_SYSTEM,
                ADJUDICATE_PROMPT.format(diff=diff[:30000], candidate=c["issue_text"]),
                effort="medium", max_tokens=2048)
            if not parsed:
                return {**c, "judge": judge_model, "is_real": False, "confidence": 0.0,
                        "reasoning": "parse-error"}
            return {**c, "judge": judge_model, "is_real": bool(parsed.get("is_real", False)),
                    "confidence": float(parsed.get("confidence", 0.0)),
                    "reasoning": str(parsed.get("reasoning", ""))}
    return await asyncio.gather(*[adj(c) for c in candidates])


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=200, help="sample size (default 200)")
    ap.add_argument("--framework", default=None, help="filter by framework (e.g. metareview-realistic)")
    ap.add_argument("--seed", type=int, default=42, help="random seed for sampling")
    args = ap.parse_args()
    random.seed(args.seed)

    print("=== Re-judging gpt-5.2 'hallucinations' with opus-5 + gpt-5.6-sol ===", flush=True)
    print("(uses STORED adjudication_records from batch 083 — no re-discovery needed)\n", flush=True)

    rows = load_hallucinations(args.framework)
    print(f"Loaded {len(rows)} stored hallucination candidates"
          f"{' (framework=' + args.framework + ')' if args.framework else ''}", flush=True)
    if not rows:
        print("No hallucinations found. Exiting.", flush=True)
        return

    sample = stratified_sample(rows, args.sample)
    print(f"Sampled {len(sample)} (stratified by framework) for re-adjudication\n", flush=True)

    # cache diffs per PR URL (only 6 PRs)
    diffs = {}
    urls = set(r["url"] for r in sample)
    for url in urls:
        pr = _pr_sample(url)
        diffs[url] = pr.diff
        print(f"  diff cached: {url} ({len(pr.diff)} chars)", flush=True)
    print(flush=True)

    # re-adjudicate with each strong judge — group candidates by URL so the diff matches
    results = {}
    for judge in STRONG_JUDGES:
        t0 = time.time()
        # batch by URL to attach the correct diff
        verdicts = []
        for url in urls:
            cands = [r for r in sample if r["url"] == url]
            v = await readjudicate(cands, diffs[url], judge)
            verdicts.extend(v)
        n_real = sum(1 for v in verdicts if v["is_real"] and v["confidence"] >= REAL_THRESHOLD)
        n_halluc = len(verdicts) - n_real
        results[judge] = {"verdicts": verdicts, "n_real": n_real, "n_halluc": n_halluc,
                         "flip_rate": n_real / len(verdicts) if verdicts else 0}
        print(f"[{judge}] {n_real}/{len(verdicts)} hallucinations FLIP to real "
              f"(flip rate {n_real/len(verdicts)*100:.0f}%)  ({time.time()-t0:.0f}s)", flush=True)

    # verdict comparison table
    print("\n" + "=" * 110, flush=True)
    print("VERDICT COMPARISON (candidates gpt-5.2 called 'hallucination')", flush=True)
    print("=" * 110, flush=True)
    print(f"{'#':>3}  {'gpt-5.2':>8}  {'opus-5':>8}  {'gpt-5.6-sol':>12}  framework/model  candidate (truncated)", flush=True)
    print("-" * 110, flush=True)
    opus_v = {v["issue_text"]: v for v in results["claude-opus-5"]["verdicts"]}
    sol_v = {v["issue_text"]: v for v in results["gpt-5.6-sol"]["verdicts"]}
    for i, r in enumerate(sample):
        o = opus_v[r["issue_text"]]; s = sol_v[r["issue_text"]]
        def tag(v): return "REAL" if v["is_real"] and v["confidence"] >= REAL_THRESHOLD else "hal"
        print(f"{i+1:>3}  {'hal':>8}  {tag(o):>8}  {tag(s):>12}  {r['framework'][:10]:10}/{r['model'][:12]:12}  {r['issue_text'][:50]}", flush=True)

    # impact summary
    print("\n" + "=" * 110, flush=True)
    print("IMPACT: if hallucinations are actually real, hidden-gold is UNDERCOUNTED", flush=True)
    print("=" * 110, flush=True)
    print(f"  gpt-5.2 (baseline):  {len(rows)} hallucinations (deduped, 1 run/cell) across 450 cells", flush=True)
    for judge in STRONG_JUDGES:
        fr = results[judge]["flip_rate"]
        projected_flips = round(fr * len(rows))
        print(f"  {judge}: {results[judge]['n_real']}/{len(sample)} sample flips "
              f"({fr*100:.0f}% flip rate) → ~{projected_flips} of {len(rows)} would flip to real", flush=True)
    print(f"\n  Interpretation: a high flip rate means gpt-5.2 is too aggressive (rejecting real bugs).", flush=True)
    print(f"  Those flipped candidates are REAL hidden gold — currently miscounted as hallucinations.", flush=True)

    out = Path("results/hallucination_rejudge.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "sample_size": len(sample), "total_stored_hallucinations": len(rows),
        "framework_filter": args.framework,
        "rejudges": {j: {"n_real": results[j]["n_real"], "n_halluc": results[j]["n_halluc"],
                          "flip_rate": results[j]["flip_rate"],
                          "verdicts": results[j]["verdicts"]} for j in STRONG_JUDGES},
    }, indent=2, default=str))
    print(f"\n-> {out}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
