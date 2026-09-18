#!/usr/bin/env python3
"""FINAL REPORT compute engine — reads analysis/final_report_dataset.json and emits
analysis/final_report_metrics.json plus markdown tables on stdout.

Methodology (REPORT_FINAL.md §Methodology mirrors this):
  * cell = (model, framework, effort); matrix surface = 8 models x 3 frameworks x 3 efforts
    on the six severity-top PRs (CAMPAIGN_GLOSSARY.md ordering).
  * one selected run per (cell, PR) — selection rule in tools/final_report_extract.py.
  * recall (per profile Strict/Core/All) from the frozen matcher via per_golden_matches.
  * adjP = TP_all / (TP_all + hallucinations); hallucination/beyond-gold counts use
    readjudication3 (v3.1 clustered, k=1 — the campaign lock) when the run has an rj3
    file, else the in-run adjudication (v2 three-way since 2026-09-07; v1 binary for
    pre-2026-09-07 vanilla reuse runs, flagged). Per-cell instrument recorded.
  * metered $ from the published price table (retrieved 2026-09-16, see PRICE_* below):
    fresh input / cached read / cache write / output (incl. reasoning) token split from
    per_model_usage. Anthropic rows cross-checked against provider-reported cost_usd.
  * cluster (PR-level) bootstrap, B=10,000, seed 20260916: resample the PRs with
    replacement, recompute every metric from per-PR TP/FN/hallucination/real/token/$
    sums, report the 2.5–97.5 percentile interval. The PR is the sampling unit.
  * paired deltas (framework vs vanilla, high vs medium, flash vs vision) resample the
    SAME PR indices for both cells and bootstrap the difference.

Usage: .venv/bin/python tools/final_report_compute.py
"""
import json, os, glob, sys, difflib
import numpy as np
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 10_000
SEED = 20260916
rng = np.random.default_rng(SEED)

MODELS = ["claude-fable-5-1", "gpt-6-astra", "gpt-5.6-sol", "claude-opus-5",
          "glm-5.3-vision-background", "gpt-5.6-terra", "claude-sonnet-5",
          "glm-5.3-flash-background"]
FRAMEWORKS = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
EFFORTS = ["low", "medium", "high"]
FW_SHORT = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV"}
M_SHORT = {"claude-fable-5-1": "fable", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
           "claude-opus-5": "opus", "glm-5.3-vision-background": "glm-vis",
           "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet",
           "glm-5.3-flash-background": "glm-flash"}

# --- price table, per 1M tokens, USD, retrieved 2026-09-16 --------------------
#   z.ai:            https://docs.z.ai/guides/overview/pricing (GLM-5.3 $1.40/$0.26/$4.40;
#                    GLM-5.3-Flash $0.15/$0.03/$0.50; no separate cache-write price)
#   Anthropic:       https://platform.claude.com/docs/en/about-claude/pricing
#                    (fable-5.1 $10/$0.25hit/$12.50w/$50; opus-5 $5/$0.50/$6.25/$25;
#                     sonnet-5 $2/$0.20/$2.50/$10)
#   OpenAI standard: https://developers.openai.com/api/docs/pricing (.md export)
#                    (astra $10/$1.00/$12.50/$50; sol $4/$0.40/$5.00/$20 promotional;
#                     terra $2/$0.20/$2.50/$12.00)
PRICES = {
    "claude-fable-5-1":          {"in": 10.00, "cached": 0.25, "w": 12.50, "out": 50.00},
    "claude-opus-5":             {"in": 5.00,  "cached": 0.50, "w": 6.25,  "out": 25.00},
    "claude-sonnet-5":           {"in": 2.00,  "cached": 0.20, "w": 2.50,  "out": 10.00},
    "gpt-6-astra":               {"in": 10.00, "cached": 1.00, "w": 12.50, "out": 50.00},
    "gpt-5.6-sol":               {"in": 4.00,  "cached": 0.40, "w": 5.00,  "out": 20.00},
    "gpt-5.6-terra":             {"in": 2.00,  "cached": 0.20, "w": 2.50,  "out": 12.00},
    "glm-5.3-vision-background": {"in": 1.40,  "cached": 0.26, "w": 0.0,   "out": 4.40},
    "glm-5.3-flash-background":  {"in": 0.15,  "cached": 0.03, "w": 0.0,   "out": 0.50},
    # legacy rows (capability-floor aside only; same retrieval date)
    "gpt-5.2":                   {"in": 1.75,  "cached": 0.175, "w": 0.0,   "out": 14.00},
    "claude-opus-4-5-20251101":  {"in": 5.00,  "cached": 0.50, "w": 6.25,  "out": 25.00},
    "glm-5.3-background":        {"in": 1.40,  "cached": 0.26, "w": 0.0,   "out": 4.40},
    "glm-5.2-vision-flex":        {"in": 1.40,  "cached": 0.26, "w": 0.0,   "out": 4.40},
    "kimi-k3":                   {"in": np.nan, "cached": np.nan, "w": 0.0, "out": np.nan},
}
PRICE_RETRIEVED = "2026-09-16"

def metered(r):
    p = PRICES[r["model"]]
    return (r["fresh_in"] * p["in"] + r["cached_in"] * p["cached"]
            + r["cache_w"] * p["w"] + r["out_tok"] * p["out"]) / 1e6

# --- load dataset --------------------------------------------------------------
D = json.load(open(f"{ROOT}/analysis/final_report_dataset.json"))
TOP6 = D["top6"]; T6 = set(TOP6)
SEV = {u: D["pr_golden"][u]["sev_weight"] for u in TOP6}

def per_pr_vectors(runs):
    """url -> metric vector for one cell's selected runs."""
    out = {}
    for r in runs:
        hal = bug = imp = unres = 0
        inst = "none"
        if r["rj3"]:
            hal, bug, imp, unres = r["rj3"]["hal"], r["rj3"]["bug"], r["rj3"]["imp"], r["rj3"]["unres"]
            inst = "rj3"
        else:
            hal, bug, imp, unres = (r["inrun"]["hal"], r["inrun"]["bug"],
                                    r["inrun"]["imp"], r["inrun"]["unres"])
            inst = r["inrun"]["instrument"]
        out[r["url"]] = {
            "tp": r["tp"], "fn": r["fn"],
            "tp_core": r["prof"]["Core"]["tp"], "fn_core": r["prof"]["Core"]["fn"],
            "tp_strict": r["prof"]["Strict"]["tp"], "fn_strict": r["prof"]["Strict"]["fn"],
            "hal": hal, "real": bug + imp, "bug": bug, "imp": imp, "unres": unres,
            "cost": metered(r),
            "tok": r["fresh_in"] + r["cached_in"] + r["cache_w"] + r["out_tok"],
            "fresh": r["fresh_in"], "cached": r["cached_in"], "cw": r["cache_w"], "o": r["out_tok"],
            "wall": (r["wall_ms"] or 0) / 1000.0, "nfind": r["n_findings"],
            "inst": inst, "pmu_cost": r["pmu_cost_usd"],
            "judge": r["judge"], "batch": r["batch"], "ts": r["ts"], "rid": r["run_id"],
        }
    return out

sel = defaultdict(dict)   # (m,fw,eff) -> url -> vec
for r in D["selected_runs"]:
    v = per_pr_vectors([r])
    sel[(r["model"], r["framework"], r["effort"])][r["url"]] = v[r["url"]]
legacy_sel = defaultdict(dict)
for r in D["legacy_runs"]:
    v = per_pr_vectors([r])
    legacy_sel[(r["model"], r["framework"], r["effort"])][r["url"]] = v[r["url"]]

KEYS = ["tp", "fn", "tp_core", "fn_core", "tp_strict", "fn_strict", "hal", "real",
        "cost", "tok", "fresh", "cached", "cw", "o", "wall", "nfind", "bug", "imp"]

def cell_matrix(cell, urls):
    """(n_pr, len(KEYS)) float matrix aligned to urls."""
    M = np.zeros((len(urls), len(KEYS)))
    for i, u in enumerate(urls):
        v = sel[cell][u]
        for j, k in enumerate(KEYS):
            M[i, j] = v[k]
    return M

def metrics_from_sums(s):
    """s: dict key->sum (or array indexed like KEYS). Returns dict of metrics."""
    tp, fn = s["tp"], s["fn"]
    hal, real = s["hal"], s["real"]
    n = s.get("n_pr", len(s.get("urls", [])))
    rec = tp / (tp + fn) if tp + fn else 0.0
    adjp = tp / (tp + hal) if tp + hal else 0.0
    f1 = 2 * rec * adjp / (rec + adjp) if rec + adjp else 0.0
    f2 = 5 * rec * adjp / (4 * adjp + rec) if rec + adjp else 0.0
    rec_c = s["tp_core"] / (s["tp_core"] + s["fn_core"]) if s["tp_core"] + s["fn_core"] else 0.0
    rec_s = s["tp_strict"] / (s["tp_strict"] + s["fn_strict"]) if s["tp_strict"] + s["fn_strict"] else 0.0
    reals = tp + real
    return {
        "recall": rec, "adjP": adjp, "F1": f1, "F2": f2, "recall_core": rec_c,
        "recall_strict": rec_s, "TP": tp, "FN": fn, "hal": hal, "real_beyond": real,
        "real_total": reals, "cost_run": s["cost"] / n, "tok_run": s["tok"] / n,
        "wall_run": s["wall"] / n,
        "usd_per_real": s["cost"] / reals if reals else np.inf,
        "usd_per_tp": s["cost"] / tp if tp else np.inf,
        "usd_per_beyond": s["cost"] / real if real else np.inf,
        "tok_per_real": s["tok"] / reals if reals else np.inf,
        "wall_per_real": s["wall"] / reals if reals else np.inf,
        "findings_run": s["nfind"] / n,
        "price_per_ktok": 1000.0 * s["cost"] / s["tok"] if s["tok"] else np.inf,
    }

def sums_of(M):
    return {k: float(M[:, j].sum()) for j, k in enumerate(KEYS)}

def boot_ci(M, n_pr, keys=("recall", "adjP", "F1", "F2", "usd_per_real", "usd_per_tp",
                           "tok_run", "cost_run", "wall_run", "real_total", "price_per_ktok",
                           "tok_per_real", "wall_per_real", "recall_core", "recall_strict")):
    """Cluster bootstrap over PRs. Returns {metric: (point, lo, hi, frac_finite)}."""
    n = M.shape[0]
    idx = rng.integers(0, n, size=(B, n))
    S = M[idx]                      # (B, n, K)
    sums = S.sum(axis=1)            # (B, K)
    kcol = {k: j for j, k in enumerate(KEYS)}
    out = {}
    base = metrics_from_sums(sums_of(M) | {"n_pr": n})
    for key in keys:
        vals = np.empty(B)
        if key == "recall":
            d = sums[:, kcol["tp"]] + sums[:, kcol["fn"]]
            vals = np.where(d > 0, sums[:, kcol["tp"]] / np.where(d > 0, d, 1), 0.0)
        elif key == "adjP":
            d = sums[:, kcol["tp"]] + sums[:, kcol["hal"]]
            vals = np.where(d > 0, sums[:, kcol["tp"]] / np.where(d > 0, d, 1), 0.0)
        elif key == "F1" or key == "F2":
            d1 = sums[:, kcol["tp"]] + sums[:, kcol["fn"]]
            rec = np.where(d1 > 0, sums[:, kcol["tp"]] / np.where(d1 > 0, d1, 1), 0.0)
            d2 = sums[:, kcol["tp"]] + sums[:, kcol["hal"]]
            adj = np.where(d2 > 0, sums[:, kcol["tp"]] / np.where(d2 > 0, d2, 1), 0.0)
            if key == "F1":
                s_ = rec + adj
                vals = np.where(s_ > 0, 2 * rec * adj / np.where(s_ > 0, s_, 1), 0.0)
            else:
                s_ = 4 * adj + rec
                vals = np.where(s_ > 0, 5 * rec * adj / np.where(s_ > 0, s_, 1), 0.0)
        elif key == "recall_core":
            d = sums[:, kcol["tp_core"]] + sums[:, kcol["fn_core"]]
            vals = np.where(d > 0, sums[:, kcol["tp_core"]] / np.where(d > 0, d, 1), 0.0)
        elif key == "recall_strict":
            d = sums[:, kcol["tp_strict"]] + sums[:, kcol["fn_strict"]]
            vals = np.where(d > 0, sums[:, kcol["tp_strict"]] / np.where(d > 0, d, 1), 0.0)
        elif key in ("usd_per_real", "usd_per_tp", "usd_per_beyond", "tok_per_real", "wall_per_real"):
            if key == "usd_per_real": den = sums[:, kcol["tp"]] + sums[:, kcol["real"]]
            elif key == "usd_per_tp": den = sums[:, kcol["tp"]]
            elif key == "usd_per_beyond": den = sums[:, kcol["real"]]
            elif key == "tok_per_real": den = sums[:, kcol["tp"]] + sums[:, kcol["real"]]
            else: den = sums[:, kcol["tp"]] + sums[:, kcol["real"]]
            num = sums[:, kcol["cost"]] if key.startswith("usd") else (
                sums[:, kcol["tok"]] if key.startswith("tok") else sums[:, kcol["wall"]])
            vals = np.where(den > 0, num / np.where(den > 0, den, 1), np.inf)
        elif key == "cost_run": vals = sums[:, kcol["cost"]] / n
        elif key == "tok_run": vals = sums[:, kcol["tok"]] / n
        elif key == "wall_run": vals = sums[:, kcol["wall"]] / n
        elif key == "real_total": vals = sums[:, kcol["tp"]] + sums[:, kcol["real"]]
        elif key == "price_per_ktok":
            vals = 1000.0 * sums[:, kcol["cost"]] / np.maximum(sums[:, kcol["tok"]], 1)
        else:
            raise KeyError(key)
        finite = np.isfinite(vals)
        frac = float(finite.mean())
        v = vals[finite] if finite.any() else np.array([base[key]])
        out[key] = (float(base[key]), float(np.percentile(v, 2.5)),
                    float(np.percentile(v, 97.5)), frac)
    return out

def paired_delta(cellA, cellB, urls, keys=("recall", "F1", "adjP", "real_total")):
    """Bootstrap CI of metric(A) - metric(B), resampling the same PRs for both."""
    MA, MB = cell_matrix(cellA, urls), cell_matrix(cellB, urls)
    n = len(urls)
    idx = rng.integers(0, n, size=(B, n))
    kcol = {k: j for j, k in enumerate(KEYS)}
    out = {}
    for key in keys:
        def metric_of(MS):
            tp = MS[:, kcol["tp"]]; fn = MS[:, kcol["fn"]]; hal = MS[:, kcol["hal"]]
            real = MS[:, kcol["real"]]
            if key == "recall":
                d = tp + fn
                return np.where(d > 0, tp / np.where(d > 0, d, 1), 0.0)
            if key == "adjP":
                d = tp + hal
                return np.where(d > 0, tp / np.where(d > 0, d, 1), 0.0)
            if key == "F1":
                d1 = tp + fn; d2 = tp + hal
                r = np.where(d1 > 0, tp / np.where(d1 > 0, d1, 1), 0.0)
                a = np.where(d2 > 0, tp / np.where(d2 > 0, d2, 1), 0.0)
                s_ = r + a
                return np.where(s_ > 0, 2 * r * a / np.where(s_ > 0, s_, 1), 0.0)
            if key == "real_total":
                return tp + real
            if key == "tok_run":
                return MS[:, kcol["tok"]] / n
            if key == "cost_run":
                return MS[:, kcol["cost"]] / n
            if key == "wall_run":
                return MS[:, kcol["wall"]] / n
            raise KeyError(key)
        dA = metric_of(MA[idx].sum(axis=1))
        dB = metric_of(MB[idx].sum(axis=1))
        delta = dA - dB
        pt = float(metric_of(MA.sum(axis=0)[None, :])[0] - metric_of(MB.sum(axis=0)[None, :])[0])
        out[key] = (pt, float(np.percentile(delta, 2.5)), float(np.percentile(delta, 97.5)))
    return out

def ci_txt(t, fmt="{:.2f}"):
    p, lo, hi, fr = t
    if fr < 0.975:
        return f"{fmt.format(p)} [{fmt.format(lo)}, {fmt.format(hi)}]*"
    return f"{fmt.format(p)} [{fmt.format(lo)}, {fmt.format(hi)}]"

# ============================================================================
# 1. The §8 matrix: per-cell metrics + CIs on the top-6
# ============================================================================
matrix = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            cell = (m, fw, e)
            urls = [u for u in TOP6 if u in sel[cell]]
            if not urls:
                continue
            M = cell_matrix(cell, urls)
            s = sums_of(M)
            s["n_pr"] = len(urls)
            met = metrics_from_sums(s)
            ci = boot_ci(M, len(urls))
            insts = sorted({sel[cell][u]["inst"] for u in urls})
            judges = sorted({sel[cell][u]["judge"] for u in urls})
            batches = sorted({sel[cell][u]["batch"] for u in urls})
            ts = sorted({sel[cell][u]["ts"][:10] for u in urls})
            pre_fix = sum(1 for u in urls if sel[cell][u]["ts"] < "2026-09-15T23:00")
            n_pmu_miss = sum(1 for r0 in D["selected_runs"]
                             if r0["model"] == m and r0["framework"] == fw and r0["effort"] == e
                             and r0["url"] in urls and r0.get("pmu_missing"))
            met.update({
                "n_pr": len(urls), "instruments": insts, "judges": judges,
                "batches": batches, "run_dates": ts,
                "glm_prefix_runs": pre_fix if m.startswith("glm") else None,
                "pmu_missing_runs": n_pmu_miss,
                "ci": ci,
                "wall_median": float(np.median([sel[cell][u]["wall"] for u in urls])),
            })
            matrix[f"{m}|{fw}|{e}"] = met

# wall-clock CI (median-of-PRs bootstrap, same machinery via percentile of resample)
def wall_ci(cell, urls):
    w = np.array([sel[cell][u]["wall"] for u in urls])
    idx = rng.integers(0, len(urls), size=(B, len(urls)))
    meds = np.median(w[idx], axis=1)
    return float(np.median(w)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))

for k, met in matrix.items():
    m, fw, e = k.split("|")
    urls = [u for u in TOP6 if u in sel[(m, fw, e)]]
    met["wall_med_ci"] = wall_ci((m, fw, e), urls)

# per-PR severity + recall for monotonicity (uses full-50 rows)
monotone = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            cell = (m, fw, e)
            urls = sorted(sel[cell])
            if len(urls) < 40:
                continue
            xs, ys = [], []
            for u in urls:
                v = sel[cell][u]
                xs.append(D["pr_golden"][u]["sev_weight"])
                d = v["tp"] + v["fn"]
                ys.append(v["tp"] / d if d else None)
            pairs = [(x, y) for x, y in zip(xs, ys) if y is not None]
            if len(pairs) < 10:
                continue
            x = np.array([p[0] for p in pairs]); y = np.array([p[1] for p in pairs])
            # Spearman by rank
            rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
            rho = float(np.corrcoef(rx, ry)[0, 1])
            monotone[f"{m}|{fw}|{e}"] = {"rho": rho, "n_pr": len(pairs)}

# F1-per-dollar ratio CI (separate seeded RNG so the frozen numbers above are unchanged)
rng2 = np.random.default_rng(SEED + 1)
for k, met in matrix.items():
    m, fw, e = k.split("|")
    cell = (m, fw, e)
    urls = [u for u in TOP6 if u in sel[cell]]
    Mr = cell_matrix(cell, urls)
    n = len(urls)
    idx = rng2.integers(0, n, size=(B, n))
    S = Mr[idx].sum(axis=1)
    kcol = {kk: j for j, kk in enumerate(KEYS)}
    tp = S[:, kcol["tp"]]; fn = S[:, kcol["fn"]]; hal = S[:, kcol["hal"]]
    d1 = tp + fn; d2 = tp + hal
    rec = np.where(d1 > 0, tp / np.where(d1 > 0, d1, 1), 0.0)
    adj = np.where(d2 > 0, tp / np.where(d2 > 0, d2, 1), 0.0)
    s_ = rec + adj
    f1 = np.where(s_ > 0, 2 * rec * adj / np.where(s_ > 0, s_, 1), 0.0)
    cost = S[:, kcol["cost"]] / n
    ratio = np.where(cost > 0, f1 / np.maximum(cost, 1e-12), np.inf)
    finite = np.isfinite(ratio)
    v = ratio[finite] if finite.any() else np.array([0.0])
    pt = met["F1"] / met["cost_run"] if met["cost_run"] else np.inf
    met["ci_f1_per_dollar"] = (float(pt), float(np.percentile(v, 2.5)),
                                float(np.percentile(v, 97.5)), float(finite.mean()))

# ============================================================================
# 2. Selection effect: top-6 vs full-50 on rows with >=40 PRs
# ============================================================================
sel_effect = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            cell = (m, fw, e)
            urls = sorted(sel[cell])
            if len(urls) < 40:
                continue
            Mfull = cell_matrix(cell, urls)
            s = sums_of(Mfull); s["n_pr"] = len(urls)
            full = metrics_from_sums(s)
            M6 = cell_matrix(cell, [u for u in TOP6 if u in sel[cell]])
            s6 = sums_of(M6); s6["n_pr"] = 6
            t6 = metrics_from_sums(s6)
            sel_effect[f"{m}|{fw}|{e}"] = {
                "n_full": len(urls),
                "recall_t6": t6["recall"], "recall_full": full["recall"],
                "adjP_t6": t6["adjP"], "adjP_full": full["adjP"],
                "F1_t6": t6["F1"], "F1_full": full["F1"],
                "F2_t6": t6["F2"], "F2_full": full["F2"],
                "ci_full_recall": boot_ci(Mfull, len(urls), keys=("recall", "F1"))["recall"],
                "ci_full_F1": boot_ci(Mfull, len(urls), keys=("recall", "F1"))["F1"],
            }

# ranking agreement: models ranked by F1 on top-6 vs full-50 within (fw, effort)
def _rank(vals):
    order = np.argsort(np.argsort(-np.array(vals)))
    return order

rank_agree = {}
for fw in FRAMEWORKS:
    for e in EFFORTS:
        models = [m for m in MODELS if f"{m}|{fw}|{e}" in sel_effect]
        if len(models) < 4:
            continue
        r6 = _rank([sel_effect[f"{m}|{fw}|{e}"]["F1_t6"] for m in models])
        rf = _rank([sel_effect[f"{m}|{fw}|{e}"]["F1_full"] for m in models])
        # Spearman on ranks
        rho = float(np.corrcoef(r6, rf)[0, 1])
        exact = int((r6 == rf).sum())
        rank_agree[f"{fw}|{e}"] = {"models": models, "spearman": rho, "exact_top1": exact == len(models),
                                   "ranks_t6": r6.tolist(), "ranks_full": rf.tolist()}

# ============================================================================
# 3. Framework deltas (harness vs vanilla), paired on top-6
# ============================================================================
fw_delta = {}
for m in MODELS:
    for fw in ("compound-realistic", "metareview-realistic"):
        for e in EFFORTS:
            A = (m, fw, e); V = (m, "vanilla-engineered", e)
            urls = [u for u in TOP6 if u in sel[A] and u in sel[V]]
            if len(urls) < 6:
                continue
            fw_delta[f"{m}|{fw}|{e}"] = paired_delta(A, V, urls)

# token multiple + cost multiple harness vs vanilla (point + CI)
tok_mult = {}
for m in MODELS:
    for fw in ("compound-realistic", "metareview-realistic"):
        for e in EFFORTS:
            A = (m, fw, e); V = (m, "vanilla-engineered", e)
            urls = [u for u in TOP6 if u in sel[A] and u in sel[V]]
            if len(urls) < 6:
                continue
            MA, MV = cell_matrix(A, urls), cell_matrix(V, urls)
            kcol = {k: j for j, k in enumerate(KEYS)}
            idx = rng.integers(0, len(urls), size=(B, len(urls)))
            ra = MA[idx].sum(axis=1)[:, kcol["tok"]] / len(urls)
            rv = MV[idx].sum(axis=1)[:, kcol["tok"]] / len(urls)
            ca = MA[idx].sum(axis=1)[:, kcol["cost"]] / len(urls)
            cv = MV[idx].sum(axis=1)[:, kcol["cost"]] / len(urls)
            tok_mult[f"{m}|{fw}|{e}"] = {
                "tok_ratio": (float(MA[:, kcol["tok"]].sum() / MV[:, kcol["tok"]].sum()),
                              float(np.percentile(ra / rv, 2.5)), float(np.percentile(ra / rv, 97.5))),
                "cost_ratio": (float(MA[:, kcol["cost"]].sum() / MV[:, kcol["cost"]].sum()),
                               float(np.percentile(ca / cv, 2.5)), float(np.percentile(ca / cv, 97.5))),
            }

# ============================================================================
# 4. Effort ladder: high vs medium paired deltas + cost ratio
# ============================================================================
effort = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        A = (m, fw, "high"); Md = (m, fw, "medium")
        urls = [u for u in TOP6 if u in sel[A] and u in sel[Md]]
        if len(urls) < 6:
            continue
        d = paired_delta(A, Md, urls, keys=("recall", "F1", "adjP", "real_total"))
        MA, MM = cell_matrix(A, urls), cell_matrix(Md, urls)
        kcol = {k: j for j, k in enumerate(KEYS)}
        cr = float(MA[:, kcol["cost"]].sum() / MM[:, kcol["cost"]].sum()) if MM[:, kcol["cost"]].sum() else np.inf
        idx = rng.integers(0, len(urls), size=(B, len(urls)))
        ca = MA[idx].sum(axis=1)[:, kcol["cost"]] / len(urls)
        cm = MM[idx].sum(axis=1)[:, kcol["cost"]] / len(urls)
        effort[f"{m}|{fw}"] = {
            "delta": d, "cost_ratio": (cr, float(np.percentile(ca / cm, 2.5)),
                                       float(np.percentile(ca / cm, 97.5)))
        }

# ============================================================================
# 5. Model-tier deltas: flash vs vision (paired, per framework/effort)
# ============================================================================
tier = {}
for fw in FRAMEWORKS:
    for e in EFFORTS:
        A = ("glm-5.3-flash-background", fw, e); V = ("glm-5.3-vision-background", fw, e)
        urls = [u for u in TOP6 if u in sel[A] and u in sel[V]]
        if len(urls) == 6:
            tier[f"{fw}|{e}"] = paired_delta(A, V, urls, keys=("recall", "F1", "adjP", "real_total"))

# legacy aside: glm-5.3-background vanilla top-6 (era-legal vanilla reuse)
legacy_aside = {}
for (m, fw, e), urls in legacy_sel.items():
    u6 = [u for u in TOP6 if u in urls]
    if fw == "vanilla-engineered" and len(u6) >= 5:
        M = np.zeros((len(u6), len(KEYS)))
        for i, u in enumerate(u6):
            v = legacy_sel[(m, fw, e)][u]
            for j, k in enumerate(KEYS):
                M[i, j] = v[k]
        s = sums_of(M); s["n_pr"] = len(u6)
        legacy_aside[f"{m}|{fw}|{e}"] = metrics_from_sums(s) | {"n_pr": len(u6)}

# ============================================================================
# 6. Pareto frontier on (usd_per_real, F1) — top-6 cells
# ============================================================================
pareto = []
for k, met in matrix.items():
    m, fw, e = k.split("|")
    if met["n_pr"] < 6:
        continue
    pareto.append({"cell": k, "model": m, "fw": fw, "eff": e,
                   "F1": met["F1"], "F2": met["F2"], "recall": met["recall"],
                   "adjP": met["adjP"], "usd_per_real": met["usd_per_real"],
                   "cost_run": met["cost_run"],
                   "F1_ci": met["ci"]["F1"], "usd_ci": met["ci"]["usd_per_real"]})
frontier = []
for p in pareto:
    dominated = any((q["F1"] >= p["F1"] and q["usd_per_real"] <= p["usd_per_real"]
                     and (q["F1"] > p["F1"] or q["usd_per_real"] < p["usd_per_real"]))
                    for q in pareto)
    if not dominated:
        frontier.append(p["cell"])
frontier = sorted(frontier, key=lambda c: pareto[[p["cell"] for p in pareto].index(c)]["usd_per_real"])

# ============================================================================
# 7. Cost-structure ratios (claim 2): per-token / tokens-per-task / cost-per-task
# ============================================================================
def blended(cell, urls=None):
    urls = urls or [u for u in TOP6 if u in sel[cell]]
    M = cell_matrix(cell, urls)
    s = sums_of(M)
    return s

ratio3 = {}
for glm_m, front_m, fw_g, fw_f, eff in [
    ("glm-5.3-flash-background", "claude-fable-5-1", "metareview-realistic", "vanilla-engineered", "low"),
    ("glm-5.3-vision-background", "claude-fable-5-1", "metareview-realistic", "vanilla-engineered", "low"),
    ("glm-5.3-flash-background", "claude-opus-5", "metareview-realistic", "vanilla-engineered", "low"),
    ("glm-5.3-vision-background", "claude-opus-5", "metareview-realistic", "vanilla-engineered", "low"),
    ("glm-5.3-flash-background", "gpt-6-astra", "metareview-realistic", "vanilla-engineered", "low"),
    ("glm-5.3-vision-background", "gpt-6-astra", "metareview-realistic", "vanilla-engineered", "low"),
    ("glm-5.3-flash-background", "claude-fable-5-1", "compound-realistic", "compound-realistic", "low"),
    ("glm-5.3-vision-background", "claude-fable-5-1", "compound-realistic", "compound-realistic", "low"),
    ("glm-5.3-vision-background", "claude-opus-5", "metareview-realistic", "metareview-realistic", "medium"),
]:
    A = (glm_m, fw_g, eff); F = (front_m, fw_f, eff)
    urls = [u for u in TOP6 if u in sel[A] and u in sel[F]]
    if len(urls) < 6:
        continue
    sa, sf = blended(A, urls), blended(F, urls)
    if sa["tok"] == 0 or sf["tok"] == 0 or sa["cost"] == 0 or sf["cost"] == 0:
        print(f"[ratio3] skipping zero-sum pair {A} vs {F}: sa={sa['tok']}/{sa['cost']} sf={sf['tok']}/{sf['cost']}")
        continue
    kcol = {k: j for j, k in enumerate(KEYS)}
    MA, MF = cell_matrix(A, urls), cell_matrix(F, urls)
    idx = rng.integers(0, 6, size=(B, 6))
    ta = MA[idx].sum(axis=1)[:, kcol["tok"]] / 6
    tf = MF[idx].sum(axis=1)[:, kcol["tok"]] / 6
    ca = MA[idx].sum(axis=1)[:, kcol["cost"]] / 6
    cf = MF[idx].sum(axis=1)[:, kcol["cost"]] / 6
    pa = 1000 * ca / np.maximum(ta, 1)
    pf = 1000 * cf / np.maximum(tf, 1)
    ratio3[f"{glm_m}|{fw_g}|low vs {front_m}|{fw_f}|{eff}"] = {
        "ptok_ratio": (float((sa['cost'] / sa['tok']) / (sf['cost'] / sf['tok'])),
                       float(np.percentile(pa / pf, 2.5)), float(np.percentile(pa / pf, 97.5))),
        "toktask_ratio": (float(sa['tok'] / sf['tok']),
                          float(np.percentile(ta / tf, 2.5)), float(np.percentile(ta / tf, 97.5))),
        "costtask_ratio": (float(sa['cost'] / sf['cost']),
                           float(np.percentile(ca / cf, 2.5)), float(np.percentile(ca / cf, 97.5))),
    }

# ============================================================================
# 8. Recommendation ratios: glm vision/flash @ low vs frontier reference cells
# ============================================================================
rec_cells = [("glm-5.3-vision-background", "metareview-realistic", "low"),
             ("glm-5.3-flash-background", "metareview-realistic", "low"),
             ("glm-5.3-vision-background", "compound-realistic", "low"),
             ("glm-5.3-flash-background", "compound-realistic", "low")]
front_ref = [("claude-opus-5", "compound-realistic", "low"),
             ("claude-opus-5", "compound-realistic", "high"),
             ("claude-fable-5-1", "vanilla-engineered", "low"),
             ("gpt-6-astra", "metareview-realistic", "high"),
             ("gpt-5.6-sol", "compound-realistic", "low")]
rec_ratios = {}
for A in rec_cells:
    for F in front_ref:
        urls = [u for u in TOP6 if u in sel[A] and u in sel[F]]
        if len(urls) < 6:
            continue
        kcol = {k: j for j, k in enumerate(KEYS)}
        MA, MF = cell_matrix(A, urls), cell_matrix(F, urls)
        idx = rng.integers(0, 6, size=(B, 6))
        def m_rec(MS):
            tp = MS[:, kcol["tp"]]; fn = MS[:, kcol["fn"]]
            return np.where(tp + fn > 0, tp / np.where(tp + fn > 0, tp + fn, 1), 0.0)
        def m_f1(MS):
            tp = MS[:, kcol["tp"]]; fn = MS[:, kcol["fn"]]; hal = MS[:, kcol["hal"]]
            r = np.where(tp + fn > 0, tp / np.where(tp + fn > 0, tp + fn, 1), 0.0)
            a = np.where(tp + hal > 0, tp / np.where(tp + hal > 0, tp + hal, 1), 0.0)
            s_ = r + a
            return np.where(s_ > 0, 2 * r * a / np.where(s_ > 0, s_, 1), 0.0)
        ra = m_rec(MA[idx].sum(axis=1)); rf = m_rec(MF[idx].sum(axis=1))
        fa = m_f1(MA[idx].sum(axis=1)); ff = m_f1(MF[idx].sum(axis=1))
        ca = MA[idx].sum(axis=1)[:, kcol["cost"]] / 6
        cf = MF[idx].sum(axis=1)[:, kcol["cost"]] / 6
        wa = MA[idx].sum(axis=1)[:, kcol["wall"]] / 6
        wf = MF[idx].sum(axis=1)[:, kcol["wall"]] / 6
        key = f"{'/'.join(A)} vs {'/'.join(F)}"
        rec_ratios[key] = {
            "recall_ratio": (float(m_rec(MA.sum(axis=0)[None,:])[0] / m_rec(MF.sum(axis=0)[None,:])[0]),
                             float(np.percentile(ra / np.maximum(rf, 1e-9), 2.5)),
                             float(np.percentile(ra / np.maximum(rf, 1e-9), 97.5))),
            "F1_ratio": (float(m_f1(MA.sum(axis=0)[None,:])[0] / m_f1(MF.sum(axis=0)[None,:])[0]),
                         float(np.percentile(fa / np.maximum(ff, 1e-9), 2.5)),
                         float(np.percentile(fa / np.maximum(ff, 1e-9), 97.5))),
            "cost_ratio": (float(MA[:, kcol['cost']].sum() / MF[:, kcol['cost']].sum()),
                           float(np.percentile(cf / np.maximum(ca, 1e-12), 2.5)),
                           float(np.percentile(cf / np.maximum(ca, 1e-12), 97.5))),
            "wall_ratio": (float(MA[:, kcol['wall']].sum() / MF[:, kcol['wall']].sum()),
                           float(np.percentile(wf / np.maximum(wa, 1e-9), 2.5)),
                           float(np.percentile(wf / np.maximum(wa, 1e-9), 97.5))),
            "cost_ratio_A_over_F": (float(MA[:, kcol['cost']].sum() / MF[:, kcol['cost']].sum()),
                                    float(np.percentile(ca / np.maximum(cf, 1e-12), 2.5)),
                                    float(np.percentile(ca / np.maximum(cf, 1e-12), 97.5))),
        }

# ============================================================================
# 9. Anthropic metered-vs-billed reconciliation
# ============================================================================
recon = []
for m in ("claude-fable-5-1", "claude-opus-5", "claude-sonnet-5"):
    errs = []
    for cell, urls in sel.items():
        if cell[0] != m:
            continue
        for u, v in urls.items():
            if v["pmu_cost"] > 0:
                errs.append(v["cost"] / v["pmu_cost"])
    if errs:
        recon.append({"model": m, "n": len(errs),
                      "median_metered_over_billed": float(np.median(errs)),
                      "p10": float(np.percentile(errs, 10)), "p90": float(np.percentile(errs, 90))})

# ============================================================================
# save + print
# ============================================================================
out = {
    "B": B, "seed": SEED, "price_retrieved": PRICE_RETRIEVED,
    "matrix": matrix, "monotonicity": monotone, "selection_effect": sel_effect,
    "rank_agreement": rank_agree, "framework_delta": {k: {m: list(v) if isinstance(v, tuple) else v for m, v in d.items()} for k, d in fw_delta.items()},
    "token_multiple": {k: {m: list(v) for m, v in d.items()} for k, d in tok_mult.items()},
    "effort_ladder": {k: {"delta": {m: list(v) for m, v in d["delta"].items()},
                          "cost_ratio": list(d["cost_ratio"])} for k, d in effort.items()},
    "tier_flash_vs_vision": {k: {m: list(v) for m, v in d.items()} for k, d in tier.items()},
    "legacy_aside": legacy_aside,
    "pareto": pareto, "pareto_frontier": frontier,
    "cost_structure_ratios": {k: {m: list(v) for m, v in d.items()} for k, d in ratio3.items()},
    "recommendation_ratios": rec_ratios,
    "anthropic_reconciliation": recon,
}
# ============================================================================
# 10. EXPANDED-GOLD analysis — strict benchmark vs hidden-gold union
#     (appended after every other rng consumer; rng3 keeps all frozen CIs intact)
# ============================================================================
rng3 = np.random.default_rng(SEED + 2)

# PRIMARY clustering key: file:startline:endline extracted from the finding's
# own text prefix (the same _LOC_RE pattern tools/anchor_matcher.py uses).
# Findings without an anchor fall back to rj3-normalization + difflib (0.75),
# bucketed by file path. Anchored findings sharing a line-range are one issue;
# distinct issues on the same anchor over-merge (disclosed).
import re as _re
_ANCHOR_RE = _re.compile(r"^([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4}):(\d+)(?:-(\d+))?")

def anchor_key(t):
    m = _ANCHOR_RE.match(t)
    if m:
        return ("A", m.group(1), int(m.group(2)), int(m.group(3) or m.group(2)))
    return None

def bucketed_cluster(texts, threshold=0.75):
    reps = []
    assign = [None] * len(texts)
    buckets = defaultdict(list)
    for i, t in enumerate(texts):
        buckets[(t.split(" ")[0] if t else "")].append(i)
    for b, idxs in buckets.items():
        local = []
        for i in idxs:
            norm = texts[i]
            best, best_r = -1, 0.0
            for j in local:
                ratio = 1.0 if norm == reps[j] else difflib.SequenceMatcher(None, norm, reps[j]).ratio()
                if ratio > best_r: best, best_r = j, ratio
            if best >= 0 and best_r >= threshold:
                assign[i] = best
            else:
                reps.append(norm); assign[i] = len(reps) - 1; local.append(len(reps) - 1)
    return reps, assign

pr_texts = defaultdict(list)
bounds_by_run = {}
for r in D["all_healthy_runs"]:
    bts = r.get("bugtexts") or []
    start_i = len(pr_texts[r["url"]])
    pr_texts[r["url"]] += bts
    bounds_by_run[r["run_id"]] = (start_i, start_i + len(bts))

# per-PR key assignment: anchor-primary, text-cluster fallback
assign = {}
n_anchored = 0
for u, texts in pr_texts.items():
    keys = [None] * len(texts)
    anchorless_idx = [i for i, t in enumerate(texts) if anchor_key(t) is None]
    for i, t in enumerate(texts):
        ak = anchor_key(t)
        if ak is not None:
            keys[i] = ak
            n_anchored += 1
    if anchorless_idx:
        at = [texts[i] for i in anchorless_idx]
        _, a2 = bucketed_cluster(at)
        for j, i in enumerate(anchorless_idx):
            keys[i] = ("T", a2[j])
    assign[u] = keys

n_clusters = {u: len(set(k for k in assign[u] if k)) for u in pr_texts}
n_gold = {u: D["pr_golden"][u]["n_comments"] for u in D["pr_golden"]}
exp_size = {u: n_gold[u] + n_clusters.get(u, 0) for u in n_gold}
anchor_cov = n_anchored / max(1, sum(len(v) for v in pr_texts.values()))

def own_ids_for(run):
    s_, e_ = bounds_by_run[run["run_id"]]
    return set(k for k in assign[run["url"]][s_:e_] if k)

def exp_point(run):
    own = own_ids_for(run)
    pr = run["url"]
    tp_exp = run["tp"] + len(own)
    fn_exp = exp_size[pr] - tp_exp
    hal = run["rj3"]["hal"] if run["rj3"] else run["inrun"]["hal"]
    rec = tp_exp / (tp_exp + fn_exp) if (tp_exp + fn_exp) else 0.0
    adj = tp_exp / (tp_exp + hal) if (tp_exp + hal) else 0.0
    f1 = 2 * rec * adj / (rec + adj) if (rec + adj) else 0.0
    f2 = 5 * rec * adj / (4 * adj + rec) if (rec + adj) else 0.0
    return {"tp_exp": tp_exp, "fn_exp": fn_exp, "hal": hal,
            "exp_size": exp_size[pr], "recall_exp": rec, "adjP_exp": adj,
            "F1_exp": f1, "F2_exp": f2}

exp_matrix = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            cell = (m, fw, e)
            urls = [u for u in TOP6 if u in sel[cell]]
            if not urls:
                continue
            runs_cell = [next(x for x in D["selected_runs"] if x["model"]==m and x["framework"]==fw and x["effort"]==e and x["url"]==u) for u in urls]
            per = [exp_point(r0) for r0 in runs_cell]
            n = len(per)
            TP = sum(p["tp_exp"] for p in per); HAL = sum(p["hal"] for p in per)
            exp_sz = sum(p["exp_size"] for p in per)
            rec = TP / exp_sz if exp_sz else 0.0
            adj = TP / (TP + HAL) if (TP + HAL) else 0.0
            f1 = 2 * rec * adj / (rec + adj) if (rec + adj) else 0.0
            f2 = 5 * rec * adj / (4 * adj + rec) if (rec + adj) else 0.0
            idx = rng3.integers(0, n, size=(B, n))
            arr = np.array([[p["tp_exp"], p["exp_size"], p["hal"]] for p in per])
            S = arr[idx]
            tp_b = S[:, :, 0].sum(axis=1); sz_b = S[:, :, 1].sum(axis=1); hal_b = S[:, :, 2].sum(axis=1)
            fn_b = sz_b - tp_b
            r_b = np.where(tp_b + fn_b > 0, tp_b / np.where(tp_b + fn_b > 0, tp_b + fn_b, 1), 0)
            a_b = np.where(tp_b + hal_b > 0, tp_b / np.where(tp_b + hal_b > 0, tp_b + hal_b, 1), 0)
            s_ = r_b + a_b
            f_b = np.where(s_ > 0, 2 * r_b * a_b / np.where(s_ > 0, s_, 1), 0)
            exp_matrix[f"{m}|{fw}|{e}"] = {
                "n_pr": n, "TP_exp": TP, "hal": HAL,
                "recall_exp": rec, "adjP_exp": adj, "F1_exp": f1, "F2_exp": f2,
                "ci": {"recall_exp": (float(rec), float(np.percentile(r_b, 2.5)), float(np.percentile(r_b, 97.5)), 1.0),
                        "F1_exp": (float(f1), float(np.percentile(f_b, 2.5)), float(np.percentile(f_b, 97.5)), 1.0)},
            }

# paired harness-vs-vanilla deltas under recall_exp (top-6, rng3)
fw_delta_exp = {}
for m in MODELS:
    for fw in ("compound-realistic", "metareview-realistic"):
        for e in EFFORTS:
            A = (m, fw, e); V = (m, "vanilla-engineered", e)
            urls = [u for u in TOP6 if u in sel[A] and u in sel[V]]
            if len(urls) < 6:
                continue
            def percell(cell):
                rs = [next(x for x in D["selected_runs"] if (x["model"],x["framework"],x["effort"],x["url"])==(cell[0],cell[1],cell[2],u)) for u in urls]
                return [exp_point(r0) for r0 in rs]
            perA = percell(A); perV = percell(V)
            n = len(urls)
            idx = rng3.integers(0, n, size=(B, n))
            def mk(per):
                return (np.array([p["tp_exp"] for p in per]), np.array([p["exp_size"] for p in per]), np.array([p["hal"] for p in per]))
            tpA, szA, halA = mk(perA); tpV, szV, halV = mk(perV)
            def mets(tp, sz, hal, ix):
                t = tp[ix].sum(axis=1); s = sz[ix].sum(axis=1); h = hal[ix].sum(axis=1)
                f = s - t
                r = np.where(t + f > 0, t / np.where(t + f > 0, t + f, 1), 0)
                a = np.where(t + h > 0, t / np.where(t + h > 0, t + h, 1), 0)
                su = r + a
                f1 = np.where(su > 0, 2 * r * a / np.where(su > 0, su, 1), 0)
                return r, f1
            rA, fA = mets(tpA, szA, halA, idx); rV, fV = mets(tpV, szV, halV, idx)
            pt_rA = tpA.sum()/(tpA.sum()+(szA-tpA).sum()) if tpA.sum()+(szA-tpA).sum() else 0
            pt_rV = tpV.sum()/(tpV.sum()+(szV-tpV).sum()) if tpV.sum()+(szV-tpV).sum() else 0
            fw_delta_exp[f"{m}|{fw}|{e}"] = {
                "dRecall_exp": (float(pt_rA - pt_rV), float(np.percentile(rA - rV, 2.5)), float(np.percentile(rA - rV, 97.5))),
            }

# full-50 expanded metrics per cell (sample-bias check under the real-world lens)
# + per-PR expanded recall (selection view) for cells with >=40 PRs
SHloc = {"claude-fable-5-1": "fable-5.1", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
         "claude-opus-5": "opus-5", "glm-5.3-vision-background": "glm-vis",
         "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet-5",
         "glm-5.3-flash-background": "glm-flash",
         "vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV"}
sel_effect_exp = {}
percell_exp = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            cell = (m, fw, e)
            urls = sorted(sel[cell])
            if len(urls) < 40:
                continue
            runs_cell = [next(x for x in D["selected_runs"] if (x["model"], x["framework"], x["effort"], x["url"]) == (m, fw, e, u)) for u in urls]
            per = [exp_point(r0) for r0 in runs_cell]
            TP = sum(p["tp_exp"] for p in per); HAL = sum(p["hal"] for p in per); SZ = sum(p["exp_size"] for p in per)
            rec_full = TP / SZ if SZ else 0.0
            adj_full = TP / (TP + HAL) if (TP + HAL) else 0.0
            f1_full = 2 * rec_full * adj_full / (rec_full + adj_full) if (rec_full + adj_full) else 0.0
            t6 = exp_matrix.get(f"{m}|{fw}|{e}")
            sel_effect_exp[f"{m}|{fw}|{e}"] = {
                "recall_exp_t6": t6["recall_exp"] if t6 else None,
                "recall_exp_full": rec_full,
                "F1_exp_t6": t6["F1_exp"] if t6 else None,
                "F1_exp_full": f1_full,
            }
            label = f"{SHloc[m]}·{SHloc[fw]}·{e}"
            percell_exp[label] = {"model": m, "fw": fw, "eff": e, "prs": [
                {"pr": u.rsplit("/", 1)[-1], "sev": D["pr_golden"][u]["sev_weight"],
                 "rec_exp": p["recall_exp"],
                 "rec": (r0["tp"] / (r0["tp"] + r0["fn"])) if (r0["tp"] + r0["fn"]) else None,
                 "top6": u in TOP6}
                for u, p, r0 in zip(urls, per, runs_cell)]}

out["expanded_gold"] = {
    "construction": ("per PR, cluster ALL confirmed-bug findings (rj3 'bug' / in-run "
                     "'real_but_ungold') across ALL healthy scored runs (era-legal universe, "
                     "low/medium/high efforts). PRIMARY key = file:startline:endline "
                     "extracted from each finding's own text prefix (the anchor_matcher "
                     "pattern); fallback for anchorless findings = rj3 normalization + "
                     "difflib 0.75 bucketed by file path. Expanded set = goldens + distinct "
                     "keys. tp_exp = golden TP + own distinct keys; fn_exp = expanded size "
                     "- tp_exp; adjP_exp = tp_exp/(tp_exp+hallucinations). Over-merge risk: "
                     "distinct issues sharing one anchor; under-merge risk: cross-file "
                     "rewordings => recall_exp conservative. important_non_bug excluded "
                     "(bugs only). Golden-vs-cluster overlaps may double-count a few "
                     "entries => further conservative. SUPERSEDED by "
                     "expanded_gold_semantic (§10b): the §10 key-union overcounts "
                     "distinct bugs ~17x (paraphrase splits), and a 2026-09-17 extract "
                     "bugfix (rj3 records were silently dropped from bugtexts — 706 "
                     "confirmed bugs, mostly vanilla cells) means §10 also "
                     "underrepresents rj3-adjudicated runs. §10 retained for provenance."),
    "anchor_coverage": float(anchor_cov),
    "per_pr": {u: {"golden": n_gold[u], "union": n_clusters.get(u, 0), "expanded": exp_size[u]} for u in TOP6},
    "matrix_exp": exp_matrix,
    "framework_delta_exp": fw_delta_exp,
    "sel_effect_exp": sel_effect_exp,
    "percell_exp": percell_exp,
}

# ============================================================================
# §10b — SEMANTIC UNION (honest denominators; rj3-fix universe; PRIMARY result)
# ============================================================================
# Source: analysis/exp_union_semantic_pilot_<slug>.json — LLM semantic merge
# (judge gpt-5.2, dedup_bugs_llm prompt from branch sdlc-loop-experiment, run
# 2026-09-17 on the rj3-FIXED dataset). Clusters = distinct real bugs.
# rng4 = SEED+3 appended after all other rng consumers: frozen CIs byte-identical.
rng4 = np.random.default_rng(SEED + 3)

_sem_by_url = {}
for _u in TOP6:
    _slug = _u.rstrip("/").split("/")[-1]
    _sem_by_url[_u] = json.load(open(f"{ROOT}/analysis/exp_union_semantic_pilot_{_slug}.json"))

def _sem_flat(url):
    """Rebuild the pilot's flat finding order: (run_id, text) per all-healthy run."""
    _runs = [r for r in D["all_healthy_runs"] if r["url"] == url]
    return [(_r["run_id"], _t) for _r in _runs for _t in (_r.get("bugtexts") or [])]

def _sem_bounds(url):
    """run_id -> [start, end) over the pilot's flat order (runs in dataset order,
    texts within run). ALL runs of the PR get an entry — zero-width for runs with
    no confirmed bugs (their own-cluster count is 0)."""
    bnd, i = {}, 0
    for r in D["all_healthy_runs"]:
        if r["url"] != url:
            continue
        n = len(r.get("bugtexts") or [])
        bnd[r["run_id"]] = [i, i + n]
        i += n
    return bnd

def _sem_own_and_counts(m, fw, e, u):
    """(own clusters, hal, imp, golden tp) for the selected run of cell (m,fw,e) on PR u."""
    p = _sem_by_url[u]
    f2c = {int(k): v for k, v in p["finding_to_cluster"].items()}
    bnd = _sem_bounds(u)
    r0 = next(x for x in D["selected_runs"] if (x["model"], x["framework"], x["effort"], x["url"]) == (m, fw, e, u))
    s_, e_ = bnd[r0["run_id"]]
    own = len({f2c[i2] for i2 in range(s_, e_)})
    v = r0["rj3"] or r0["inrun"]
    return own, v["hal"], v["imp"], r0["tp"]

_sem_cells = {}
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            cell = (m, fw, e)
            urls = [u for u in TOP6 if u in sel[cell]]
            if not urls:
                continue
            rows = []
            for u in urls:
                own, hal, imp, tp = _sem_own_and_counts(m, fw, e, u)
                p = _sem_by_url[u]
                rows.append([tp + own,
                             p["goldens"] + p["semantic_union_size"], hal, imp])
            n = len(rows)
            arr = np.array(rows, dtype=float)
            TP, DEN, HAL, IMP = arr[:, 0].sum(), arr[:, 1].sum(), arr[:, 2].sum(), arr[:, 3].sum()
            rec = TP / DEN if DEN else 0.0
            adj = TP / (TP + HAL) if (TP + HAL) else 0.0
            adjp = TP / (TP + HAL + IMP) if (TP + HAL + IMP) else 0.0
            f1 = 2 * rec * adj / (rec + adj) if (rec + adj) else 0.0
            f1p = 2 * rec * adjp / (rec + adjp) if (rec + adjp) else 0.0
            idx = rng4.integers(0, n, size=(B, n))
            S = arr[idx]
            tp_b = S[:, :, 0].sum(axis=1); den_b = S[:, :, 1].sum(axis=1)
            hal_b = S[:, :, 2].sum(axis=1); imp_b = S[:, :, 3].sum(axis=1)
            r_b = np.where(den_b > 0, tp_b / np.where(den_b > 0, den_b, 1), 0)
            a_b = np.where(tp_b + hal_b > 0, tp_b / np.where(tp_b + hal_b > 0, tp_b + hal_b, 1), 0)
            ap_b = np.where(tp_b + hal_b + imp_b > 0, tp_b / np.where(tp_b + hal_b + imp_b > 0, tp_b + hal_b + imp_b, 1), 0)
            f_b = np.where(r_b + a_b > 0, 2 * r_b * a_b / np.where(r_b + a_b > 0, r_b + a_b, 1), 0)
            fp_b = np.where(r_b + ap_b > 0, 2 * r_b * ap_b / np.where(r_b + ap_b > 0, r_b + ap_b, 1), 0)
            _sem_cells[f"{m}|{fw}|{e}"] = {
                "n_pr": n, "TP_sem": int(TP), "hal": int(HAL), "imp": int(IMP),
                "recall_sem": float(rec), "adjP": float(adj), "adjPp": float(adjp),
                "F1": float(f1), "F1p": float(f1p),
                "ci": {"recall_sem": (float(rec), float(np.percentile(r_b, 2.5)), float(np.percentile(r_b, 97.5)), 1.0),
                        "F1": (float(f1), float(np.percentile(f_b, 2.5)), float(np.percentile(f_b, 97.5)), 1.0),
                        "F1p": (float(f1p), float(np.percentile(fp_b, 2.5)), float(np.percentile(fp_b, 97.5)), 1.0)},
            }

def _sem_rows(cell, urls, with_counts=True):
    rows = []
    for u in urls:
        own, hal, imp, tp = _sem_own_and_counts(cell[0], cell[1], cell[2], u)
        p = _sem_by_url[u]
        r = [tp + own, p["goldens"] + p["semantic_union_size"]]
        if with_counts:
            r += [hal, imp]
        rows.append(r)
    return np.array(rows, dtype=float)

# paired CE-vs-MRV deltas under the semantic metrics (per model·effort, rng4)
_sem_pairs = {}
for m in MODELS:
    for e in EFFORTS:
        cCE, cMRV = (m, "compound-realistic", e), (m, "metareview-realistic", e)
        urls = [u for u in TOP6 if u in sel[cCE] and u in sel[cMRV]]
        if len(urls) < 2:
            continue
        A, Mv = _sem_rows(cCE, urls), _sem_rows(cMRV, urls)
        n = len(urls)
        def _mets(X, ix):
            t = X[ix][:, 0].sum(axis=1); d = X[ix][:, 1].sum(axis=1)
            h = X[ix][:, 2].sum(axis=1); im = X[ix][:, 3].sum(axis=1)
            r = np.where(d > 0, t / np.where(d > 0, d, 1), 0)
            a = np.where(t + h > 0, t / np.where(t + h > 0, t + h, 1), 0)
            ap = np.where(t + h + im > 0, t / np.where(t + h + im > 0, t + h + im, 1), 0)
            f1 = np.where(r + a > 0, 2 * r * a / np.where(r + a > 0, r + a, 1), 0)
            f1p = np.where(r + ap > 0, 2 * r * ap / np.where(r + ap > 0, r + ap, 1), 0)
            return r, f1, f1p
        idx = rng4.integers(0, n, size=(B, n))
        rA, fA, fpA = _mets(A, idx); rM, fM, fpM = _mets(Mv, idx)
        def _pm(X):
            t, d, h, im = X[:, 0].sum(), X[:, 1].sum(), X[:, 2].sum(), X[:, 3].sum()
            r_ = t / d if d else 0
            a_ = t / (t + h) if (t + h) else 0
            ap_ = t / (t + h + im) if (t + h + im) else 0
            f_ = 2 * r_ * a_ / (r_ + a_) if (r_ + a_) else 0
            fp_ = 2 * r_ * ap_ / (r_ + ap_) if (r_ + ap_) else 0
            return r_, f_, fp_
        rA0, fA0, fpA0 = _pm(A); rM0, fM0, fpM0 = _pm(Mv)
        _sem_pairs[f"{m}|{e}"] = {
            "n_pr": n,
            "dRecall_sem": (float(rM0 - rA0), float(np.percentile(rM - rA, 2.5)), float(np.percentile(rM - rA, 97.5))),
            "dF1": (float(fM0 - fA0), float(np.percentile(fM - fA, 2.5)), float(np.percentile(fM - fA, 97.5))),
            "dF1p": (float(fpM0 - fpA0), float(np.percentile(fpM - fpA, 2.5)), float(np.percentile(fpM - fpA, 97.5))),
        }

# paired harness-vs-vanilla deltas under recall_sem (T10 analogue, rng4)
_hv_sem = {}
for m in MODELS:
    for fw in ("compound-realistic", "metareview-realistic"):
        for e in EFFORTS:
            Ah = (m, fw, e); V = (m, "vanilla-engineered", e)
            urls = [u for u in TOP6 if u in sel[Ah] and u in sel[V]]
            if len(urls) < 2:
                continue
            XA = _sem_rows(Ah, urls, with_counts=False)
            XV = _sem_rows(V, urls, with_counts=False)
            n = len(urls)
            idx = rng4.integers(0, n, size=(B, n))
            SA, SV = XA[idx], XV[idx]
            rA = np.where(SA[:, :, 1] > 0, SA[:, :, 0] / np.where(SA[:, :, 1] > 0, SA[:, :, 1], 1), 0).sum(axis=1) / n
            rV = np.where(SV[:, :, 1] > 0, SV[:, :, 0] / np.where(SV[:, :, 1] > 0, SV[:, :, 1], 1), 0).sum(axis=1) / n
            pA = XA[:, 0].sum() / XA[:, 1].sum() if XA[:, 1].sum() else 0
            pV = XV[:, 0].sum() / XV[:, 1].sum() if XV[:, 1].sum() else 0
            _hv_sem[f"{m}|{fw}|{e}"] = {
                "n_pr": n,
                "dRecall_sem": (float(pA - pV), float(np.percentile(rA - rV, 2.5)), float(np.percentile(rA - rV, 97.5))),
            }

out["expanded_gold_semantic"] = {
    "construction": ("§10b PRIMARY real-world result. Per top-6 PR, ALL confirmed-bug "
                     "findings (rj3 'bug' / in-run 'real_but_ungold'; hallucinations and "
                     "important_non_bug EXCLUDED at the adjudication gate) across ALL "
                     "healthy scored runs are semantically clustered into DISTINCT REAL "
                     "BUGS by judge gpt-5.2 (file-grouped dedup_bugs_llm prompt from "
                     "branch sdlc-loop-experiment; chunked per-file clustering + per-file "
                     "rep merge + cross-file merge to fixpoint; artifacts "
                     "analysis/exp_union_semantic_pilot_<pr>.json, run 2026-09-17 on the "
                     "rj3-FIXED dataset — extract bugfix: rj3 records were previously "
                     "dropped, 706 confirmed bugs missing, mostly vanilla cells). Union "
                     "= 359 distinct bugs + 42 goldens across the 6 PRs. tp_sem = golden "
                     "TP + distinct clusters hit by the cell's selected run. recall_sem = "
                     "tp_sem/(goldens+union). adjP = tp_sem/(tp_sem+hallucinations) "
                     "(claim soundness; strict-benchmark-compatible). adjPp = "
                     "tp_sem/(tp_sem+hallucinations+important_non_bug) (user lens: every "
                     "nitpick the reader wades through). F1 = harmonic(recall_sem, adjP); "
                     "F1p = harmonic(recall_sem, adjPp). Residual under-merge => union "
                     "mildly overcounts distinct bugs => recall_sem conservative. LLM "
                     "clustering is not deterministic; provenance = judge model + prompt "
                     "+ stored artifacts + date. CIs: cluster (PR-level) bootstrap, "
                     "B=10000, seed 20260916, rng4=SEED+3."),
    "per_pr": {u: {"goldens": _sem_by_url[u]["goldens"],
                    "union_sem": _sem_by_url[u]["semantic_union_size"],
                    "n_findings": _sem_by_url[u]["n_findings"],
                    "judge_calls": _sem_by_url[u]["judge_calls"]} for u in TOP6},
    "matrix_sem": _sem_cells,
    "ce_vs_mrv": _sem_pairs,
    "harness_vs_vanilla_sem": _hv_sem,
}

# pairs-level aggregate: resample the (model·effort) pairs themselves (rng4)
_pair_keys = sorted(_sem_pairs)
_pm = {met: np.array([_sem_pairs[k][met][0] for k in _pair_keys])
       for met in ("dRecall_sem", "dF1", "dF1p")}
_npairs = len(_pair_keys)
_pidx = rng4.integers(0, _npairs, size=(B, _npairs))
out["expanded_gold_semantic"]["pairs_summary"] = {
    "n_pairs": _npairs,
    "signs": {met: {"pos": int((_pm[met] > 0).sum()), "zero": int((_pm[met] == 0).sum()), "neg": int((_pm[met] < 0).sum())}
               for met in ("dRecall_sem", "dF1", "dF1p")},
    "mean": {met: float(_pm[met].mean()) for met in ("dRecall_sem", "dF1", "dF1p")},
    "ci_mean": {met: (float(_pm[met].mean()),
                        float(np.percentile(_pm[met][_pidx].mean(axis=1), 2.5)),
                        float(np.percentile(_pm[met][_pidx].mean(axis=1), 97.5)))
                 for met in ("dRecall_sem", "dF1", "dF1p")},
}


# ============================================================================
# §10c — VERIFIED UNION (dedup + golden-overlap corrected; supersedes §10b levels)
# ============================================================================
# Two corrections to §10b, both measured by the LLM verification passes:
#   (1) UNDER-MERGE: a stricter whole-PR re-merge collapsed 359 raw clusters -> 258.
#   (2) GOLDEN OVERLAP: 49 raw clusters describe defects ALREADY in the golden set
#       (the official text-only matcher missed them); a strict adversarial re-check
#       decides which survive. Counting them as new inflated both the denominator
#       and the per-run credit.
# Credit rules reported side by side:
#   A (benchmark-compatible): goldens found = the official matcher's TP identities only.
#   B (real-world, PRIMARY):  goldens found = official ∪ goldens the run's own clusters
#      were verified to be the same defect as (credit for finding it regardless of
#      which instrument noticed). Both avoid double counting: an additional cluster is
#      only counted when it is NOT a golden overlap.
# rng5 = SEED+4 (appended after all other rng consumers; earlier sections untouched).
rng5 = np.random.default_rng(SEED + 4)

def _ci(pt, lo, hi):
    """Percentile CI, clamped to contain the point estimate (tiny-n bootstrap resamples can
    produce percentile bounds that exclude the observed value; negative error bars downstream)."""
    return (float(pt), float(min(lo, pt)), float(max(hi, pt)), 1.0)

_VERIFIED_OK = True
_vrfy, _strict = {}, {}
for _u in TOP6:
    _slug = _u.rstrip("/").split("/")[-1]
    try:
        _vrfy[_u] = json.load(open(f"{ROOT}/analysis/semantic_true_golden_verify_{_slug}.json"))
        _strict[_u] = json.load(open(f"{ROOT}/analysis/semantic_overlap_locked_{_slug}.json"))
    except FileNotFoundError:
        _VERIFIED_OK = False
        break

def _goldens_list(pr):
    import glob as _glob
    for _f in _glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json"):
        for _e in json.load(open(_f)):
            if _e["url"] == pr:
                return [c["comment"] for c in _e["comments"]]
    return []

if _VERIFIED_OK:
    _v_pr = {}
    for _u in TOP6:
        _groups = _vrfy[_u]["clusters"]
        _sc = _strict[_u]["clusters"]
        assert len(_groups) == len(_sc)
        _raw2g = {}
        for _gi, _g in enumerate(_groups):
            for _r in _g["merge_group"]:
                _raw2g[_r] = _gi
        _gl = _goldens_list(_u)
        _strict_g = [c.get("locked_golden") for c in _sc]   # locked overlap (None = verified additional)
        _v_pr[_u] = {
            "goldens": _gl, "raw2g": _raw2g,
            "group_golden": _strict_g,                     # None -> additional
            "n_additional": sum(1 for x in _strict_g if x is None),
            "n_merged": len(_groups),
            "n_overlap_strict": sum(1 for x in _strict_g if x is not None),
        }

    def _verified_rows(cell, urls):
        rows = []
        for u in urls:
            p = _v_pr[u]
            f2c = {int(k): v for k, v in _sem_by_url[u]["finding_to_cluster"].items()}
            bnd = _sem_bounds(u)   # all runs of the PR, zero-width when no confirmed findings
            r0 = next(x for x in D["selected_runs"] if (x["model"], x["framework"], x["effort"], x["url"]) == (cell[0], cell[1], cell[2], u))
            s_, e_ = bnd[r0["run_id"]]
            own_groups = {p["raw2g"][f2c[i2]] for i2 in range(s_, e_)}
            own_add = sum(1 for g in own_groups if p["group_golden"][g] is None)
            own_gv = {p["group_golden"][g] for g in own_groups if p["group_golden"][g] is not None}
            official = {p["goldens"].index(t) for t in (r0.get("matched_goldens") or []) if t in p["goldens"]}
            v = r0["rj3"] or r0["inrun"]
            rows.append({"tpA": len(official) + own_add, "tpB": len(official | own_gv) + own_add,
                         "den": len(p["goldens"]) + p["n_additional"], "hal": v["hal"], "imp": v["imp"]})
        return rows

    _vcells, _vcells_A = {}, {}
    for m in MODELS:
        for fw in FRAMEWORKS:
            for e in EFFORTS:
                cell = (m, fw, e)
                urls = [u for u in TOP6 if u in sel[cell]]
                if not urls:
                    continue
                rows = _verified_rows(cell, urls)
                n = len(rows)
                arr = np.array([[r["tpA"], r["tpB"], r["den"], r["hal"], r["imp"]] for r in rows], dtype=float)
                idx = rng5.integers(0, n, size=(B, n))
                S = arr[idx]
                def _vec(tp, den, hal, imp):
                    rec = np.where(den > 0, tp / np.where(den > 0, den, 1), 0)
                    adj = np.where(tp + hal > 0, tp / np.where(tp + hal > 0, tp + hal, 1), 0)
                    adjp = np.where(tp + hal + imp > 0, tp / np.where(tp + hal + imp > 0, tp + hal + imp, 1), 0)
                    f1 = np.where(rec + adj > 0, 2 * rec * adj / np.where(rec + adj > 0, rec + adj, 1), 0)
                    f1p = np.where(rec + adjp > 0, 2 * rec * adjp / np.where(rec + adjp > 0, rec + adjp, 1), 0)
                    return rec, adj, adjp, f1, f1p

                def _pt(tp, den, hal, imp):
                    t, d, h, im = float(tp.sum()), float(den.sum()), float(hal.sum()), float(imp.sum())
                    rec = t / d if d else 0.0
                    adj = t / (t + h) if (t + h) else 0.0
                    adjp = t / (t + h + im) if (t + h + im) else 0.0
                    f1 = 2 * rec * adj / (rec + adj) if (rec + adj) else 0.0
                    f1p = 2 * rec * adjp / (rec + adjp) if (rec + adjp) else 0.0
                    return rec, adj, adjp, f1, f1p
                # aggregate each bootstrap replicate over the sampled PRs (axis=1)
                tpBv, denv, halv, impv = S[:, :, 1].sum(axis=1), S[:, :, 2].sum(axis=1), S[:, :, 3].sum(axis=1), S[:, :, 4].sum(axis=1)
                tpAv = S[:, :, 0].sum(axis=1)
                recB, adjB, adjpB, f1B, f1pB = _vec(tpBv, denv, halv, impv)
                recA, adjA, adjpA, f1A, f1pA = _vec(tpAv, denv, halv, impv)
                pA = _pt(arr[:, 0], arr[:, 2], arr[:, 3], arr[:, 4])
                pB = _pt(arr[:, 1], arr[:, 2], arr[:, 3], arr[:, 4])
                _vcells[f"{m}|{fw}|{e}"] = {
                    "n_pr": n, "TP_sem": int(arr[:, 1].sum()), "TP_bench": int(arr[:, 0].sum()),
                    "den": int(arr[:, 2].sum()), "hal": int(arr[:, 3].sum()), "imp": int(arr[:, 4].sum()),
                    "recall_sem": pB[0], "adjP": pB[1], "adjPp": pB[2], "F1": pB[3], "F1p": pB[4],
                    "recall_bench": pA[0], "F1_bench": pA[3],
                    "ci": {"recall_sem": _ci(pB[0], np.percentile(recB, 2.5), np.percentile(recB, 97.5)),
                           "F1": _ci(pB[3], np.percentile(f1B, 2.5), np.percentile(f1B, 97.5)),
                           "F1p": _ci(pB[4], np.percentile(f1pB, 2.5), np.percentile(f1pB, 97.5))},
                }

    def _pm_of(X):
        t = X[:, 0].sum(); d = X[:, 1].sum(); h = X[:, 2].sum(); im = X[:, 3].sum()
        r = t / d if d else 0.0
        a = t / (t + h) if (t + h) else 0.0
        ap = t / (t + h + im) if (t + h + im) else 0.0
        f = 2 * r * a / (r + a) if (r + a) else 0.0
        fp = 2 * r * ap / (r + ap) if (r + ap) else 0.0
        return r, f, fp

    _vpairs = {}
    for m in MODELS:
        for e in EFFORTS:
            cCE, cMRV = (m, "compound-realistic", e), (m, "metareview-realistic", e)
            urls = [u for u in TOP6 if u in sel[cCE] and u in sel[cMRV]]
            if len(urls) < 2:
                continue
            def _rows(cell):
                return np.array([[r["tpB"], r["den"], r["hal"], r["imp"]] for r in _verified_rows(cell, urls)], dtype=float)
            A_, M_ = _rows(cCE), _rows(cMRV)
            n = len(urls)
            idx = rng5.integers(0, n, size=(B, n))
            def _m(X, ix):
                t = X[ix][:, 0].sum(axis=1); d = X[ix][:, 1].sum(axis=1)
                h = X[ix][:, 2].sum(axis=1); im = X[ix][:, 3].sum(axis=1)
                r = np.where(d > 0, t / np.where(d > 0, d, 1), 0)
                a = np.where(t + h > 0, t / np.where(t + h > 0, t + h, 1), 0)
                ap = np.where(t + h + im > 0, t / np.where(t + h + im > 0, t + h + im, 1), 0)
                f1 = np.where(r + a > 0, 2 * r * a / np.where(r + a > 0, r + a, 1), 0)
                f1p = np.where(r + ap > 0, 2 * r * ap / np.where(r + ap > 0, r + ap, 1), 0)
                return r, f1, f1p
            rA, fA, fpA = _m(A_, idx); rM, fM, fpM = _m(M_, idx)
            rA0, fA0, fpA0 = _pm_of(A_); rM0, fM0, fpM0 = _pm_of(M_)
            _vpairs[f"{m}|{e}"] = {
                "n_pr": n,
                "dRecall_sem": (float(rM0 - rA0), float(np.percentile(rM - rA, 2.5)), float(np.percentile(rM - rA, 97.5))),
                "dF1": (float(fM0 - fA0), float(np.percentile(fM - fA, 2.5)), float(np.percentile(fM - fA, 97.5))),
                "dF1p": (float(fpM0 - fpA0), float(np.percentile(fpM - fpA, 2.5)), float(np.percentile(fpM - fpA, 97.5))),
            }

    _vhv = {}
    for m in MODELS:
        for fw in ("compound-realistic", "metareview-realistic"):
            for e in EFFORTS:
                Ah = (m, fw, e); V = (m, "vanilla-engineered", e)
                urls = [u for u in TOP6 if u in sel[Ah] and u in sel[V]]
                if len(urls) < 2:
                    continue
                XA = np.array([[r["tpB"], r["den"]] for r in _verified_rows(Ah, urls)], dtype=float)
                XV = np.array([[r["tpB"], r["den"]] for r in _verified_rows(V, urls)], dtype=float)
                n = len(urls)
                idx = rng5.integers(0, n, size=(B, n))
                SA, SV = XA[idx], XV[idx]
                rA = np.where(SA[:, :, 1] > 0, SA[:, :, 0] / np.where(SA[:, :, 1] > 0, SA[:, :, 1], 1), 0).mean(axis=1)
                rV = np.where(SV[:, :, 1] > 0, SV[:, :, 0] / np.where(SV[:, :, 1] > 0, SV[:, :, 1], 1), 0).mean(axis=1)
                pA = XA[:, 0].sum() / XA[:, 1].sum() if XA[:, 1].sum() else 0
                pV = XV[:, 0].sum() / XV[:, 1].sum() if XV[:, 1].sum() else 0
                _vhv[f"{m}|{fw}|{e}"] = {"n_pr": n,
                    "dRecall_sem": (float(pA - pV), float(np.percentile(rA - rV, 2.5)), float(np.percentile(rA - rV, 97.5)))}

    _pkeys = sorted(_vpairs)
    _P = {met: np.array([_vpairs[k][met][0] for k in _pkeys]) for met in ("dRecall_sem", "dF1", "dF1p")}
    _pidx = rng5.integers(0, len(_pkeys), size=(B, len(_pkeys)))
    out["expanded_gold_verified"] = {
        "construction": ("§10c VERIFIED union (supersedes §10b levels). Corrects two measured defects: "
                         "(1) a stricter whole-PR LLM re-merge collapsed 359 raw clusters to 258 distinct "
                         "defects; (2) 49 raw clusters describe defects already in the golden set (official "
                         "text-only matcher false negatives); a strict adversarial re-check (same-root-cause, "
                         "not same-area) assigns at most one cluster per golden, giving a locked overlap count. "
                         "denominator per PR = n_goldens + verified additional defects. Credit rule B (primary, "
                         "real-world): a run's goldens-found = official matcher TP identities ∪ goldens whose "
                         "verified overlapping cluster the run produced; additional found = verified non-golden "
                         "groups hit. Rule A (benchmark-compatible): official TP identities only. No bug is "
                         "counted twice in either rule. Artifacts: analysis/semantic_true_golden_verify_<pr>.json "
                         "(re-merge + first-pass overlap), analysis/semantic_overlap_locked_<pr>.json (finding-level "
                         "overlap check: a cluster overlaps a golden only if a single member finding is that golden's "
                         "defect; judged per finding because cluster representatives are broader than any one "
                         "golden). CIs: cluster bootstrap, B=10000, seed 20260916, rng5=SEED+4. Provenance: "
                         "judge gpt-5.2, 2026-09-17; LLM steps are not deterministic — the stored artifacts are "
                         "the record; residual under-merge makes verified recall a mild lower bound."),
        "per_pr": {u: {"goldens": len(_v_pr[u]["goldens"]), "n_merged": _v_pr[u]["n_merged"],
                       "n_overlap_strict": _v_pr[u]["n_overlap_strict"],
                       "n_verified_additional": _v_pr[u]["n_additional"]} for u in TOP6},
        "totals": {"goldens": sum(len(_v_pr[u]["goldens"]) for u in TOP6),
                   "n_merged": sum(_v_pr[u]["n_merged"] for u in TOP6),
                   "n_overlap_strict": sum(_v_pr[u]["n_overlap_strict"] for u in TOP6),
                   "n_verified_additional": sum(_v_pr[u]["n_additional"] for u in TOP6)},
        "matrix_sem": _vcells,
        "ce_vs_mrv": _vpairs,
        "harness_vs_vanilla_sem": _vhv,
        "pairs_summary": {
            "n_pairs": len(_pkeys),
            "signs": {met: {"pos": int((_P[met] > 0).sum()), "zero": int((_P[met] == 0).sum()), "neg": int((_P[met] < 0).sum())}
                      for met in _P},
            "mean": {met: float(_P[met].mean()) for met in _P},
            "ci_mean": {met: (float(_P[met].mean()), float(np.percentile(_P[met][_pidx].mean(axis=1), 2.5)),
                               float(np.percentile(_P[met][_pidx].mean(axis=1), 97.5))) for met in _P},
        },
    }
    print("§10c verified union totals:", json.dumps(out["expanded_gold_verified"]["totals"]))

with open(f"{ROOT}/analysis/final_report_metrics.json", "w") as fh:
    json.dump(out, fh, indent=1)

# ---- markdown dumps ----
print("=== MATRIX (top-6): recall/adjP/F1/F2 with 95% cluster-bootstrap CI ===")
hdr = (f"{'model':<12} {'fw':<4} {'eff':<6} {'n':>3} {'recall':>20} {'adjP':>20} "
       f"{'F1':>20} {'F2':>20} {'beyond/PR':>9} {'$/run':>18} {'inst':>10}")
print(hdr); print("-" * len(hdr))
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            k = f"{m}|{fw}|{e}"
            if k not in matrix:
                continue
            M = matrix[k]
            print(f"{M_SHORT[m]:<12} {FW_SHORT[fw]:<4} {e:<6} {M['n_pr']:>3} "
                  f"{ci_txt(M['ci']['recall']):>20} {ci_txt(M['ci']['adjP']):>20} "
                  f"{ci_txt(M['ci']['F1']):>20} {ci_txt(M['ci']['F2']):>20} "
                  f"{M['real_beyond']/M['n_pr']:>9.1f} {ci_txt(M['ci']['cost_run'], '${:.2f}'):>18} "
                  f"{'/'.join(M['instruments']):>10}")
print()
print("=== MATRIX cost metrics (top-6) ===")
hdr = f"{'model':<12} {'fw':<4} {'eff':<6} {'$/real':>22} {'$/TP':>22} {'tok/run':>16} {'wall_s/run':>20} {'¢/ktok':>14}"
print(hdr); print("-" * len(hdr))
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            k = f"{m}|{fw}|{e}"
            if k not in matrix:
                continue
            M = matrix[k]
            print(f"{M_SHORT[m]:<12} {FW_SHORT[fw]:<4} {e:<6} "
                  f"{ci_txt(M['ci']['usd_per_real'], '${:.3f}'):>22} "
                  f"{ci_txt(M['ci']['usd_per_tp'], '${:.3f}'):>22} "
                  f"{ci_txt(M['ci']['tok_run'], '{:,.0f}'):>16} "
                  f"{ci_txt(M['ci']['wall_run'], '{:,.0f}'):>20} "
                  f"{ci_txt(M['ci']['price_per_ktok'], '${:.4f}'):>14}")
print()
print("=== Pareto frontier (usd/real-finding vs F1, top-6, n=6 cells) ===")
for c in frontier:
    p = [q for q in pareto if q["cell"] == c][0]
    m, fw, e = c.split("|")
    print(f"  {M_SHORT[m]:<12} {FW_SHORT[fw]:<4} {e:<6} F1={p['F1']:.2f} "
          f"[{p['F1_ci'][1]:.2f},{p['F1_ci'][2]:.2f}]  $/real={p['usd_per_real']:.3f} "
          f"[{p['usd_ci'][1]:.3f},{p['usd_ci'][2]:.3f}]")
print()
print("=== Selection effect (>=40 PRs): top-6 vs full-50 ===")
print(f"{'cell':<44} {'n':>3} {'rec_t6':>7} {'rec_full':>8} {'F1_t6':>6} {'F1_full':>7}")
for k, v in sel_effect.items():
    m, fw, e = k.split("|")
    print(f"{M_SHORT[m]+' '+FW_SHORT[fw]+' '+e:<44} {v['n_full']:>3} {v['recall_t6']:>7.2f} "
          f"{v['recall_full']:>8.2f} {v['F1_t6']:>6.2f} {v['F1_full']:>7.2f}")
print()
print("=== Rank agreement top-6 vs full-50 (Spearman of model ranks by F1) ===")
for k, v in rank_agree.items():
    print(f"  {k}: rho={v['spearman']:.2f} models={v['models']}")
print()
print("=== Monotonicity (sev-weight vs per-PR recall, full rows) ===")
neg = [(k, v["rho"]) for k, v in monotone.items() if v["rho"] < 0]
print(f"  cells with >=40 PRs tested: {len(monotone)}; negative rho: {len(neg)}; "
      f"mean rho = {np.mean([v['rho'] for v in monotone.values()]):.2f}")
for k, r in sorted(monotone.items(), key=lambda kv: kv[1]['rho']):
    print(f"  {k:<44} rho={r['rho']:>5.2f} n={r['n_pr']}")
print()
print("=== Framework deltas (harness - vanilla, paired top-6) ===")
for k, d in fw_delta.items():
    r = d["recall"]; tm = tok_mult.get(k, {"tok_ratio": (0,0,0), "cost_ratio": (0,0,0)})
    print(f"  {k:<52} dRec={r[0]:+.2f} [{r[1]:+.2f},{r[2]:+.2f}] "
          f"tokX={tm['tok_ratio'][0]:.1f} costX={tm['cost_ratio'][0]:.2f}")
print()
print("=== Effort ladder high vs medium (paired top-6) ===")
for k, d in effort.items():
    dr = d["delta"]["recall"]; df1 = d["delta"]["F1"]
    print(f"  {k:<36} dRec={dr[0]:+.2f} [{dr[1]:+.2f},{dr[2]:+.2f}] "
          f"dF1={df1[0]:+.2f} [{df1[1]:+.2f},{df1[2]:+.2f}] cost(high/med)={d['cost_ratio'][0]:.2f}")
print()
print("=== flash vs vision (paired top-6) ===")
for k, d in tier.items():
    dr = d["recall"]; dn = d["real_total"]
    print(f"  {k:<44} dRec={dr[0]:+.2f} [{dr[1]:+.2f},{dr[2]:+.2f}] "
          f"dReal={dn[0]:+.1f} [{dn[1]:+.1f},{dn[2]:+.1f}]")
print()
print("=== Legacy aside (vanilla, top-6, era-legal reuse) ===")
for k, v in legacy_aside.items():
    print(f"  {k:<44} n={v['n_pr']} recall={v['recall']:.2f} real/PR={v['real_beyond']/v['n_pr']:.1f}")
print()
print("=== Cost-structure ratios (claim 2) ===")
for k, d in ratio3.items():
    print(f"  {k}")
    print(f"    per-token ratio  {d['ptok_ratio'][0]:.4f} [{d['ptok_ratio'][1]:.4f},{d['ptok_ratio'][2]:.4f}]  "
          f"(glm per-token price as fraction of frontier)")
    print(f"    tokens/task ratio {d['toktask_ratio'][0]:.1f} [{d['toktask_ratio'][1]:.1f},{d['toktask_ratio'][2]:.1f}]  "
          f"(glm tokens per task / frontier tokens per task)")
    print(f"    cost/task ratio  {d['costtask_ratio'][0]:.4f} [{d['costtask_ratio'][1]:.4f},{d['costtask_ratio'][2]:.4f}]")
print()
print("=== Recommendation ratios (glm low vs frontier refs) ===")
for k, d in rec_ratios.items():
    print(f"  {k}")
    print(f"    recall {d['recall_ratio'][0]:.3f} [{d['recall_ratio'][1]:.3f},{d['recall_ratio'][2]:.3f}]  "
          f"F1 {d['F1_ratio'][0]:.3f} [{d['F1_ratio'][1]:.3f},{d['F1_ratio'][2]:.3f}]  "
          f"cost(A/F) {d['cost_ratio_A_over_F'][0]:.4f} [{d['cost_ratio_A_over_F'][1]:.4f},{d['cost_ratio_A_over_F'][2]:.4f}]")
print()
print("=== Anthropic metered/billed reconciliation ===")
for r in recon:
    print(f"  {r['model']}: n={r['n']} median metered/billed={r['median_metered_over_billed']:.3f} "
          f"[p10 {r['p10']:.3f}, p90 {r['p90']:.3f}]")

# ------------------------------------------------------------------------------------------------
# Append the TRUE-golden-set section (the PRIMARY analysis) so a rebuild of this artifact cannot drop it.
# The section is written by tools/final_report_true_gold.py, which guards that every pre-existing
# top-level key survives byte-identical.
import subprocess as _sp, sys as _sys  # noqa: E402
_r = _sp.run([_sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "final_report_true_gold.py")],
             capture_output=True, text=True)
print(_r.stdout.strip() or _r.stderr.strip()[-400:])
