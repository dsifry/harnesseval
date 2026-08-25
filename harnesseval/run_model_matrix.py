"""Run the (model x effort) matrix across hard PRs for vanilla vs metareview.

Phase B signal-gathering run (per user 2026-08-22): the 6 hardest PRs across a variety of
models and effort levels, vanilla-engineered vs metareview. Judge layer = the calibrated
trio (claude-opus-4-5 / sonnet-4-5 / gpt-5.2); PRIMARY judge is cross-family to the
model-under-test (anti self-preference, SPEC §9). Effort axis = provider-native reasoning
knob (SPEC §6.1). Every run adjudicated (real-but-ungold vs hallucination) + decomposed
(deterministic_gate_recall vs llm_lens_recall).

Usage:
  uv run python -m harnesseval.run_model_matrix --prs 6 \
      --models claude-opus-4-5-20251101,claude-sonnet-4-5-20250929,gpt-5.2,glm-5.2-vision-flex,kimi-k3 \
      --efforts low,xhigh --frameworks vanilla-engineered,metareview
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
from harnesseval.judge import judge_pairs_router, score_from_matches
from harnesseval.adjudicate import reclassify_async
from harnesseval.runs import register

# Cross-family judge selection (SPEC §9): for a given under-test model, use a DIFFERENT family
# as the primary judge. claude-* -> gpt-5.2; gpt-* -> claude-opus-4-5; glm/kimi -> gpt-5.2.
def primary_judge(under_test_model: str) -> str:
    m = under_test_model.lower()
    if "claude" in m: return "gpt-5.2"               # OpenAI judges Anthropic
    if "gpt" in m:   return "claude-opus-4-5-20251101" # Anthropic judges OpenAI
    return "gpt-5.2"                                  # OpenAI judges GLM/Kimi


def _pr_sample(url: str) -> PRSample:
    gc = martian.golden_comments_by_url()
    bdata = json.load(open(martian.OFFLINE / "results" / "benchmark_data.json"))
    entry = bdata.get(url, {})
    d = fetch_diff(url)
    return PRSample(url=url, pr_title=entry.get("pr_title", ""), source_repo=entry.get("source_repo", ""),
                    diff=d["diff"], files=d["files"], golden_comments=gc.get(url, []))


def _decompose(scored, findings) -> dict:
    cand_source = {f.issue_text: f.source for f in findings}
    det_tp = lens_tp = 0
    for tp in scored.get("true_positives", []):
        src = cand_source.get(tp.get("matched_candidate", ""), "")
        if "deterministic" in src: det_tp += 1
        elif "lens" in src: lens_tp += 1
    total_golden = scored.get("total_golden", 0)
    return {"deterministic_tp": det_tp, "llm_lens_tp": lens_tp,
            "deterministic_gate_recall": det_tp / total_golden if total_golden else 0.0,
            "llm_lens_recall": lens_tp / total_golden if total_golden else 0.0}


def _diff_context_hash(diff: str) -> str:
    """SHA1 of the diff context the adjudicator saw (diff[:30000], matching adjudicate.py).
    Re-adjudication can verify it's re-judging the same context."""
    import hashlib
    return hashlib.sha1(diff[:30000].encode("utf-8", "replace")).hexdigest()


def _build_finding_records(run, scored, adjudicated, judge_model: str, diff: str) -> dict:
    """Per-finding adjudication records + per-golden match decisions (docs/METAREVIEW_IMPROVEMENTS.md
    Cross-cutting data needs #1-3). Lets stored findings be re-adjudicated later with a frontier
    panel WITHOUT re-running the framework: each finding carries its source-lens, matched-golden,
    primary-judge verdict, and adjudication verdict/confidence/rationale + the diff-context hash.
    """
    # candidate -> matched golden(s) + primary-judge confidence/reasoning (from the greedy match)
    cand_to_goldens: dict[str, list[dict]] = {}
    for tp in scored.get("true_positives", []):
        c = tp.get("matched_candidate")
        if c is None:
            continue
        cand_to_goldens.setdefault(c, []).append(
            {"golden_comment": tp.get("golden_comment"), "confidence": tp.get("confidence"),
             "reasoning": tp.get("reasoning")})
    # candidate -> adjudication verdict record
    ru_map = {r["candidate"]: r for r in adjudicated.get("real_but_ungold", [])}
    hal_map = {r["candidate"]: r for r in adjudicated.get("hallucination", [])}
    dch = _diff_context_hash(diff)
    records = []
    for f in run.findings:
        issue = f.issue_text
        matched = cand_to_goldens.get(issue)
        if matched:
            verdict = "matched"; adj = {"adjudicating_judge": None, "confidence": None, "rationale": None}
            matched_goldens = [m["golden_comment"] for m in matched]
            primary_conf = max((m["confidence"] for m in matched), default=None)
            primary_reason = next((m["reasoning"] for m in matched if m["reasoning"]), None)
        elif issue in ru_map:
            r = ru_map[issue]
            verdict = "real_but_ungold"
            adj = {"adjudicating_judge": judge_model, "confidence": r.get("confidence"),
                   "rationale": r.get("reasoning")}
            matched_goldens = None
            primary_conf = primary_reason = None
        elif issue in hal_map:
            r = hal_map[issue]
            verdict = "hallucination"
            adj = {"adjudicating_judge": judge_model, "confidence": r.get("confidence"),
                   "rationale": r.get("reasoning")}
            matched_goldens = None
            primary_conf = primary_reason = None
        else:
            verdict = "unjudged"  # shouldn't happen; every candidate is matched/ru/hal
            adj = {"adjudicating_judge": None, "confidence": None, "rationale": None}
            matched_goldens = None
            primary_conf = primary_reason = None
        records.append({
            "issue_text": issue, "source_lens": f.source, "file": f.file, "line": f.line,
            "severity": f.severity, "category": f.category,
            "matched_golden_ids": matched_goldens, "primary_judge_verdict": verdict,
            "primary_judge": judge_model if matched else None,
            "primary_judge_confidence": primary_conf, "primary_judge_reasoning": primary_reason,
            "adjudication": {"verdict": verdict, **adj, "diff_context_hash": dch},
        })
    per_golden_matches = list(scored.get("true_positives", [])) + list(scored.get("false_negatives", []))
    return {"adjudication_records": records, "per_golden_matches": per_golden_matches,
            "diff_context_hash": dch, "primary_judge": judge_model,
            "adjudicating_judge": judge_model}


def _run_cell(pr, framework, model, effort, judge_model) -> dict:
    """One cell, run in its own event loop (adapters + judge are async internally)."""
    return asyncio.run(_run_cell_async(pr, framework, model, effort, judge_model))


async def _run_cell_async(pr, framework, model, effort, judge_model, mode: str = "api") -> dict:
    from harnesseval.adapters import vanilla, metareview as mrv
    from harnesseval.adapters import metareview_realistic as mr
    from harnesseval.adapters import superpowers as sp, superpowers_realistic as spr
    from harnesseval.adapters import compound as cp, compound_realistic as cpr
    if framework == "vanilla-engineered":
        run = await vanilla.review_async(pr, model=model, effort=effort, mode=mode, variant="engineered")
    elif framework == "vanilla-naive":
        run = await vanilla.review_async(pr, model=model, effort=effort, mode=mode, variant="naive")
    elif framework == "metareview":
        run = await mrv.review_async(pr, model=model, effort=effort, mode=mode)
    elif framework == "metareview-realistic":
        run = await mr.review_realistic_async(pr, model=model, effort=effort)
    elif framework == "superpowers":
        run = await sp.review_async(pr, model=model, effort=effort, mode=mode)
    elif framework == "superpowers-realistic":
        run = await spr.review_realistic_async(pr, model=model, effort=effort)
    elif framework == "compound":
        run = await cp.review_async(pr, model=model, effort=effort, mode=mode)
    elif framework == "compound-realistic":
        run = await cpr.review_realistic_async(pr, model=model, effort=effort)
    else:
        raise ValueError(framework)
    if run.error:
        return {"error": run.error, "tokens_in": run.tokens_in, "tokens_out": run.tokens_out, "wall_ms": run.wall_ms, "execution_mode": run.execution_mode}
    goldens = pr.golden_comments
    cand_texts = [f.issue_text for f in run.findings]
    if not goldens or not cand_texts:
        return {"tp": 0, "fp": 0, "fn": len(goldens), "precision": 0, "recall": 0,
                "tokens_in": run.tokens_in, "tokens_out": run.tokens_out, "n_findings": len(run.findings),
                "adjudicated_precision": 0.0, "incremental_recall": 0.0,
                "n_real_ungold": 0, "n_hallucination": 0, "decomposition": {},
                "findings": [{"issue_text": f.issue_text, "source_lens": f.source} for f in run.findings],
                "goldens": [{"comment": g["comment"], "severity": g.get("severity"),
                             "category": g.get("category")} for g in goldens],
                "per_golden_matches": [], "adjudication_records": [],
                "diff_context_hash": _diff_context_hash(pr.diff),
                "primary_judge": judge_model, "adjudicating_judge": judge_model}
    pairs = [(g["comment"], c) for g in goldens for c in cand_texts]
    results = await judge_pairs_router(judge_model, pairs, concurrency=15)
    scored = score_from_matches(goldens, cand_texts, results)
    adjudicated = await reclassify_async(scored, cand_texts, pr.diff, model=judge_model)
    decomp = _decompose(adjudicated, run.findings)
    fr = _build_finding_records(run, scored, adjudicated, judge_model, pr.diff)
    return {"tp": scored["tp"], "fp": scored["fp"], "fn": scored["fn"],
            "precision": scored["precision"], "recall": scored["recall"],
            "n_findings": len(run.findings), "n_golden": len(goldens),
            "tokens_in": run.tokens_in, "tokens_out": run.tokens_out, "wall_ms": run.wall_ms,
            "per_model_usage": run.per_model_usage, "total_cost_usd": run.total_cost_usd,
            "resolved_model": run.model,
            "adjudicated_precision": adjudicated.get("adjudicated_precision", 0.0),
            "incremental_recall": adjudicated.get("incremental_recall", 0.0),
            "n_real_ungold": len(adjudicated.get("real_but_ungold", [])),
            "n_hallucination": len(adjudicated.get("hallucination", [])),
            "decomposition": decomp,
            # Per-finding adjudication records + per-golden match decisions + goldens, so stored
            # findings can be re-adjudicated with a frontier panel (opus-5/gpt-5.6-sol/Fable)
            # WITHOUT re-running the framework (docs/METAREVIEW_IMPROVEMENTS.md Cross-cutting #1-3).
            "findings": [{"issue_text": f.issue_text, "source_lens": f.source,
                          "file": f.file, "line": f.line, "severity": f.severity,
                          "category": f.category} for f in run.findings],
            "goldens": [{"comment": g["comment"], "severity": g.get("severity"),
                         "category": g.get("category")} for g in goldens],
            "per_golden_matches": fr["per_golden_matches"],
            "adjudication_records": fr["adjudication_records"],
            "diff_context_hash": fr["diff_context_hash"],
            "primary_judge": fr["primary_judge"], "adjudicating_judge": fr["adjudicating_judge"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prs", type=int, default=6)
    ap.add_argument("--models", default="claude-opus-5,gpt-5.6-sol,glm-5.2-vision-flex")
    # NOTE: models-UNDER-TEST are the NEWER set (SPEC §14.1): opus-5, codex 5.6-sol, glm. The OLD
    # trio (opus-4.5, sonnet-4.5, gpt-5.2) are JUDGE-only (calibrated, SPEC §9) - pass them via
    # --models only if deliberately re-running an anchor; primary_judge() routes them as judges.
    ap.add_argument("--efforts", default="low,xhigh")
    ap.add_argument("--frameworks", default="vanilla-engineered,metareview")
    ap.add_argument("--mode", default="api", choices=["api", "cli"], help="reviewer execution mode (cli=OAuth realistic)")
    ap.add_argument("--concurrency", type=int, default=4, help="max concurrent cells (cli: keep 3-4 to avoid rate limits)")
    ap.add_argument("--out", default="results/phase_b_model_matrix.json")
    ap.add_argument("--run-batch", default=None, help="reuse an existing run_batch id (for fill-ins of errored cells); default generates a new one")
    ap.add_argument("--fill", default=None, help="comma-sep list of fw/model/effort[/url-suffix] to run ONLY those cells (fill-in mode); adding the url-suffix (a substring of the PR url) targets one specific PR. e.g. compound-realistic/claude-opus-5/xhigh/11059")
    args = ap.parse_args()

    import glob
    rows = []
    for f in glob.glob(str(martian.GOLDEN_DIR / "*.json")):
        for pr in json.load(open(f)):
            cs = pr.get("comments", [])
            sev_w = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
            rows.append((sum(sev_w.get(c.get("severity", "Low"), 1) for c in cs), len(cs), pr["url"]))
    rows.sort(reverse=True)
    urls = [u for _, _, u in rows[: args.prs]]
    models = args.models.split(",")
    efforts = args.efforts.split(",")
    frameworks = args.frameworks.split(",")
    n_cells = len(urls) * len(models) * len(efforts) * len(frameworks)
    print(f"[mx] {len(urls)} PRs x {len(models)} models x {len(efforts)} efforts x {len(frameworks)} fw = {n_cells} cells")

    samples = {u: _pr_sample(u) for u in urls}
    # Build all cells, then run with bounded concurrency (parallel OAuth CLI sessions).
    cells = []
    fill = set()
    if args.fill:
        # each spec: fw/model/effort OR fw/model/effort/url-suffix (the url-suffix is a substring of the PR url)
        for x in args.fill.split(","):
            parts = x.split("/", 3)
            fill.add(tuple(parts))  # (fw, model, effort) or (fw, model, effort, url-suffix)
    for url in urls:
        pr = samples[url]
        for model in models:
            judge = primary_judge(model)
            for effort in efforts:
                for fw in frameworks:
                    if fill:
                        matched = False
                        pr_num = url.rstrip("/").rsplit("/", 1)[-1]
                        for spec in fill:
                            if len(spec) == 3 and (fw, model, effort) == spec:
                                matched = True; break
                            if len(spec) == 4 and (fw, model, effort) == spec[:3] and spec[3] == pr_num:
                                matched = True; break
                        if not matched:
                            continue
                    cells.append((pr, fw, model, effort, judge))
    print(f"[mx] running {len(cells)} cells with concurrency={args.concurrency} (mode={args.mode})")

    # one batch id for this whole matrix run — every cell registers with it so the run is
    # cleanly queryable later (runs.query(run_batch=...)) and failed cells can be targeted for rerun.
    import time as _t
    if args.run_batch:
        batch_id = args.run_batch
    else:
        batch_id = _t.strftime("%Y%m%d-%H%M%S", _t.gmtime()) + f"-{args.mode}-{len(cells)}cells"
    print(f"[mx] run_batch={batch_id}")

    async def run_all():
        sem = asyncio.Semaphore(args.concurrency)
        results = [None] * len(cells)
        async def run_one(i, pr, fw, model, effort, judge):
            async with sem:
                t0 = time.time()
                tag = f"[{i+1}/{len(cells)}] {fw} {model} {effort}"
                print(f"[mx] {tag} ...", flush=True)
                try:
                    res = await _run_cell_async(pr, fw, model, effort, judge, mode=args.mode)
                except Exception as e:
                    res = {"error": str(e)[:120]}
                dt = time.time() - t0
                if "error" in res and res.get("tp") is None:
                    print(f"[mx] {tag} ERR {dt:.0f}s: {res['error'][:70]}", flush=True)
                else:
                    print(f"[mx] {tag} TP={res['tp']} FP={res['fp']} FN={res['fn']} rec={res['recall']:.2f} "
                          f"adj_p={res['adjudicated_precision']:.2f} incr_r={res['incremental_recall']:.2f} "
                          f"real={res['n_real_ungold']} hal={res['n_hallucination']} "
                          f"{res['tokens_in']+res['tokens_out']:,}tok {dt:.0f}s", flush=True)
                res["url"] = pr.url; res["framework"] = fw; res["model"] = model
                res["effort"] = effort; res["judge"] = judge; res["wall_s"] = dt
                res.setdefault("execution_mode", args.mode)
                res["run_batch"] = batch_id
                # register
                register(phase="B", model=model, framework=fw, effort=effort, run_n=0,
                         status="pass" if res.get("tp") is not None else "fail",
                         metrics={"tp": res.get("tp",0), "fp": res.get("fp",0), "fn": res.get("fn",0),
                                  "precision": res.get("precision",0), "recall": res.get("recall",0),
                                  "adjudicated_precision": res.get("adjudicated_precision",0),
                                  "incremental_recall": res.get("incremental_recall",0),
                                  "n_real_ungold": res.get("n_real_ungold",0),
                                  "n_hallucination": res.get("n_hallucination",0)},
                         tokens_in=res.get("tokens_in",0), tokens_out=res.get("tokens_out",0),
                         wall_s=dt, summary=res, run_batch=batch_id)
                results[i] = res
        await asyncio.gather(*[run_one(i, *c) for i, c in enumerate(cells)])
        return [r for r in results if r]

    all_results = asyncio.run(run_all())

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_results, indent=2))
    print(f"\n[mx] {len(all_results)} cells -> {out}")

    # summary: per (framework, model, effort) summed across PRs
    print("\n[mx] SUMMARY (per fw/model/effort, summed across PRs):")
    print(f"{'fw':18s} {'model':30s} {'eff':5s} {'TP':>3} {'FP':>4} {'FN':>3} {'rec':>5} {'adj_p':>5} {'incr_r':>6} {'real':>4} {'hal':>4} {'tok':>8}")
    for fw in frameworks:
        for model in models:
            for effort in efforts:
                rs = [r for r in all_results if r["framework"]==fw and r["model"]==model and r["effort"]==effort and r.get("tp") is not None]
                if not rs: continue
                tp=sum(r["tp"] for r in rs); fp=sum(r["fp"] for r in rs); fn=sum(r["fn"] for r in rs)
                ru=sum(r["n_real_ungold"] for r in rs); hal=sum(r["n_hallucination"] for r in rs)
                tok=sum(r["tokens_in"]+r["tokens_out"] for r in rs)
                rec=tp/(tp+fn) if (tp+fn) else 0; ap_=tp/(tp+hal) if (tp+hal) else 0
                ir=(tp+ru)/((tp+fn+ru)) if (tp+fn+ru) else 0
                print(f"{fw:18s} {model:30s} {effort:5s} {tp:>3} {fp:>4} {fn:>3} {rec:>5.2f} {ap_:>5.2f} {ir:>6.2f} {ru:>4} {hal:>4} {tok:>8,}")


if __name__ == "__main__":
    main()
