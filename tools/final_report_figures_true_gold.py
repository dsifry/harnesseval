#!/usr/bin/env python3
"""True-gold figures: the PRIMARY charts, built on the deduplicated verified hidden-gold DEFECT set.

Reads analysis/final_report_metrics.json -> true_gold_defects (verified block; 42 goldens + 110 defects)
and the frozen cost matrix M["matrix"], and writes:
  analysis/figures/fig_true_gold_pareto.png      recall vs F1' (up and to the right is better)
  analysis/figures/fig_true_gold_efficiency.png  $ per true bug vs recall
CIs are the cluster/bootstrap intervals computed in tools/verified_gold_defect_metrics.py.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(f"{ROOT}/analysis/final_report_metrics.json"))
TG = M["true_gold_defects"]
BLOCK = TG["verified"]
CELLS = BLOCK["cells"]
MATRIX = M["matrix"]
FIG = f"{ROOT}/analysis/figures"
os.makedirs(FIG, exist_ok=True)

FW_SHORT = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV"}
M_SHORT = {"claude-fable-5-1": "fable", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
           "claude-opus-5": "opus", "glm-5.3-vision-background": "glm-vis",
           "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet",
           "glm-5.3-flash-background": "glm-flash"}
FWCOL = {"vanilla-engineered": "#8c8c8c", "compound-realistic": "#1f6feb", "metareview-realistic": "#d1495b"}
plt.rcParams.update({"figure.dpi": 150, "font.size": 8, "axes.grid": True,
                     "grid.alpha": 0.22, "axes.axisbelow": True, "axes.spines.top": False,
                     "axes.spines.right": False})
HEAD = BLOCK["headline"]
GOLD = next(iter(CELLS.values()))["den"]          # the true golden set size (152)


def rows():
    out = []
    for key, c in CELLS.items():
        m, fw, e = key.split("|")
        ci = (c.get("ci") or {})
        r = ci.get("recall") or [c["recall"], c["recall"], c["recall"]]
        f = ci.get("F1p") or [c["F1p"], c["F1p"], c["F1p"]]
        mx = MATRIX.get(key) or {}
        cost = mx.get("cost_run")
        n = c.get("n_pr") or mx.get("n_pr") or 1
        per_true = (cost * n / c["TP"]) if (cost and c.get("TP")) else None
        out.append({"key": key, "m": m, "fw": fw, "e": e, "recall": c["recall"], "rlo": r[1], "rhi": r[2],
                    "F1p": c["F1p"], "flo": f[1], "fhi": f[2], "adjP": c.get("adjP"),
                    "per_true": per_true, "TP": c.get("TP")})
    return out


R = rows()


def scatter(ax, xk, xlo, xhi, yk, ylo, yhi, xlog=False):
    for fw in ("vanilla-engineered", "compound-realistic", "metareview-realistic"):
        g = [r for r in R if r["fw"] == fw and r[xk] is not None and r[yk] is not None]
        if not g:
            continue
        ax.errorbar([r[xk] for r in g], [r[yk] for r in g],
                    xerr=[[max(0.0, r[xk] - r[xlo]) for r in g], [max(0.0, r[xhi] - r[xk]) for r in g]],
                    yerr=[[max(0.0, r[yk] - r[ylo]) for r in g], [max(0.0, r[yhi] - r[yk]) for r in g]],
                    fmt="o", ms=4.5, lw=0, elinewidth=0.7, alpha=0.85, color=FWCOL[fw],
                    label={"vanilla-engineered": "vanilla", "compound-realistic": "Compound Engineering (CE)",
                           "metareview-realistic": "metareview (MRV)"}[fw], capsize=0)
    for r in R:
        if r[xk] is None or r[yk] is None:
            continue
        ax.annotate(f"{M_SHORT.get(r['m'], r['m'])} {FW_SHORT[r['fw']]} {r['e'][:1]}",
                    (r[xk], r[yk]), fontsize=5.4, xytext=(3, 2), textcoords="offset points",
                    color="#333", alpha=0.85)
    if xlog:
        ax.set_xscale("log")


# ---- fig 1: recall vs F1' -------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 5.0))
scatter(ax, "F1p", "flo", "fhi", "recall", "rlo", "rhi")
ax.set_xlabel("F1′  (equal-weight, nitpick-averse F-score)  →  better\n"
              "NOTE: F2′ (recall-weighted 4:1) is the recommended composite — it reverses this ordering for "
              "high-recall cells; see REPORT_FINAL §10d")
ax.set_ylabel("recall of the true golden set  (152 = 42 goldens + 110 verified defects)  →  better")
ax.set_title("True-gold frontier: does a harness actually find more real bugs per unit of noise?\n"
             "each point is one (model, framework, effort) cell; bars are cluster-bootstrap 95% CIs",
             fontsize=8.5, loc="left")
bx = max(r["F1p"] for r in R)
h = HEAD.get("harness", {}).get("best_f1p", {})
v = HEAD.get("vanilla", {}).get("best_f1p", {})
ax.axvline(v.get("F1p", 0), color=FWCOL["vanilla-engineered"], lw=0.7, ls=":", alpha=0.7)
ax.text(v.get("F1p", 0), ax.get_ylim()[0], " best vanilla F1′", fontsize=6, color="#555", va="bottom")
ax.legend(loc="lower right", frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_true_gold_pareto.png")
plt.close(fig)

# ---- fig 2: $ per true bug vs recall -------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 5.0))
scatter(ax, "per_true", "per_true", "per_true", "recall", "rlo", "rhi", xlog=True)
ax.set_xlabel("$ per TRUE bug found  (list price; log scale — each gridline right is ~10× more)")
ax.set_ylabel("recall of the true golden set  →  better")
ax.set_title("What a caught real bug costs (true golden set)\n"
             "the buyer's panel: up and to the left is better; bars are cluster-bootstrap 95% CIs",
             fontsize=8.5, loc="left")
ax.legend(loc="lower left", frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(f"{FIG}/fig_true_gold_efficiency.png")
plt.close(fig)

# ---- markdown headline block ---------------------------------------------------
L = ["## True-gold headline (deduplicated verified hidden-gold set)", "",
     f"Denominator (the true golden set): **{GOLD}** = 42 Martian goldens + {GOLD - 42} verified hidden-gold "
     f"defects. TP counts are per cell over the campaign's 6 PRs; `totals.TP/den` ({BLOCK['totals']['TP']}/"
     f"{BLOCK['totals']['den']}) sums findings across cells and is not the gold-set ratio.", "",
     "| | cell | recall | F1′ | adjusted precision |", "|---|---|---|---|---|"]
for name, hh in (("best harness recall", h), ("best harness F1′", h),
                 ("best vanilla (recall & F1′)", v)):
    pass
rows_md = [("best harness recall", HEAD["harness"]["best_recall"]),
           ("best harness F1′", HEAD["harness"]["best_f1p"]),
           ("best vanilla recall", HEAD["vanilla"]["best_recall"]),
           ("best vanilla F1′", HEAD["vanilla"]["best_f1p"])]
for lab, hh in rows_md:
    L.append(f"| {lab} | `{hh['cell']}` | {hh['recall']:.3f} | {hh['F1p']:.3f} | {hh['adjP']:.3f} |")
L += ["", f"- peak-recall ratio, harness ÷ vanilla: **{HEAD['peak_recall_ratio_harness_over_vanilla']:.2f}×**",
      f"- best-F1′ ratio, harness ÷ vanilla: **{HEAD['best_f1p_ratio_harness_over_vanilla']:.2f}×** "
      f"({'vanilla ahead' if HEAD['best_f1p_ratio_harness_over_vanilla'] < 1 else 'harness ahead'})", ""]
open(f"{ROOT}/analysis/verified_gold/TRUE_GOLD_HEADLINES.md", "w").write("\n".join(L))
print("\n".join(L))

# ---- fig 3: hidden-gold defects found vs F1' rank (the "F1' misleads" chart) ----
import hashlib
VG = f"{ROOT}/analysis/verified_gold"
D = json.load(open(f"{ROOT}/analysis/final_report_dataset.json"))
ASSIGN = json.load(open(f"{VG}/DEFECT_ASSIGN.json"))
VALID = {d["id"] for d in json.load(open(f"{VG}/DEFECT_REGISTRY.json"))["defects"]}
SEL = {(r["model"], r["framework"], r["effort"], r["url"]): r for r in D["selected_runs"]}
SLUG = {u: u.rstrip("/").split("/")[-1] for u in M["expanded_gold"]["per_pr"]}


def sha(t):
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def found(m, fw, e):
    G = Dp = H = I = 0
    for u, pr in SLUG.items():
        r = SEL.get((m, fw, e, u))
        if not r:
            return None
        amap = ASSIGN.get(pr, {})
        own = {amap.get(sha(t)) for t in (r.get("bugtexts") or [])}
        own = {d for d in own if d and d in VALID}
        v = r["rj3"] or r["inrun"]
        G += r["tp"]; Dp += len(own); H += v["hal"]; I += v["imp"]
    return G, Dp, H, I


bars = []
for k, c in CELLS.items():
    m, fw, e = k.split("|")
    f = found(m, fw, e)
    if not f or c["n_pr"] != 6:
        continue
    G, Dp, H, I = f
    bars.append({"k": k, "label": f"{M_SHORT.get(m, m)} {FW_SHORT[fw]} {e[:1]}", "fw": fw,
                 "gold": G, "def": Dp, "F1p": c["F1p"], "recall": c["recall"],
                 "nit": I / max(1, G + Dp + H + I)})
bars.sort(key=lambda b: -(b["gold"] + b["def"]))
fig, ax = plt.subplots(figsize=(9.5, 6.4))
ys = list(range(len(bars)))[::-1]
for i, b in zip(ys, bars):
    ax.barh(i, b["gold"], color="#c9c9c9", height=0.7)
    ax.barh(i, b["def"], left=b["gold"], color=FWCOL[b["fw"]], height=0.7)
    ax.text(b["gold"] + b["def"] + 1.0, i, f"F1′ rank {sorted(bars, key=lambda x: -x['F1p']).index(b)+1:<2d} "
            f"· nitpick {b['nit']:.0%}", fontsize=5.6, va="center", color="#444")
ax.set_yticks(ys); ax.set_yticklabels([b["label"] for b in bars], fontsize=5.6)
ax.set_xlabel("real bugs found on the true golden set  ·  gray = Martian goldens, "
              "color = hidden-gold defects the benchmark never scores")
ax.set_title("Finding real bugs ≠ winning F1′\n"
             "cells sorted by real bugs found; the F1′ leaderboard penalty is dominated by how many of a "
             "cell's findings the adjudicator classifies as nitpicks",
             fontsize=9, loc="left")
ax.set_xlim(0, max(b["gold"] + b["def"] for b in bars) * 1.30)
for fw in ("vanilla-engineered", "compound-realistic", "metareview-realistic"):
    if any(b["fw"] == fw for b in bars):
        ax.barh(0, 0, color=FWCOL[fw],
                label={"vanilla-engineered": "vanilla", "compound-realistic": "Compound Engineering (CE)",
                       "metareview-realistic": "metareview (MRV)"}[fw])
ax.legend(loc="lower right", frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(f"{FIG}/fig_true_gold_defects_found.png"); plt.close(fig)
print("wrote fig_true_gold_defects_found.png")
