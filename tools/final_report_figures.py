#!/usr/bin/env python3
"""FINAL REPORT figures — every chart carries the cluster-bootstrap 95% CIs.

Reads analysis/final_report_dataset.json + analysis/final_report_metrics.json and
writes analysis/figures/*.png. Reproducible: no randomness here; the CIs were
bootstrapped in tools/final_report_compute.py (B=10,000, seed 20260916).
"""
import json, os, textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(f"{ROOT}/analysis/final_report_dataset.json"))
M = json.load(open(f"{ROOT}/analysis/final_report_metrics.json"))
# TRUE golden set (§10d, PRIMARY): 42 goldens + the deduplicated, individually test-validated defects.
# Compatibility view: the figure code reads TP_sem / recall_sem / F1 / F1p + CIs, so map the defect-level
# cells onto those names. (Previously this pointed at expanded_gold_verified.matrix_sem, the superseded
# LLM-merged §10c keyset.)
SEM = {k: {"TP_sem": c["TP"], "recall_sem": c["recall"], "F1": c["F1"], "F1p": c["F1p"],
           "F2": c["F2"], "F2p": c["F2p"],
           "adjP": c["adjP"], "adjPp": c["adjPp"],
           "ci": {"recall_sem": c["ci"]["recall"], "F1": c["ci"]["F1"], "F1p": c["ci"]["F1p"],
                  "F2": c["ci"]["F2"], "F2p": c["ci"]["F2p"]}}
       for k, c in M["true_gold_defects"]["verified"]["cells"].items()}

def sem_cell(m, fw, e):
    return SEM.get(f"{m}|{fw}|{e}")
FIG = f"{ROOT}/analysis/figures"
os.makedirs(FIG, exist_ok=True)

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
CMAP = plt.get_cmap("tab10")
MCOL = {m: CMAP(i) for i, m in enumerate(MODELS)}
plt.rcParams.update({"figure.dpi": 150, "font.size": 8, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.axisbelow": True})

def cell(m, fw, e):
    return M["matrix"].get(f"{m}|{fw}|{e}")

# Derived true-gold universe (42 goldens + N verified distinct defects) — never hardcode the counts.
TGDER = M["true_gold_defects"]["verified"]["derived"]["coverage"]
TG_GOLDENS = int(TGDER["goldens_den"])          # 42 Martian goldens
TG_DEFECTS = int(TGDER["defects_den"])           # verified distinct hidden-gold defects (105)
TG_DEN = int(TGDER["den"])                       # true-bug universe size (147)

def err(ci):
    return [[ci[0] - ci[1]], [ci[2] - ci[0]]]

# ---------------------------------------------------------------- 1. Pareto
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, met, xlab in ((axes[0], "recall_sem", "recall, true golden set (CI)"),
                      (axes[1], "F2p_sem", "F2\u2032 (our evaluator) - true golden set, CIs")):
    pts = []
    for k, v in M["matrix"].items():
        if v["n_pr"] < 6:
            continue
        m, fw, e = k.split("|")
        sc = sem_cell(m, fw, e)
        if not sc:
            continue
        yci = sc["ci"]["recall_sem" if met == "recall_sem" else "F2p"]
        pts.append((v["ci"]["usd_per_real"][0], yci[0], m, fw, e,
                    v["ci"]["usd_per_real"], yci))
    pts.sort(key=lambda p: p[0])
    # frontier on the point estimates
    front = []
    best = -1
    for p in pts:
        if p[1] > best:
            front.append(p)
            best = p[1]
    fx = [p[0] for p in front]; fy = [p[1] for p in front]
    for p in pts:
        x, y, m, fw, e = p[0], p[1], p[2], p[3], p[4]
        col = MCOL[m]
        ax.errorbar(x, y, xerr=[[x - p[5][1]], [p[5][2] - x]], yerr=[[y - p[6][1]], [p[6][2] - y]],
                    fmt="o", ms=3, color=col, alpha=0.75, lw=0.8, capsize=1)
        if (x, y) in zip(fx, fy):
            ax.annotate(f"{M_SHORT[m]}·{FW_SHORT[fw]}·{e[:3]}", (x, y), fontsize=5.5,
                        xytext=(3, 3), textcoords="offset points")
    ax.step(fx, fy, where="post", color="k", lw=0.8, alpha=0.4, label="Pareto frontier")
    ax.set_xscale("log")
    ax.set_xlabel("metered $ per real finding (TP + beyond-gold real), log scale — CI")
    ax.set_ylabel(xlab)
    ax.set_ylim(0.0, 0.5)
    if met == "recall_sem":
        ax.legend(fontsize=6)
fig.suptitle(textwrap.fill(
    f"Cost/quality frontier, verified true golden set ({TG_GOLDENS} goldens + {TG_DEFECTS} additional bugs "
    f"= {TG_DEN} true bugs) — top-6 cells", width=80), fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_pareto_frontier.png"); fig.savefig(f"{FIG}/fig_pareto_frontier.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 2. cost per cell bars
fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=False)
width = 0.27
for ax, e in zip(axes, EFFORTS):
    xs, i = [], 0
    for fw in FRAMEWORKS:
        for m in MODELS:
            v = cell(m, fw, e)
            if v is None:
                continue
            c = v["ci"]["cost_run"]
            col = MCOL[m]
            ax.bar(i, c[0], width=width, color=col, alpha=0.8)
            ax.errorbar(i, c[0], yerr=err(c), color="k", lw=0.8, capsize=1)
            ax.annotate(FW_SHORT[fw][:1], (i, c[0]), xytext=(0, 2), textcoords="offset points",
                        ha="center", fontsize=5)
            i += 1
    ax.set_xticks(range(i))
    ax.set_xticklabels([f"{M_SHORT[m]}" for fw in FRAMEWORKS for m in MODELS
                        if cell(m, fw, e)], rotation=90, fontsize=6)
    ax.set_yscale("log")
    ax.set_title(f"effort = {e}  (v=vanilla, C=CE, M=MRV)", fontsize=8)
    ax.set_ylabel("metered $ / run (top-6, log)")
fig.suptitle("Metered cost per PR-review run per cell, with 95% cluster-bootstrap CIs", fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_cost_per_cell.png"); fig.savefig(f"{FIG}/fig_cost_per_cell.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 3. token composition
sel = {}
for r in D["selected_runs"]:
    if r["url"] in D["top6"]:
        sel.setdefault((r["model"], r["framework"], r["effort"]), {})[r["url"]] = r
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, e in zip(axes, EFFORTS):
    labels, fresh, cached, cw, out = [], [], [], [], []
    for fw in FRAMEWORKS:
        for m in MODELS:
            runs = sel.get((m, fw, e), {})
            if len(runs) < 6:
                continue
            nf = sum(r["fresh_in"] for r in runs.values()) / 6 / 1000
            nc = sum(r["cached_in"] for r in runs.values()) / 6 / 1000
            nw = sum(r["cache_w"] for r in runs.values()) / 6 / 1000
            no = sum(r["out_tok"] for r in runs.values()) / 6 / 1000
            labels.append(f"{M_SHORT[m]}·{FW_SHORT[fw]}")
            fresh.append(nf); cached.append(nc); cw.append(nw); out.append(no)
    x = np.arange(len(labels))
    ax.bar(x, fresh, label="fresh input", color="#4C72B0")
    ax.bar(x, cached, bottom=fresh, label="cached read", color="#55A868")
    ax.bar(x, cw, bottom=np.array(fresh) + np.array(cached), label="cache write", color="#C44E52")
    ax.bar(x, out, bottom=np.array(fresh) + np.array(cached) + np.array(cw),
           label="output (incl. reasoning)", color="#CCB974")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=5.5)
    ax.set_ylabel("mean k-tokens / run (top-6)")
    ax.set_title(f"effort = {e}", fontsize=8)
    if e == "low":
        ax.legend(fontsize=6)
fig.suptitle("Token composition per run: why a harness is cheap or expensive (fresh/cached/write/output)", fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_token_composition.png"); fig.savefig(f"{FIG}/fig_token_composition.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 4. effort ladder
fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
for ax, fw in zip(axes, FRAMEWORKS):
    for m in MODELS:
        xs, ys, xlo, xhi, ylo, yhi = [], [], [], [], [], []
        for e in EFFORTS:
            v = cell(m, fw, e)
            sc = sem_cell(m, fw, e)
            if v is None or not sc or v["n_pr"] < 6:   # partial-coverage cells excluded (1–2 PRs)
                continue
            yci = sc["ci"]["F2p"]
            xs.append(v["ci"]["cost_run"][0]); ys.append(yci[0])
            xlo.append(v["ci"]["cost_run"][1]); xhi.append(v["ci"]["cost_run"][2])
            ylo.append(yci[1]); yhi.append(yci[2])
        if not xs:
            continue
        ax.plot(xs, ys, "-o", color=MCOL[m], ms=3, lw=1, label=M_SHORT[m])
        for x, y, a, b, c2, d in zip(xs, ys, xlo, xhi, ylo, yhi):
            ax.errorbar(x, y, xerr=[[x - a], [b - x]], yerr=[[y - c2], [d - y]],
                        color=MCOL[m], lw=0.7, capsize=1, alpha=0.6)
    ax.set_xscale("log")
    ax.set_xlabel("metered $ / run (log)")
    ax.set_ylabel("F2\u2032 (our evaluator, true golden set)"); ax.set_ylim(0, 0.5)
    ax.set_title(fw, fontsize=8)
    ax.legend(fontsize=5.5, ncol=2)
fig.suptitle(textwrap.fill(
    "Effort ladder: real-world quality vs cost as effort rises (low → medium → high), CIs shown — "
    "complete 6-PR cells only (partial-coverage cells with 1–2 PRs are excluded)", width=86), fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_effort_ladder.png"); fig.savefig(f"{FIG}/fig_effort_ladder.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 5. selection effect
se = M["selection_effect"]
fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
for ax, ka, kb, lab in ((axes[0], "recall_t6", "recall_full", "recall"),
                        (axes[1], "F1_t6", "F1_full", "F1")):
    for k, v in se.items():
        m, fw, e = k.split("|")
        c = MCOL.get(m, "k")
        ax.errorbar(v[kb], v[ka],
                    xerr=[[v[kb] - v.get("ci_full_" + lab, [v[kb]] * 4)[1]],
                          [v.get("ci_full_" + lab, [v[kb]] * 4)[2] - v[kb]]],
                    fmt="o", ms=3, color=c, alpha=0.7, lw=0.7, capsize=1)
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="y = x")
    ax.set_xlabel(f"{lab} on full 50 (rows with ≥40/50 PRs), CI")
    ax.set_ylabel(f"{lab} on top-6")
    ax.set_xlim(0.1, 0.95); ax.set_ylim(0.1, 0.95)
    ax.legend(fontsize=6)
    for m, c in MCOL.items():
        ax.scatter([], [], color=c, s=6, label=M_SHORT[m])
    handles, labels_ = ax.get_legend_handles_labels()
    ax.legend(handles[-9:], labels_[-9:], fontsize=5, ncol=2, loc="upper left")
fig.suptitle(textwrap.fill(
    "Selection effect: top-6 (hardest PRs) vs full-50 — points ABOVE y=x score higher on the "
    "selected top-6 than on the full 50 (the selection favored them); points BELOW do relatively "
    "better on the full 50", width=80), fontsize=9)
for _ax in axes:
    _ax.text(0.13, 0.93, "above the line:\nrelatively stronger on the top-6", transform=_ax.transAxes,
             fontsize=6, color="#555", va="top")
    _ax.text(0.60, 0.13, "below the line:\nrelatively stronger on the full 50", transform=_ax.transAxes,
             fontsize=6, color="#555", va="bottom")
fig.tight_layout()
fig.savefig(f"{FIG}/fig_selection_effect.png"); fig.savefig(f"{FIG}/fig_selection_effect.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 6. wall clock
fig, ax = plt.subplots(figsize=(13, 4.6))
labels, meds, los, his, cols = [], [], [], [], []
for fw in FRAMEWORKS:
    for e in EFFORTS:
        for m in MODELS:
            v = cell(m, fw, e)
            if v is None:
                continue
            lo, hi = v["wall_med_ci"][1], v["wall_med_ci"][2]
            labels.append(f"{M_SHORT[m]}·{FW_SHORT[fw]}·{e[:2]}")
            meds.append(v["wall_med_ci"][0]); los.append(v["wall_med_ci"][0] - lo); his.append(hi - v["wall_med_ci"][0])
            cols.append(MCOL[m])
x = np.arange(len(labels))
ax.bar(x, meds, color=cols, alpha=0.8)
ax.errorbar(x, meds, yerr=[los, his], fmt="none", ecolor="k", lw=0.7, capsize=1)
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=5)
ax.set_ylabel("median wall seconds / run (top-6)")
ax.set_title("Wall-clock per run per cell (median of PRs, 95% cluster-bootstrap CI)", fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_wallclock.png"); fig.savefig(f"{FIG}/fig_wallclock.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 7. recall grid bars
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
for ax, e in zip(axes, EFFORTS):
    labels, vals, ci, cols = [], [], [], []
    for fw in FRAMEWORKS:
        for m in MODELS:
            v = cell(m, fw, e)
            if v is None:
                continue
            labels.append(f"{M_SHORT[m]}·{FW_SHORT[fw]}")
            c = v["ci"]["recall"]
            vals.append(c[0]); ci.append(c)
            cols.append(MCOL[m])
    x = np.arange(len(labels))
    ax.bar(x, vals, color=cols, alpha=0.8)
    ax.errorbar(x, vals, yerr=[[v[0] - v[1] for v in ci], [v[2] - v[0] for v in ci]],
                fmt="none", ecolor="k", lw=0.8, capsize=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=5.5)
    ax.set_ylim(0, 1)
    ax.set_ylabel("golden recall (All profile)")
    ax.set_title(f"effort = {e}", fontsize=8)
fig.suptitle("Golden recall per cell on the severity top-6, 95% cluster-bootstrap CIs", fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_recall_grid.png"); fig.savefig(f"{FIG}/fig_recall_grid.svg")   # vector twin, same basename
plt.close(fig)

# ------------------------------------------------------ 8. efficiency 2x2
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
pts = []
for k, v in M["matrix"].items():
    if v["n_pr"] < 6:
        continue
    m, fw, e = k.split("|")
    pts.append((m, fw, e, v))

def scatter_ci(ax, xs, xlo, xhi, ys, ylo, yhi, m, fw, e, xlog=True):
    ax.errorbar(xs, ys, xerr=[[xs - xlo], [xhi - xs]], yerr=[[ys - ylo], [yhi - ys]],
                fmt="o", ms=3, color=MCOL[m], alpha=0.75, lw=0.8, capsize=1)
    if xlog:
        ax.set_xscale("log")

def cluster_hull(ax, pts, color, label):
    """Shade a per-model cluster (angular sort around centroid) + star centroid + label."""
    if len(pts) < 2:
        return
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    import math
    srt = sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    ax.fill([p[0] for p in srt] + [srt[0][0]], [p[1] for p in srt] + [srt[0][1]],
            color=color, alpha=0.12, lw=0, zorder=1)
    ax.plot([cx], [cy], "*", color=color, ms=8, mec="k", mew=0.5, zorder=5)
    ax.annotate(label, (cx, cy), xytext=(4, -9), textcoords="offset points",
                fontsize=6, weight="bold", color=color, zorder=6)

# (a) price/performance: $/run vs F1' (true golden set), model clusters shaded
ax = axes[0][0]
for m, fw, e, v in pts:
    sc = sem_cell(m, fw, e)
    if not sc:
        continue
    c, f = v["ci"]["cost_run"], sc["ci"]["F2p"]
    scatter_ci(ax, c[0], c[1], c[2], f[0], f[1], f[2], m, fw, e)
clusters = {}
for m, fw, e, v in pts:
    sc = sem_cell(m, fw, e)
    if not sc:
        continue
    clusters.setdefault(m, []).append((v["ci"]["cost_run"][0], sc["F2p"]))
for m, cpts in clusters.items():
    cluster_hull(ax, cpts, MCOL[m], M_SHORT[m])
ax.set_xlabel("metered $ / run (log)"); ax.set_ylabel("F2\u2032 (our evaluator) [CI]"); ax.set_ylim(0, 0.5)
ax.set_title("(a) price/performance: $ per PR review vs F2\u2032 — model clusters shaded", fontsize=9)

# (b) F1' per dollar (true golden set; approx CI = F1' CI / cost point)
ax = axes[0][1]
rows = []
for m, fw, e, v in pts:
    sc = sem_cell(m, fw, e)
    if not sc:
        continue
    rows.append((m, fw, e, sc["F2p"] / v["ci"]["cost_run"][0], sc["ci"]["F2p"], v["ci"]["cost_run"][0]))
rows.sort(key=lambda r: -r[3])
rows = rows[:20]
labels = [f"{M_SHORT[m]}·{FW_SHORT[fw]}·{e[:3]}" for m, fw, e, _, _, _ in rows]
vals = [r[3] for r in rows]
los = [r[3] - r[4][1] / r[5] for r in rows]
his = [r[4][2] / r[5] - r[3] for r in rows]
cols = [MCOL[r[0]] for r in rows]
ypos = np.arange(len(rows))[::-1]
ax.barh(ypos, vals, color=cols, alpha=0.8)
ax.errorbar(vals, ypos, xerr=[los, his], fmt="none", ecolor="k", lw=0.8, capsize=1)
ax.set_yticks(ypos); ax.set_yticklabels(labels, fontsize=5.5)
ax.set_xlabel("F2\u2032 per $ per run (approx CI)")
ax.set_title("(b) F2\u2032 per dollar (top 20 cells)", fontsize=9)

# (c) F1' vs wall time, model clusters shaded
ax = axes[1][0]
for m, fw, e, v in pts:
    sc = sem_cell(m, fw, e)
    if not sc:
        continue
    w, f = v["ci"]["wall_run"], sc["ci"]["F2p"]
    scatter_ci(ax, w[0], w[1], w[2], f[0], f[1], f[2], m, fw, e)
clusters = {}
for m, fw, e, v in pts:
    sc = sem_cell(m, fw, e)
    if not sc:
        continue
    clusters.setdefault(m, []).append((v["ci"]["wall_run"][0], sc["F2p"]))
for m, cpts in clusters.items():
    cluster_hull(ax, cpts, MCOL[m], M_SHORT[m])
ax.set_xlabel("wall seconds / run (log)"); ax.set_ylabel("F2\u2032 (our evaluator) [CI]"); ax.set_ylim(0, 0.5)
ax.set_title("(c) F2\u2032 vs wall-clock per run — model clusters shaded", fontsize=9)
for m, c in MCOL.items():
    ax.scatter([], [], color=c, s=6, label=M_SHORT[m])
ax.legend(fontsize=5, ncol=2, loc="lower right")

# (d) recall (true golden set) vs $/true bug found
ax = axes[1][1]
for m, fw, e, v in pts:
    sc = sem_cell(m, fw, e)
    if not sc or not sc["TP_sem"]:
        continue
    x = v["ci"]["cost_run"][0] * v["n_pr"] / sc["TP_sem"]
    r = sc["ci"]["F2p"]
    scatter_ci(ax, x, x * 0.98, x * 1.02, r[0], r[1], r[2], m, fw, e)
ax.set_xlabel("metered $ per true bug found (log)"); ax.set_ylabel("F2\u2032 (our evaluator) [CI]")
ax.set_ylim(0, 0.5)
ax.set_title(f"(d) cost per true bug vs F2\u2032 ({TG_DEN} true bugs)", fontsize=9)

fig.suptitle("Efficiency 2×2, verified true golden set — top-6 cells, 95% cluster-bootstrap CIs", fontsize=10)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_efficiency_2x2.png"); fig.savefig(f"{FIG}/fig_efficiency_2x2.svg")   # vector twin, same basename
plt.close(fig)

print("figures written:", sorted(os.listdir(FIG)))
