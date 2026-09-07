#!/usr/bin/env python3
"""Honest re-adjudication: correct two systematic biases in the original hallucination scoring.

Diagnosed 2026-09-06 on run 37fce30f7003 (mrv x glm-5.3 smoke, PR 11059):
  1. DIFF TRUNCATION — the original adjudicator saw diff[:30000]; on the largest top-6 PRs that
     hides 15-41% of the diff, so findings referencing hidden code were rejected as
     "speculation about code not in the diff". Pilot: 14 of 40 rejections flipped to REAL
     with the full diff.
  2. PARSE-FAILURE TAX — gpt-5.2's reasoning consumed the 1024-token budget -> empty JSON ->
     the finding was counted as a HALLUCINATION with no verdict at all (the red flag
     documented in adjudicate.py's own comment). Pilot: 14 of 40 were parse failures;
     11 of 14 resolved REAL at max_tokens=4096.

Corrections applied here: FULL diff + max_tokens=4096. Parse failures are counted as
UNRESOLVED (reported separately, NOT as hallucination). Everything else is identical to the
original pass: same per-cell cross-family judge, same prompt, effort=medium, 0.7 threshold.

Scope: only findings the primary judge left unmatched AND the original pass ruled
hallucination. TP and real_but_ungold verdicts stand (they passed under a STRICTER context).

Usage:
  uv run python readjudicate.py --run <run_id>            # one run
  uv run python readjudicate.py --batch <batch> [--limit N] [--dry-run]
Output: runs/<id>/readjudication.json (original summaries untouched); resume-safe.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.adjudicate import ADJUDICATE_PROMPT, ADJUDICATE_SYSTEM
from harnesseval.model_router import call_model_json

REAL_THRESHOLD = 0.7
MAX_TOKENS = 4096
DIFF_LIMIT = 1_000_000  # full diff


def latest_pass_summaries(batch: str) -> list[tuple[str, dict]]:
    """Latest pass run per (framework, model, effort, url) — the report's published selection."""
    best = {}
    for line in open("runs/registry.jsonl"):
        if batch not in line:
            continue
        d = json.loads(line)
        if d.get("status") != "pass" or not d.get("summary_path"):
            continue
        try:
            s = json.load(open(d["summary_path"]))
        except Exception:
            continue
        if not s.get("url"):
            continue
        best[(d["framework"], d["model"], d["effort"], s["url"])] = (d["run_id"], s)
    return sorted(best.values(), key=lambda t: t[0])


async def readjudicate_run(run_id: str, s: dict, concurrency: int = 15) -> dict | None:
    out_path = Path(f"runs/{run_id}/readjudication.json")
    recs = s.get("adjudication_records") or []
    halls = [r for r in recs if r.get("primary_judge_verdict") == "hallucination"]
    if not halls:
        return None
    if out_path.exists():
        return json.load(open(out_path))  # resume: already done

    url = s["url"]
    diff = fetch_diff(url)["diff"]
    judge = s.get("adjudicating_judge") or "gpt-5.2"
    tp, fn = s["tp"], s["fn"]
    orig_real = s.get("n_real_ungold", 0)

    sem = asyncio.Semaphore(concurrency)

    async def adj(cand: str):
        async with sem:
            for attempt in (1, 2):
                try:
                    parsed, _, _, _ = await call_model_json(
                        judge, ADJUDICATE_SYSTEM,
                        ADJUDICATE_PROMPT.format(diff=diff[:DIFF_LIMIT], candidate=cand),
                        effort="medium", max_tokens=MAX_TOKENS)
                    if parsed:
                        conf = float(parsed.get("confidence", 0.0) or 0.0)
                        verdict = ("real_but_ungold" if parsed.get("is_real") and conf >= REAL_THRESHOLD
                                   else "hallucination")
                        return {"verdict": verdict, "confidence": conf,
                                "rationale": str(parsed.get("reasoning", ""))[:400]}
                except Exception as e:
                    last = f"{type(e).__name__}: {str(e)[:100]}"
                    await asyncio.sleep(2 * attempt)
            return {"verdict": "unresolved", "confidence": None, "rationale": "adjudicator-failure"}

    t0 = time.time()
    verdicts = await asyncio.gather(*[adj(r["issue_text"]) for r in halls])

    new_real = new_hall = unresolved = 0
    records = []
    for r, v in zip(halls, verdicts):
        verdict = v.get("verdict", "unresolved")
        if verdict == "real_but_ungold":
            new_real += 1
        elif verdict == "hallucination":
            new_hall += 1
        else:
            unresolved += 1
        records.append({"issue_text": r["issue_text"], "source_lens": r.get("source_lens"),
                        "old_verdict": "hallucination", "new_verdict": verdict,
                        "confidence": v.get("confidence"), "rationale": v.get("rationale", "")})

    corrected = {
        "n_readjudicated": len(halls), "flipped_to_real": new_real,
        "n_real_ungold": orig_real + new_real, "n_hallucination": new_hall,
        "n_unresolved": unresolved,
        "adj_p": round(tp / (tp + new_hall), 4) if (tp + new_hall) else 0.0,
        "incr": round((tp + orig_real + new_real) / (tp + fn + orig_real + new_real), 4) if (tp + fn) else 0.0,
        "judge": judge, "diff_chars": len(diff), "wall_s": round(time.time() - t0, 1),
    }
    obj = {"run_id": run_id, "url": s.get("url"), "framework": s.get("framework"),
           "model": s.get("model"), "effort": s.get("effort"),
           "original": {"n_real_ungold": orig_real, "n_hallucination": s.get("n_hallucination", 0),
                        "adj_p": s.get("adjudicated_precision"), "incr": s.get("incremental_recall"),
                        "tp": s.get("tp"), "fn": s.get("fn")},
           "corrected": corrected, "records": records}
    out_path.write_text(json.dumps(obj, indent=1))
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="single run id")
    ap.add_argument("--batch", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.run:
        s = json.load(open(f"runs/{args.run}/summary.json"))
        r = asyncio.run(readjudicate_run(args.run, s, args.concurrency))
        print(json.dumps(r["corrected"], indent=1) if r else "no hallucinations to re-adjudicate")
        return

    if not args.batch:
        raise SystemExit("either --run or --batch is required")
    targets = [(rid, s) for rid, s in latest_pass_summaries(args.batch) if s.get("n_hallucination", 0) > 0]
    if args.limit:
        targets = targets[:args.limit]
    total_halls = sum(s.get("n_hallucination", 0) for _, s in targets)
    print(f"[re-adj] {len(targets)} published-selection runs, {total_halls} hallucinations to re-adjudicate")
    if args.dry_run:
        for rid, s in targets:
            print(f"  {rid[:8]} {s.get('framework','?')[:16]}/{s.get('model','?')[:18]}/{s.get('effort')}"
                  f" hal={s.get('n_hallucination')}")
        return
    for i, (rid, s) in enumerate(targets):
        try:
            r = asyncio.run(readjudicate_run(rid, s, args.concurrency))
            if r:
                c, o = r["corrected"], r["original"]
                print(f"  [{i+1}/{len(targets)}] {rid[:8]} {s.get('framework','?')[:14]}/{s.get('model','')[:16]}"
                      f" adj_p {o['adj_p']:.2f}->{c['adj_p']:.2f}"
                      f" real {o['n_real_ungold']}->{c['n_real_ungold']}"
                      f" hal {o['n_hallucination']}->{c['n_hallucination']}"
                      f" (unresolved {c['n_unresolved']}, {c['wall_s']}s)")
        except Exception as e:
            print(f"  [{i+1}/{len(targets)}] {rid[:8]} ERROR {type(e).__name__}: {str(e)[:120]}")


if __name__ == "__main__":
    main()
