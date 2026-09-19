#!/usr/bin/env python3
"""Interactive Plotly fragments for the report's four *dynamic* figures.

Writes analysis/figures/interactive/<basename>.json for the four figures the report marks
`*(interactive …)*`, plus manifest.json. Each fragment is plain Plotly JSON:
    {"traces": [...], "layout": {...}, "config": {...}}
so the report's HTML renderer (tools/report_to_html.py, wave 2b) can call
`Plotly.newPlot(div, traces, layout, config)` and get a live chart whose legend entries toggle
series and whose CI button flips the error bars.

Data sources are exactly the ones the static figure tools use:
  analysis/final_report_metrics.json        (true_gold_defects.verified.cells|derived|headline, matrix,
                                             selection_effect)
  analysis/final_report_dataset.json        (selected_runs, for the per-cell found-decomposition)
  analysis/verified_gold/DEFECT_ASSIGN.json (finding -> defect assignment, for defects found)
No data is invented: every point estimate mirrors the static figure; the only *added* quantity is a
cluster-bootstrap CI on the per-cell "total real bugs found" bar in fig_true_gold_defects_found
(same estimator/seed convention as the campaign, documented in the fragment title and hover).

Usage: .venv/bin/python tools/report_interactive_charts.py
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import plotly.graph_objects as go

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(f"{ROOT}/analysis/final_report_metrics.json"))
D = json.load(open(f"{ROOT}/analysis/final_report_dataset.json"))
VG = f"{ROOT}/analysis/verified_gold"
ASSIGN = json.load(open(f"{VG}/DEFECT_ASSIGN.json"))
REGISTRY = json.load(open(f"{VG}/DEFECT_REGISTRY.json"))
# The metrics scorer (tools/verified_gold_defect_metrics.py) credits only D-verified defects in the
# verified variant; withdrawn/duplicate-tier entries must not inflate a cell's bugs-found count.
VALID = {d["id"] for d in REGISTRY["defects"] if d.get("tier") == "D-verified"}

CELLS = M["true_gold_defects"]["verified"]["cells"]
MATRIX = M["matrix"]
DER = M["true_gold_defects"]["verified"]["derived"]["coverage"]
HEAD = M["true_gold_defects"]["verified"]["headline"]
GOLD = int(DER["den"])
GOLDDEN = int(DER["goldens_den"])
NDEF = GOLD - GOLDDEN

OUT = f"{ROOT}/analysis/figures/interactive"
os.makedirs(OUT, exist_ok=True)

FW = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
EFF = ["low", "medium", "high"]
FW_SHORT = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV"}
FW_NAME = {"vanilla-engineered": "one-shot (vanilla)", "compound-realistic": "Compound Engineering (CE)",
           "metareview-realistic": "metareview (MRV)"}
FWCOL = {"vanilla-engineered": "#8c8c8c", "compound-realistic": "#1f6feb", "metareview-realistic": "#d1495b"}
MODELS = ["claude-fable-5-1", "gpt-6-astra", "gpt-5.6-sol", "claude-opus-5",
          "glm-5.3-vision-background", "gpt-5.6-terra", "claude-sonnet-5", "glm-5.3-flash-background"]
M_SHORT = {"claude-fable-5-1": "fable", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
           "claude-opus-5": "opus", "glm-5.3-vision-background": "glm-vis",
           "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet",
           "glm-5.3-flash-background": "glm-flash"}
MODELCOL = dict(zip(MODELS, ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                             "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]))
CONFIG = {"displayModeBar": True, "displaylogo": False, "responsive": True,
          "modeBarButtonsToRemove": ["lasso2d", "select2d"]}
FONT = dict(family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif", size=11)

manifest: dict[str, dict] = {}


def save(fig: go.Figure, name: str, title: str, source: str) -> None:
    """Write <name>.json (CI off) and <name>_ci.json (CI on).

    The CI toggle is NOT a Plotly button menu: those float over the plot area and overlap the chart
    title. Instead the two states are separate specs, and the HTML renderer exposes them through the
    same checkbox it uses for the dashboard panels (see tools/report_to_html.py). Error-bar
    visibility is the only difference between the two specs.
    """
    raw = json.loads(fig.to_json())            # JSON-safe by construction (no NaN/Inf)
    layout = raw["layout"]
    layout.pop("updatemenus", None)            # never ship the floating button menu
    # keep room for the in-chart title
    layout.setdefault("margin", {})["t"] = max(int(layout.get("margin", {}).get("t", 0) or 0), 72)

    traces = raw["data"]

    def variant(ci_on: bool) -> list[dict]:
        out = []
        for t in traces:
            t2 = json.loads(json.dumps(t))
            for key in ("error_x", "error_y"):
                if isinstance(t2.get(key), dict):
                    t2[key]["visible"] = ci_on
            out.append(t2)
        return out

    base = {"traces": variant(False), "layout": layout, "config": CONFIG}
    has_err = any(isinstance(t.get("error_x"), dict) or isinstance(t.get("error_y"), dict) for t in traces)
    with open(f"{OUT}/{name}.json", "w") as fh:
        json.dump(base, fh, indent=1, allow_nan=False)
    if has_err:
        ci = {"traces": variant(True), "layout": layout, "config": CONFIG}
        with open(f"{OUT}/{name}_ci.json", "w") as fh:
            json.dump(ci, fh, indent=1, allow_nan=False)
    manifest[name] = {"title": title, "source": source}
    print(f"  {name}.json: {len(base['traces'])} traces, "
          f"{sum(len(t.get('x', [])) for t in base['traces'])} x-points, "
          f"error-bar CI variant={'yes' if has_err else 'no'}, updatemenus=no")


def cell_rows(complete_only: bool = True):
    rows = []
    for k, c in CELLS.items():
        m, fw, e = k.split("|")
        n = int(c.get("n_pr") or MATRIX.get(k, {}).get("n_pr") or 1)
        if complete_only and n < 6:
            continue
        mx = MATRIX.get(k, {})
        ci = c.get("ci") or {}
        rows.append({
            "key": k, "m": m, "fw": fw, "e": e, "n": n,
            "recall": c["recall"], "rlo": (ci.get("recall") or [0, 0, 0])[1], "rhi": (ci.get("recall") or [0, 0, 0])[2],
            "F2p": c["F2p"], "flo": (ci.get("F2p") or [0, 0, 0])[1], "fhi": (ci.get("F2p") or [0, 0, 0])[2],
            "TP": c.get("TP"), "den": c.get("den"),
            "inst": ",".join(c.get("instruments") or []) or "?",
            "advisory_measured": c.get("advisory_measured", False),
            "advisory_status": (
                ("advisory credit measured" if c.get("advisory_measured", False) else
                 "advisory credit incomplete; observed bonus only, not fully comparable")
                + "<br>F2′ advisory instrument: " + (", ".join(c.get("advisory_instruments") or []) or "not recorded")
                + "<br>classified findings below scoring threshold: " + str(c.get("advisory_below_threshold", c.get("advisory_unresolved", 0)))
                + ("<br>F2′ classification-sensitivity bounds (not CI; all penalties → all advisories): "
                   + " → ".join(f"{x:.3f}" for x in c["F2p_unresolved_bounds"])
                   if c.get("F2p_unresolved_bounds") is not None else "")),
            "usd": (mx.get("ci", {}).get("usd_per_real") or [mx.get("usd_per_real")])[0],
            "usdlo": (mx.get("ci", {}).get("usd_per_real") or [None, None, None])[1],
            "usdhi": (mx.get("ci", {}).get("usd_per_real") or [None, None, None])[2],
        })
    return rows


# =====================================================================  1. defects found
def chart_defects_found() -> None:
    """Per-cell decomposition of reported findings into goldens / hidden-gold defects / hallucinations /
    useful advisory, with the advisory credit shown as n/a on v1-instrument cells."""
    import hashlib as _h
    SEL = {(r["model"], r["framework"], r["effort"], r["url"]): r for r in D["selected_runs"]}
    SLUG = {u: u.rstrip("/").split("/")[-1] for u in M["expanded_gold"]["per_pr"]}

    def sha(t):
        return _h.sha1(t.encode()).hexdigest()[:16]

    def per_pr(m, fw, e):
        """[goldens, defects, hallucinations, useful advisories] contributed per PR (6 values each)."""
        G, Dp, H, I = [], [], [], []
        for u, pr in SLUG.items():
            r = SEL.get((m, fw, e, u))
            if not r:
                return None
            amap = ASSIGN.get(pr, {})
            own = {amap.get(sha(t)) for t in (r.get("bugtexts") or [])}
            own = {d for d in own if d and d in VALID}
            v = r["rj3"] or r["inrun"]
            G.append(r["tp"]); Dp.append(len(own)); H.append(v["hal"]); I.append(v["imp"])
        return np.array([G, Dp, H, I], dtype=float)

    B, SEED = 10000, 20260916 + 6
    rng = np.random.default_rng(SEED)

    def boot_total_ci(g, d):                    # cluster bootstrap over the 6 PRs, campaign convention
        tot = g + d
        idx = rng.integers(0, len(tot), size=(B, len(tot)))
        draws = tot[idx].sum(axis=1)
        return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))

    rows = []
    for k, c in CELLS.items():
        m, fw, e = k.split("|")
        if c.get("n_pr") != 6:
            continue
        pp = per_pr(m, fw, e)
        if pp is None:
            continue
        inst = c.get("instruments") or []
        v1_only = not c.get("advisory_measured", "v1" not in inst)
        g, d, h, i = (float(x.sum()) for x in pp)
        h = c.get("penalty_count", h)
        i = c.get("advisory_count", i)
        lo, hi = boot_total_ci(pp[0], pp[1])
        rows.append({"key": k, "m": m, "fw": fw, "e": e, "gold": g, "def": d, "hal": h,
                     "nit": i, "v1": v1_only, "real": g + d, "lo": lo, "hi": hi,
                     "label": f"{M_SHORT[m]}·{FW_SHORT[fw]}·{e[:1]}" + ("†" if v1_only else "")})
    rows.sort(key=lambda r: -(r["real"]))

    xs = [r["label"] for r in rows]
    fig = go.Figure()
    # stacked components, one trace per (component, framework family) so the key can isolate both
    components = [("gold", "Martian goldens found", "#c9c9c9"),
                  ("def", "hidden-gold defects found", "family"),
                  ("hal", "unsupported / style-only / vague findings", "#b03060"),
                  ("nit", "useful advisory findings", "#2a9d6f")]
    for comp, name, colour in components:
        for fw in FW:
            ys, hovers = [], []
            for r in rows:
                if r["fw"] != fw:
                    ys.append(None); hovers.append(None); continue
                if comp == "nit" and r["v1"]:
                    ys.append(r[comp])
                    hovers.append(f"useful advisories: <b>{int(r[comp])} observed; advisory adjudication incomplete</b><br>"
                                  f"{r['label']} · lower credit, not fully comparable")
                    continue
                ys.append(r[comp])
                hovers.append(f"{r['label']} · {name}: <b>{int(r[comp])}</b>")
            fig.add_trace(go.Bar(
                x=xs, y=ys, name=f"{FW_NAME[fw]} · {name}",
                legendgroup=f"{name}", legendgrouptitle_text=name,
                marker=dict(color=(FWCOL[fw] if colour == "family" else colour)),
                customdata=hovers, hovertemplate="%{customdata}<extra></extra>",
            ))
    # total-real-bugs CI overlay (toggled by the CI menu)
    err_idx = []
    fig.add_trace(go.Scatter(
        x=xs, y=[r["real"] for r in rows], mode="markers", name="95% CI on total real bugs found",
        marker=dict(color="rgba(0,0,0,0)", size=1),
        error_y=dict(type="data", symmetric=False,
                     array=[r["hi"] - r["real"] for r in rows],
                     arrayminus=[r["real"] - r["lo"] for r in rows],
                     color="#444", thickness=1.1, width=3),
        legendgroup="95% CI", showlegend=True,
        hovertemplate=("total real bugs found: <b>%{y:.0f}</b><br>95% CI %{customdata}<br>"
                       "<i>cluster bootstrap over the 6 PRs</i><extra></extra>"),
        customdata=[f"[{r['lo']:.0f}, {r['hi']:.0f}]" for r in rows],
    ))
    err_idx.append(len(fig.data) - 1)

    fig.update_layout(
        barmode="stack", bargap=0.25,
        title=dict(text=(f"Credited units per cell, decomposed — true golden set ({GOLD} true bugs = "
                         f"{GOLDDEN} goldens + {NDEF} verified defects)<br>"
                         "<sup>toggle legend entries to isolate families/components · "
                         "† = incomplete advisory adjudication: observed credit only, not fully comparable<br>Credited units = distinct bugs + adjudicated finding counts; totals are not raw reported findings</sup>"), font=dict(size=13)),
        xaxis=dict(title="cell (sorted by real bugs found)", tickangle=-90, tickfont=dict(size=9),
                   categoryorder="array", categoryarray=xs),
        yaxis=dict(title="credited units (distinct bugs + adjudicated finding counts)", rangemode="tozero"),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", font=dict(size=9),
                    orientation="v", x=1.02, y=1, bordercolor="#d9dee5", borderwidth=1),
        margin=dict(l=60, r=210, t=110, b=120), font=FONT, plot_bgcolor="white",
    )
    save(fig, "fig_true_gold_defects_found",
         "Credited units per cell, decomposed (goldens / hidden-gold defects / unsupported findings / useful advisories)",
         "interactive build of analysis/figures/fig_true_gold_defects_found.png; "
         "counts from final_report_dataset.json + DEFECT_ASSIGN.json; CI = cluster bootstrap (B=10,000)")


# =====================================================================  2. true-gold pareto
def quality_range(rows, point, upper):
    """Use the same CI-inclusive scale in both checkbox states."""
    return [0, max(0.1, max(max(r[point], r[upper]) for r in rows) * 1.08)]


def chart_true_gold_pareto() -> None:
    comp = [r for r in cell_rows(complete_only=True) if r["advisory_measured"]]
    part = [r for r in cell_rows(complete_only=False) if r["advisory_measured"]]
    part = [r for r in part if r["n"] < 6]
    fig = go.Figure()
    err_idx = []
    for fw in FW:
        for e in EFF:
            g = [r for r in comp if r["fw"] == fw and r["e"] == e]
            if not g:
                continue
            fig.add_trace(go.Scatter(
                x=[r["recall"] for r in g], y=[r["F2p"] for r in g], mode="markers",
                name=f"{FW_NAME[fw]} · {e}", legendgroup=fw,
                marker=dict(color=FWCOL[fw], size=11, line=dict(color="white", width=1),
                            symbol={"low": "circle", "medium": "diamond", "high": "square"}[e]),
                error_x=dict(type="data", symmetric=False,
                             array=[r["rhi"] - r["recall"] for r in g],
                             arrayminus=[r["recall"] - r["rlo"] for r in g],
                             color=FWCOL[fw], thickness=1, width=3),
                error_y=dict(type="data", symmetric=False,
                             array=[r["fhi"] - r["F2p"] for r in g],
                             arrayminus=[r["F2p"] - r["flo"] for r in g],
                             color=FWCOL[fw], thickness=1, width=3),
                customdata=[[r["key"], r["TP"], r["den"], r["inst"], r["advisory_status"]] for r in g],
                hovertemplate=("<b>%{customdata[0]}</b><br>recall %{x:.3f} · F2′ (bug quality + advisory credit) %{y:.3f}<br>"
                               "TP %{customdata[1]} of %{customdata[2]} true bugs · "
                               "legacy bug-matching instrument: %{customdata[3]}<br>%{customdata[4]}<extra></extra>"),
            ))
            err_idx.append(len(fig.data) - 1)
    # partial-coverage cells: open markers, dimmed, in the key so they can be toggled
    for fw in FW:
        g = [r for r in part if r["fw"] == fw]
        if not g:
            continue
        fig.add_trace(go.Scatter(
            x=[r["recall"] for r in g], y=[r["F2p"] for r in g], mode="markers",
            name=f"{FW_NAME[fw]} · partial coverage (open)", legendgroup=fw,
            marker=dict(color=FWCOL[fw], size=12, symbol="circle-open", opacity=0.6,
                        line=dict(width=2)),
            customdata=[[r["key"], r["n"], r["advisory_status"]] for r in g],
            hovertemplate=("<b>%{customdata[0]}</b> (<b>%{customdata[1]} PR</b> — partial coverage, "
                           "not comparable)<br>recall %{x:.3f} · F2′ (bug quality + advisory credit) %{y:.3f}<br>%{customdata[2]}<extra></extra>"),
        ))
    v = HEAD.get("vanilla", {}).get("best_f2p", {})
    if v.get("F2p"):
        fig.add_hline(y=v["F2p"], line=dict(color=FWCOL["vanilla-engineered"], width=1, dash="dot"),
                      annotation_text=f"best vanilla F2′ {v['F2p']:.3f}",
                      annotation_position="bottom right", annotation_font_size=10)
    fig.update_layout(
        title=dict(text=(f"Recall vs F2′ — true golden set ({GOLD} true bugs: {GOLDDEN} goldens + "
                         f"{NDEF} verified defects)<br>"
                         "<sup>each point is one complete cell; whiskers are 95% cluster-bootstrap CIs · "
                         f"open markers = partial coverage; {len(comp)} eligible complete cells; unmeasured advisory cells omitted</sup>"), font=dict(size=13)),
        xaxis=dict(title="recall (true golden set)", range=quality_range(comp + part, "recall", "rhi")),
        yaxis=dict(title="F2′ (bug quality + advisory credit)", range=quality_range(comp + part, "F2p", "fhi")),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", font=dict(size=10),
                    x=1.02, y=1, bordercolor="#d9dee5", borderwidth=1),
        margin=dict(l=70, r=240, t=100, b=70), font=FONT, plot_bgcolor="white",
    )
    save(fig, "fig_true_gold_pareto",
         "Recall vs F2′ on the 147-bug true golden set, with 95% CIs",
         "interactive build of analysis/figures/fig_true_gold_pareto.png; "
         "final_report_metrics.json true_gold_defects.verified.cells")


# =====================================================================  3. cost/quality frontier
def chart_pareto_frontier() -> None:
    comp = [r for r in cell_rows(complete_only=True) if r["usd"]]
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, shared_yaxes=False, horizontal_spacing=0.09,
                        subplot_titles=("cost vs recall", "cost vs F2′"))
    err_idx = []
    for col, (ykey, ylo, yhi, ylab) in enumerate(
            (("recall", "rlo", "rhi", "recall (true golden set)"),
             ("F2p", "flo", "fhi", "F2′ (bug quality + advisory credit)")), start=1):
        pts = sorted([r for r in comp if ykey != "F2p" or r["advisory_measured"]], key=lambda r: r["usd"])
        front, best = [], -1.0
        for p in pts:                                   # same algorithm as the static figure
            if p[ykey] > best:
                front.append(p); best = p[ykey]
        fx = [p["usd"] for p in front]; fy = [p[ykey] for p in front]
        for fw in FW:
            g = [r for r in pts if r["fw"] == fw]
            if not g:
                continue
            fig.add_trace(go.Scatter(
                x=[r["usd"] for r in g], y=[r[ykey] for r in g], mode="markers",
                name=FW_NAME[fw], legendgroup=fw, showlegend=(col == 1),
                marker=dict(color=FWCOL[fw], size=9, line=dict(color="white", width=1)),
                error_x=dict(type="data", symmetric=False,
                             array=[r["usdhi"] - r["usd"] for r in g],
                             arrayminus=[r["usd"] - r["usdlo"] for r in g],
                             color=FWCOL[fw], thickness=1, width=3),
                error_y=dict(type="data", symmetric=False,
                             array=[r[yhi] - r[ykey] for r in g],
                             arrayminus=[r[ykey] - r[ylo] for r in g],
                             color=FWCOL[fw], thickness=1, width=3),
                customdata=[[r["key"], r["usd"], r["n"], r["advisory_status"]] for r in g],
                hovertemplate=("<b>%{customdata[0]}</b><br>$%{x:.4f} per campaign model-adjudicated finding (legacy; repeats included) · "
                               + ylab + " %{y:.3f}<br>n=%{customdata[2]} PRs<br>%{customdata[3]}<extra></extra>"),
            ), row=1, col=col)
            err_idx.append(len(fig.data) - 1)
        # frontier envelope + labelled frontier cells
        fig.add_trace(go.Scatter(x=fx, y=fy, mode="lines+markers", name="Pareto frontier (point estimates)",
                                 legendgroup="frontier", showlegend=(col == 1),
                                 line=dict(color="black", width=1.2, shape="hv"),
                                 marker=dict(color="black", size=12, symbol="circle-open", line=dict(width=2)),
                                 hovertemplate="frontier point<br>$%{x:.4f} · %{y:.3f}<extra></extra>"),
                      row=1, col=col)
        for i, p in enumerate(front):
            # Plotly annotations on log axes take log10 coordinates (traces take raw values).
            fig.add_annotation(x=float(np.log10(p["usd"])), y=p[ykey], text=str(i + 1),
                               showarrow=True, arrowhead=0, arrowwidth=0.6, arrowcolor="#888",
                               ax=8, ay=-18 if i % 2 == 0 else 18,
                               bgcolor="white", font=dict(size=10, color="#333"), row=1, col=col)
        key = "<br>".join(f"{i + 1}. {M_SHORT[p['m']]}·{FW_SHORT[p['fw']]}·{p['e']}"
                             for i, p in enumerate(front))
        fig.add_annotation(x=0, y=-0.23, xref=f"x{'' if col == 1 else col} domain",
                           yref="paper", text=key, showarrow=False, xanchor="left", yanchor="top",
                           align="left", font=dict(size=10))
        fig.update_xaxes(type="log", title_text="metered $ per campaign model-adjudicated finding (legacy; log)", row=1, col=col)
        fig.update_yaxes(title_text=ylab, range=quality_range(pts, ykey, yhi), row=1, col=col)
    fig.update_layout(
        title=dict(text=("Cost/quality frontier — complete cells only<br>"
                         "<sup>x: original campaign model judgments, including repeated reports; y: recall or revised F2′<br>"
                         "unmeasured advisory cells are omitted from F2′ panels</sup>"), font=dict(size=13)),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", font=dict(size=10),
                    x=1.02, y=1, bordercolor="#d9dee5", borderwidth=1),
        margin=dict(l=70, r=200, t=110, b=185), height=680, font=FONT, plot_bgcolor="white",
    )
    save(fig, "fig_pareto_frontier",
         "Cost/quality frontier: dollars per original campaign model-adjudicated finding (including repeats) vs recall and revised F2′",
         "interactive build of analysis/figures/fig_pareto_frontier.png; matrix ci.usd_per_real + "
         "true_gold_defects.verified.cells")


# =====================================================================  4. selection effect
def chart_selection_effect() -> None:
    se = M["selection_effect"]
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                        subplot_titles=("recall", "F1 (strict 42-golden lens)"))
    err_idx = []
    for col, (ka, kb, cik, lab) in enumerate(
            (("recall_t6", "recall_full", "ci_full_recall", "recall"),
             ("F1_t6", "F1_full", "ci_full_F1", "F1")), start=1):
        for m in MODELS:
            g = [(k, v) for k, v in se.items() if k.split("|")[0] == m]
            if not g:
                continue
            x = [v[kb] for _, v in g]; y = [v[ka] for _, v in g]
            lo = [v.get(cik, [v[kb]] * 4)[1] for _, v in g]
            hi = [v.get(cik, [v[kb]] * 4)[2] for _, v in g]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="markers", name=M_SHORT[m], legendgroup=m, showlegend=(col == 1),
                marker=dict(color=MODELCOL[m], size=9, line=dict(color="white", width=1)),
                error_x=dict(type="data", symmetric=False,
                             array=[h - xx for h, xx in zip(hi, x)],
                             arrayminus=[xx - l for xx, l in zip(x, lo)],
                             color=MODELCOL[m], thickness=1, width=3),
                customdata=[[k, v.get("n_full"), f"{v[ka] - v[kb]:+.3f}"] for k, v in g],
                hovertemplate=("<b>%{customdata[0]}</b><br>top-6 " + lab + " %{y:.3f} · "
                               "full-50 %{x:.3f} (n=%{customdata[1]} PRs)<br>"
                               "gap (top-6 − full-50) %{customdata[2]}<extra></extra>"),
            ), row=1, col=col)
            err_idx.append(len(fig.data) - 1)
        fig.add_trace(go.Scatter(x=[0.05, 0.95], y=[0.05, 0.95], mode="lines",
                                 name="y = x (no selection effect)", legendgroup="diag",
                                 showlegend=(col == 1), line=dict(color="black", dash="dash", width=1),
                                 hoverinfo="skip"), row=1, col=col)
        fig.add_annotation(x=0.05, y=0.55, xref=f"x{'' if col == 1 else col} domain",
                           yref=f"y{'' if col == 1 else col} domain", showarrow=False,
                           text="above the line: did <b>better</b> on the selected top-6 than on the full 50",
                           font=dict(size=9, color="#555"), xanchor="left", align="left", row=1, col=col)
        fig.add_annotation(x=0.95, y=0.05, xref=f"x{'' if col == 1 else col} domain",
                           yref=f"y{'' if col == 1 else col} domain", showarrow=False,
                           text="below the line: relatively stronger on the full 50",
                           font=dict(size=9, color="#555"), xanchor="right", align="right", row=1, col=col)
        fig.update_xaxes(title_text=f"{lab} on the full 50-PR benchmark (cells with ≥40/50 scored PRs)",
                         range=[0.05, 0.95], row=1, col=col)
        fig.update_yaxes(title_text=f"{lab} on the selected top-6", range=[0.05, 0.95], row=1, col=col)
    fig.update_layout(
        title=dict(text=("Selection effect: the top-6 sample vs the full 50-PR benchmark<br>"
                         "<sup>points above the diagonal scored <b>higher</b> on the selected six than on the "
                         "full 50 — the selection favoured them (the opposite of a 'harder than average' reading)</sup>"),
                   font=dict(size=13)),
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers", font=dict(size=10),
                    x=1.02, y=1, bordercolor="#d9dee5", borderwidth=1),
        margin=dict(l=70, r=190, t=110, b=70), font=FONT, plot_bgcolor="white",
    )
    save(fig, "fig_selection_effect",
         "Selection effect: top-6 vs full-50 per cell (the corrected direction)",
         "interactive build of analysis/figures/fig_selection_effect.png; "
         "final_report_metrics.json selection_effect")


def main() -> None:
    print("writing interactive fragments to analysis/figures/interactive/")
    chart_defects_found()
    chart_true_gold_pareto()
    chart_pareto_frontier()
    chart_selection_effect()
    with open(f"{OUT}/manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    print(f"manifest.json: {len(manifest)} entries")


if __name__ == "__main__":
    main()
