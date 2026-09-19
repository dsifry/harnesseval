#!/usr/bin/env python3
"""Build the interactive HTML dashboard (analysis/figures/interactive_dashboard.html).

Single self-contained page (plotly.js via CDN) with:
  1. Efficiency explorer — scatter of all complete top-6 cells; x/y metric dropdowns
     ($/run, wall s/run, $/golden TP, $/real finding, tokens/run  ×  F1, F2, recall, adjP),
     log toggle, error-bar CIs, hover card, click-to-open cell details side panel,
     legend isolate (double-click a model), framework as marker symbol.
  2. Effort ladder — F1 vs $/run per model with framework dropdown.
  3. Token composition — stacked fresh/cached/cache-write/output per cell, effort dropdown.
  4. Selection effect — full-50 vs top-6 recall, y=x reference line.
Style: OWID/NYT-inspired minimal chrome, direct annotation of the recommendation cell.

Usage: .venv/bin/python tools/final_report_html.py
"""
import json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(f"{ROOT}/analysis/final_report_metrics.json"))
D = json.load(open(f"{ROOT}/analysis/final_report_dataset.json"))

# Derived true-gold universe (never hardcode the counts — they change with the verified registry).
TGDER = M["true_gold_defects"]["verified"]["derived"]["coverage"]
TG_DEN = int(TGDER["den"])            # 147 true bugs
TG_GOLDENS = int(TGDER["goldens_den"])  # 42 Martian goldens
TG_DEFECTS = int(TGDER["defects_den"])  # verified distinct hidden-gold defects (105)

MODELS = ["claude-fable-5-1", "gpt-6-astra", "gpt-5.6-sol", "claude-opus-5",
          "glm-5.3-vision-background", "gpt-5.6-terra", "claude-sonnet-5",
          "glm-5.3-flash-background"]
FWS = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
SH = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV",
      "claude-fable-5-1": "fable-5.1", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
      "claude-opus-5": "opus-5", "glm-5.3-vision-background": "glm-vis",
      "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet-5",
      "glm-5.3-flash-background": "glm-flash"}
MCOL = {"claude-fable-5-1": "#B07AA1", "gpt-6-astra": "#4C72B0", "gpt-5.6-sol": "#DD8452",
        "claude-opus-5": "#937860", "glm-5.3-vision-background": "#8172B3",
        "gpt-5.6-terra": "#9372B0", "claude-sonnet-5": "#DA8BC2",
        "glm-5.3-flash-background": "#55A868"}
SYM = {"vanilla-engineered": "circle", "compound-realistic": "square", "metareview-realistic": "triangle-up"}

cells = []
for k, v in M["matrix"].items():
    if v["n_pr"] < 6:
        continue
    m, fw, e = k.split("|")
    c = {"model": m, "modelShort": SH[m], "fw": fw, "fwShort": SH[fw], "eff": e,
         "color": MCOL[m], "symbol": SYM[fw]}
    for met in ("recall", "adjP", "F1", "F2", "cost_run", "usd_per_real", "usd_per_tp",
                "tok_run", "wall_run", "price_per_ktok", "recall_core", "recall_strict"):
        ci = v["ci"].get(met)
        if ci:
            c[met] = ci[0]; c[met + "_lo"] = ci[1]; c[met + "_hi"] = ci[2]
    c["beyond_per_pr"] = v["real_beyond"] / v["n_pr"]
    kx = f"{m}|{fw}|{e}"
    ex = M["expanded_gold"]["matrix_exp"].get(kx)
    if ex:
        c["TP_exp"] = ex["TP_exp"]
        c["usd_per_tp_exp"] = (v["ci"]["cost_run"][0] * v["n_pr"] / ex["TP_exp"]) if ex["TP_exp"] else None
    # TRUE golden set (§10d): 42 goldens + the deduplicated, verified defects with archived reproduction/fix-test evidence
    se = M["true_gold_defects"]["verified"]["cells"].get(kx)
    if se:
        c["TP_sem"] = se["TP"]
        c["usd_per_tp_sem"] = (v["ci"]["cost_run"][0] * v["n_pr"] / se["TP"]) if se["TP"] else None
        c["recall_sem"] = se["recall"]; c["recall_sem_lo"] = se["ci"]["recall"][1]; c["recall_sem_hi"] = se["ci"]["recall"][2]
        c["F1_sem"] = se["F1"]; c["F1_sem_lo"] = se["ci"]["F1"][1]; c["F1_sem_hi"] = se["ci"]["F1"][2]
        c["F1p_sem"] = se["F1p"]; c["F1p_sem_lo"] = se["ci"]["F1p"][1]; c["F1p_sem_hi"] = se["ci"]["F1p"][2]
        c["adjP_sem"] = se["adjP"]; c["adjPp_sem"] = se["adjPp"]
        c["advisory_measured"] = se.get("advisory_measured", False)
        c["advisory_count"] = se.get("advisory_count", 0)
        c["advisory_instruments"] = "/".join(se.get("advisory_instruments") or []) or "not recorded"
        c["advisory_unresolved"] = se.get("advisory_below_threshold", se.get("advisory_unresolved", 0))
        c["F2p_unresolved_bounds"] = se.get("F2p_unresolved_bounds")
        c["advisory_status"] = ("measured" if se.get("advisory_measured", False) else
                                "partly or wholly unmeasured; observed credit only, not fully comparable")
    c["F2_sem"] = se.get("F2"); c["F2p_sem"] = se.get("F2p")
    c["F2p_sem_lo"] = se["ci"]["F2p"][1] if se.get("ci", {}).get("F2p") else None
    c["F2p_sem_hi"] = se["ci"]["F2p"][2] if se.get("ci", {}).get("F2p") else None
    c["TP_golden"] = v.get("TP")
    _pp = {u: {"goldens": v["goldens"], "union_sem": v["verified_defects"]}
           for u, v in M["true_gold_defects"]["per_pr"].items()}
    _cov = [r["url"] for r in D["selected_runs"] if r["model"] == m and r["framework"] == fw and r["effort"] == e and r["url"] in _pp]
    c["ceiling"] = sum(_pp[u]["goldens"] + _pp[u]["union_sem"] for u in _cov)
    c["instruments"] = "/".join(v["instruments"]); c["judges"] = "/".join(v["judges"])
    c["run_dates"] = ",".join(v["run_dates"])
    c["glm_prefix"] = v["glm_prefix_runs"]; c["pmu_missing"] = v["pmu_missing_runs"]
    cells.append(c)

# token composition per cell (mean per PR, k tokens)
tok = {}
for m in MODELS:
    for fw in FWS:
        for e in ("low", "medium", "high"):
            runs = [r for r in D["selected_runs"]
                    if r["model"] == m and r["framework"] == fw and r["effort"] == e
                    and r["url"] in D["top6"]]
            if len(runs) < 6:
                continue
            label = f"{SH[m]}·{SH[fw]}·{e}"
            fresh = sum(r["fresh_in"] for r in runs) / 6 / 1000
            cached = sum(r["cached_in"] for r in runs) / 6 / 1000
            cw = sum(r["cache_w"] for r in runs) / 6 / 1000
            out = sum(r["out_tok"] for r in runs) / 6 / 1000
            tok[label] = {"label": label, "model": m, "fw": fw, "eff": e,
                          "fresh": fresh, "cached": cached, "cw": cw,
                          "out": out, "total": fresh + cached + cw + out,
                          "color": MCOL[m]}

sel_effect = [{"cell": k, **{kk: vv for kk, vv in v.items() if kk != "ci_full_F1"}}
              for k, v in M["selection_effect"].items()]

# per-PR severity vs recall for full-50 cells (the selection view)
SEV_W = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
percell = {}
for m in MODELS:
    for fw in FWS:
        for e in ("low", "medium", "high"):
            runs = [r for r in D["selected_runs"]
                    if r["model"] == m and r["framework"] == fw and r["effort"] == e]
            if len(runs) < 40:
                continue
            label = f"{SH[m]}·{SH[fw]}·{e}"
            percell[label] = {"model": m, "fw": fw, "eff": e, "prs": [
                              {"pr": r["url"].rsplit("/", 1)[-1],
                               "sev": D["pr_golden"][r["url"]]["sev_weight"],
                               "rec": (r["tp"] / (r["tp"] + r["fn"])) if (r["tp"] + r["fn"]) else None,
                               "top6": r["url"] in D["top6"]}
                              for r in runs]}

def round5(o):
    """Cap every presented number at 5 decimal places (recursively).
    Classic trick: multiply by 1e6, truncate to int, divide by 1e6. Handles dicts,
    lists AND tuples."""
    if isinstance(o, float):
        return int(o * 100000) / 100000
    if isinstance(o, dict):
        return {k: round5(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [round5(v) for v in o]
    return o

expd = {}
for k, v in M["true_gold_defects"]["verified"]["cells"].items():
    st = M["matrix"].get(k)
    if not st:
        continue
    expd[k] = {"recall": st["recall"], "F1": st["F1"],
               "recall_sem": v["recall"], "ci_recall_sem": list(v["ci"]["recall"]),
               "F1_sem": v["F1"], "ci_F1_sem": list(v["ci"]["F1"]),
               "F1p_sem": v["F1p"], "F2_sem": v.get("F2"), "F2p_sem": v.get("F2p"),
               "adjP_sem": v["adjP"], "adjPp_sem": v["adjPp"]}

# Compare identical complete model/effort cohorts across all three frameworks.
verified = M["true_gold_defects"]["verified"]
complete = {f"{c['model']}|{c['eff']}" for c in cells if c["advisory_measured"]}
matched = sorted(me for me in complete if all(
    any(c["model"] + "|" + c["eff"] == me and c["fw"] == fw and c["advisory_measured"]
        for c in cells) for fw in FWS))
means = {fw: sum(verified["cells"][f"{me.rsplit('|', 1)[0]}|{fw}|{me.rsplit('|', 1)[1]}"]["F2p"]
                 for me in matched) / len(matched) for fw in FWS}
paired = [verified["pairs"][me]["dF2p"] for me in matched]
positive = sum(ci[1] > 0 for ci in paired)
negative = sum(ci[2] < 0 for ci in paired)
framework_summary = (
    f"<b>Matched framework comparison:</b> across {len(matched)} identical model/effort cohorts, "
    f"mean F2′ is <b>MRV {means['metareview-realistic']:.3f}</b>, "
    f"CE {means['compound-realistic']:.3f}, and vanilla {means['vanilla-engineered']:.3f}. "
    f"MRV leads CE in {sum(ci[0] > 0 for ci in paired)}/{len(paired)} point comparisons; "
    f"paired 95% intervals favor MRV in {positive}, CE in {negative}, and include zero in "
    f"{len(paired) - positive - negative}. These averages differ from the individual configurations plotted below."
)

DATA = round5({"cells": cells, "tok": tok, "sel": sel_effect, "percell": percell, "exp": expd})

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>harnesseval — final report interactive explorer</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  :root { --ink:#1a1a1a; --muted:#666; --line:#e6e6e6; --bg:#fdfdfd; --card:#fff; }
  * { box-sizing:border-box; }
  body { font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         color:var(--ink); background:var(--bg); margin:0; padding:0; }
  .wrap { max-width:1180px; margin:0 auto; padding:36px 28px 64px; }
  h1 { font-size:26px; margin:0 0 4px; font-weight:700; letter-spacing:-.02em; }
  .sub { color:var(--muted); font-size:14px; margin:0 0 8px; }
  .caveat { font-size:13px; color:var(--muted); border-left:3px solid #b07aa1; padding:6px 12px; margin:12px 0 28px; background:#faf7fa; }
  .panel { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:18px 18px 8px; margin-bottom:30px; box-shadow:0 1px 2px rgba(0,0,0,.04); }
  .panel h2 { font-size:17px; margin:0 0 2px; }
  .panel .note { color:var(--muted); font-size:12.5px; margin:0 0 12px; }
  .panel .note .mech { margin-top:7px; padding-top:7px; border-top:1px solid var(--line); font-size:11.5px; }
  .controls { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:10px; font-size:13px; }
  .controls select { font:inherit; padding:4px 8px; border:1px solid #ccc; border-radius:6px; background:#fff; }
  .controls label { display:flex; align-items:center; gap:4px; color:var(--muted); }
  .layout { display:grid; grid-template-columns: minmax(0,1fr) 300px; gap:18px; }
  #chart1 { height:520px; }
  #details { border:1px solid var(--line); border-radius:8px; padding:14px; font-size:13px; background:#fbfbfb; height:fit-content; }
  #details h3 { margin:0 0 6px; font-size:14px; }
  #details table { border-collapse:collapse; width:100%; }
  #details td { padding:2px 4px; vertical-align:top; }
  #details td:first-child { color:var(--muted); white-space:nowrap; }
  #chart2,#chart3,#chart4 { height:420px; }
  footer { color:var(--muted); font-size:12px; margin-top:26px; }
  a { color:#4C72B0; text-decoration:none; } a:hover { text-decoration:underline; }
  @media (max-width:900px){ .layout{grid-template-columns:1fr} }

  /* ---- filter dock: sticky; shrinks to the side when the checkbox area scrolls off, reverses on scroll up ---- */
  #filtersSentinel { height:1px; margin:0; padding:0; }
  #filterWrap { position:sticky; top:10px; z-index:60; will-change:transform;
    transition: width .3s cubic-bezier(.2,.75,.3,1), transform .3s cubic-bezier(.2,.75,.3,1),
                margin .3s cubic-bezier(.2,.75,.3,1), box-shadow .3s ease; }
  #filterWrap .panel { transition: padding .3s ease, box-shadow .3s ease, border-radius .3s ease; }
  /* dock to the LEFT, and when the viewport is wider than the content column, slide into the left
     whitespace so the box sits beside the chart instead of over it. The translate is the available
     gutter, clamped at 0 (narrow windows simply dock at the column edge). */
  #filterWrap.docked { width:340px; margin-left:0; margin-right:auto; transform-origin:top left;
    transform: translateX(calc(-1 * max(0px, (100vw - 1180px) / 2 - 4px))) scale(.88); }
  #filterWrap.docked .panel { padding:11px 13px 9px; border-radius:12px;
    box-shadow:0 10px 30px rgba(0,0,0,.16), 0 2px 6px rgba(0,0,0,.08); background:rgba(255,255,255,.985);
    max-height:calc(100vh - 26px); overflow:auto; }
  #filterWrap.docked .panel h2 { font-size:12.5px; margin-bottom:4px; }
  #filterWrap.docked .panel .note { display:none; }
  #filterWrap.docked .controls { gap:3px 7px; margin-bottom:2px; }
  #filterWrap.docked .controls > div { gap:6px !important; }
  #filterWrap.docked .controls b { font-size:10.5px !important; min-width:66px !important; }
  #filterWrap.docked label { font-size:11px; }
  #filterWrap.docked input[type=checkbox] { transform:scale(.92); }
</style>
</head>
<body>
<div class="wrap">
  <h1>Automated code review — final campaign explorer</h1>
  <div class="sub">8 models × 3 harnesses × 3 effort levels on the six severity-hardest Martian-benchmark PRs · 66 complete cells · data freeze 2026-09-16 09:35 · quality panels use the <b>true golden set</b> (__TGGOLD__ goldens + __TGDEF__ verified defects with archived reproduction/fix-test evidence = __TGDEN__ true bugs — REPORT.md §3.1; catalogue: GOLD_DEFECT_CATALOG.md)</div>
  <div id="filtersSentinel"></div>
  <div id="filterWrap">
  <div class="panel" id="filtersPanel">
    <h2>Filters — one key area, applies to every panel below</h2>
    <div class="controls" style="flex-direction:column;align-items:flex-start;gap:7px">
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b style="font-size:12px;min-width:104px;display:inline-block">models</b> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="claude-fable-5-1" checked> fable-5.1</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="gpt-6-astra" checked> astra</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="gpt-5.6-sol" checked> sol</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="claude-opus-5" checked> opus-5</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="glm-5.3-vision-background" checked> glm-vis</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="gpt-5.6-terra" checked> terra</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="claude-sonnet-5" checked> sonnet-5</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fm" value="glm-5.3-flash-background" checked> glm-flash</label></div>
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b style="font-size:12px;min-width:104px;display:inline-block">harnesses</b> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="ff" value="vanilla-engineered" checked> vanilla-engineered (van)</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="ff" value="compound-realistic" checked> Compound Engineering (ce)</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="ff" value="metareview-realistic" checked> metareview (mrv)</label></div>
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b style="font-size:12px;min-width:104px;display:inline-block">connections</b> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" id="showlines" checked> connect effort steps (low &rarr; medium &rarr; high) on charts 1a&ndash;1e, one line per model &times; harness</label></div>
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b style="font-size:12px;min-width:104px;display:inline-block">effort levels</b> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fe" value="low" checked> low</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fe" value="medium" checked> medium</label> <label style="display:inline-flex;align-items:center;gap:3px"><input type="checkbox" class="fe" value="high" checked> high</label></div>
    </div>
    <div class="note">Untick to hide; every chart, ladder, bar, and dumbbell below redraws instantly. Default: all on.
      This box sticks to the top as you scroll, shrinks, and slides to the LEFT into the page margin when there is room (it slides back when you scroll up).</div>
  </div>
  </div>

  <div class="caveat">__FRAMEWORK_SUMMARY__</div>
  <div class="caveat">Quality panels score <b>F2′</b>: real bugs found on the true golden set (__TGGOLD__ goldens + __TGDEF__ verified defects), with credit for accepted useful advisories and penalties for unsupported claims, style-only findings, and vague concerns. F2′ = (5T + A) / (4D + T + A + H), where T = distinct true bugs found, D = true-set size, A = accepted useful advisories, and H = effective unsupported findings. All 403 selected reviews have completed adjudication. Advisory credit requires classifier confidence ≥0.70; unsupported-finding penalties require ≥0.80. Findings below the applicable cutoff remain classified but unscored. Confidence is model-reported, not a calibrated probability. Rankings require complete six-PR coverage. The F2′ advisory instrument is recorded separately from legacy bug-matching judges. Verified bug assignments fix bug credit and prevent those findings from receiving advisory credit or unsupported penalties. Every point is one (model × harness × effort level) cell, one selected healthy scored run per PR (n=6). Bars/whiskers are 95% cluster-bootstrap CIs over PRs. <b>Hover</b> for detail; <b>click</b> a point for the full cell card (right); <b>double-click</b> a legend entry to isolate a model; single-click to toggle. Full report: <a href="../../REPORT.md">REPORT.md</a> · coverage: <a href="../COVERAGE.md">COVERAGE.md</a>.</div>

  <div class="panel">
  <div class="panel">
    <h2>1a · Value for money — how many real bugs does a dollar per PR review buy?</h2>
    <div class="note"><div><b>How to read the y-axis — F2′, our overall quality score.</b> It rewards <b>finding real bugs</b> and gives additional credit for <b>accepted useful advisories</b>. The true golden set contains __TGGOLD__ Martian goldens + __TGDEF__ verified defects (__TGDEN__ total). <b>F2′ = (5T + A) / (4D + T + A + H)</b>: T is distinct true bugs found, D is true-set size, A is accepted important non-bug advisories from the merged full review, and H is effective unsupported findings (including false claims, style-only findings, and vague concerns). Advisories add credit without changing bug recall. Legacy F1′ and adjP′ retain their burden-based definitions. All selected reviews are adjudicated. Only useful advisories at confidence ≥0.70 receive credit; unsupported findings at ≥0.80 receive penalties. Lower-confidence findings are classified but unscored. F2′ is a custom score, not measured developer utility. Higher is better; the axis fits the observed scores and confidence intervals. <i>Full definition: REPORT.md §3.1.</i></div><div class="mech">x = metered $ per PR review (log) — what a single review costs. One point per complete six-PR cell; all selected reviews are adjudicated. <b>Color</b> = model; <b>shape</b> = harness (○ van, □ CE, △ MRV); <b>connecting lines</b> follow one model × harness across effort levels (solid vanilla, dashed CE, dotted MRV). <b>Hover</b> for the value + CI; <b>click</b> a point for its card below; <b>double-click</b> a legend entry to isolate a model. CIs are off by default.</div></div>
    <div class="controls"><label><input type="checkbox" id="showci1a"> show 95% CIs</label></div>
    <div id="chart1a" style="height:430px"></div>
    <div class="takeaway" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"><b>Takeaway:</b> compare the upper-left cells for strong bug quality plus advisory credit at lower cost. Use the cell cards for observed advisory counts and uncertainty; these panels compare complete six-PR cells.</div>
    <div id="details1a" style="margin-top:10px;border:1px solid var(--line);border-radius:8px;padding:14px;font-size:13px;background:#fbfbfb"><h3 style="margin:0 0 6px;font-size:14px">Cell details</h3><div style="color:#888">Click a point.</div></div>
  </div>

  <div class="panel">
    <h2>1b · Does a slower setup buy a better review?</h2>
    <div class="note"><div><b>A setup that makes you wait longer is only worth it if it reviews better.</b> Every point is one setup; the further left, the less time you spend waiting for the review. When two setups sit at the same height they have the same observed F2′ point estimate; the one further left has lower measured latency. Compare their confidence intervals, then pilot the candidates and measure developer triage time. <b>The target is up and to the left.</b> A point that is high but far right is thorough at the cost of wall-clock rather than dollars — and for a person waiting on a PR, minutes often matter more than cents. y = <b>F2′</b>, our overall quality score — bug quality plus accepted advisory credit, penalised for unsupported findings. <i>Full definition under 1a.</i></div><div class="mech">One point per complete six-PR cell; all selected reviews are adjudicated. <b>Color</b> = model; <b>shape</b> = harness (○ van, □ CE, △ MRV); <b>connecting lines</b> follow one model × harness across effort levels (solid vanilla, dashed CE, dotted MRV). <b>Hover</b> for the value + CI; <b>click</b> a point for its card below; <b>double-click</b> a legend entry to isolate a model. CIs are off by default.</div></div>
    <div class="controls"><label><input type="checkbox" id="showci1b"> show 95% CIs</label></div>
    <div id="chart1b" style="height:430px"></div>
    <div class="takeaway" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"><b>Takeaway:</b> GLM Flash and Vision MRV at low effort take about 79 and 95 seconds per review, versus about 100 seconds for Opus MRV low. Several frontier one-shot cells are faster still. GLM medium/high-effort cells can take much longer; compare the individual configurations and their uncertainty. These are measured end-to-end latencies, and this experiment does not isolate the cause of the differences.</div>
    <div id="details1b" style="margin-top:10px;border:1px solid var(--line);border-radius:8px;padding:14px;font-size:13px;background:#fbfbfb"><h3 style="margin:0 0 6px;font-size:14px">Cell details</h3><div style="color:#888">Click a point.</div></div>
  </div>

  <div class="panel">
    <h2>1c · What does it cost to catch one true bug?</h2>
    <div class="note"><div><b>This is the price per true bug</b> — one of the __TGDEN__ real bugs in our golden set (__TGGOLD__ Martian goldens plus __TGDEF__ verified against archived evidence) — plotted against overall review quality. Cheap and high is the win. A setup far to the left but low is buying cheap catches while missing a lot; one far right and high is thorough but you pay for it. Compare it with 1d, and mind the denominators: <b>1c counts each distinct true bug once</b> (a bug is credited once no matter how many times it was reported), while <b>1d divides by findings labelled real by the original campaign model adjudicators</b> — the same bug reported repeatedly counts each time, and beyond-gold findings count too — so the two cost measures use different judgments and denominators. A wide 1c↔1d gap means many campaign model-adjudicated findings per distinct credited bug. y = <b>F2′</b>, our overall quality score — bug quality plus accepted advisory credit, penalised for unsupported findings. <i>Full definition under 1a.</i></div><div class="mech">One point per complete six-PR cell; all selected reviews are adjudicated. <b>Color</b> = model; <b>shape</b> = harness (○ van, □ CE, △ MRV); <b>connecting lines</b> follow one model × harness across effort levels (solid vanilla, dashed CE, dotted MRV). <b>Hover</b> for the value + CI; <b>click</b> a point for its card below; <b>double-click</b> a legend entry to isolate a model. CIs are off by default.</div></div>
    <div class="controls"><label><input type="checkbox" id="showci1c"> show 95% CIs</label></div>
    <div id="chart1c" style="height:430px"></div>
    <div class="takeaway" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"><b>Takeaway (true golden set):</b> per distinct true bug found, the GLM harness cells pay far less than the frontier models: glm-flash · MRV · low $0.0020/bug, glm-vis · MRV · low $0.0185/bug, glm-vis · MRV · high $0.204/bug, versus opus · CE · low $0.272/bug and fable · vanilla · high $0.152/bug — and fable finds 51 real bugs to glm-vis MRV high's 76.</div>
    <div id="details1c" style="margin-top:10px;border:1px solid var(--line);border-radius:8px;padding:14px;font-size:13px;background:#fbfbfb"><h3 style="margin:0 0 6px;font-size:14px">Cell details</h3><div style="color:#888">Click a point.</div></div>
  </div>

  <div class="panel">
    <h2>1d · Cost per campaign model-adjudicated finding</h2>
    <div class="note"><div><b>This panel retains the original campaign’s finding-cost accounting.</b> <b>x uses original campaign model judgments and includes repeated reports; y uses revised F2′.</b> The x-axis divides the run's cost by every finding the original campaign model adjudicators labelled real — golden hits plus beyond-gold real findings, counted with multiplicity: if a setup reports the same bug three times, it counts three times. That is a different denominator from panel 1c, which prices each of the __TGDEN__ distinct true bugs (__TGGOLD__ goldens + __TGDEF__ verified hidden-gold) once. For glm-vis · MRV · low the same run is $0.0037 per campaign model-adjudicated finding (360 reports, including repeats) but $0.019 per distinct true bug (72 credited) — the two numbers are 5× apart and answer different questions: 1d asks 'what does a campaign model-adjudicated finding cost', 1c asks 'what does a distinct bug cost'. <b>Cheap and high is best.</b> A wide 1c↔1d gap means many campaign model-adjudicated findings per distinct bug — including duplicates and beyond-gold items the true-set score does not credit. This legacy denominator is not the revised deduplicated T + A. y = <b>F2′</b>, our overall quality score — bug quality plus accepted advisory credit, penalised for unsupported findings. <i>Full definition under 1a.</i></div><div class="mech">One point per complete six-PR cell; all selected reviews are adjudicated. <b>Color</b> = model; <b>shape</b> = harness (○ van, □ CE, △ MRV); <b>connecting lines</b> follow one model × harness across effort levels (solid vanilla, dashed CE, dotted MRV). <b>Hover</b> for the value + CI; <b>click</b> a point for its card below; <b>double-click</b> a legend entry to isolate a model. CIs are off by default.</div></div>
    <div class="controls"><label><input type="checkbox" id="showci1d"> show 95% CIs</label></div>
    <div id="chart1d" style="height:430px"></div>
    <div class="takeaway" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"><b>Takeaway:</b> counting findings labelled real by the original campaign model adjudicators (golden + beyond-gold, with multiplicity), $ per campaign model-adjudicated finding runs $0.0002–$0.37 across cells — the GLM harness cells sit at the cheap end and the high-effort frontier-model cells at the expensive end. Do not read this as the price of a distinct true bug — that is panel 1c, 5× higher for the recommended cell. The frontier panels show which cells offer the strongest observed quality at each price; six-PR scope and classifier uncertainty apply.</div>
    <div id="details1d" style="margin-top:10px;border:1px solid var(--line);border-radius:8px;padding:14px;font-size:13px;background:#fbfbfb"><h3 style="margin:0 0 6px;font-size:14px">Cell details</h3><div style="color:#888">Click a point.</div></div>
  </div>

  <div class="panel">
    <h2>1e · Do extra tokens buy a better review?</h2>
    <div class="note"><div><b>More tokens should mean a better review, or they are just a bigger bill.</b> Every point is one setup; the further left, the fewer tokens a review consumes (cached reads and writes included). If a setup using fewer tokens sits as high as one using more, their observed F2′ point estimates match; this alone does not establish equivalent review quality. Compare confidence intervals and validate developer triage time in a pilot. <b>Up and to the left is best.</b> This is where harness design shows itself: the same model wrapped in a harness usually spends several times the tokens of a single pass, and this panel shows how token use varies alongside observed F2′; a pilot can test whether those differences improve developer outcomes. y = <b>F2′</b>, our overall quality score — bug quality plus accepted advisory credit, penalised for unsupported findings. <i>Full definition under 1a.</i></div><div class="mech">One point per complete six-PR cell; all selected reviews are adjudicated. <b>Color</b> = model; <b>shape</b> = harness (○ van, □ CE, △ MRV); <b>connecting lines</b> follow one model × harness across effort levels (solid vanilla, dashed CE, dotted MRV). <b>Hover</b> for the value + CI; <b>click</b> a point for its card below; <b>double-click</b> a legend entry to isolate a model. CIs are off by default.</div></div>
    <div class="controls"><label><input type="checkbox" id="showci1e"> show 95% CIs</label></div>
    <div id="chart1e" style="height:430px"></div>
    <div class="takeaway" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"><b>Takeaway:</b> harness cells burn a median of ~10× the tokens of a vanilla single pass (matched pairs range from ~1× to ~76×); the frontier harnesses are 75–90% cached reads at 10% of list input (why their blended rate drops to 0.14–0.18 ¢ per k-token), while the GLM harnesses use 100–570k tokens/run at list input rates — both arrive cheap per token, ~13× apart in $ per task.</div>
    <div id="details1e" style="margin-top:10px;border:1px solid var(--line);border-radius:8px;padding:14px;font-size:13px;background:#fbfbfb"><h3 style="margin:0 0 6px;font-size:14px">Cell details</h3><div style="color:#888">Click a point.</div></div>
  </div>



  <div class="panel">
    <h2>1f · How many real bugs does each setup actually find — and how many does the benchmark ignore?</h2>
    <div class="note"><div><b>This is the &ldquo;how much does it actually find&rdquo; panel — with the benchmark&rsquo;s blind spot exposed.</b> Each bar is one setup. The grey part is bugs the strict benchmark knows about and scores; the coloured part is <b>real bugs the benchmark never scores</b> — defects verified against archived reproduction and fix-test evidence; some catalogue entries share a test or container-level evidence. A long coloured section means the setup found genuine problems that a benchmark-based score simply cannot see. <b>Read this ranked by bugs found, not by F2′</b>: a setup can lead here and still sit mid-table on quality, because F2′ also rewards accepted useful advisories and penalises unsupported findings. Advisory completeness is tracked separately from the original bug-matching instrument. The two panels answer different questions: 1f asks &ldquo;how much did it find?&rdquo;, the quality panels ask &ldquo;how good is what it found?&rdquo;</div><div class="mech">One bar per setup, sorted by total real bugs found. <b>Grey</b> = Martian goldens (the only thing the strict benchmark scores); <b>coloured</b> = hidden-gold defects it never scores. The dashed line at <b>__TGDEN__</b> is the observed reference set on the six PRs (__TGGOLD__ goldens + __TGDEF__ verified defects); the small grey tick on a row is that setup&rsquo;s <i>coverage ceiling</i> — some setups cover fewer than the six PRs and cannot reach __TGDEN__. <b>Hover</b> for details.</div></div>
    <div id="chart1f" style="height:920px"></div>
    <div id="takeaway1f" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"></div>
  </div>

  <div class="panel">
    <h2>2 · Does more effort buy a better review — and where does it stop paying off?</h2>
    <div class="note"><div><b>Every line follows one model and harness as you turn its effort setting up</b> (low → medium → high). If the line climbs, the higher effort has a higher observed F2′; if it flattens or falls, the extra effort has not improved that point estimate. <b>Compare paired uncertainty and pilot developer outcomes before choosing a setting.</b> These six-PR observations do not establish a causal benefit or harm from effort. Compare lines against each other to see whether a cheap model at high effort beats an expensive one at low effort — which is the question most people actually have.</div><div class="mech">One line per model × harness with points at low → medium → high (left to right). x = metered $ per run (log) — each gridline to the right costs roughly 10× more; y = <b>F2′</b>, our overall quality score (defined under 1a). Colour = model; marker shape = harness (○ vanilla, □ CE, △ MRV). The harness dropdown isolates one harness at a time. The y-axis fits the observed scores and their confidence intervals so the differences remain visible. Hover a point for its value and CI.</div></div>
    <div class="controls"><label>harness <select id="fwsel"></select></label></div>
    <div id="chart2"></div>
  </div>

  <div class="panel">
    <h2>3 · Where does a review's token bill actually come from?</h2>
    <div class="note"><div><b>Two setups can deliver similar review quality at very different cost, and this panel shows where the money went.</b> Each bar breaks a review's tokens into the four things you pay for: input read for the first time, input re-read from cached context, cache writes paid to store that context, and the model's own output including its reasoning. A setup that is expensive because of output is doing a lot of thinking; one that is expensive because of cache writes is paying to remember things it may never reuse. <b>Read this when you want to change a cost, not just compare it</b> — it tells you which lever to pull.</div><div class="mech">The report export shows <b>low effort</b>; use this dashboard’s effort dropdown for medium or high. One stacked bar per cell = mean k-tokens per PR across the six PRs, split into fresh input, cached read, cache write and output (incl. reasoning). Label = model · harness · effort level. Default sort: total tokens, descending. Use the effort dropdown to compare like with like, and the sort dropdown to group rows by model or by harness. The global effort filter above also applies here: the panel shows the intersection of the global filter and the local dropdown selection.</div></div>
    <div class="controls"><label>effort <select id="effsel"></select></label><label>sort <select id="sortsel"><option value="tokens_desc">by total tokens (desc)</option><option value="tokens_asc">by total tokens (asc)</option><option value="model_fw">by model, then harness</option><option value="fw_model">by harness, then model</option></select></label></div>
    <div id="chart3"></div>
  </div>

  <div class="panel">
    <h2>4 · How does original-gold scoring change between the top six and the broader run set?</h2>
    <div class="note"><div><b>This compares original benchmark goldens for setups with broad coverage.</b> Each dot is a setup’s top-six score minus its score across its available 40–50 PRs. Positive gaps mean the six-PR score is higher. These paired descriptive comparisons do not establish out-of-sample rankings or validate the __TGDEN__-bug reference set, which was constructed only for the six selected PRs.</div><div class="mech">One row per cell with at least 40 of 50 PRs covered. Both recall and F1 use the original-gold benchmark lens. x = Δ (top-six − broader run set); the dashed line is zero. Rows are sorted by |Δ|. Use the metric dropdown to switch between recall and F1.</div></div>
    <div class="controls"><label>metric <select id="selmet"><option value="recall">recall</option><option value="F1">F1</option></select></label></div>
    <div id="chart4" style="height:720px"></div>
    <div id="takeaway4" style="margin-top:10px;padding:10px 14px;border-left:4px solid #B07AA1;background:#faf7fa;font-size:13.5px;border-radius:0 8px 8px 0"></div>
  </div>

  <div class="panel">
    <h2>5 · How were the six pull requests selected?</h2>
    <div class="note"><div><b>The six were selected for high golden-comment severity weight.</b> Each dot shows one PR’s severity weight and original-gold recall for the selected setup. The highlighted six average severity weight 18.2, compared with 6.1 for the other 44 benchmark PRs; the lowest selected severity ties the highest unselected severity. This describes a deliberately difficult slice. It does not establish how the six-PR true-gold results generalize to other PRs.</div><div class="mech">x = summed severity weight of original golden comments (Critical = 4, High = 3, Medium = 2, Low = 1). y = per-PR original-gold recall. The dropdown offers setups covering at least 40 PRs; only their available runs are plotted. Highlighted dots = selected PRs; grey = other covered PRs. Dashed lines show unweighted mean per-PR recall within each group, distinct from the pooled recall comparison in panel 4.</div></div>
    <div class="controls"><label>cell <select id="cellsel"></select></label></div>
    <div id="chart5"></div>
  </div>

  <footer>Sources: metered list prices retrieved 2026-09-16 (z.ai, platform.claude.com, developers.openai.com) · numbers from <code>analysis/final_report_metrics.json</code> (cluster bootstrap B=10,000, seed 20260916) · static PNGs in <code>analysis/figures/</code> · built by <code>tools/final_report_html.py</code>.</footer>
</div>

<script>
const DATA = __DATA__;
const mcol = __MCOL__; const msym = __MSYM__; const SH2 = __SH2__;
// ---- global filters (one key area, drives every panel)
const fModels = new Set(Object.keys(mcol));
const fFws = new Set(Object.keys(msym));
const fEffs = new Set(['low','medium','high']);
const vis = c => fModels.has(c.model) && fFws.has(c.fw) && fEffs.has(c.eff);
function redrawAll(){
  // isolate every panel: a filter combination that empties one panel must not stop the others redrawing
  const safe = (fn, arg) => { try { fn(arg); } catch (e) { console.warn('panel redraw failed', e); } };
  VIEWS.forEach(v => safe(drawView, v));
  safe(draw2); safe(refreshEffsel); safe(draw3); safe(draw4); safe(refreshCellsel); safe(draw5); safe(draw6);
}
(function dockFilters(){
  const wrap = document.getElementById('filterWrap');
  const sentinel = document.getElementById('filtersSentinel');
  if (!wrap || !sentinel) return;
  // the sentinel sits immediately ABOVE the filter box: once it has scrolled past the top, the box is
  // pinned -> dock it (shrink + slide right). Scrolling back up re-intersects the sentinel -> undock.
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => wrap.classList.toggle('docked', !es[0].isIntersecting),
      { rootMargin: '-4px 0px 0px 0px', threshold: 0 });
    io.observe(sentinel);
  } else {
    const onScroll = () => {
      const r = sentinel.getBoundingClientRect();
      wrap.classList.toggle('docked', r.bottom < 4);
    };
    window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  }
})();
const _showlines = document.getElementById('showlines');
if (_showlines) _showlines.onchange = () => redrawAll();
document.querySelectorAll('.fm').forEach(cb=>cb.onchange=()=>{ cb.checked?fModels.add(cb.value):fModels.delete(cb.value); redrawAll(); });
document.querySelectorAll('.ff').forEach(cb=>cb.onchange=()=>{ cb.checked?fFws.add(cb.value):fFws.delete(cb.value); redrawAll(); });
document.querySelectorAll('.fe').forEach(cb=>cb.onchange=()=>{ cb.checked?fEffs.add(cb.value):fEffs.delete(cb.value); redrawAll(); });

// N-decimal-places float→string (twin of tools/presfmt.py), default N=5:
// toFixed(N) does exact decimal rounding (kills binary-tail artifacts), then
// parseFloat().toString() strips trailing zeros.
const fmt = (v, n=5) => { if(v==null||isNaN(v)||!isFinite(v)) return '—'; return parseFloat(v.toFixed(n)).toString(); };
// adaptive: < $0.01 -> cents (self-describing ¢), else $ (twin of presfmt.money_adaptive)
const fmtA = (v, n=5) => { if(v==null||isNaN(v)||!isFinite(v)) return '—'; if(Math.abs(v)>0 && Math.abs(v)<0.01) return parseFloat((v*100).toFixed(n)).toString()+'¢'; return '$'+parseFloat(v.toFixed(n)).toString(); };
// bracket takes the POINT's unit (no $/¢ mixing inside one CI)
const fmtAB = (pt, lo, hi, n=5) => { if(Math.abs(pt)>0 && Math.abs(pt)<0.01) return fmtA(pt,n)+' ['+fmtA(lo,n)+', '+fmtA(hi,n)+']'; return '$'+fmt(pt,n)+' [$'+fmt(lo,n)+', $'+fmt(hi,n)+']'; };
const metName = {cost_run:'$/run', usd_per_tp_sem:'$/true bug found', usd_per_real:'$/campaign model-adjudicated finding (legacy; includes repeats)', tok_run:'tokens/run', wall_run:'wall s/run', price_per_ktok:'price per k-tok', F1_sem:'F1 (true set, real-bug precision)', F1p_sem:'F1\u2032 (legacy burden lens)', F2_sem:'F2 (true set, recall-weighted 4:1)', F2p_sem:'F2\u2032 (bug quality + advisory credit)', recall_sem:'recall (true golden set)', adjP_sem:'adjP (claim soundness)', adjPp_sem:'adjP\u2032 (legacy burden lens)'};

function tracesFor(xmet, ymet, showci) {
  const ts = [];
  const EFF_ORDER = ['low','medium','high'];
  const DASH = {'vanilla-engineered':'solid','compound-realistic':'dash','metareview-realistic':'dot'};
  const _sl = document.getElementById('showlines');
  const linesOn = !_sl || _sl.checked;
  for (const m in mcol) {
    const pts = DATA.cells.filter(c => c.model === m && vis(c) && (ymet !== 'F2p_sem' || c.advisory_measured));
    if (!pts.length) continue;                    // nothing visible for this model: nothing to draw
    const hasXCI = pts[0][xmet+'_lo'] != null, hasYCI = pts[0][ymet+'_lo'] != null;
    const t = {
      x: pts.map(c => c[xmet]), y: pts.map(c => c[ymet]),
      mode: 'markers', name: m,
      marker: { color: mcol[m], symbol: pts.map(c => msym[c.fw]), size: 8, line:{width:1,color:'#333',opacity:.4} },
      customdata: pts.map(c => c),
      hovertemplate: '<b>%{customdata.modelShort} · %{customdata.fwShort} · %{customdata.eff}</b><br>' +
        metName[xmet] + ': %{x:.4g}' + (hasXCI ? ' [%{customdata.'+xmet+'_lo:.4g}, %{customdata.'+xmet+'_hi:.4g}]' : '') + '<br>' +
        metName[ymet] + ': %{y:.4g}' + (hasYCI ? ' [%{customdata.'+ymet+'_lo:.4g}, %{customdata.'+ymet+'_hi:.4g}]' : '') + '<br>' +
        'observed useful advisories: %{customdata.advisory_count}<br>F2′ advisory instrument: %{customdata.advisory_instruments}<br>classified findings below scoring threshold: %{customdata.advisory_unresolved}<br>%{customdata.advisory_status}<br>beyond-gold/PR: %{customdata.beyond_per_pr:.1f}<extra></extra>',
    };
    if (showci) {
      if (hasXCI) t.error_x = { type:'data', symmetric:false, array: pts.map(c => Math.max(0,c[xmet+'_hi']-c[xmet])), arrayminus: pts.map(c => Math.max(0,c[xmet]-c[xmet+'_lo'])), thickness:.6, width:2, color:'#555', opacity:.5 };
      if (hasYCI) t.error_y = { type:'data', symmetric:false, array: pts.map(c => Math.max(0,c[ymet+'_hi']-c[ymet])), arrayminus: pts.map(c => Math.max(0,c[ymet]-c[ymet+'_lo'])), thickness:.6, width:2, color:'#555', opacity:.5 };
    }
    ts.push(t);
    if (linesOn) {
      // one connector per model x harness: the effort trajectory low -> medium -> high in the model's colour,
      // dash matching the marker symbol. A filtered-out effort level becomes a null gap, so the line is
      // BROKEN rather than bridging a point the user has hidden.
      for (const fw of ['vanilla-engineered','compound-realistic','metareview-realistic']) {
        const byEff = {};
        pts.forEach(c => { if (c.fw === fw) byEff[c.eff] = c; });
        if (Object.keys(byEff).length < 2) continue;     // nothing to connect
        const xs = [], ys = [];
        EFF_ORDER.forEach(e => {
          const c = byEff[e];
          if (c) { xs.push(c[xmet]); ys.push(c[ymet]); }
          else { xs.push(null); ys.push(null); }
        });
        ts.push({ x: xs, y: ys, mode: 'lines', showlegend: false, hoverinfo: 'skip',
                  line: { color: mcol[m], width: 1.3, dash: DASH[fw] } });
      }
    }
  }
  return ts;
}
// Keep the CI-inclusive scale stable when CIs or filters are toggled.
function qualityRange(metric) {
  const values = DATA.cells.flatMap(c => [c[metric], c[metric+'_hi']]).filter(Number.isFinite);
  return [0, Math.max(0.1, ...values) * 1.08];
}
const layoutFor = (xmet, ymet, annotate) => ({
  margin:{l:56,r:16,t:8,b:44}, paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
  xaxis:{title:{text:metName[xmet]}, type:'log', gridcolor:'#eee', zeroline:false},
  yaxis:{title:{text:metName[ymet]}, gridcolor:'#eee', zeroline:false,
         range: ['F2_sem','F2p_sem'].includes(ymet) ? qualityRange(ymet) : (['F1','F2','recall','adjP','F1_sem','F1p_sem','F2_sem','F2p_sem','recall_sem','adjP_sem','adjPp_sem'].includes(ymet) ? [0,1] : undefined)},
  legend:{font:{size:10}, orientation:'h', y:-0.2},
  hoverlabel:{font:{size:12}},
});
// five independent views: [chartDiv, ciCheckbox, detailsDiv, xmet, ymet, annotate]
const VIEWS = [
  ['chart1a','showci1a','details1a','cost_run','F2p_sem',false],
  ['chart1b','showci1b','details1b','wall_run','F2p_sem',false],
  ['chart1c','showci1c','details1c','usd_per_tp_sem','F2p_sem',false],
  ['chart1d','showci1d','details1d','usd_per_real','F2p_sem',false],
  ['chart1e','showci1e','details1e','tok_run','F2p_sem',false],
];
function drawView(v){
  const [div, ci, card, xm, ym, ann] = v;
  Plotly.react(div, tracesFor(xm, ym, document.getElementById(ci).checked), layoutFor(xm, ym, ann), {displayModeBar:false, responsive:true});
}
VIEWS.forEach(v => {
  drawView(v);
  document.getElementById(v[0]).on('plotly_click', ev => {
  const c = ev.points[0].customdata; const d = document.getElementById(v[2]);
  const rows = [['model', c.model],['framework', c.fw],['effort', c.eff],['n PRs', c.n||6],
    ['recall (true golden set)', c.recall_sem!=null ? fmt(c.recall_sem)+' ['+fmt(c.recall_sem_lo)+','+fmt(c.recall_sem_hi)+']' : '—'],
    ['F2\u2032 (bug quality + advisory credit)', c.F2p_sem!=null ? fmt(c.F2p_sem)+(c.F2p_sem_lo!=null?' ['+fmt(c.F2p_sem_lo)+','+fmt(c.F2p_sem_hi)+']':'') : '—'],
    ['F2 (true set, claim-soundness precision)', c.F2_sem!=null ? fmt(c.F2_sem) : '—'],
    ['F1 (true set) / F1\u2032 (legacy burden lens)', (c.F1_sem!=null ? fmt(c.F1_sem) : '—')+' / '+(c.F1p_sem!=null ? fmt(c.F1p_sem) : '—')],
    ['Observed useful advisories', (c.advisory_count ?? 0)+' · '+c.advisory_status],
    ['F2′ advisory instrument', c.advisory_instruments],
    ['Classified findings below scoring threshold', c.advisory_unresolved ?? 0],
    ['F2′ classification-sensitivity bounds (not CI; all penalties → all advisories)', c.F2p_unresolved_bounds ? c.F2p_unresolved_bounds.map(x=>fmt(x)).join(' → ') : '—'],
    ['adjP / adjP\u2032 (legacy burden lens)', c.adjP_sem!=null ? fmt(c.adjP_sem)+' / '+fmt(c.adjPp_sem) : '—'],
    ['$/true bug found', c.usd_per_tp_sem!=null ? fmtA(c.usd_per_tp_sem) : '—'],
    ['recall (benchmark)', fmt(c.recall)+' ['+fmt(c.recall_lo)+','+fmt(c.recall_hi)+']'],
    ['adjP (benchmark)', fmt(c.adjP)+' ['+fmt(c.adjP_lo)+','+fmt(c.adjP_hi)+']'],
    ['F1 (benchmark)', fmt(c.F1)+' ['+fmt(c.F1_lo)+','+fmt(c.F1_hi)+']'],
    ['F2 (benchmark)', fmt(c.F2)+' ['+fmt(c.F2_lo)+','+fmt(c.F2_hi)+']'],
    ['cost/run', fmtAB(c.cost_run, c.cost_run_lo, c.cost_run_hi)],
    ['per golden TP (benchmark)', fmtA(c.usd_per_tp)],['per campaign model-adjudicated finding (legacy; includes repeats)', fmtA(c.usd_per_real)],
    ['tokens/run', Math.round(c.tok_run).toLocaleString()],['wall s/run', Math.round(c.wall_run)],
    ['beyond-gold/PR', fmt(c.beyond_per_pr)],['Legacy bug-matching instrument', c.instruments],['Legacy bug-matching judge', c.judges],
    ['run dates', c.run_dates],['GLM pre-fix runs', c.glm_prefix==null?'—':c.glm_prefix+'/6'],
    ['no-pmu runs', c.pmu_missing||0]];
  d.innerHTML = '<h3>'+c.modelShort+' · '+c.fwShort+' · '+c.eff+'</h3><table>'+rows.map(r=>'<tr><td>'+r[0]+'</td><td>'+r[1]+'</td></tr>').join('')+'</table>'+
    '<p style="margin:8px 0 0"><a href="../COVERAGE.md">coverage & sampling</a></p>';
  });
  document.getElementById(v[1]).onchange = () => drawView(v);
});

// ---- 1f what each setup actually found (stacked: goldens + additional real bugs)
function draw6(){
  const rows = DATA.cells.filter(c=>vis(c) && DATA.exp[c.model+'|'+c.fw+'|'+c.eff])
    .map(c=>{const ex=DATA.exp[c.model+'|'+c.fw+'|'+c.eff];
             const tpSem=c.TP_sem??0, tpGold=c.TP_golden??0;
             return {k:c.modelShort+'·'+c.fwShort+'·'+c.eff, m:c.model, fw:c.fw, e:c.eff, ceiling:c.ceiling,
                     gold: tpGold, extra: Math.max(0,tpSem-tpGold), tot: tpSem,
                     rec: ex.recall_sem, ci: ex.ci_recall_sem};})
    .sort((a,b)=>b.tot-a.tot);
  const labels=rows.map(r=>r.k), yx=rows.map((r,i)=>i);
  const ts=[
    {x:rows.map(r=>r.gold), y:yx, orientation:'h', type:'bar', name:'golden bugs found', marker:{color:'#bbb'},
     customdata:rows, hovertemplate:'<b>%{customdata.k}</b><br>golden bugs: %{x}<extra></extra>'},
    {x:rows.map(r=>r.extra), y:yx, orientation:'h', type:'bar', name:'real bugs found (beyond goldens)', marker:{color:'#B07AA1'},
     customdata:rows, hovertemplate:'<b>%{customdata.k}</b><br>real bugs beyond goldens: %{x}<br>total: %{customdata.tot} · recall_sem %{customdata.rec:.3f} [%{customdata.ci[1]:.3f}, %{customdata.ci[2]:.3f}]<extra></extra>'},
    {x:rows.map(r=>r.ceiling), y:yx, mode:'markers', name:'coverage ceiling for this cell', marker:{color:'#666',symbol:'line-ns-open',size:8,line:{width:1}},
     customdata:rows, hovertemplate:'<b>%{customdata.k}</b><br>coverage ceiling (covered PRs): %{x}<extra></extra>'},
  ];
  const PERFECT = __TGDEN__; // "perfect" agent = __TGGOLD__ goldens + __TGDEF__ verified defects with archived reproduction/fix-test evidence (facetious: bounded by what the campaign found)
  const shapes=[{type:'line', xref:'x', x0:PERFECT, x1:PERFECT, yref:'y', y0:-0.5, y1:rows.length-0.5,
    line:{color:'#333', width:1.2, dash:'dash'}, layer:'below'}];
  const annotations=[{xref:'x', x:PERFECT, yref:'y', y:-0.5, text:'"perfect" agent (as far as we know): __TGGOLD__ goldens + __TGDEF__ verified defects', showarrow:false, font:{size:9}, xanchor:'right', yanchor:'bottom'}];
  Plotly.react('chart1f', ts, {shapes:shapes, annotations:annotations, barmode:'stack', margin:{l:150,r:16,t:8,b:44},
    xaxis:{title:'distinct real bugs found (of __TGGOLD__ goldens + __TGDEF__ verified defects)', gridcolor:'#eee'},
    yaxis:{tickvals:yx, ticktext:labels, tickfont:{size:9.5}, autorange:'reversed'},
    legend:{font:{size:11},orientation:'h',y:-0.06}, paper_bgcolor:'rgba(0,0,0,0)'}, {displayModeBar:false, responsive:true});
  const el=document.getElementById('takeaway1f');
  el.innerHTML='<b>Takeaway:</b> the colored segments are nearly invisible for vanilla cells — single-pass finds the goldens and little else — while harness cells (especially GLM at any effort, and fable-5.1 on metareview) pile up long colored sections: dozens of real bugs the strict benchmark never scores. This is the whole true-gold (§10d) story in one chart.';
}
draw6();

// ---- 2 effort ladder
const fwsel=document.getElementById('fwsel');
const FW_FULL = {van:'vanilla', 'CE':'Compound Engineering (ce)', 'MRV':'metareview (mrv)'};
fwsel.add(new Option('All harnesses','ALL'));
['van','CE','MRV'].forEach(f=>fwsel.add(new Option(FW_FULL[f],f)));
fwsel.value='ALL';
function draw2(){
  const sel = fwsel.value; const ts=[];
  const fws = sel==='ALL' ? ['van','CE','MRV'] : [sel];
  for (const m in mcol){
    for (const fw of fws){
      const pts = DATA.cells.filter(c=>c.fwShort===fw && c.model===m && vis(c) && c.advisory_measured).sort((a,b)=>['low','medium','high'].indexOf(a.eff)-['low','medium','high'].indexOf(b.eff));
      if(!pts.length) continue;
      ts.push({x:pts.map(c=>c.cost_run), y:pts.map(c=>(DATA.exp[c.model+'|'+c.fw+'|'+c.eff]||{}).F2p_sem ?? c.F2), mode:'lines+markers', name:m+(fws.length>1?'':''),
        line:{color:mcol[m],width:1.4, dash: sel==='ALL'&&fw==='CE'?'dot':undefined},
        marker:{color:mcol[m],symbol:msym[fw],size:7},
        customdata:pts.map(c=>({...c, fwFull: FW_FULL[c.fwShort]})),
        hovertemplate:'<b>%{customdata.modelShort} · %{customdata.fwFull} · %{customdata.eff}</b><br>$%{x:.3g} / run · F2\u2032 (bug quality + advisory credit) %{y:.3f}<br>F2′ advisory instrument: %{customdata.advisory_instruments}<br>classified findings below scoring threshold: %{customdata.advisory_unresolved}<extra></extra>',
        showlegend: sel!=='ALL' || fw==='van'});
    }
  }
  Plotly.react('chart2', ts, {margin:{l:56,r:16,t:8,b:44}, xaxis:{title:'metered $ / run (log)',type:'log',gridcolor:'#eee'}, yaxis:{title:'F2\u2032 (bug quality + advisory credit)',gridcolor:'#eee',range:qualityRange('F2p_sem')}, legend:{font:{size:11},orientation:'h',y:-0.2}, paper_bgcolor:'rgba(0,0,0,0)'}, {displayModeBar:false, responsive:true});
}
fwsel.onchange=draw2; draw2();

// ---- 3 token composition
const effsel=document.getElementById('effsel');
['low','medium','high'].forEach(e=>effsel.add(new Option(e,e)));
effsel.value='low';
const sortsel=document.getElementById('sortsel');
// keep the panel-local effort dropdown in sync with the GLOBAL effort filter: only offer efforts
// the global checkboxes leave visible, and fall back to the first visible one if the current
// selection gets hidden. draw3() then intersects: local selection AND global filter.
function refreshEffsel(){
  const cur=effsel.value;
  const avail=['low','medium','high'].filter(x=>fEffs.has(x));
  effsel.innerHTML='';
  avail.forEach(x=>effsel.add(new Option(x,x)));
  effsel.value = avail.includes(cur) ? cur : (avail[0]||'');
}
function draw3(){
  const e=effsel.value; const sort=sortsel.value;
  let keys=Object.keys(DATA.tok).filter(k=>{const t=DATA.tok[k]; return t.eff===e && fModels.has(t.model) && fFws.has(t.fw) && fEffs.has(t.eff);});
  const fwOrder={van:0, CE:1, MRV:2};
  const parse=k=>{const p=k.split('·');return {m:p[0], fw:p[1], eff:p[2]};};
  if (sort==='tokens_desc') keys.sort((a,b)=>DATA.tok[b].total-DATA.tok[a].total);
  else if (sort==='tokens_asc') keys.sort((a,b)=>DATA.tok[a].total-DATA.tok[b].total);
  else if (sort==='model_fw') keys.sort((a,b)=>{const A=parse(a),B=parse(b); return A.m.localeCompare(B.m)||fwOrder[A.fw]-fwOrder[B.fw];});
  else keys.sort((a,b)=>{const A=parse(a),B=parse(b); return fwOrder[A.fw]-fwOrder[B.fw]||A.m.localeCompare(B.m);});
  const labels=keys.map(k=>DATA.tok[k].label);
  const metadata=keys.map(k=>({model:DATA.tok[k].model, fw:DATA.tok[k].fw, eff:DATA.tok[k].eff}));
  const t=(field)=>keys.map(k=>DATA.tok[k][field]);
  Plotly.react('chart3', [
    {x:labels,y:t('fresh'),customdata:metadata,name:'fresh input',type:'bar',marker:{color:'#4C72B0'},hovertemplate:'%{x}<br>%{y:,.0f} k-tok<extra></extra>'},
    {x:labels,y:t('cached'),customdata:metadata,name:'cached read',type:'bar',marker:{color:'#55A868'},hovertemplate:'%{x}<br>%{y:,.0f} k-tok<extra></extra>'},
    {x:labels,y:t('cw'),customdata:metadata,name:'cache write',type:'bar',marker:{color:'#C44E52'},hovertemplate:'%{x}<br>%{y:,.0f} k-tok<extra></extra>'},
    {x:labels,y:t('out'),customdata:metadata,name:'output (incl. reasoning)',type:'bar',marker:{color:'#CCB974'},hovertemplate:'%{x}<br>%{y:,.0f} k-tok<extra></extra>'}],
    {barmode:'stack', margin:{l:56,r:16,t:8,b:120}, xaxis:{tickangle:-45,tickfont:{size:10},gridcolor:'#eee'}, yaxis:{title:'k-tokens / run',gridcolor:'#eee'}, legend:{font:{size:11},orientation:'h',y:-0.42}, paper_bgcolor:'rgba(0,0,0,0)'}, {displayModeBar:false, responsive:true});
}
effsel.onchange=draw3; sortsel.onchange=draw3; draw3();

// ---- 4 sample-bias check: dumbbell of the pairs (top-6 vs full-50)
const selmet=document.getElementById('selmet');
function draw4(){
  const met=selmet.value; const fk=met+'_full', tk=met+'_t6';
  const rows=DATA.sel.filter(v=>{const p=v.cell.split('|'); return fModels.has(p[0]) && fFws.has(p[1]) && fEffs.has(p[2]);})
                   .map(v=>({cell:v.cell, full:v[fk], t6:v[tk], gap:v[tk]-v[fk],
                             model:v.cell.split('|')[0], mshort:SH2[v.cell.split('|')[0]],
                             fw:v.cell.split('|')[1], eff:v.cell.split('|')[2]}))
                   .sort((a,b)=>Math.abs(b.gap)-Math.abs(a.gap));
  const labels=rows.map(r=>r.mshort+'·'+SH2[r.fw]+'·'+r.eff);
  const yx=rows.map((r,i)=>i);
  const shapes=[{type:'line', xref:'x', yref:'y', x0:0, x1:0, y0:-0.8, y1:rows.length-0.5,
    line:{color:'#999', width:1, dash:'dot'}, layer:'below'}];
  const ts=[];
  for (const m in mcol){
    const pts = rows.map((r,i)=>({...r, yi:yx[i]})).filter(r=>r.model===m);
    if(!pts.length) continue;
    ts.push({x:pts.map(r=>r.gap), y:pts.map(r=>r.yi), mode:'markers', name:m,
      marker:{color:mcol[m], symbol:pts.map(r=>msym[r.fw]), size:8, line:{width:.5,color:'#333',opacity:.4}},
      customdata:pts, hovertemplate:'<b>%{customdata.mshort}·%{customdata.fw}·%{customdata.eff}</b><br>top-6: %{customdata.t6:.2f}<br>broader run set: %{customdata.full:.2f}<br>Δ (top-six − broader run set): %{x:+.2f}<extra></extra>'});
  }
  Plotly.react('chart4', ts, {shapes:shapes, margin:{l:130,r:16,t:8,b:44},
    xaxis:{title:'Δ (top-six − broader run set), original-gold '+met, range:[-1, 1].map(sign=>sign*Math.max(0.05,...rows.map(r=>Math.abs(r.gap)*1.1))), zeroline:true, zerolinecolor:'#999', zerolinewidth:1, gridcolor:'#eee'},
    yaxis:{tickvals:yx, ticktext:labels, tickfont:{size:10}, gridcolor:'#eee', autorange:'reversed', range:[rows.length-0.5, -0.8]},
    legend:{font:{size:11},orientation:'h',y:-0.06}, paper_bgcolor:'rgba(0,0,0,0)'}, {displayModeBar:false, responsive:true});
}
selmet.onchange=draw4; draw4();
function takeaway4(met){
  const el=document.getElementById('takeaway4');
  const paired=DATA.sel.filter(r=>met==='recall' || r.cell.split('|')[1]!=='vanilla-engineered');
  const gaps=paired.map(r=>r[met+'_t6']-r[met+'_full']);
  const group=met==='recall' ? 'all paired cells' : 'paired harness cells (CE and MRV only)';
  const mean=gaps.reduce((sum,gap)=>sum+gap,0)/gaps.length;
  el.innerHTML='<b>Takeaway (original-gold '+met+'):</b> the mean top-six minus broader-run-set gap across '+gaps.length+' '+group+' is '+(mean>=0?'+':'')+mean.toFixed(3)+'. This is a descriptive within-benchmark comparison; it does not establish generalization of the six-PR true-gold rankings.';
}
takeaway4(selmet.value);
selmet.addEventListener('change',()=>takeaway4(selmet.value));

// ---- 5 selection view (per PR): severity weight vs recall, top-6 in bold color
const cellsel=document.getElementById('cellsel');
function refreshCellsel(){
  const cur=cellsel.value;
  cellsel.innerHTML='';
  Object.keys(DATA.percell).filter(k=>{const t=DATA.percell[k]; return fModels.has(t.model) && fFws.has(t.fw) && fEffs.has(t.eff);}).sort().forEach(c=>cellsel.add(new Option(c,c)));
  cellsel.value = Object.keys(DATA.percell).includes(cur) && fModels.has(DATA.percell[cur].model) && fFws.has(DATA.percell[cur].fw) && fEffs.has(DATA.percell[cur].eff) ? cur : (cellsel.options[0] ? cellsel.options[0].value : '');
}
refreshCellsel();
function draw5(){
  const c=cellsel.value; if(!c) return; const cell=DATA.percell[c];
  const pts=cell.prs.map(p=>({...p, model:cell.model, fw:cell.fw, eff:cell.eff}));
  const top6=pts.filter(p=>p.top6), rest=pts.filter(p=>!p.top6);
  const mrest=rest.filter(p=>p.rec!=null).reduce((a,p)=>a+p.rec,0)/rest.filter(p=>p.rec!=null).length;
  const mtop=top6.filter(p=>p.rec!=null).reduce((a,p)=>a+p.rec,0)/top6.filter(p=>p.rec!=null).length;
  const ts=[
    {x:rest.map(p=>p.sev), y:rest.map(p=>p.rec), mode:'markers', name:'other covered PRs',
     marker:{color:'#bbb',size:7}, customdata:rest, hovertemplate:'<b>PR %{customdata.pr}</b><br>sev %{x} · original-gold recall %{y:.3f}<extra>not selected</extra>'},
    {x:top6.map(p=>p.sev), y:top6.map(p=>p.rec), mode:'markers', name:'top-6 selected PRs',
     marker:{color:'#B07AA1',size:11,line:{width:1.5,color:'#333'}}, customdata:top6, hovertemplate:'<b>PR %{customdata.pr}</b><br>sev %{x} · original-gold recall %{y:.3f}<extra>top-6</extra>'},
    {x:[0,26],y:[mrest,mrest],mode:'lines',name:'mean original-gold recall, other covered PRs',line:{color:'#999',dash:'dash',width:1},hoverinfo:'skip'},
    {x:[0,26],y:[mtop,mtop],mode:'lines',name:'mean original-gold recall, top-6',line:{color:'#B07AA1',dash:'dash',width:1.5},hoverinfo:'skip'},
  ];
  Plotly.react('chart5', ts, {margin:{l:56,r:16,t:8,b:44}, xaxis:{title:'golden-comment severity weight (Critical=4 … Low=1)',gridcolor:'#eee'}, yaxis:{title:'per-PR original-gold recall',gridcolor:'#eee'}, legend:{font:{size:11},orientation:'h',y:-0.2}, paper_bgcolor:'rgba(0,0,0,0)'}, {displayModeBar:false, responsive:true});
}
cellsel.onchange=draw5; draw5();
</script>
</body>
</html>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",", ":")).replace("</", "<\\/")) \
          .replace("__MCOL__", json.dumps(MCOL)) \
          .replace("__MSYM__", json.dumps(SYM)) \
          .replace("__SH2__", json.dumps(SH)) \
          .replace("__TGDEN__", str(TG_DEN)) \
          .replace("__TGGOLD__", str(TG_GOLDENS)) \
          .replace("__TGDEF__", str(TG_DEFECTS)) \
          .replace("__FRAMEWORK_SUMMARY__", framework_summary)
path = f"{ROOT}/analysis/figures/interactive_dashboard.html"
open(path, "w").write(out)
print("wrote", path, len(out), "bytes")
