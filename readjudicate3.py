#!/usr/bin/env python3
"""Honest re-adjudication v2: three-way finding classification + two bias fixes.

History of the measurement problem (all diagnosed on run 37fce30f7003, mrv x glm-5.3, PR 11059):
  v0 (original): adjudicator saw diff[:30000] + 1024 max_tokens; every unmatched finding that
     wasn't CONFIRMED a verifiable defect (conf >= 0.7) counted as "hallucination".
     -> 40 of 67 unmatched findings labeled hallucination.
  v1 (binary honest): full diff + 4096 tokens -> 16 hal / 51 real. But the rejections
     concentrated in testing-quality/completeness/scope/architecture lenses — real, specific,
     important review findings that are NOT "verifiable defects in the diff". Counting them as
     hallucinations conflates waste (fake findings) with breadth (real, useful, non-bug).
  v2 (this tool, three-way): every unmatched finding is classified as
       bug                — verifiable defect in the diff (golden-matched ones are TP)
       important_non_bug  — real, specific, grounded-in-this-diff review concern that is not a
                            defect: missing tests for new nontrivial behavior, completeness
                            gaps, scope/architecture risk. Cites specific diff code; generic
                            advice does NOT qualify.
       hallucination      — false, misreads the diff, fabricated behavior, pure style nit, vague.
     Judge instruction: plausible-but-unverifiable -> confidence < 0.5, not auto-reject.

Accounting (proposal to be validated on the full matrix):
  TRUE hallucinations = "hallucination" category  -> the only waste (precision tax)
  hidden findings     = bug_ungold + important_non_bug (both are real hidden findings;
                        reported separately so bug-recall and issue-recall are distinguishable)
  precision           = TP / (TP + true_hallucinations)
  unresolved          = adjudicator failures (reported separately, never a hallucination)

Usage:
  uv run python readjudicate.py --run <id>            # one run
  uv run python readjudicate.py --batch <id> [--limit N] [--dry-run]
Output: runs/<id>/readjudication3.json (original summaries untouched); resume-safe.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.model_router import call_model_json

V2_PROMPT = """You are verifying a code review finding against a PR diff. Classify the finding into exactly one category:

DIFF (unified):
```diff
{diff}
```

FINDING:
{candidate}

Categories:
- "bug": a real, verifiable defect introduced or exposed by this diff (correctness, security, data loss, broken behavior).
- "important_non_bug": a real, SPECIFIC, substantive review concern grounded in this diff that is not a defect — e.g. missing tests for newly added nontrivial logic, an incomplete migration, a scope/architecture risk created by the change. It must cite specific code in the diff. Generic advice ("add more tests", "consider refactoring") is NOT important_non_bug — that is "hallucination"-grade noise for this purpose.
- "hallucination": false, misreads the diff, references behavior that does not exist, pure style/format nit, or too vague to act on.

Rules: judge ONLY what the diff shows. If the finding is plausible but you cannot verify it from the diff, return "bug" with confidence < 0.5 rather than rejecting it. Respond with ONLY:
{{"category": "bug|important_non_bug|hallucination", "reasoning": "brief, grounded in the diff", "confidence": 0.0-1.0}}"""

V2_SYSTEM = "You are a strict code review verifier. Always respond with valid JSON."
MAX_TOKENS = 4096
DIFF_LIMIT = 1_000_000  # full diff
CONF_FLOOR = 0.5  # below this, a "bug"/"important" verdict is downgraded to unresolved (unverifiable)


def latest_pass_summaries(batch: str) -> list[tuple[str, dict]]:
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


async def classify_run(run_id: str, s: dict, concurrency: int) -> dict | None:
    out_path = Path(f"runs/{run_id}/readjudication3.json")
    if out_path.exists():
        return json.load(open(out_path))  # resume-safe
    recs = s.get("adjudication_records") or []
    unmatched = [r for r in recs if r.get("primary_judge_verdict") in ("hallucination", "real_but_ungold")]
    if not unmatched:
        return None
    url = s["url"]
    diff = fetch_diff(url)["diff"]
    judge = s.get("adjudicating_judge") or "gpt-5.2"
    tp, fn = s["tp"], s["fn"]
    orig_real = s.get("n_real_ungold", 0)   # v1's real_but_ungold (bug-only standard)
    orig_hal = s.get("n_hallucination", 0)

    sem = asyncio.Semaphore(concurrency)

    async def adj(cand: str):
        async with sem:
            for attempt in (1, 2):
                try:
                    parsed, _, _, _ = await call_model_json(
                        judge, "You are a strict code review verifier. Always respond with valid JSON.",
                        V2_PROMPT.format(diff=diff[:DIFF_LIMIT], candidate=cand),
                        effort="medium", max_tokens=MAX_TOKENS)
                    if parsed:
                        cat = str(parsed.get("category") or "").strip().lower()
                        conf = float(parsed.get("confidence", 0.0) or 0.0)
                        if cat not in ("bug", "important_non_bug", "hallucination"):
                            return {"verdict": "unresolved", "confidence": None, "rationale": f"bad category: {cat!r}"}
                        if cat in ("bug", "important_non_bug") and conf < CONF_FLOOR:
                            # prompt tells the judge: unverifiable -> low confidence. A low-confidence
                            # positive is NOT evidence; count it unresolved rather than hidden gold.
                            return {"verdict": "unresolved", "confidence": conf,
                                    "rationale": f"below CONF_FLOOR ({conf:.2f})"}
                        return {"verdict": cat, "confidence": conf,
                                "rationale": str(parsed.get("reasoning", ""))[:400]}
                except Exception:
                    await asyncio.sleep(2 * attempt)
            return {"verdict": "unresolved", "confidence": None, "rationale": "adjudicator-failure"}

    t0 = time.time()
    verdicts = await asyncio.gather(*[adj(r["issue_text"]) for r in unmatched])

    records = [{"issue_text": r["issue_text"], "source_lens": r.get("source_lens"),
                "old_verdict": r.get("primary_judge_verdict"), "new_verdict": v.get("verdict", "unresolved"),
                "confidence": v.get("confidence"), "rationale": v.get("rationale", "")}
               for r, v in zip(unmatched, verdicts)]
    n_bug = sum(1 for x in records if x["new_verdict"] == "bug")
    n_imp = sum(1 for x in records if x["new_verdict"] == "important_non_bug")
    n_hal = sum(1 for x in records if x["new_verdict"] == "hallucination")
    n_unres = sum(1 for x in records if x["new_verdict"] == "unresolved")

    # v2 is the single source of truth for ALL unmatched findings (old halls AND old
    # real_but_ungold were both re-judged under full context). The old ruling was made under a
    # truncated diff, so v2 may demote an old "real" to hallucination or refine bug <-> important.
    from collections import Counter
    flips = Counter((x["old_verdict"], x["new_verdict"]) for x in records)
    corrected = {
        "n_unmatched": len(unmatched), "rejudged": len(unmatched),
        "n_bug_ungold": n_bug, "n_important": n_imp, "n_true_hallucination": n_hal,
        "n_unresolved": n_unres,
        "n_hidden_findings_unmatched": n_bug + n_imp,
        "waste_precision": round(tp / (tp + n_hal), 4) if (tp + n_hal) else 0.0,
        "flips": {f"{a}->{b}": n for (a, b), n in sorted(flips.items())},
        "judge": judge, "diff_chars": len(diff), "wall_s": round(time.time() - t0, 1),
    }
    obj = {"run_id": run_id, "url": s.get("url"), "framework": s.get("framework"),
           "model": s.get("model"), "effort": s.get("effort"),
           "original": {"tp": s.get("tp"), "fn": s.get("fn"),
                        "n_real_ungold": s.get("n_real_ungold", 0),
                        "n_hallucination": s.get("n_hallucination", 0),
                        "adj_p": s.get("adjudicated_precision"), "incr": s.get("incremental_recall")},
           "corrected": corrected, "records": records}
    out_path.write_text(json.dumps(obj, indent=1))
    return obj


def latest_pass_summaries(batch: str) -> list[tuple[str, dict]]:
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--batch", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.run:
        s = json.load(open(f"runs/{args.run}/summary.json"))
        r = asyncio.run(classify_run(args.run, s, args.concurrency))
        print(json.dumps(r["corrected"], indent=1) if r else "nothing to classify")
        return

    if not args.batch:
        raise SystemExit("either --run or --batch required")
    targets = [(rid, s) for rid, s in latest_pass_summaries(args.batch)
               if (s.get("n_hallucination", 0) + s.get("n_real_ungold", 0)) > 0]
    if args.limit:
        targets = targets[:args.limit]
    total = sum(s.get("n_hallucination", 0) + s.get("n_real_ungold", 0) for _, s in targets)
    print(f"[v2] {len(targets)} runs, {total} unmatched findings to classify (batch {args.batch})")
    if args.dry_run:
        for rid, s in targets:
            print(f"  {rid[:8]} {s.get('framework','?')[:16]}/{s.get('model','?')[:20]}/{s.get('effort')}")
        return
    for i, (rid, s) in enumerate(targets):
        out = Path(f"runs/{rid}/readjudication3.json")
        if out.exists():
            continue
        try:
            r = asyncio.run(classify_run(rid, s, args.concurrency))
            if r:
                c = r["corrected"]
                print(f"  [{i+1}/{len(targets)}] {rid[:8]} {s.get('framework','?')[:14]}/{s.get('model','')[:16]}"
                      f" hal {s.get('n_hallucination')}->{c['n_true_hallucination']}"
                      f" bug+{c['n_bug_ungold']} important+{c['n_important']}"
                      f" unres {c['n_unresolved']} ({c['wall_s']}s)", flush=True)
        except Exception as e:
            print(f"  [{i+1}/{len(targets)}] {rid[:8]} ERROR {type(e).__name__}: {str(e)[:120]}", flush=True)


if __name__ == "__main__":
    main()
