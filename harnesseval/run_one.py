"""Run one adapter on one Martian PR end-to-end: fetch diff -> review -> extract -> judge -> score.

Phase B proof: proves the full pipeline works on a real PR. Registers the run.

Usage:
  uv run python -m harnesseval.run_one --url <golden-url> --framework vanilla-engineered --mode api
  uv run python -m harnesseval.run_one --url <golden-url> --framework vanilla-engineered --mode cli --effort medium
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from harnesseval.dataset import martian
from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.adapters.base import PRSample
from harnesseval.judge import judge_pairs, score_from_matches
from harnesseval.runs import register


def _pr_sample(url: str) -> PRSample:
    gc = martian.golden_comments_by_url()
    bd = martian.shipped_evaluations("opus")  # for pr_title/source_repo we use benchmark_data
    # pr_title / source_repo live in benchmark_data.json
    import json as _json
    bdata = _json.load(open(Path(martian.OFFLINE / "results" / "benchmark_data.json")))
    entry = bdata.get(url, {})
    d = fetch_diff(url)
    return PRSample(url=url, pr_title=entry.get("pr_title", ""), source_repo=entry.get("source_repo", ""),
                    diff=d["diff"], files=d["files"], golden_comments=gc.get(url, []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="golden-comment PR URL")
    ap.add_argument("--framework", default="vanilla-engineered",
                    choices=["vanilla-naive", "vanilla-engineered", "metareview"])
    ap.add_argument("--model", default="claude-opus-4-5-20251101")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--mode", default="api", choices=["api", "cli"])
    ap.add_argument("--judge-model", default="claude-opus-4-5-20251101")
    args = ap.parse_args()

    pr = _pr_sample(args.url)
    print(f"[run_one] PR: {pr.source_repo} — {pr.pr_title}")
    print(f"[run_one] diff: {len(pr.diff)} bytes, {len(pr.files)} files, {len(pr.golden_comments)} golden comments")

    # 1. review
    run = None
    if args.framework.startswith("vanilla-"):
        from harnesseval.adapters import vanilla
        variant = "naive" if args.framework == "vanilla-naive" else "engineered"
        run = vanilla.review(pr, model=args.model, effort=args.effort, mode=args.mode, variant=variant)
    elif args.framework == "metareview":
        from harnesseval.adapters import metareview as mrv
        run = mrv.review(pr, model=args.model, effort=args.effort, mode=args.mode)
    t0 = time.time()
    print(f"[run_one] review ({run.framework}/{run.execution_mode}): {len(run.findings)} findings, "
          f"{run.tokens_in:,}+{run.tokens_out:,} tok, {run.wall_ms:.0f}ms  err={run.error}")
    if run.error:
        print(f"[run_one] FAILED: {run.error}"); raise SystemExit(1)
    print(f"[run_one] raw review (first 300 chars):\n{run.raw_output[:300]}")

    # 2. judge findings vs golden (Martian JUDGE_PROMPT)
    goldens = pr.golden_comments
    cand_texts = [f.issue_text for f in run.findings]
    if not goldens or not cand_texts:
        print("[run_one] nothing to judge (no goldens or no findings)"); raise SystemExit(0)
    pairs = [(g["comment"], c) for g in goldens for c in cand_texts]
    from harnesseval import keys
    client = keys.anthropic_client()
    results = asyncio.run(judge_pairs(client, args.judge_model, pairs, concurrency=15))
    scored = score_from_matches(goldens, cand_texts, results)
    print(f"[run_one] SCORED: TP={scored['tp']} FP={scored['fp']} FN={scored['fn']}  "
          f"prec={scored['precision']:.3f} rec={scored['recall']:.3f}")
    if scored["true_positives"]:
        print(f"[run_one] a TP: {scored['true_positives'][0]['golden_comment'][:80]}")
        print(f"   matched: {scored['true_positives'][0]['matched_candidate'][:80]}")
    if scored["false_negatives"]:
        print(f"[run_one] a FN (missed golden): {scored['false_negatives'][0]['golden_comment'][:100]}")

    # 3. register the run
    summary = {"url": args.url, "framework": run.framework, "model": run.model, "effort": run.effort,
               "mode": run.execution_mode, "tp": scored["tp"], "fp": scored["fp"], "fn": scored["fn"],
               "precision": scored["precision"], "recall": scored["recall"],
               "tokens_in": run.tokens_in, "tokens_out": run.tokens_out, "wall_ms": run.wall_ms,
               "n_findings": len(run.findings), "n_golden": len(goldens),
               "findings": cand_texts, "raw_review": run.raw_output[:2000]}
    rid = register(phase="B", model=run.model, framework=run.framework, effort=args.effort,
                   run_n=1, status="pass",
                   metrics={"tp": scored["tp"], "fp": scored["fp"], "fn": scored["fn"],
                            "precision": scored["precision"], "recall": scored["recall"],
                            "n_findings": len(run.findings)},
                   tokens_in=run.tokens_in, tokens_out=run.tokens_out,
                   wall_s=run.wall_ms / 1000, summary=summary)
    print(f"[run_one] registered run {rid}")


if __name__ == "__main__":
    main()
