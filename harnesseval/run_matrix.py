"""Run multiple frameworks across multiple PRs, with adjudication + score decomposition.

Phase B expansion: prove the recall/precision/cost pattern holds across the HARDEST PRs
and measure variance. For each (PR, framework): fetch diff -> review -> extract -> judge ->
score -> adjudicate FPs (real-but-ungold vs hallucination) -> decompose metareview into
deterministic_gate_recall + llm_lens_recall. Registers every run.

Usage:
  uv run python -m harnesseval.run_matrix --prs 5 --frameworks vanilla-engineered,metareview
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
from harnesseval.adjudicate import reclassify
from harnesseval.runs import register


def _pr_sample(url: str) -> PRSample:
    gc = martian.golden_comments_by_url()
    bdata = json.load(open(martian.OFFLINE / "results" / "benchmark_data.json"))
    entry = bdata.get(url, {})
    d = fetch_diff(url)
    return PRSample(url=url, pr_title=entry.get("pr_title", ""), source_repo=entry.get("source_repo", ""),
                    diff=d["diff"], files=d["files"], golden_comments=gc.get(url, []))


def _decompose(scored: dict, findings) -> dict:
    """Split metareview TP by source: deterministic_gate vs llm_lens (SPEC §6.3)."""
    det_sources = {f.source for f in findings if "deterministic" in (f.source or "")}
    lens_sources = {f.source for f in findings if "lens" in (f.source or "")}
    # a TP is "deterministic" if its matched_candidate came from a deterministic-source finding
    cand_source = {f.issue_text: f.source for f in findings}
    det_tp = lens_tp = 0
    for tp in scored.get("true_positives", []):
        src = cand_source.get(tp.get("matched_candidate", ""), "")
        if "deterministic" in src: det_tp += 1
        elif "lens" in src: lens_tp += 1
    total_golden = scored.get("total_golden", 0)
    n_fn = scored.get("fn", 0)
    return {"deterministic_tp": det_tp, "llm_lens_tp": lens_tp,
            "deterministic_gate_recall": det_tp / total_golden if total_golden else 0.0,
            "llm_lens_recall": lens_tp / total_golden if total_golden else 0.0,
            "n_det_findings": len(det_sources), "n_lens_findings": len(lens_sources)}


def _run_one_cell(pr: PRSample, framework: str, model: str, effort: str, mode: str,
                  judge_model: str) -> dict:
    """One (PR, framework) cell. Returns full result incl adjudication + decomposition."""
    from harnesseval.adapters import vanilla, metareview as mrv
    if framework.startswith("vanilla-"):
        variant = "naive" if framework == "vanilla-naive" else "engineered"
        run = vanilla.review(pr, model=model, effort=effort, mode=mode, variant=variant)
    elif framework == "metareview":
        run = mrv.review(pr, model=model, effort=effort, mode=mode)
    else:
        raise ValueError(framework)
    if run.error:
        return {"framework": framework, "url": pr.url, "error": run.error,
                "tokens_in": run.tokens_in, "tokens_out": run.tokens_out, "wall_ms": run.wall_ms}

    goldens = pr.golden_comments
    cand_texts = [f.issue_text for f in run.findings]
    if not goldens or not cand_texts:
        return {"framework": framework, "url": pr.url, "error": "nothing to judge",
                "tp": 0, "fp": 0, "fn": len(goldens), "tokens_in": run.tokens_in,
                "tokens_out": run.tokens_out, "wall_ms": run.wall_ms, "n_findings": len(run.findings)}
    pairs = [(g["comment"], c) for g in goldens for c in cand_texts]
    from harnesseval import keys
    client = keys.anthropic_client()
    results = asyncio.run(judge_pairs(client, judge_model, pairs, concurrency=15))
    scored = score_from_matches(goldens, cand_texts, results)

    # adjudicate the false positives (the "are these FPs real?" answer)
    adjudicated = reclassify(scored, cand_texts, pr.diff, model=judge_model)

    # decompose (only meaningful for metareview, computed for all)
    decomp = _decompose(adjudicated, run.findings)

    return {"framework": framework, "url": pr.url, "pr_title": pr.pr_title,
            "tp": scored["tp"], "fp": scored["fp"], "fn": scored["fn"],
            "precision": scored["precision"], "recall": scored["recall"],
            "n_findings": len(run.findings), "n_golden": len(goldens),
            "tokens_in": run.tokens_in, "tokens_out": run.tokens_out, "wall_ms": run.wall_ms,
            "raw_review": run.raw_output[:3000],
            # adjudication
            "real_but_ungold": adjudicated.get("real_but_ungold", []),
            "hallucination": adjudicated.get("hallucination", []),
            "adjudicated_precision": adjudicated.get("adjudicated_precision", 0.0),
            "incremental_recall": adjudicated.get("incremental_recall", 0.0),
            # decomposition
            "decomposition": decomp,
            "findings": [{"issue_text": f.issue_text, "source": f.source} for f in run.findings]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prs", type=int, default=5, help="number of hardest PRs to run")
    ap.add_argument("--frameworks", default="vanilla-engineered,metareview")
    ap.add_argument("--model", default="claude-opus-4-5-20251101")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--mode", default="api", choices=["api", "cli"])
    ap.add_argument("--judge-model", default="claude-opus-4-5-20251101")
    ap.add_argument("--out", default="results/phase_b_matrix.json")
    args = ap.parse_args()

    # hardest PRs by (severity-weighted golden count)
    import glob
    rows = []
    for f in glob.glob(str(martian.GOLDEN_DIR / "*.json")):
        for pr in json.load(open(f)):
            cs = pr.get("comments", [])
            sev_w = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            score = sum(sev_w.get(c.get("severity", "Low"), 1) for c in cs)
            rows.append((score, len(cs), pr["url"]))
    rows.sort(reverse=True)
    urls = [u for _, _, u in rows[: args.prs]]
    frameworks = args.frameworks.split(",")
    print(f"[matrix] {len(urls)} hardest PRs x {len(frameworks)} frameworks = {len(urls)*len(frameworks)} cells")
    print(f"[matrix] model={args.model} judge={args.judge_model} mode={args.mode}")

    all_results = []
    for url in urls:
        pr = _pr_sample(url)
        print(f"\n[matrix] PR: {pr.url.split('/pull/')[-1]} — {pr.pr_title[:60]} ({len(pr.golden_comments)} golden, {len(pr.diff)}B diff)")
        for fw in frameworks:
            t0 = time.time()
            print(f"[matrix]   {fw} ...", end=" ", flush=True)
            res = _run_one_cell(pr, fw, args.model, args.effort, args.mode, args.judge_model)
            dt = time.time() - t0
            if "error" in res and res.get("tp") is None:
                print(f"ERROR ({dt:.0f}s): {res['error'][:80]}")
            else:
                print(f"TP={res['tp']} FP={res['fp']} FN={res['fn']} prec={res['precision']:.2f} rec={res['recall']:.2f} | "
                      f"adjud_prec={res['adjudicated_precision']:.2f} incr_rec={res['incremental_recall']:.2f} | "
                      f"real-ungold={len(res['real_but_ungold'])} halluc={len(res['hallucination'])} | "
                      f"{res['tokens_in']+res['tokens_out']:,}tok {dt:.0f}s")
            all_results.append(res)
            # register
            rid = register(phase="B", model=args.model, framework=fw, effort=args.effort, run_n=0,
                          status="pass" if res.get("tp") is not None else "fail",
                          metrics={"tp": res.get("tp",0), "fp": res.get("fp",0), "fn": res.get("fn",0),
                                   "precision": res.get("precision",0), "recall": res.get("recall",0),
                                   "adjudicated_precision": res.get("adjudicated_precision",0),
                                   "incremental_recall": res.get("incremental_recall",0),
                                   "n_real_ungold": len(res.get("real_but_ungold",[])),
                                   "n_hallucination": len(res.get("hallucination",[]))},
                          tokens_in=res.get("tokens_in",0), tokens_out=res.get("tokens_out",0),
                          wall_s=dt, summary=res)

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_results, indent=2))
    print(f"\n[matrix] all results -> {out}")
    # summary table
    print("\n[matrix] SUMMARY (per framework, summed across PRs):")
    for fw in frameworks:
        rs = [r for r in all_results if r["framework"] == fw and r.get("tp") is not None]
        if not rs: continue
        tp = sum(r["tp"] for r in rs); fp = sum(r["fp"] for r in rs); fn = sum(r["fn"] for r in rs)
        ru = sum(len(r["real_but_ungold"]) for r in rs); hal = sum(len(r["hallucination"]) for r in rs)
        tin = sum(r["tokens_in"] for r in rs); tout = sum(r["tokens_out"] for r in rs)
        prec = tp/(tp+fp) if (tp+fp) else 0; rec = tp/(tp+fn) if (tp+fn) else 0
        adj_prec = tp/(tp+hal) if (tp+hal) else 0
        incr_rec = (tp+ru)/((tp+fn+ru)) if (tp+fn+ru) else 0
        print(f"  {fw:20s} TP={tp} FP={fp} FN={fn} prec={prec:.2f} rec={rec:.2f} | "
              f"adj_prec={adj_prec:.2f} incr_rec={incr_rec:.2f} (real-ungold={ru} halluc={hal}) | "
              f"tokens={tin+tout:,}")


if __name__ == "__main__":
    main()
