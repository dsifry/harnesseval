"""Phase A.1 — Martian judge/scorer reproduction (the calibration gate).

Strategy (budget-aware, per docs/PLAN.md "sample if budget-bound"):
  We do NOT re-judge all 38,402 pairs. We re-judge a PILOT set of (url, tool) pairs with our
  Anthropic judge (Opus 4.5, matching Martian's headline judge) and compare:
    (a) pairwise match/no-match agreement vs their stored evaluations.json, and
    (b) per-(url,tool) TP/FP/FN vs theirs (the ±2 gate).
  Their stored true_positives[].matched_candidate reconstructs their per-pair decisions, so
  we can measure agreement without re-running their judge.

Usage:
  uv run python -m harnesseval.calibrate --pilot-prs 2     # tiny: validate code + cost
  uv run python -m harnesseval.calibrate --pilot-prs 5     # expand once code validated
  uv run python -m harnesseval.calibrate --judge sonnet     # cross-check judge
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path

from harnesseval import keys
from harnesseval.dataset import martian
from harnesseval.judge import judge_pairs, score_from_matches, JUDGE_SYSTEM


def their_pair_decisions(their_eval: dict, candidates: list[dict], golden: list[dict]) -> dict[tuple[str, str], bool]:
    """Reconstruct their per-(golden, candidate) match decisions from stored TP/FP/FN.

    Martian uses GREEDY best-confidence matching: each matched golden has exactly one
    matched_candidate (from true_positives). So (golden, candidate)=True IFF candidate is
    THAT golden's matched_candidate — NOT merely "candidate matched some golden".
    """
    matched_pairs = set()
    for tp in their_eval.get("true_positives", []):
        gc = tp.get("golden_comment"); mc = tp.get("matched_candidate")
        if gc and mc:
            matched_pairs.add((gc, mc))
    out = {}
    for g in golden:
        for c in candidates:
            out[(g["comment"], c["text"])] = (g["comment"], c["text"]) in matched_pairs
    return out


def run_pilot(judge_key: str, pilot_pairs: list[tuple[str, str]], concurrency: int = 20) -> dict:
    """Re-judge selected (url, tool) pairs and compare to shipped decisions."""
    goldens = martian.golden_comments_by_url()
    candidates_all = martian.candidates_by_url(judge_key)
    dedup_all = martian.dedup_groups_by_url(judge_key)
    shipped = martian.shipped_evaluations(judge_key)

    model = martian.ANTHROPIC_JUDGE_IDS[judge_key]
    client = keys.anthropic_client()

    all_pairs, pair_meta, per_url_tool = [], [], []
    for url, tool in pilot_pairs:
        golden = goldens.get(url, [])
        cands = candidates_all.get(url, {}).get(tool, [])
        if not golden or not cands or tool not in shipped.get(url, {}):
            continue
        cand_texts = [c["text"] for c in cands if c.get("text")]
        if not cand_texts:
            continue
        for g in golden:
            for c in cand_texts:
                all_pairs.append((g["comment"], c))
                pair_meta.append((url, tool, g["comment"], c))
        per_url_tool.append((url, tool, golden, cand_texts))

    print(f"[pilot] judge={model}  (url,tool) pairs={len(per_url_tool)}  judge calls={len(all_pairs)}")
    t0 = time.time()
    results = asyncio.run(judge_pairs(client, model, all_pairs, concurrency=concurrency))
    dt = time.time() - t0
    n_err = sum(1 for r in results if r.error)
    print(f"[pilot] judged {len(results)} pairs in {dt:.1f}s  ({len(results)/max(dt,1):.0f}/s)  errors={n_err}")

    # Pairwise agreement vs their stored decisions
    their_decisions = {(url, tool): their_pair_decisions(shipped[url][tool], candidates_all[url][tool], goldens[url])
                       for url, tool, _, _ in per_url_tool}
    agree = disagree = 0
    disagreements = []
    for (url, tool, g, c), r in zip(pair_meta, results):
        if r.error:
            continue
        theirs = their_decisions[(url, tool)].get((g, c))
        ours = bool(r.match)
        if ours == theirs:
            agree += 1
        else:
            disagree += 1
            disagreements.append({"url": url, "tool": tool, "golden": g[:120],
                                 "candidate": c[:120], "ours": ours, "theirs": theirs,
                                 "confidence": r.confidence, "reasoning": (r.reasoning or "")[:160]})
    total_cmp = agree + disagree
    agreement = agree / total_cmp if total_cmp else 0.0
    print(f"[pilot] PAIRWISE AGREEMENT: {agree}/{total_cmp} = {agreement:.4f}  (disagreements={disagree})")

    # Per-(url,tool) TP/FP/FN comparison
    pair_results_by_ut = defaultdict(list)
    for (url, tool, g, c), r in zip(pair_meta, results):
        pair_results_by_ut[(url, tool)].append(r)
    print(f"[pilot] per-(url,tool) TP/FP/FN  ours vs theirs (Δ must be ≤ ±2):")
    max_abs_delta = 0
    for url, tool, golden, cand_texts in per_url_tool:
        ut_results = []
        idx = 0
        for g in golden:
            for c in cand_texts:
                ut_results.append(pair_results_by_ut[(url, tool)][idx]); idx += 1
        groups = dedup_all.get(url, {}).get(tool)
        ours = score_from_matches(golden, cand_texts, ut_results, groups)
        theirs = shipped[url][tool]
        dt_ = ours["tp"] - theirs["tp"]; df_ = ours["fp"] - theirs["fp"]; dn_ = ours["fn"] - theirs["fn"]
        max_abs_delta = max(max_abs_delta, abs(dt_), abs(df_), abs(dn_))
        print(f"   {tool:24s}  ours(tp={ours['tp']},fp={ours['fp']},fn={ours['fn']})  "
              f"theirs(tp={theirs['tp']},fp={theirs['fp']},fn={theirs['fn']})  Δ=({dt_:+d},{df_:+d},{dn_:+d})")
    print(f"[pilot] max |Δ| across (url,tool): {max_abs_delta}")
    # PRIMARY gate = aggregate TP/FP/FN within ±2 (the eval's actual metric). Martian judged via
    # their proxy (api.withmartian.com) with the same Opus 4.5 model; we use native Anthropic — same
    # weights, different API path. Pairwise <95% is expected: (a) proxy-vs-native path differences,
    # (b) greedy scoring credits ONE candidate per golden, so semantically-equivalent duplicate
    # candidates are 'theirs=False' pairwise but not FPs in aggregate. So pairwise is DIAGNOSTIC.
    aggregate_pass = max_abs_delta <= 2
    pairwise_pass = agreement >= 0.80  # diagnostic threshold (95% unreachable/meaningless per above)
    passed = aggregate_pass and pairwise_pass
    print(f"[pilot] GATE  PRIMARY aggregate max|Δ|≤2: {'PASS ✅' if aggregate_pass else 'FAIL ❌'} ({max_abs_delta})")
    print(f"[pilot] GATE  diagnostic pairwise ≥0.80: {'PASS ✅' if pairwise_pass else 'FAIL ❌'} ({agreement:.4f}; 95% is not achievable/meaningful)")
    return {"judge": model, "pilot_pairs": len(per_url_tool), "judge_calls": len(all_pairs),
            "agreement": agreement, "max_abs_delta": max_abs_delta, "passed": passed,
            "aggregate_pass": aggregate_pass, "pairwise_pass": pairwise_pass,
            "errors": n_err, "wall_s": dt, "disagreements": disagreements}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=5,
                    help="number of (url,tool) pairs to re-judge (budget-smart; ~$1/pair)")
    ap.add_argument("--judge", choices=["opus", "sonnet"], default="opus")
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--out", default="results/phase_a1_pilot.json")
    args = ap.parse_args()

    cands = martian.candidates_by_url(args.judge)
    shipped = martian.shipped_evaluations(args.judge)
    goldens = martian.golden_comments_by_url()
    all_ut = [(url, tool) for url, tools in cands.items() for tool in tools
              if tool in shipped.get(url, {})]
    # spread selection across distinct tools for representativeness, then fill by size
    seen: set[str] = set()
    selected: list[tuple[str, str]] = []
    rest: list[tuple[str, str]] = []
    for ut in all_ut:
        (selected if ut[1] not in seen else rest).append(ut)
        seen.add(ut[1])
    selected = (selected + rest)[: args.pairs]
    est = sum(len(goldens.get(u, [])) * len(cands[u][t]) for u, t in selected)
    print(f"[pilot] selected {len(selected)} (url,tool) pairs across {len({t for _, t in selected})} tools; "
          f"est judge calls ≈ {est}")
    summary = run_pilot(args.judge, selected, concurrency=args.concurrency)

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"[pilot] summary written to {out}")
    print("[pilot] If PASS and cost acceptable, expand: --pairs 20, then toward full reproduction.")
    raise SystemExit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
