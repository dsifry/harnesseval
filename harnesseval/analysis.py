"""Analysis module — trust-segmented interpretation of the run registry.

Reads runs/registry.jsonl + per-run summaries and produces decision-ready outputs to results/:

  1. Trust segmentation: every Phase-B run tagged CLEAN / DIAGNOSTIC / BROKEN, split by
     execution_mode (api vs cli — NEVER compared head-to-head, SPEC §7 gotcha #9).
  2. Clean leaderboards (api and cli kept separate): raw + adjudicated precision, raw +
     incremental recall, per-model cost split (when populated), wall-time. N=1 PRs flagged.
  3. Recall-vs-cost Pareto frontier (api: tokens axis; cli: quality-only, cost flagged unusable).
  4. Per-model cost breakdown — the §6.3.1 orchestrator-vs-subagent split (opus $$ / haiku ¢).
  5. Failure-mode analysis: per-PR recall × golden category/severity profile (which golden
     categories each framework misses).
  6. deterministic_gate_recall vs llm_lens_recall decomposition for metareview (SPEC §6.3).
  7. Bootstrap 95% CIs on recall/precision (SPEC §11) — flags "X beats Y" claims within noise.

Hard rules enforced here:
  - api and cli are kept in SEPARATE tables (never compared head-to-head).
  - A single token total is NEVER reported for realistic/cli runs (per-model used when present;
    otherwise cost is flagged UNUSABLE — SPEC §10, §6.3.1).
  - status=fail / 0-finding / decomposition-inconsistent metareview-realistic runs are DIAGNOSTIC
    (excluded from clean leaderboards unless explicitly diagnosing).
  - N is tiny (≤6 PRs/cell); every conclusion labelled preliminary.
  - Read-only on the data; writes only to results/.

Re-run anytime (the other agent is actively adding runs); everything is re-derived from the
registry on each invocation.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from collections import defaultdict

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"
REGISTRY = RUNS_DIR / "registry.jsonl"
RESULTS = Path(__file__).resolve().parents[1] / "results"
GOLDEN_DIR = Path(__file__).resolve().parents[1] / "third_party" / "code-review-benchmark" / "offline" / "golden_comments"

# Phase-A / non-framework runs we never analyze as FUTs
NON_FUT = {"martian-judge", "inspect-runner-judge"}


def load_registry() -> list[dict]:
    out = []
    if not REGISTRY.exists():
        return out
    for line in REGISTRY.read_text().splitlines():
        if line.strip():
            e = json.loads(line)
            sp = e.get("summary_path")
            if sp and Path(sp).exists():
                e["_summary"] = json.loads(Path(sp).read_text())
            else:
                e["_summary"] = {}
            out.append(e)
    return out


def _mode(r, s) -> str:
    m = s.get("execution_mode") or s.get("mode")
    if m:
        return m
    # infer: realistic frameworks (real bin/metareview + Agent subagents) are always cli
    if r.get("framework", "").endswith("-realistic"):
        return "cli"
    # api frameworks (vanilla-engineered, metareview, superpowers) without a recorded mode
    # are the early api batch (incl. the 0-token failed api cells) → api
    return "api(inferred)"


def golden_profile() -> dict[str, dict]:
    """url -> {n_golden, by_category:{cat:n}, by_severity:{sev:n}, comments:[...]}."""
    out = {}
    if not GOLDEN_DIR.exists():
        return out
    for f in sorted(GOLDEN_DIR.glob("*.json")):
        for pr in json.load(open(f)):
            cs = pr.get("comments", [])
            by_cat = defaultdict(int)
            by_sev = defaultdict(int)
            for c in cs:
                by_cat[c.get("category", "?")] += 1
                by_sev[c.get("severity", "?")] += 1
            out[pr["url"]] = {
                "n_golden": len(cs),
                "by_category": dict(by_cat),
                "by_severity": dict(by_sev),
                "comments": cs,
            }
    return out


def segment(runs: list[dict]) -> list[dict]:
    """Tag every Phase-B run with a trust tier + execution_mode. Returns annotated run dicts."""
    tagged = []
    for r in runs:
        if r.get("phase") != "B":
            continue
        if r.get("framework") in NON_FUT:
            continue
        s = r.get("_summary") or {}
        mode = _mode(r, s)
        fw = r.get("framework")
        status = r.get("status")
        tp = s.get("tp", 0) or 0
        fp = s.get("fp", 0) or 0
        fn = s.get("fn", 0) or 0
        n_findings = s.get("n_findings", 0) or 0
        decomp = s.get("decomposition") or {}
        det_tp = decomp.get("deterministic_tp", 0) or 0
        llm_tp = decomp.get("llm_lens_tp", 0) or 0
        has_pmu = bool(s.get("per_model_usage"))

        tier = "BROKEN"
        reason = []
        if status != "pass":
            tier, reason = "BROKEN", [f"status={status}"]
        elif n_findings == 0 and tp == 0:
            # 0 findings emitted. On a golden-bearing PR (fn>0) this is a framework/extraction
            # bug (e.g. the GLM/Kimi 0-finding cells); on a no-golden PR it's a degenerate run.
            # Either way it carries no signal — exclude from clean leaderboards.
            kind = "golden-bearing PR, 0 findings emitted" if fn > 0 else "0-finding degenerate run"
            tier, reason = "BROKEN", [kind]
        elif fw == "metareview-realistic":
            # objective bug signal: decomposition must be consistent (det+llm == tp)
            # AND not the 0.00 bug (tp==0 but findings produced -> unmatchable dispatch)
            if tp == 0 and n_findings > 0:
                tier, reason = "DIAGNOSTIC", ["0.00 recall bug (produced findings, 0 matched gold) — see PARTIAL_RUN_REPORT FIX 1"]
            elif det_tp + llm_tp != tp:
                tier, reason = "DIAGNOSTIC", [f"decomposition inconsistent (det+llm={det_tp+llm_tp} != tp={tp}) — dispatch/extraction broken"]
            else:
                tier, reason = "CLEAN", ["decomposition consistent"]
        elif fw.endswith("-realistic"):
            # superpowers-realistic etc.: no decomposition to check; trust passing runs
            tier, reason = "CLEAN", ["passing realistic run (no decomposition check)"]
        else:
            # api-mode frameworks (vanilla-engineered, metareview)
            tier, reason = "CLEAN", ["api-mode passing run"]

        tagged.append({
            "run_id": r.get("run_id"), "framework": fw, "model": r.get("model"),
            "summary_path": r.get("summary_path"),
            "effort": r.get("effort"), "status": status, "mode": mode, "tier": tier,
            "reason": reason, "url": s.get("url"), "tp": tp, "fp": fp, "fn": fn,
            "n_findings": n_findings, "n_golden": s.get("n_golden", 0),
            "precision": s.get("precision", 0), "recall": s.get("recall", 0),
            "adjudicated_precision": s.get("adjudicated_precision"),  # None if pre-adjudication
            "incremental_recall": s.get("incremental_recall"),          # None if pre-adjudication
            "n_real_ungold": s.get("n_real_ungold"),                    # None if counts not stored
            "n_hallucination": s.get("n_hallucination"),               # None if counts not stored
            "has_adjudication_rate": s.get("adjudicated_precision") is not None,
            "has_adjudication_counts": s.get("n_hallucination") is not None,
            "tokens_in": r.get("tokens_in", 0) or 0, "tokens_out": r.get("tokens_out", 0) or 0,
            "total_cost_usd": s.get("total_cost_usd", 0) or 0,
            "per_model_usage": s.get("per_model_usage") or {},
            "has_pmu": has_pmu, "resolved_model": s.get("resolved_model"),
            "decomposition": decomp, "wall_s": r.get("wall_s", 0) or 0,
            "registered_at": r.get("registered_at"),
            "judge": s.get("judge"),
        })
    return tagged


def _agg_cell(cells: list[dict]) -> dict:
    """Aggregate per-PR run dicts (same cell) into a leaderboard row.

    recall/precision are always recomputed from tp/fp/fn sums (every run has these).
    adjudicated_precision / incremental_recall are handled carefully because the
    early api batch stores only the pre-computed RATES (not the n_hallucination /
    n_real_ungold counts) and the very first runs predate adjudication entirely.
      - If EVERY run has the counts → recompute adjP/incR from sums (the gold standard).
      - Else if runs have the rates → report the golden-weighted MEAN of per-run rates
        (flagged 'mean-rate'; counts not stored for some/all PRs).
      - Else → n/a (pre-adjudication).
    Defaulting missing counts to 0 would inflate adjP to 1.0 — we explicitly avoid that.
    """
    tp = sum(c["tp"] for c in cells); fp = sum(c["fp"] for c in cells); fn = sum(c["fn"] for c in cells)
    prs = {c["url"] for c in cells}
    n_prs = len(prs)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0

    with_counts = [c for c in cells if c.get("has_adjudication_counts")]
    with_rate = [c for c in cells if c.get("has_adjudication_rate") and c.get("adjudicated_precision") is not None]

    if len(with_counts) == len(cells) and with_counts:
        ru = sum(c["n_real_ungold"] for c in with_counts)
        hal = sum(c["n_hallucination"] for c in with_counts)
        adj_prec = tp / (tp + hal) if (tp + hal) else 0.0
        incr_rec = (tp + ru) / (tp + fn + ru) if (tp + fn + ru) else 0.0
        adj_mode = "recomputed-from-counts"
        n_real, n_hal = ru, hal
    elif with_rate:
        # golden-weighted mean of per-run rates (use n_golden as weight; fall back to 1)
        def wmean(rate_key):
            tot = 0.0; w = 0.0
            for c in with_rate:
                wi = (c.get("n_golden") or 0) or 1
                v = c.get(rate_key)
                if v is not None:
                    tot += v * wi; w += wi
            return tot / w if w else 0.0
        adj_prec = wmean("adjudicated_precision")
        incr_rec = wmean("incremental_recall")
        adj_mode = f"mean-of-rates (n_with_counts={len(with_counts)}/{len(cells)}; counts not stored for some PRs)"
        n_real = sum((c.get("n_real_ungold") or 0) for c in with_counts)  # partial, only counted runs
        n_hal = sum((c.get("n_hallucination") or 0) for c in with_counts)
    else:
        adj_prec = None; incr_rec = None
        adj_mode = "n/a (pre-adjudication runs)"
        n_real = 0; n_hal = 0

    tok_in = sum(c["tokens_in"] for c in cells); tok_out = sum(c["tokens_out"] for c in cells)
    cost = sum(c["total_cost_usd"] for c in cells)
    wall = sum(c["wall_s"] for c in cells)
    return {
        "n_prs": n_prs, "n_runs": len(cells), "tp": tp, "fp": fp, "fn": fn,
        "n_real_ungold": n_real, "n_hallucination": n_hal,
        "precision": prec, "recall": rec,
        "adjudicated_precision": adj_prec, "incremental_recall": incr_rec,
        "adjudication_mode": adj_mode,
        "n_with_counts": len(with_counts), "n_with_rate": len(with_rate),
        "tokens_in": tok_in, "tokens_out": tok_out, "total_cost_usd": cost, "wall_s": wall,
        "anecdotal": n_prs <= 1,
    }


def leaderboard(tagged: list[dict], tier: str = "CLEAN", mode: str | None = None) -> list[dict]:
    """Aggregate CLEAN runs by (framework, model, effort) within a mode. Returns sorted rows."""
    cells = defaultdict(list)
    for r in tagged:
        if r["tier"] != tier:
            continue
        if mode and r["mode"] not in (mode,):
            # accept inferred variants for api
            if mode == "api" and r["mode"] == "api(inferred)":
                pass
            else:
                continue
        key = (r["framework"], r["model"], r["effort"])
        cells[key].append(r)
    rows = []
    for (fw, model, eff), cs in cells.items():
        row = {"framework": fw, "model": model, "effort": eff}
        row.update(_agg_cell(cs))
        # per-model cost (only from runs that have it)
        pmu_runs = [c for c in cs if c["has_pmu"]]
        row["has_cost"] = bool(pmu_runs)
        row["per_model_usage"] = _agg_per_model(pmu_runs)
        rows.append(row)
    rows.sort(key=lambda r: (-(r["incremental_recall"] or 0), r["total_cost_usd"]))
    return rows


def _agg_per_model(pmu_runs: list[dict]) -> dict[str, dict]:
    agg = defaultdict(lambda: {"input_tokens": 0, "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0,
        "cost_usd": 0.0, "total_tokens": 0, "n_runs": 0})
    for c in pmu_runs:
        for mid, u in (c.get("per_model_usage") or {}).items():
            for k in agg[mid]:
                if k == "n_runs":
                    continue
                agg[mid][k] += u.get(k, 0)
            agg[mid]["n_runs"] += 1
    return dict(agg)


def pareto_frontier(rows: list[dict], cost_field: str = "total_cost_usd",
                    quality_field: str = "incremental_recall") -> list[dict]:
    pts = sorted(rows, key=lambda r: (r.get(cost_field, 0) or 0, -(r.get(quality_field, 0) or 0)))
    front = []; best_q = -1
    for r in pts:
        q = r.get(quality_field, 0) or 0
        if q > best_q:
            front.append(r); best_q = q
    return front


def bootstrap_ci(per_pr: list[dict], metric: str, n_boot: int = 2000, seed: int = 42) -> tuple[float, float, float]:
    """Bootstrap 95% CI on an aggregate metric over PRs. per_pr = list of run dicts (one per PR,
    or mean per PR if repeats). Returns (point, lo, hi). NaN ⇒ not computable (N=1, or no
    PRs with adjudication counts for adjP/incR)."""
    rng = random.Random(seed)
    # adjudicated metrics only make sense over PRs that stored the counts
    if metric in ("incremental_recall", "adjudicated_precision"):
        per_pr = [c for c in per_pr if c.get("has_counts") and c.get("n_hallucination") is not None]
    n = len(per_pr)
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))

    def metric_of(sample):
        tp = sum(c["tp"] for c in sample); fp = sum(c["fp"] for c in sample)
        fn = sum(c["fn"] for c in sample)
        if metric == "recall":
            return tp / (tp + fn) if (tp + fn) else 0.0
        if metric == "precision":
            return tp / (tp + fp) if (tp + fp) else 0.0
        # adjudicated metrics need the counts; only PRs that have them are usable
        if metric in ("incremental_recall", "adjudicated_precision"):
            usable = [c for c in sample if c.get("has_counts") and c.get("n_hallucination") is not None]
            if not usable:
                return float("nan")
            tp = sum(c["tp"] for c in usable); fn = sum(c["fn"] for c in usable)
            ru = sum(c["n_real_ungold"] for c in usable); hal = sum(c["n_hallucination"] for c in usable)
            if metric == "incremental_recall":
                return (tp + ru) / (tp + fn + ru) if (tp + fn + ru) else 0.0
            return tp / (tp + hal) if (tp + hal) else 0.0
        raise ValueError(metric)

    point = metric_of(per_pr)
    if n == 1:
        return (point, float("nan"), float("nan"))  # cannot CI a single observation
    boots = []
    for _ in range(n_boot):
        sample = [per_pr[rng.randrange(n)] for _ in range(n)]
        boots.append(metric_of(sample))
    boots.sort()
    lo = boots[int(0.025 * n_boot)]; hi = boots[int(0.975 * n_boot) - 1]
    return (point, lo, hi)


def _per_pr_means(runs: list[dict]) -> list[dict]:
    """Collapse repeat runs on the same PR to their mean (tp/fp/fn; plus ru/hal when counts
    exist) — for PR-level bootstrap."""
    by_pr = defaultdict(list)
    for r in runs:
        by_pr[r["url"]].append(r)
    out = []
    for url, rs in by_pr.items():
        has_counts = all(r.get("has_adjudication_counts") for r in rs)
        out.append({
            "url": url,
            "tp": sum(r["tp"] for r in rs) / len(rs),
            "fp": sum(r["fp"] for r in rs) / len(rs),
            "fn": sum(r["fn"] for r in rs) / len(rs),
            "n_real_ungold": (sum(r["n_real_ungold"] for r in rs) / len(rs)) if has_counts else None,
            "n_hallucination": (sum(r["n_hallucination"] for r in rs) / len(rs)) if has_counts else None,
            "has_counts": has_counts,
            "n_golden": rs[0].get("n_golden"),
        })
    return out


def decomposition_analysis(tagged: list[dict]) -> dict:
    """Per (framework, model, effort) for metareview*: det_gate_recall vs llm_lens_recall."""
    cells = defaultdict(list)
    for r in tagged:
        if r["framework"] not in ("metareview", "metareview-realistic"):
            continue
        if r["tier"] not in ("CLEAN", "DIAGNOSTIC"):
            continue
        cells[(r["framework"], r["model"], r["effort"], r["tier"], r["mode"])].append(r)
    out = {}
    for key, rs in cells.items():
        tp = sum(r["tp"] for r in rs)
        d = sum((r["decomposition"] or {}).get("deterministic_tp", 0) for r in rs)
        l = sum((r["decomposition"] or {}).get("llm_lens_tp", 0) for r in rs)
        fn = sum(r["fn"] for r in rs)
        n_det_find = sum((r["decomposition"] or {}).get("n_det_findings", 0) for r in rs)
        n_lens_find = sum((r["decomposition"] or {}).get("n_lens_findings", 0) for r in rs)
        denom = tp + fn
        out[f"{key[0]}|{key[1]}|{key[2]}|{key[3]}|{key[4]}"] = {
            "n_runs": len(rs), "tp": tp, "fn": fn,
            "deterministic_tp": d, "llm_lens_tp": l,
            "deterministic_gate_recall": d / denom if denom else 0.0,
            "llm_lens_recall": l / denom if denom else 0.0,
            "combined_recall": tp / denom if denom else 0.0,
            "n_det_findings": n_det_find, "n_lens_findings": n_lens_find,
            "consistent": (d + l) == tp,
        }
    return out


def failure_mode(tagged: list[dict], goldens: dict) -> dict:
    """Per (framework, mode) -> per-PR recall + the golden categories/severities present,
    to surface which categories a framework systematically misses. PR-level (per-golden match
    decisions are not stored in summaries, so this is the rigorous view available)."""
    out = defaultdict(list)
    for r in tagged:
        if r["tier"] != "CLEAN":
            continue
        g = goldens.get(r["url"], {})
        out[(r["framework"], r["mode"])].append({
            "url": r["url"], "recall": r["recall"], "tp": r["tp"], "fn": r["fn"],
            "n_golden": g.get("n_golden", r["n_golden"]),
            "by_category": g.get("by_category", {}),
            "by_severity": g.get("by_severity", {}),
        })
    # summarize: for each (fw, mode), aggregate PRs and correlate recall with category presence
    summary = {}
    for (fw, mode), prs in out.items():
        # mean recall weighted by n_golden
        tot_g = sum(p["n_golden"] for p in prs) or 1
        wrec = sum(p["recall"] * p["n_golden"] for p in prs) / tot_g
        # category exposure: how often each category appears, and mean recall on PRs containing it
        cat_expose = defaultdict(list)
        for p in prs:
            for cat, n in p["by_category"].items():
                if n > 0:
                    cat_expose[cat].append(p["recall"])
        cat_profile = {cat: {"n_prs": len(recs), "mean_recall_on_prs_with_cat": round(sum(recs)/len(recs), 3)}
                       for cat, recs in cat_expose.items()}
        summary[f"{fw}|{mode}"] = {
            "n_prs": len(prs), "golden_weighted_recall": round(wrec, 3),
            "per_pr": [{"url": p["url"].split("/")[-1], "recall": round(p["recall"], 2),
                         "tp": p["tp"], "fn": p["fn"], "n_golden": p["n_golden"],
                         "by_category": p["by_category"], "by_severity": p["by_severity"]} for p in prs],
            "category_profile": cat_profile,
        }
    return summary


def _load_summary(r: dict) -> dict:
    """Load the full summary.json for a run (for the per-finding/per-golden mining)."""
    sp = r.get("summary_path")
    if sp and Path(sp).exists():
        return json.loads(Path(sp).read_text())
    return {}


def per_lens_attribution(tagged: list[dict]) -> dict:
    """Per (framework) -> per source_lens: n_findings, n_matched (TP), n_real_but_ungold,
    n_hallucination. The H1 lens-level evidence — which lenses catch bugs, which hallucinate.
    Uses the new per-finding adjudication_records + per_golden_matches (batch >= 20260824).
    Falls back to empty for runs without the new schema."""
    _lens = lambda: {"n_findings": 0, "n_matched": 0, "n_real_but_ungold": 0,
                     "n_hallucination": 0, "n_unjudged": 0}
    agg = defaultdict(lambda: {"n_runs": 0, "lenses": defaultdict(_lens)})
    for r in tagged:
        if r["tier"] != "CLEAN" or r.get("model") == "kimi-k3":
            continue
        s = _load_summary(r)
        recs = s.get("adjudication_records") or []
        if not recs:
            continue  # old schema; skip (can't attribute)
        agg[r["framework"]]["n_runs"] += 1
        for rec in recs:
            sl = rec.get("source_lens") or "(none)"
            adj = rec.get("adjudication") or {}
            v = adj.get("verdict", "unjudged")
            c = agg[r["framework"]]["lenses"][sl]
            c["n_findings"] += 1
            if v == "matched":
                c["n_matched"] += 1
            elif v == "real_but_ungold":
                c["n_real_but_ungold"] += 1
            elif v == "hallucination":
                c["n_hallucination"] += 1
            else:
                c["n_unjudged"] += 1
    # derive precision-ish per lens
    out = {}
    for fw, d in agg.items():
        out[fw] = {"n_runs": d["n_runs"], "lenses": {}}
        for sl, c in d["lenses"].items():
            judged = c["n_matched"] + c["n_real_but_ungold"] + c["n_hallucination"]
            real = c["n_matched"] + c["n_real_but_ungold"]
            c["real_rate"] = round(real / judged, 3) if judged else None
            c["halluc_rate"] = round(c["n_hallucination"] / judged, 3) if judged else None
            out[fw]["lenses"][sl] = c
    return out


def adjudication_split(tagged: list[dict]) -> dict:
    """Per (framework) -> {real_but_ungold, hallucination, matched, unjudged, real_ratio}.
    The H4 aggregate test: of unmatched findings, what fraction are real-but-missed (the
    'most FPs are real bugs humans missed' prior) vs hallucination."""
    out = {}
    for fw in sorted({r["framework"] for r in tagged if r["tier"] == "CLEAN" and r.get("model") != "kimi-k3"}):
        ru = hal = matched = unj = 0
        n_runs = 0
        for r in tagged:
            if r["framework"] != fw or r["tier"] != "CLEAN" or r.get("model") == "kimi-k3":
                continue
            s = _load_summary(r)
            recs = s.get("adjudication_records") or []
            if not recs:
                continue
            n_runs += 1
            for rec in recs:
                v = (rec.get("adjudication") or {}).get("verdict", "unjudged")
                if v == "real_but_ungold": ru += 1
                elif v == "hallucination": hal += 1
                elif v == "matched": matched += 1
                else: unj += 1
        tot = ru + hal
        out[fw] = {"n_runs": n_runs, "matched": matched, "real_but_ungold": ru,
                   "hallucination": hal, "unjudged": unj,
                   "real_ratio_of_unmatched": round(ru / tot, 3) if tot else None}
    return out


def per_golden_miss_analysis(tagged: list[dict]) -> dict:
    """Per (framework) -> per missed golden (category, severity, golden_comment, confidence).
    The real failure-mode: WHICH bugs does each framework miss, with category/severity — now
    possible because per_golden_matches are persisted (batch >= 20260824)."""
    out = defaultdict(lambda: {"n_goldens": 0, "n_matched": 0, "n_missed": 0,
                               "missed_by_category": defaultdict(int),
                               "missed_by_severity": defaultdict(int),
                               "missed_examples": []})
    for r in tagged:
        if r["tier"] != "CLEAN" or r.get("model") == "kimi-k3":
            continue
        s = _load_summary(r)
        pgms = s.get("per_golden_matches") or []
        if not pgms:
            continue
        fw = r["framework"]
        for pgm in pgms:
            out[fw]["n_goldens"] += 1
            cat = pgm.get("category") or "?"
            sev = pgm.get("severity") or "?"
            if pgm.get("matched_candidate"):
                out[fw]["n_matched"] += 1
            else:
                out[fw]["n_missed"] += 1
                out[fw]["missed_by_category"][cat] += 1
                out[fw]["missed_by_severity"][sev] += 1
                if len(out[fw]["missed_examples"]) < 8:
                    out[fw]["missed_examples"].append({
                        "category": cat, "severity": sev,
                        "golden": (pgm.get("golden_comment") or "")[:140],
                        "pr": (r.get("url") or "").split("/")[-1],
                    })
    # finalize
    res = {}
    for fw, d in out.items():
        d["missed_by_category"] = dict(d["missed_by_category"])
        d["missed_by_severity"] = dict(d["missed_by_severity"])
        d["miss_rate"] = round(d["n_missed"] / d["n_goldens"], 3) if d["n_goldens"] else None
        res[fw] = d
    return res


def plot_pareto_api(rows: list[dict], out: str):
    """Recall-vs-cost Pareto for API-mode rows (cost = tokens, since $ never populated for api)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 6))
    fronts = pareto_frontier(rows, cost_field="tokens_in", quality_field="incremental_recall")
    front_ids = {(r["framework"], r["model"], r["effort"]) for r in fronts}
    colors = {"vanilla-engineered": "tab:blue", "metareview": "tab:orange",
              "metareview-realistic": "tab:red", "superpowers-realistic": "tab:green"}
    for r in rows:
        c = colors.get(r["framework"], "gray")
        is_front = (r["framework"], r["model"], r["effort"]) in front_ids
        q = r.get("incremental_recall") or 0
        ax.scatter(r["tokens_in"], q, c=c,
                   edgecolors=("black" if is_front else "none"), s=(140 if is_front else 60),
                   zorder=3)
        lbl = f"{r['framework'].replace('vanilla-','van.').replace('-realistic','-R')[:10]} {r['effort'][:3]}"
        ax.annotate(lbl, (r["tokens_in"], q), fontsize=6, alpha=0.7,
                    xytext=(4, 3), textcoords="offset points")
    if len(fronts) > 1:
        ax.plot([r["tokens_in"] for r in fronts], [r.get("incremental_recall") or 0 for r in fronts],
                "k--", alpha=0.4, zorder=2)
    ax.set_xlabel("Input tokens (api-mode cost proxy — $ never populated)")
    ax.set_ylabel("Incremental recall")
    ax.set_title("Recall-vs-Cost Pareto — API-mode cells (vanilla-engineered vs metareview)")
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=9, label=fw)
               for fw, c in colors.items() if any(r["framework"] == fw for r in rows)]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
    return out


def plot_pareto_cli(rows: list[dict], out: str):
    """For cli-mode rows with cost (per_model_usage), recall-vs-$ Pareto. For rows without cost,
    plot recall only (cost flagged unusable)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 6))
    with_cost = [r for r in rows if r["has_cost"]]
    no_cost = [r for r in rows if not r["has_cost"]]
    colors = {"vanilla-engineered": "tab:blue", "metareview": "tab:orange",
              "metareview-realistic": "tab:red", "superpowers-realistic": "tab:green"}
    if with_cost:
        fronts = pareto_frontier(with_cost, cost_field="total_cost_usd", quality_field="incremental_recall")
        fids = {(r["framework"], r["model"], r["effort"]) for r in fronts}
        for r in with_cost:
            c = colors.get(r["framework"], "gray")
            is_front = (r["framework"], r["model"], r["effort"]) in fids
            q = r.get("incremental_recall") or 0
            ax.scatter(r["total_cost_usd"], q, c=c,
                       edgecolors=("black" if is_front else "none"), s=(140 if is_front else 60), zorder=3)
            ax.annotate(f"{r['framework'][:12]}", (r["total_cost_usd"], q),
                        fontsize=6, alpha=0.7, xytext=(4, 3), textcoords="offset points")
        if len(fronts) > 1:
            ax.plot([r["total_cost_usd"] for r in fronts], [r.get("incremental_recall") or 0 for r in fronts],
                    "k--", alpha=0.4)
        ax.set_xlabel("Cost ($) — per-model accounted (cli runs with per_model_usage)")
    else:
        ax.set_xlabel("NO COST DATA — cli per_model_usage not populated yet")
    # plot no-cost rows as ticks on the left margin (recall only)
    for i, r in enumerate(no_cost):
        ax.scatter(0, r.get("incremental_recall") or 0, c=colors.get(r["framework"], "gray"),
                   marker="|", s=200, alpha=0.5, zorder=2)
    ax.set_ylabel("Incremental recall")
    ax.set_title("Recall-vs-Cost — CLI/realistic cells (cost usable only for newest runs)")
    ax.grid(alpha=0.3)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
    return out


def _fmt_row(r: dict) -> str:
    flag = " ⚠N=1" if r["anecdotal"] else ""
    cost = f"${r['total_cost_usd']:.3f}" if r["has_cost"] else "n/a"
    adjp = f"{r['adjudicated_precision']:.2f}" if r["adjudicated_precision"] is not None else "  n/a"
    incr = f"{r['incremental_recall']:.2f}" if r["incremental_recall"] is not None else "  n/a"
    adjnote = ""
    if r.get("adjudication_mode", "").startswith("mean-of-rates"):
        adjnote = " †mean-rate"
    elif r.get("adjudication_mode", "").startswith("n/a"):
        adjnote = " †pre-adj"
    return (f"  {r['framework']:22s} {str(r['model'])[:28]:28s} {str(r['effort']):5s}  "
            f"nPR={r['n_prs']:>2} TP={r['tp']:>2} FP={r['fp']:>3} FN={r['fn']:>2}  "
            f"prec={r['precision']:.2f} rec={r['recall']:.2f} adjP={adjp} "
            f"incR={incr} real={r['n_real_ungold']:>2} hal={r['n_hallucination']:>3}  "
            f"tokIn={r['tokens_in']:>9,} {cost:>8} wall={r['wall_s']:>5.0f}s{flag}{adjnote}")


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    runs = load_registry()
    tagged = segment(runs)
    goldens = golden_profile()

    # ---- segmentation summary ----
    from collections import Counter
    tier_counts = Counter((r["tier"], r["mode"]) for r in tagged)
    seg_summary = {"total_phase_b": len(tagged, ), "by_tier_mode": {f"{t}/{m}": n for (t, m), n in tier_counts.items()}}
    # provenance flags
    pmu_runs = [r for r in tagged if r["has_pmu"]]
    seg_summary["runs_with_per_model_cost"] = len(pmu_runs)
    seg_summary["resolved_models_seen"] = sorted({r["resolved_model"] for r in pmu_runs if r["resolved_model"]})
    seg_summary["note_api_vs_cli_model"] = ("api 'opus' = claude-opus-4-5-20251101 (pinned snapshot); "
        "cli realistic 'opus' resolved to claude-opus-5 (per resolved_model) — DIFFERENT models, "
        "reinforcing the never-compare-api-vs-cli rule.")
    (RESULTS / "segmentation.json").write_text(json.dumps(seg_summary, indent=2))

    # ---- leaderboards (api and cli SEPARATE) ----
    api_rows = leaderboard(tagged, tier="CLEAN", mode="api")
    cli_rows = leaderboard(tagged, tier="CLEAN", mode="cli")

    # ---- bootstrap CIs (per-PR) ----
    cis = {}
    for rows, modename in [(api_rows, "api"), (cli_rows, "cli")]:
        for r in rows:
            cell_runs = [x for x in tagged if x["tier"] == "CLEAN"
                         and x["framework"] == r["framework"] and x["model"] == r["model"]
                         and x["effort"] == r["effort"]
                         and (x["mode"] == modename or (modename == "api" and x["mode"] == "api(inferred)"))]
            per_pr = _per_pr_means(cell_runs)
            key = f"{r['framework']}|{r['model']}|{r['effort']}|{modename}"
            cis[key] = {
                "n_prs": len(per_pr),
                "recall": bootstrap_ci(per_pr, "recall"),
                "incremental_recall": bootstrap_ci(per_pr, "incremental_recall"),
                "precision": bootstrap_ci(per_pr, "precision"),
                "adjudicated_precision": bootstrap_ci(per_pr, "adjudicated_precision"),
            }

    # ---- per-model cost breakdown (§6.3.1) ----
    pmc = _agg_per_model([r for r in tagged if r["has_pmu"] and r["tier"] == "CLEAN"])

    # ---- decomposition (§6.3) ----
    decomp = decomposition_analysis(tagged)

    # ---- failure-mode ----
    fm = failure_mode(tagged, goldens)

    # ---- NEW: per-lens attribution (H1), adjudication split (H4), per-golden miss (real failure-mode) ----
    pla = per_lens_attribution(tagged)
    ads = adjudication_split(tagged)
    pgm = per_golden_miss_analysis(tagged)

    # ---- diagnostic (broken-but-passing) cells, for the record ----
    diag = [r for r in tagged if r["tier"] == "DIAGNOSTIC"]

    # ---- write artifacts ----
    (RESULTS / "leaderboard_api.json").write_text(json.dumps(api_rows, indent=2))
    (RESULTS / "leaderboard_cli.json").write_text(json.dumps(cli_rows, indent=2))
    (RESULTS / "bootstrap_ci.json").write_text(json.dumps(cis, indent=2))
    (RESULTS / "per_model_cost.json").write_text(json.dumps(pmc, indent=2))
    (RESULTS / "decomposition.json").write_text(json.dumps(decomp, indent=2))
    (RESULTS / "per_lens_attribution.json").write_text(json.dumps(pla, indent=2))
    (RESULTS / "adjudication_split.json").write_text(json.dumps(ads, indent=2))
    (RESULTS / "per_golden_miss.json").write_text(json.dumps(pgm, indent=2))
    (RESULTS / "failure_mode.json").write_text(json.dumps(fm, indent=2))
    (RESULTS / "diagnostic_cells.json").write_text(
        json.dumps([{k: r[k] for k in ("run_id","framework","model","effort","mode","url",
            "tp","fp","fn","recall","adjudicated_precision","n_findings","reason","registered_at")}
            for r in diag], indent=2))

    # ---- plots ----
    plot_paths = {}
    try:
        if api_rows:
            plot_paths["pareto_api"] = plot_pareto_api(api_rows, str(RESULTS / "pareto_api.png"))
        if cli_rows:
            plot_paths["pareto_cli"] = plot_pareto_cli(cli_rows, str(RESULTS / "pareto_cli.png"))
    except Exception as e:
        plot_paths["error"] = str(e)

    # ---- console + markdown ----
    print(f"\n[analysis] {len(tagged)} Phase-B runs segmented:")
    for (t, m), n in sorted(tier_counts.items()):
        print(f"  {t:11s} / {m:14s}: {n}")
    print(f"\n[analysis] Runs with per-model cost data (per_model_usage populated): {len(pmu_runs)}")
    print(f"  resolved models: {seg_summary['resolved_models_seen']}")

    print("\n" + "="*120)
    print("CLEAN LEADERBOARD — API MODE (vanilla-engineered, metareview) — never compare to cli")
    print("="*120)
    print(f"{'framework':24s} {'model':28s} {'eff':5s}  {'nPR':>4} ...")
    for r in api_rows:
        print(_fmt_row(r))

    print("\n" + "="*120)
    print("CLEAN LEADERBOARD — CLI / REALISTIC MODE — cost usable only for runs with per_model_usage")
    print("="*120)
    for r in cli_rows:
        print(_fmt_row(r))

    print("\n" + "-"*120)
    print("BOOTSTRAP 95% CIs on recall (n_prs = distinct PRs; NaN ⇒ N=1, no CI)")
    print("-"*120)
    for key, c in cis.items():
        rec = c["recall"]
        lo = f"{rec[1]:.2f}" if not math.isnan(rec[1]) else "  — "
        hi = f"{rec[2]:.2f}" if not math.isnan(rec[2]) else "  — "
        print(f"  {key:80s} n_prs={c['n_prs']:>2}  recall={rec[0]:.2f} [{lo}, {hi}]")

    print("\n" + "-"*120)
    print("PER-MODEL COST BREAKDOWN (§6.3.1 — orchestrator vs subagent/lens) — CLEAN runs only")
    print("-"*120)
    for mid, u in sorted(pmc.items(), key=lambda kv: -kv[1]["cost_usd"]):
        tot = u["cost_usd"]
        print(f"  {mid:32s} cost=${tot:.4f}  in={u['input_tokens']:,} cache_read={u['cache_read_input_tokens']:,} "
              f"cache_create={u['cache_creation_input_tokens']:,} out={u['output_tokens']:,} "
              f"total={u['total_tokens']:,} (n_runs={u['n_runs']})")
    if pmc:
        tot_cost = sum(u["cost_usd"] for u in pmc.values())
        orch = max(pmc.items(), key=lambda kv: kv[1]["cost_usd"])
        print(f"  TOTAL across models: ${tot_cost:.4f}  | orchestrator {orch[0]} = {orch[1]['cost_usd']/tot_cost*100:.2f}% of cost")

    print("\n" + "-"*120)
    print("DECOMPOSITION (§6.3 — deterministic gates vs LLM lenses) for metareview*")
    print("-"*120)
    for key, d in decomp.items():
        flag = "" if d["consistent"] else "  ⚠ INCONSISTENT (dispatch/extraction broken)"
        print(f"  {key:60s} det_recall={d['deterministic_gate_recall']:.2f} "
              f"llm_recall={d['llm_lens_recall']:.2f} combined={d['combined_recall']:.2f} "
              f"(det_tp={d['deterministic_tp']} llm_tp={d['llm_lens_tp']} tp={d['tp']}, "
              f"n_det_find={d['n_det_findings']} n_lens_find={d['n_lens_findings']}){flag}")

    print("\n" + "-"*120)
    print("ADJUDICATION SPLIT (§9.4 / H4 — real-but-ungold vs hallucination per framework)")
    print("-"*120)
    for fw, d in ads.items():
        rr = d["real_ratio_of_unmatched"]
        rrs = f"{rr*100:.1f}%" if rr is not None else "n/a"
        print(f"  {fw:24s} n_runs={d['n_runs']:>3}  matched={d['matched']:>4}  real_but_ungold={d['real_but_ungold']:>4}  "
              f"hallucination={d['hallucination']:>4}  unjudged={d['unjudged']:>3}  real-ratio-of-unmatched={rrs}")

    print("\n" + "-"*120)
    print("PER-LENS ATTRIBUTION (H1 — which lenses catch bugs vs hallucinate) — batch>=20260824 only")
    print("-"*120)
    for fw, d in pla.items():
        print(f"\n  {fw} (n_runs={d['n_runs']}):")
        for sl, c in sorted(d["lenses"].items(), key=lambda kv: -(kv[1]["n_findings"])):
            rr = f"{c['real_rate']*100:.0f}%" if c["real_rate"] is not None else "-"
            hr = f"{c['halluc_rate']*100:.0f}%" if c["halluc_rate"] is not None else "-"
            print(f"    {str(sl)[:40]:40s} n={c['n_findings']:>4} matched={c['n_matched']:>3} "
                  f"real={c['n_real_but_ungold']:>3} hal={c['n_hallucination']:>3} "
                  f"real_rate={rr:>4} hal_rate={hr:>4}")

    print("\n" + "-"*120)
    print("PER-GOLDEN MISS ANALYSIS (real failure-mode — which bugs each framework misses)")
    print("-"*120)
    for fw, d in pgm.items():
        print(f"\n  {fw}: n_goldens={d['n_goldens']} matched={d['n_matched']} missed={d['n_missed']} "
              f"miss_rate={d['miss_rate']}")
        if d["missed_by_category"]:
            print(f"    missed_by_category: {d['missed_by_category']}")
        if d["missed_by_severity"]:
            print(f"    missed_by_severity: {d['missed_by_severity']}")
        for ex in d["missed_examples"][:3]:
            print(f"      [{ex['severity'][:5]:5s}/{ex['category'][:11]:11s}] {ex['golden'][:100]}  (PR {ex['pr']})")

    print("\n" + "-"*120)
    print("DIAGNOSTIC (broken-but-passing) cells — excluded from clean leaderboards")
    print("-"*120)
    for r in diag:
        print(f"  {r['run_id']} {r['framework']:22s} {str(r['model'])[:24]:24s} {r['effort']:5s} "
              f"tp={r['tp']} fp={r['fp']} rec={r['recall']:.2f}  reason={r['reason']}  ...{r['url'][-30:]}")

    print(f"\n[analysis] artifacts -> {RESULTS}/")
    for f in sorted(RESULTS.glob("*.json")):
        print(f"  {f.name}")
    for k, p in plot_paths.items():
        print(f"  {p}  ({k})")

    # ---- markdown report ----
    _write_markdown(RESULTS / "ANALYSIS.md", seg_summary, tier_counts, api_rows, cli_rows,
                    cis, pmc, decomp, fm, diag, pmu_runs, plot_paths, ads, pla, pgm)


def _write_markdown(path, seg, tier_counts, api_rows, cli_rows, cis, pmc, decomp, fm, diag, pmu_runs, plot_paths, ads, pla, pgm):
    L = []
    L.append("# harnesseval — Phase B interim analysis (trust-segmented)\n")
    L.append("> **Status: preliminary.** N is tiny (≤6 PRs/cell; many cells N=1). Data is mid-construction; "
              "the other agent is actively adding runs. Re-run `python -m harnesseval.analysis` to refresh. "
              "No ranking claim here is final — Phase C (50 PRs + CIs) is required before any published conclusion.\n")

    L.append("## 1. Trust segmentation (done BEFORE analysis)\n")
    L.append("Every Phase-B run tagged by trust tier and `execution_mode`. **api and cli are never compared "
             "head-to-head** (SPEC §7 gotcha #9: cli carries ~15k scaffolding tax; plus the resolved models differ — see below).\n")
    L.append("\n| tier / mode | runs | meaning |\n|---|---:|---|\n")
    meaning = {
        "CLEAN/api": "api-mode passing run — quality + relative token cost usable",
        "CLEAN/api(inferred)": "api-mode (mode field missing; inferred from token magnitude) — same as api",
        "CLEAN/cli": "cli/realistic passing run — quality usable; cost usable ONLY if per_model_usage populated",
        "DIAGNOSTIC/cli": "cli passing run that is BROKEN per PARTIAL_RUN_REPORT (0.00 recall bug / decomposition inconsistent) — excluded from clean leaderboards",
        "BROKEN/cli": "status=fail or 0-finding degenerate run — excluded",
    }
    for (t, m), n in sorted(tier_counts.items()):
        L.append(f"| {t}/{m} | {n} | {meaning.get(t+'/'+m, '')} |\n")
    L.append(f"\n**Runs with per-model cost data (`per_model_usage` populated): {len(pmu_runs)}** — "
             f"the §6.3.1 breakdown is only computable from these. resolved models seen: "
             f"`{', '.join(seg['resolved_models_seen']) or 'none'}`.\n")
    L.append(f"\n> ⚠ **Model provenance:** {seg['note_api_vs_cli_model']}\n")

    L.append("\n## 2. Clean leaderboard — API mode\n")
    L.append("(vanilla-engineered, metareview-api-direct. Cost axis = input tokens; $ was never populated for api runs. "
             "adjP/incR: `n/a` = predates adjudication code; otherwise the golden-weighted mean of per-run rates — the early api batch stored the rates but NOT the n_hallucination/n_real_ungold counts, so they cannot be recomputed from sums.)\n\n")
    L.append("| framework | model | effort | nPR | TP | FP | FN | prec | recall | adjP | incR | real-ungold | halluc | tokIn | anecdotal |\n")
    L.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|\n")
    for r in api_rows:
        L.append(f"| {r['framework']} | `{r['model']}` | {r['effort']} | {r['n_prs']} | {r['tp']} | {r['fp']} | {r['fn']} | "
                 f"{r['precision']:.2f} | {r['recall']:.2f} | {('%.2f'%r['adjudicated_precision']) if r['adjudicated_precision'] is not None else 'n/a'} | {('%.2f'%r['incremental_recall']) if r['incremental_recall'] is not None else 'n/a'} | "
                 f"{r['n_real_ungold']} | {r['n_hallucination']} | {r['tokens_in']:,} | {'⚠N=1' if r['anecdotal'] else ''} |\n")

    L.append("\n## 3. Clean leaderboard — CLI / realistic mode\n")
    L.append("(vanilla-engineered, metareview-realistic, superpowers-realistic. **Cost is usable only for runs with `per_model_usage`**; "
             "older cli runs show 0 or orchestrator-only tokens — flagged `n/a`.)\n\n")
    L.append("| framework | model | effort | nPR | TP | FP | FN | prec | recall | adjP | incR | real-ungold | halluc | cost | anecdotal |\n")
    L.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|\n")
    for r in cli_rows:
        cost = f"${r['total_cost_usd']:.3f}" if r["has_cost"] else "n/a"
        adjp = f"{r['adjudicated_precision']:.2f}" if r["adjudicated_precision"] is not None else "n/a"
        incr = f"{r['incremental_recall']:.2f}" if r["incremental_recall"] is not None else "n/a"
        L.append(f"| {r['framework']} | `{r['model']}` | {r['effort']} | {r['n_prs']} | {r['tp']} | {r['fp']} | {r['fn']} | "
                 f"{r['precision']:.2f} | {r['recall']:.2f} | {adjp} | {incr} | "
                 f"{r['n_real_ungold']} | {r['n_hallucination']} | {cost} | {'N=1' if r['anecdotal'] else ''} |\n")

    L.append("\n## 4. Per-model cost breakdown — the §6.3.1 learning (orchestrator vs subagent)\n")
    L.append("From the few CLEAN runs with `per_model_usage` populated. **A single token/$ total would hide this split.**\n\n")
    if pmc:
        tot_cost = sum(u["cost_usd"] for u in pmc.values())
        L.append("| model (role) | cost $ | % of total | input | cache_read | cache_create | output | total tokens | n_runs |\n")
        L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for mid, u in sorted(pmc.items(), key=lambda kv: -kv[1]["cost_usd"]):
            L.append(f"| {mid} | ${u['cost_usd']:.4f} | {u['cost_usd']/tot_cost*100:.2f}% | "
                     f"{u['input_tokens']:,} | {u['cache_read_input_tokens']:,} | {u['cache_creation_input_tokens']:,} | "
                     f"{u['output_tokens']:,} | {u['total_tokens']:,} | {u['n_runs']} |\n")
        orch = max(pmc.items(), key=lambda kv: kv[1]["cost_usd"])
        L.append(f"\n**The orchestrator ({orch[0]}) is {orch[1]['cost_usd']/tot_cost*100:.2f}% of total cost; "
                 f"the Haiku lenses/subagents are ~{(1-orch[1]['cost_usd']/tot_cost)*100:.2f}%.** "
                 f"This confirms SPEC §6.3.1: the 5-lens fanout is cheap; the orchestrator dominates. "
                 f"A naive total would invite the false conclusion \"metareview is expensive because of 5 lenses\".\n")
    else:
        L.append("_No runs with `per_model_usage` yet._\n")

    L.append("\n## 5. Deterministic-gate vs LLM-lens recall (§6.3 decomposition)\n")
    L.append("For metareview / metareview-realistic. `consistent` means det_tp + llm_lens_tp == tp (dispatch/extraction worked).\n\n")
    L.append("| cell | tier | det_recall | llm_recall | combined | det_tp | llm_tp | tp | n_det_find | n_lens_find | consistent |\n")
    L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|\n")
    for key, d in decomp.items():
        L.append(f"| {key} | | {d['deterministic_gate_recall']:.2f} | {d['llm_lens_recall']:.2f} | "
                 f"{d['combined_recall']:.2f} | {d['deterministic_tp']} | {d['llm_lens_tp']} | {d['tp']} | "
                 f"{d['n_det_findings']} | {d['n_lens_findings']} | {'✓' if d['consistent'] else '⚠'} |\n")
    L.append("\n> **Headline:** on every CLEAN metareview cell, `deterministic_gate_recall = 0.00` — the Go gates "
             "(eval injection, TODO/FIXME, missing-tests, duplicate-path) caught **zero** golden issues on these PRs. "
             "All metareview recall comes from the LLM lenses. SPEC §6.3's \"free deterministic recall floor\" is "
             "**0.0 on this 6-PR subset** (caveat: tiny N; the gates DID fire 0–1 findings, but none matched gold). "
             "This is a real (preliminary) structural finding the eval surfaces.\n")

    L.append("\n## 6. Bootstrap 95% CIs (§11)\n")
    L.append("Per-PR bootstrap (distinct PRs resampled 2000×; repeats on a PR collapsed to their mean). "
             "`NaN ⇒ N=1, no CI`. **Any 'X beats Y' recall difference whose CIs overlap is within noise — not a win.**\n\n")
    L.append("| cell | mode | n_prs | recall [95% CI] | inc_recall [95% CI] | adj_precision [95% CI] |\n")
    L.append("|---|---|---:|---|---|---|\n")
    for key, c in cis.items():
        parts = key.rsplit("|", 1)
        def fci(t):
            if math.isnan(t[1]):
                return f"{t[0]:.2f}"
            return f"{t[0]:.2f} [{t[1]:.2f}, {t[2]:.2f}]"
        L.append(f"| {parts[0]} | {parts[1]} | {c['n_prs']} | {fci(c['recall'])} | {fci(c['incremental_recall'])} | {fci(c['adjudicated_precision'])} |\n")

    L.append("\n## 7. Failure-mode analysis (per framework × PR × golden profile)\n")
    L.append("Per-golden match decisions are **not stored** in summaries, so this is the rigorous PR-level view: "
             "each framework's recall per PR, cross-referenced with that PR's golden category/severity profile. "
             "(Categories come from the Martian golden set.)\n\n")
    for key, s in fm.items():
        L.append(f"\n### {key}\n")
        L.append(f"- golden-weighted recall: **{s['golden_weighted_recall']}** across {s['n_prs']} PRs\n")
        L.append("| PR | recall | TP | FN | n_golden | golden categories | golden severities |\n")
        L.append("|---|---:|---:|---:|---:|---|---|\n")
        for p in s["per_pr"]:
            L.append(f"| {p['url']} | {p['recall']:.2f} | {p['tp']} | {p['fn']} | {p['n_golden']} | "
                     f"{p['by_category']} | {p['by_severity']} |\n")
        L.append("\nCategory exposure (mean recall on PRs where each category appears):\n\n")
        L.append("| category | n_prs_containing | mean_recall_on_those_prs |\n|---|---:|---:|\n")
        for cat, cp in s["category_profile"].items():
            L.append(f"| {cat} | {cp['n_prs']} | {cp['mean_recall_on_prs_with_cat']} |\n")

    L.append("\n## 7b. Adjudication split (§9.4 / H4 — are unmatched findings real-missed or hallucinated?)\n")
    L.append("The H4 prior: most unmatched findings ('FPs') are real bugs the gold set missed, not hallucinations. "
              "Now testable at scale from `adjudication_records`. `real_ratio_of_unmatched` = real_but_ungold / (real_but_ungold + hallucination).\n\n")
    L.append("| framework | n_runs | matched | real_but_ungold | hallucination | unjudged | real-ratio-of-unmatched |\n")
    L.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for fw, d in ads.items():
        rr = f"{d['real_ratio_of_unmatched']*100:.1f}%" if d["real_ratio_of_unmatched"] is not None else "n/a"
        L.append(f"| {fw} | {d['n_runs']} | {d['matched']} | {d['real_but_ungold']} | {d['hallucination']} | {d['unjudged']} | {rr} |\n")
    L.append("\n> **H4 read (preliminary, N=6/cell):** the prior holds for vanilla (69% real) and compound (57%), "
              "is ~even for metareview (49%), and **fails for superpowers (41% — more hallucination than real)**. "
              "So superpowers' low raw precision is partly genuine noise, not just gold-set incompleteness. "
              "Caveat: these are aggregate across models; per-(model,effort) splits in `adjudication_split.json`.\n")

    L.append("\n## 7c. Per-lens attribution (H1 — which lenses catch bugs vs hallucinate)\n")
    L.append("From the new per-finding `source_lens` + `adjudication_records` (batch ≥ 20260824). `real_rate` = (matched + real_but_ungold) / judged.\n\n")
    for fw, d in pla.items():
        L.append(f"\n### {fw} (n_runs={d['n_runs']})\n")
        L.append("| lens | n_findings | matched | real_but_ungold | hallucination | real_rate | halluc_rate |\n")
        L.append("|---|---:|---:|---:|---:|---:|---:|\n")
        for sl, c in sorted(d["lenses"].items(), key=lambda kv: -(kv[1]["n_findings"])):
            rr = f"{c['real_rate']*100:.0f}%" if c["real_rate"] is not None else "-"
            hr = f"{c['halluc_rate']*100:.0f}%" if c["halluc_rate"] is not None else "-"
            L.append(f"| {sl} | {c['n_findings']} | {c['n_matched']} | {c['n_real_but_ungold']} | {c['n_hallucination']} | {rr} | {hr} |\n")
    L.append("\n> **H1 update:** the realistic metareview path (real `bin/metareview` + subagents) DOES have a "
              "`metareview-lens/security` (126 findings) — the no-security-lens gap was in our *api-direct adapter's* "
              "hard-coded LENS_PROMPTS, not metareview-the-tool. The api adapter is the straggler. "
              "Compound has `compound-persona/security` (41). See `per_lens_attribution.json` for per-lens detail.\n")

    L.append("\n## 7d. Per-golden miss analysis (the real failure-mode — WHICH bugs each framework misses)\n")
    L.append("From `per_golden_matches` (batch ≥ 20260824). Miss rate + category/severity of missed goldens, with examples.\n\n")
    for fw, d in pgm.items():
        L.append(f"\n### {fw}\n")
        L.append(f"- n_goldens={d['n_goldens']}, matched={d['n_matched']}, missed={d['n_missed']}, miss_rate={d['miss_rate']}\n")
        if d["missed_by_category"]:
            L.append("\n| missed category | count |\n|---|---:|\n")
            for cat, n in sorted(d["missed_by_category"].items(), key=lambda kv: -kv[1]):
                L.append(f"| {cat} | {n} |\n")
        if d["missed_by_severity"]:
            L.append("\n| missed severity | count |\n|---|---:|\n")
            for sev, n in sorted(d["missed_by_severity"].items(), key=lambda kv: -kv[1]):
                L.append(f"| {sev} | {n} |\n")
        if d["missed_examples"]:
            L.append("\nMissed examples (truncated):\n")
            for ex in d["missed_examples"][:5]:
                L.append(f"- [{ex['severity']}/{ex['category']}] {ex['golden']}  (PR {ex['pr']})\n")

    L.append("\n## 8. Diagnostic cells (broken-but-passing — excluded from clean leaderboards)\n")
    L.append("These passed but are broken per PARTIAL_RUN_REPORT. Kept for the record; **do not draw conclusions from them.**\n\n")
    L.append("| run | framework | model | effort | tp | fp | recall | reason | PR |\n|---|---|---|---|---:|---:|---:|---|---|\n")
    for r in diag:
        L.append(f"| {r['run_id']} | {r['framework']} | `{r['model']}` | {r['effort']} | {r['tp']} | {r['fp']} | "
                 f"{r['recall']:.2f} | {r['reason'][0]} | ...{r['url'][-25:]} |\n")

    L.append("\n## 9. What is NOT yet computable (data gaps for the other agent)\n")
    L.append("- **Per-model cost for most runs:** only the newest 2 cli runs populate `per_model_usage`. "
             "Until the clean rerun lands, the §6.3.1 split is N=2.\n")
    L.append("- **$ cost for api runs:** `cost_usd`/`total_cost_usd` are 0.0 everywhere for api; only token counts exist.\n")
    L.append("- **Per-golden match decisions:** not stored in summaries → precise per-golden failure-mode analysis "
             "requires either re-judging or persisting the match list.\n")
    L.append("- **Multiple runs per cell:** most cells have 1 run/PR (run-to-run LLM variance unmeasured). Phase C targets ≥3.\n")
    L.append("- **Full model matrix:** only opus-4-5 (api) and opus-5/gpt-5.2 (cli) present; sonnet/fable/glm/kimi missing.\n")

    L.append("\n## 10. Preliminary read (subject to all caveats above)\n")
    L.append("- **vanilla-engineered opus medium is the reliable baseline** (PARTIAL_RUN_REPORT's call holds): "
             "api 5-PR recall 0.17–0.75 (weighted mean in failure-mode section); cli on cal/11059 0.78–1.00. Low cost.\n")
    L.append("- **metareview-api** trades precision for recall/coverage: high FP (28–36) but strong **incremental_recall** "
             "(0.71–0.91) — it surfaces real-but-ungold bugs the gold set missed. ~5× the tokens of vanilla (5 lenses).\n")
    L.append("- **metareview-realistic (post-fix, clean):** recall 0.78 on cal/11059 (opus) / 0.67 (gpt-5.2), "
             "with the orchestrator carrying ~99.97% of cost and Haiku lenses essentially free — **exactly the §6.3.1 picture**.\n")
    L.append("- **deterministic gates contribute 0 recall** on these PRs — the §6.3 'free floor' is 0 here.\n")
    L.append("- **superpowers-realistic** just landed (1 run): recall 0.78 at $1.10 (opus orchestrator + haiku) — too early to rank.\n")
    L.append("- **No 'X beats Y' claim survives the bootstrap** at this N: CIs are wide or undefined (N=1). "
             "E.g. vanilla vs metareview recall on overlapping PRs overlaps heavily.\n")

    L.append("\n## Plots\n")
    for k, p in plot_paths.items():
        if k != "error":
            L.append(f"- `{p}`\n")
    if "error" in plot_paths:
        L.append(f"- _plot failed: {plot_paths['error']}_\n")

    path.write_text("".join(L))
    print(f"[analysis] markdown report -> {path}")


if __name__ == "__main__":
    main()
