#!/usr/bin/env python3
"""Render sdlc-report.html: the short, developer-facing edition of the report.

REPORT.html is the complete scientific record. This page is the practitioner's cut: three findings,
three charts, what to do next, and what the data does not prove, each pointing back to the REPORT.html
section that carries the full method.

Two rules keep the page honest:

1. **No typed numbers.** Every figure in the page's prose is a ``{{fact}}`` placeholder filled from
   analysis/final_report_metrics.json. The template (tools/sdlc_report_template.html) contains no
   numerals in its visible text; tests/test_sdlc_report.py enforces that.
2. **Claim guards.** The prose also makes qualitative claims ("four of the top five scores are
   open-weight"). ``check_guards`` re-derives each one from the data and refuses to render if a
   future data revision makes the sentence false, so the wording must be revisited, not just the digits.

Output is deterministic (no timestamps), so the page is byte-reproducible from the frozen metrics.

Usage: .venv/bin/python tools/sdlc_report_html.py
"""
from __future__ import annotations

import ast
import html
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qr  # noqa: E402  (tools/qr.py: dependency-free QR encoder for the share images)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = f"{ROOT}/analysis/final_report_metrics.json"
DATASET = f"{ROOT}/analysis/final_report_dataset.json"
TEMPLATE = f"{ROOT}/tools/sdlc_report_template.html"
ONESHOT_SOURCE = "harnesseval/adapters/vanilla.py"  # the prompt REPORT.md §2.2 prints; the page links there
OUT = f"{ROOT}/sdlc-report.html"

# Where the page will be served from. Used only for share links and Open Graph tags.
PUBLIC_BASE = "https://dsifry.github.io/harnesseval/"
PAGE_NAME = ""  # published as the site index (tools/publish_site.sh), so links point at the root
OG_IMAGE = "analysis/figures/dash_chart1a.png"

VAN, CE, MRV = "vanilla-engineered", "compound-realistic", "metareview-realistic"
FW_SHORT = {VAN: "one-shot", CE: "CE", MRV: "MRV"}
FW_LONG = {VAN: "one-shot", CE: "Compound Engineering", MRV: "metareview"}
FW_URL = {CE: "https://github.com/EveryInc/compound-engineering-plugin", MRV: "https://github.com/dsifry/metareview"}
FW_PROSE = {VAN: "as a one-shot prompt", CE: "running Compound Engineering", MRV: "running metareview"}
EFFORTS = ["low", "medium", "high"]
MODEL_NAME = {
    "claude-fable-5-1": "Fable", "claude-opus-5": "Opus", "claude-sonnet-5": "Sonnet",
    "gpt-6-astra": "Astra", "gpt-5.6-sol": "Sol", "gpt-5.6-terra": "Terra",
    "glm-5.3-vision-background": "GLM vision", "glm-5.3-flash-background": "GLM flash",
}
MODEL_FULL = {
    "claude-fable-5-1": "Fable 5.1", "claude-opus-5": "Opus 5", "claude-sonnet-5": "Sonnet 5",
    "gpt-6-astra": "GPT-6 Astra", "gpt-5.6-sol": "GPT-5.6 Sol", "gpt-5.6-terra": "GPT-5.6 Terra",
    "glm-5.3-vision-background": "GLM-5.3", "glm-5.3-flash-background": "GLM-5.3-Flash",
}
VENDOR = {"claude": "Anthropic", "gpt": "OpenAI", "glm": "Z.ai"}
OPEN_WEIGHT = {"glm-5.3-vision-background", "glm-5.3-flash-background"}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
         9: "nine", 10: "ten"}

SHARE_IDS = ["f-harness", "f-cost", "f-effort", "c-harness", "c-money", "c-effort", "c-explore"]
PILOT = f"glm-5.3-vision-background|{MRV}|low"
PILOT_CHEAP = f"glm-5.3-flash-background|{MRV}|low"
CLOSED_SAME_HARNESS = f"claude-opus-5|{MRV}|low"
CE_PILOT = f"glm-5.3-flash-background|{CE}|low"  # the Compound Engineering pick for the next-steps list


class ClaimGuardError(AssertionError):
    """A sentence in the template is no longer true of the data."""


def word(n: int) -> str:
    return WORDS.get(int(n), str(int(n)))


def money(x: float) -> str:
    return f"${x:.3f}" if x < 0.1 else f"${x:.2f}"


def one_over(r: float) -> str:
    """0.0745 -> '1/13'."""
    return f"1/{round(1 / r)}"


def duration(secs: float) -> str:
    """95 -> '95 seconds', 188 -> '3.1 minutes', 2282 -> '38 minutes'."""
    if secs < 120:
        return f"{round(secs)} seconds"
    return f"{secs / 60:.1f} minutes" if secs < 600 else f"{round(secs / 60)} minutes"


def oneshot_prompt() -> tuple[str, int]:
    """The engineered one-shot prompt, read from the adapter source (not imported, not retyped), and its line."""
    tree = ast.parse(open(f"{ROOT}/{ONESHOT_SOURCE}", encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "ENGINEERED_PROMPT":
            return ast.literal_eval(node.value), node.lineno
    raise ClaimGuardError(f"ENGINEERED_PROMPT not found in {ONESHOT_SOURCE}")


def signed(x: float) -> str:
    """0.09 -> '+0.09', -0.072 -> '−0.07' (true minus sign)."""
    return f"{x:+.2f}".replace("-", "−")


def signed3(x: float) -> str:
    return f"{x:+.3f}".replace("-", "−")


def cell_label(key: str) -> str:
    """The shorthand REPORT.md uses ('Opus · CE · medium'). Kept for cross-checks; the page spells names out."""
    m, f, e = key.split("|")
    return f"{MODEL_NAME[m]} · {FW_SHORT[f]} · {e}"


def chart_label(key: str) -> str:
    """For marks inside a chart whose legend spells out CE and MRV: 'Opus 5 · CE · medium'."""
    m, f, e = key.split("|")
    return f"{MODEL_FULL[m]} · {FW_SHORT[f]} · {e}"


def long_label(key: str) -> str:
    """For tables, tooltips and captions, where no legend is in sight: 'Opus 5 · Compound Engineering · medium'."""
    m, f, e = key.split("|")
    return f"{MODEL_FULL[m]} · {FW_LONG[f]} · {e}"


def fw_url(key: str) -> str:
    """The repo of the harness a configuration ran. A one-shot prompt has none; check_guards rejects a pick without one."""
    return FW_URL.get(key.split("|")[1], "")


def prose_label(key: str) -> str:
    """For sentences: 'Opus 5 running Compound Engineering at medium effort'."""
    m, f, e = key.split("|")
    return f"{MODEL_FULL[m]} {FW_PROSE[f]} at {e} effort"


def compute(M: dict, D: dict) -> tuple[dict, dict, dict]:
    """Return (facts, data, guards): prose strings, chart rows, and the inputs to check_guards."""
    tg = M["true_gold_defects"]["verified"]
    cells, matrix = tg["cells"], M["matrix"]
    der, head = tg["derived"], tg["headline"]
    full = {k: c for k, c in cells.items() if c.get("n_pr") == max(c2.get("n_pr", 0) for c2 in cells.values())}

    rows = []
    for k in sorted(full):
        c, x = full[k], matrix[k]
        m, f, e = k.split("|")
        rows.append({
            "key": k, "label": chart_label(k), "long": long_label(k), "model": MODEL_FULL[m], "vendor": VENDOR[m.split("-")[0]], "model_id": m, "fw": FW_SHORT[f],
            "effort": e, "open": m in OPEN_WEIGHT, "bugs": int(c["TP"]), "score": round(c["F2p"], 3),
            "score_lo": round(c["ci"]["F2p"][1], 3), "score_hi": round(c["ci"]["F2p"][2], 3),
            "advice": int(c["advisory_count"]), "unsupported": int(c["penalty_count"]),
            "cost": round(x["cost_run"], 4), "secs": round(x["wall_run"]), "tokens": round(x["tok_run"]),
        })
    by_key = {r["key"]: r for r in rows}

    # ---- finding 1: harness vs one-shot, same model and effort --------------------------------
    hv = der["harness_vs_vanilla"]
    ratios, exceptions = {}, []
    for r in rows:
        if r["fw"] == "one-shot":
            continue
        m, f, e = r["key"].split("|")
        base = by_key.get(f"{m}|{VAN}|{e}")
        if base:
            ratios[r["key"]] = r["bugs"] / base["bugs"]
            if r["bugs"] <= base["bugs"]:
                exceptions.append(r["key"])
    models = []
    for m in MODEL_NAME:
        per = {f: [by_key[f"{m}|{f}|{e}"]["bugs"] for e in EFFORTS if f"{m}|{f}|{e}" in by_key]
               for f in (VAN, CE, MRV)}
        if all(len(v) == len(EFFORTS) for v in per.values()):
            mean = {f: statistics.mean(v) for f, v in per.items()}
            models.append({"model": MODEL_FULL[m], "open": m in OPEN_WEIGHT,
                           "oneshot": round(mean[VAN], 1), "ce": round(mean[CE], 1),
                           "mrv": round(mean[MRV], 1),
                           "ratio": round((mean[CE] + mean[MRV]) / 2 / mean[VAN], 2)})
    models.sort(key=lambda r: -(r["ce"] + r["mrv"]))
    tok = statistics.median(v["tok_ratio"][0] for v in M["token_multiple"].values())
    cost_mult = statistics.median(v["cost_ratio"][0] for v in M["token_multiple"].values())
    one_shot = [r for r in rows if r["fw"] == "one-shot"]
    harness = [r for r in rows if r["fw"] != "one-shot"]

    # ---- finding 2: open-weight + harness vs closed + harness ---------------------------------
    ranked = sorted(rows, key=lambda r: -r["score"])
    top, pilot, cheap, closed = ranked[0], by_key[PILOT], by_key[PILOT_CHEAP], by_key[CLOSED_SAME_HARNESS]
    best_oneshot = by_key[head["vanilla"]["best_f2p"]["cell"]]
    top_n = 5  # rank six is a tie at three decimals (GLM vision vs Opus, both MRV low), so stop above it
    n_open_top = sum(r["open"] for r in ranked[:top_n])
    closed_h = [r for r in harness if not r["open"]]
    closed_above = [r for r in closed_h if r["score"] > pilot["score"]]
    runner = max((r for r in closed_h if r["model_id"] != top["model_id"]), key=lambda r: r["score"])
    # the strongest harness model from each closed vendor, among models whose harness grid was completed
    best_by_vendor = {}
    for r in closed_h:
        v = VENDOR[r["model_id"].split("-")[0]]
        if v not in best_by_vendor or r["score"] > best_by_vendor[v]["score"]:
            best_by_vendor[v] = r
    # the answer box: open-weight harness runs against closed one-shot prompts, and who leads the leaderboard
    open_h = [r for r in harness if r["open"]]
    closed_oneshot = [r for r in one_shot if not r["open"]]
    by_bugs = sorted(rows, key=lambda r: (-r["bugs"], -r["score"]))  # the leaderboard's default order
    harness_lead = min(next(i for i, r in enumerate(order) if r["fw"] == "one-shot") for order in (by_bugs, ranked))
    ce_pilot = by_key[CE_PILOT]
    csr = M["cost_structure_ratios"][
        f"glm-5.3-flash-background|{MRV}|low vs claude-fable-5-1|{VAN}|low"]

    # ---- finding 3: effort ladder (42-golden benchmark lens, high vs medium, paired) -----------
    effort = []
    for k, v in M["effort_ladder"].items():
        m, f = k.split("|")
        pt, lo, hi = v["delta"]["F1"]
        verdict = "better" if lo > 0 else "worse" if hi < 0 else "unresolved"
        effort.append({"model_id": m, "fw": FW_SHORT[f], "label": f"{MODEL_FULL[m]} · {FW_SHORT[f]}",
                       "long": f"{MODEL_FULL[m]} · {FW_LONG[f]}", "prose": f"{MODEL_FULL[m]} {FW_PROSE[f]}", "d": round(pt, 3), "lo": round(lo, 3),
                       "hi": round(hi, 3), "cost": round(v["cost_ratio"][0], 2), "verdict": verdict})
    effort.sort(key=lambda r: -r["d"])
    n_eff = {v: sum(r["verdict"] == v for r in effort) for v in ("better", "worse", "unresolved")}
    lo_hi = [(by_key[f"{m}|{f}|low"], by_key[f"{m}|{f}|high"]) for m in MODEL_NAME for f in (VAN, CE, MRV)
             if f"{m}|{f}|low" in by_key and f"{m}|{f}|high" in by_key]

    # wall-clock: harness vs one-shot, and what effort does to it within a model x harness
    wall_mult = statistics.median(r["secs"] / by_key[f"{r['model_id']}|{VAN}|{r['effort']}"]["secs"] for r in harness
                                  if f"{r['model_id']}|{VAN}|{r['effort']}" in by_key)
    ladders = {}
    for r in harness:
        ladders.setdefault((r["model_id"], r["fw"]), {})[r["effort"]] = r
    ladders = [v for v in ladders.values() if len(v) == len(EFFORTS)]
    low_fastest = sum(min(v, key=lambda e: v[e]["secs"]) == "low" for v in ladders)
    low_best_value = sum(min(v, key=lambda e: v[e]["cost"] / v[e]["bugs"]) == "low" for v in ladders)
    pm, fw_p = PILOT.split("|")[0], PILOT.split("|")[1]
    cm = CLOSED_SAME_HARNESS.split("|")[0]
    slow = {e: (by_key[f"{pm}|{fw_p}|{e}"]["secs"], by_key[f"{cm}|{fw_p}|{e}"]["secs"]) for e in ("medium", "high")}

    # the clearest gain, and the largest gain this sample could not resolve
    eff_best = effort[0]
    eff_ex = next((r for r in effort if r["verdict"] == "unresolved"), effort[-1])  # guards reject the fallback
    eb = {f: by_key.get(f"{eff_best['model_id']}|{f}|{e}", {}).get("bugs", 0) for f, e in ((VAN, "high"), (CE, "low"), (MRV, "low"))}

    # efficiency frontier: the best score available at or below each price
    frontier, best = [], -1.0
    for r in sorted(rows, key=lambda r: (r["cost"], -r["score"])):
        if r["score"] > best:
            frontier.append(r)
            best = r["score"]
    cheap_floor = cheap["bugs"] // 10 * 10

    # the wider campaign, and the check that the six-PR slice is not misleading (benchmark labels only)
    sel = {k: v for k, v in M["selection_effect"].items() if v["n_full"] >= 40}
    sel_recall_gap = statistics.mean(v["recall_t6"] - v["recall_full"] for v in sel.values())
    sel_f1_gap = statistics.mean(v["F1_t6"] - v["F1_full"] for k, v in sel.items() if VAN not in k)
    sel_adjp_gap = statistics.mean(v["adjP_t6"] - v["adjP_full"] for k, v in sel.items() if VAN not in k)
    pilot_sel = M["selection_effect"][PILOT]
    rank = M["rank_agreement"]
    rank_high = sum(v["spearman"] >= 0.8 - 1e-9 for v in rank.values())
    all_repos = {u.split("/pull/")[0].rsplit("/", 1)[-1].split("-")[0] for u in D["pr_golden"]}

    cov = der["coverage"]
    repos = {p["url"].split("/pull/")[0] for c in full.values() for p in c["per_pr"]}
    n_pr = next(iter(full.values()))["n_pr"]

    facts = {
        # scope
        "n_prs": word(n_pr), "n_prs_cap": word(n_pr).capitalize(), "n_codebases": word(len(repos)),
        "n_models": word(len(MODEL_NAME)), "n_models_cap": word(len(MODEL_NAME)).capitalize(), "n_models_num": str(len(MODEL_NAME)),
        "n_ways": word(len(FW_SHORT)), "n_ways_num": str(len(FW_SHORT)),
        "n_efforts": word(len(EFFORTS)), "n_efforts_num": str(len(EFFORTS)),
        "n_cells": str(len(rows)), "n_cells_total": str(len(cells)),
        "gold_total": str(cov["den"]), "gold_benchmark": str(cov["goldens_den"]),
        "gold_hidden": str(cov["defects_den"]),
        "union_found": str(cov["all_cells"]), "union_missed": word(cov["unfound_total"]),
        # finding 1
        "hv_pos": str(hv["n_positive_recall"]), "hv_pairs": str(hv["n_pairs"]),
        "hv_exceptions": word(len(exceptions)),
        "hv_exception_names": ", ".join(sorted({prose_label(k).rsplit(" at ", 1)[0] for k in exceptions})),
        "hv_ratio": f"{statistics.median(ratios.values()):.1f}",
        "hv_recall_pts": f"{hv['mean_dRecall'] * 100:.1f}",
        "pilot_ratio": f"{ratios[PILOT]:.1f}", "cheap_ratio": f"{ratios[PILOT_CHEAP]:.1f}",
        "pilot_base_bugs": str(by_key[f'glm-5.3-vision-background|{VAN}|low']["bugs"]),
        "cheap_base_bugs": str(by_key[f'glm-5.3-flash-background|{VAN}|low']["bugs"]),
        "best_bugs": str(top["bugs"]), "best_oneshot_bugs": str(best_oneshot["bugs"]),
        "best_oneshot_label": best_oneshot["long"], "best_oneshot_score": f"{best_oneshot['score']:.3f}",
        "tok_mult": f"{tok:.0f}", "cost_mult": f"{cost_mult:.0f}",
        "unsup_oneshot": f"{statistics.median(r['unsupported'] for r in one_shot):g}",
        "unsup_harness": f"{statistics.median(r['unsupported'] for r in harness):g}",
        "advice_oneshot": f"{statistics.median(r['advice'] for r in one_shot):g}",
        "advice_harness": f"{statistics.median(r['advice'] for r in harness):g}",
        # finding 2
        "top_label": top["long"], "top_prose": prose_label(top["key"]), "top_score": f"{top['score']:.3f}", "top_cost": money(top["cost"]),
        "pilot_label": pilot["long"], "pilot_prose": prose_label(pilot["key"]), "pilot_score": f"{pilot['score']:.3f}",
        "pilot_cost": money(pilot["cost"]), "pilot_bugs": str(pilot["bugs"]), "pilot_secs": str(pilot["secs"]),
        "pilot_unsup": str(pilot["unsupported"]),
        "cheap_label": cheap["long"], "cheap_prose": prose_label(cheap["key"]), "cheap_score": f"{cheap['score']:.3f}",
        "cheap_cost": money(cheap["cost"]), "cheap_bugs": str(cheap["bugs"]), "cheap_secs": str(cheap["secs"]),
        "cheap_unsup": str(cheap["unsupported"]),
        "closed_label": closed["long"], "closed_prose": prose_label(closed["key"]), "closed_score": f"{closed['score']:.3f}",
        "closed_cost": money(closed["cost"]), "closed_bugs": str(closed["bugs"]),
        "pilot_vs_closed": one_over(pilot["cost"] / closed["cost"]),
        "pilot_vs_top": one_over(pilot["cost"] / top["cost"]),
        "top_vs_pilot_x": f"{top['cost'] / pilot['cost']:.0f}",
        "n_open_h": str(len(open_h)), "open_h_min_score": f"{min(r['score'] for r in open_h):.3f}",
        "open_h_min_bugs": str(min(r["bugs"] for r in open_h)),
        "closed_oneshot_best_score": f"{max(r['score'] for r in closed_oneshot):.3f}",
        "closed_oneshot_best_bugs": str(max(r["bugs"] for r in closed_oneshot)),
        "harness_lead": str(harness_lead), "top_dur": duration(top["secs"]),
        "ce_pilot_model_full": MODEL_FULL[ce_pilot["model_id"]], "ce_pilot_effort": ce_pilot["effort"],
        "ce_pilot_bugs": str(ce_pilot["bugs"]), "ce_pilot_cost": money(ce_pilot["cost"]),
        "ce_pilot_dur": duration(ce_pilot["secs"]), "ce_pilot_unsup": str(ce_pilot["unsupported"]),
        "n_open_top": word(n_open_top), "n_open_top_cap": word(n_open_top).capitalize(), "top_n": word(top_n),
        "ptok_pct": f"{csr['ptok_ratio'][0] * 100:.1f}%", "ptask_pct": f"{csr['costtask_ratio'][0] * 100:.1f}%",
        # finding 3
        "eff_pairs": str(len(effort)), "eff_unresolved": str(n_eff["unresolved"]),
        "eff_better": word(n_eff["better"]), "eff_worse": word(n_eff["worse"]),
        "eff_cost_lo": f"{min(r['cost'] for r in effort):.2f}", "eff_cost_hi": f"{max(r['cost'] for r in effort):.1f}",
        "eff_lohi_pairs": str(len(lo_hi)),
        "eff_lohi_more_bugs": f"{statistics.mean(h['bugs'] - l['bugs'] for l, h in lo_hi):.0f}",
        "eff_unsup_down": str(sum(h["unsupported"] < l["unsupported"] for l, h in lo_hi)),
        "eff_unsup_up": str(sum(h["unsupported"] > l["unsupported"] for l, h in lo_hi)),
        "eff_cost_more": str(sum(r["cost"] > 1 for r in effort)),
        "eff_ex_label": eff_ex["prose"], "eff_ex_d": signed(eff_ex["d"]), "eff_ex_lo": signed(eff_ex["lo"]),
        "eff_ex_hi": signed(eff_ex["hi"]),
        "eff_best_label": eff_best["prose"], "eff_best_model": MODEL_FULL[eff_best["model_id"]],
        "eff_best_d": signed(eff_best["d"]), "eff_best_lo": signed(eff_best["lo"]), "eff_best_hi": signed(eff_best["hi"]),
        "eff_best_high_bugs": str(eb[VAN]), "eff_best_ce_low_bugs": str(eb[CE]), "eff_best_mrv_low_bugs": str(eb[MRV]),
        "cheap_floor": str(cheap_floor), "top_vs_cheap": f"1/{round(top['cost'] / cheap['cost'], -1):.0f}",
        "top_unsup": str(top["unsupported"]),
        "n_runs": f"{len(D['all_healthy_runs']):,}", "n_bench_prs": str(len(D["pr_golden"])),
        "n_bench_codebases": word(len(all_repos)),
        "pilot_f1_six": f"{pilot_sel['F1_t6']:.2f}", "pilot_f1_full": f"{pilot_sel['F1_full']:.2f}",
        "rank_groups": word(len(rank)), "rank_high": word(rank_high),
        "sel_cells": str(len(sel)), "sel_recall_gap": signed3(sel_recall_gap), "sel_f1_gap": signed(sel_f1_gap), "sel_f1_gap_abs": f"{abs(sel_f1_gap):.2f}",
        "n_closed_h": str(len(closed_h)), "n_closed_above": word(len(closed_above)),
        "ptok_ref_model_full": MODEL_FULL["claude-fable-5-1"],
        "pilot_model_full": MODEL_FULL[pm], "cheap_model_full": MODEL_FULL[cheap["model_id"]],
        "pilot_effort": pilot["effort"], "top_effort": top["effort"], "cheap_effort": cheap["effort"],
        "pilot_fw_long": FW_LONG[pilot["key"].split("|")[1]], "top_fw_long": FW_LONG[top["key"].split("|")[1]],
        "cheap_fw_long": FW_LONG[cheap["key"].split("|")[1]],
        # each pick's harness name and repo link are read off that pick's own key, never typed beside it
        "pilot_fw_url": fw_url(pilot["key"]), "top_fw_url": fw_url(top["key"]), "cheap_fw_url": fw_url(cheap["key"]),
        "closed_model_full": MODEL_FULL[closed["model_id"]], "runner_model_full": MODEL_FULL[runner["model_id"]],
        "closed_vendor": VENDOR[closed["model_id"].split("-")[0]], "runner_vendor": VENDOR[runner["model_id"].split("-")[0]],
        "runner_model": runner["model"], "runner_label": runner["long"], "runner_prose": prose_label(runner["key"]), "runner_score": f"{runner['score']:.3f}",
        "runner_cost": money(runner["cost"]),
        "top_model_full": MODEL_FULL[top["model_id"]],
        "wall_mult": f"{wall_mult:.1f}",
        "wall_harness_low": duration(statistics.median(r["secs"] for r in harness if r["effort"] == "low")),
        "wall_oneshot_low": duration(statistics.median(r["secs"] for r in one_shot if r["effort"] == "low")),
        "n_ladders": str(len(ladders)), "low_fastest": str(low_fastest), "low_best_value": str(low_best_value),
        "pilot_dur": duration(pilot["secs"]), "closed_dur": duration(closed["secs"]), "cheap_dur": duration(cheap["secs"]),
        "pilot_family": f"{MODEL_FULL[pm]} · {FW_LONG[fw_p]}", "closed_model": MODEL_FULL[cm],
        "pilot_med_dur": duration(slow["medium"][0]), "pilot_high_dur": duration(slow["high"][0]),
        "closed_med_dur": duration(slow["medium"][1]), "closed_high_dur": duration(slow["high"][1]),
        # plumbing
        "page_url": PUBLIC_BASE + PAGE_NAME, "report_url": PUBLIC_BASE + "REPORT.html",
        "pilot_vendor": VENDOR[pm.split("-")[0]], "og_image": PUBLIC_BASE + OG_IMAGE,
        "price_date": M["price_retrieved"] if isinstance(M["price_retrieved"], str) else "",
    }
    data = {"cells": rows, "models": models, "effort": effort, "gold_total": cov["den"],
            "labelled": [top["key"], pilot["key"], cheap["key"], best_oneshot["key"]],
            "model_order": list(MODEL_NAME), "frontier": [r["key"] for r in frontier],
            "compare": [top["key"], closed["key"], pilot["key"], cheap["key"], best_oneshot["key"]],
            # a scannable link for each share image; the explorer's is its section link (the pinned set varies)
            "qr": {sid: qr.as_strings(qr.encode(f"{PUBLIC_BASE}{PAGE_NAME}#{sid}")) for sid in SHARE_IDS},
            "page_url": facts["page_url"]}
    guards = {"ranked": ranked, "top": top, "pilot": pilot, "closed": closed, "cheap": cheap,
              "frontier": frontier, "open_h": open_h, "closed_oneshot": closed_oneshot, "harness_lead": harness_lead, "lead_fws": {r["fw"] for r in by_bugs[:harness_lead]} | {r["fw"] for r in ranked[:harness_lead]}, "ce_pilot": ce_pilot, "harness": harness, "cheap_floor": cheap_floor, "rows": rows, "eff_best": eff_best, "eb": eb,
              "best_by_vendor": best_by_vendor, "closed_h": closed_h, "closed_above": closed_above, "runner": runner, "low_fastest": low_fastest, "low_best_value": low_best_value, "n_ladders": len(ladders), "slow": slow,
              "sel_adjp_gap": sel_adjp_gap, "pilot_sel": pilot_sel, "sel_recall_gap": sel_recall_gap, "sel_f1_gap": sel_f1_gap, "top_n": top_n, "exceptions": exceptions, "ratios": ratios, "n_eff": n_eff, "effort": effort}
    return facts, data, guards


def check_guards(g: dict) -> None:
    """Each check names the template sentence it protects."""
    def need(ok: bool, sentence: str) -> None:
        if not ok:
            raise ClaimGuardError(f"template claim no longer holds: {sentence}")

    fw_of = lambda key: key.split("|")[1]
    need(all(fw_of(g[n]["key"]) in FW_URL for n in ("top", "pilot", "cheap", "ce_pilot")),
         "'every pick is a harness run, so its tile can link to that harness'")
    need(fw_of(PILOT) == fw_of(PILOT_CHEAP) == fw_of(CLOSED_SAME_HARNESS) == MRV and fw_of(CE_PILOT) == CE,
         "the template's prose says 'running metareview' for the pilot, budget and same-harness picks, and "
         "'running Compound Engineering' for the CE pick: change the template if these constants change")

    need(not g["top"]["open"] and g["top"]["fw"] != "one-shot",
         "'the single highest score belongs to a closed model in a harness'")
    need(all(r["open"] and r["fw"] != "one-shot" for r in g["ranked"][1:g["top_n"]]),
         "'every other score in the top group is an open-weight model in a harness'")
    need(g["ranked"][g["top_n"] - 1]["score"] - g["ranked"][g["top_n"]]["score"] > 0.005,
         "'top group' boundary is not a rounding tie")
    need(abs(g["pilot"]["score"] - g["closed"]["score"]) < 0.005,
         "'open-weight + harness matched Opus in the same harness (same score)'")
    need(g["closed_above"] == [g["top"]], "'only one closed-model harness configuration scored higher'")
    need(all(r["cost"] > g["pilot"]["cost"] for r in g["closed_h"]), "'and none cost less'")
    need({v: r["model_id"] for v, r in g["best_by_vendor"].items()}
         == {"Anthropic": g["closed"]["model_id"], "OpenAI": g["runner"]["model_id"]},
         "'the two named models were the strongest Anthropic and OpenAI models in a harness'")
    need(g["runner"]["score"] < g["pilot"]["score"] and g["runner"]["cost"] > g["pilot"]["cost"],
         "'the next-best closed model scored lower and cost more'")
    need(g["pilot"]["cost"] < g["closed"]["cost"] / 10, "'at less than a tenth of the cost'")
    need(min(g["ratios"][PILOT], g["ratios"][PILOT_CHEAP]) > 2,
         "'more than double on the open-weight models'")
    need(len({k.split("|")[0] + k.split("|")[1] for k in g["exceptions"]}) <= 1,
         "'the exceptions were all one model in one harness'")
    need(g["frontier"][-1] is g["top"] and all(r["open"] for r in g["frontier"][:-1]),
         "'every configuration on the frontier except the most expensive is an open-weight model'")
    need(min((r for r in g["rows"] if r["bugs"] >= g["cheap_floor"]), key=lambda r: r["cost"]) is g["cheap"],
         "'the cheapest configuration to find that many bugs'")
    need(g["pilot"]["unsupported"] < g["cheap"]["unsupported"], "'with fewer unsupported findings'")
    need(g["pilot"] in g["frontier"] and g["cheap"] in g["frontier"],
         "'best value' and 'tightest budget': both picks sit on the efficiency frontier")
    need(min(r["score"] for r in g["open_h"]) > max(r["score"] for r in g["closed_oneshot"])
         and min(r["bugs"] for r in g["open_h"]) > max(r["bugs"] for r in g["closed_oneshot"]),
         "'every open-weight harness configuration beat every closed-model one-shot prompt, on score and on bugs'")
    need(min(g["harness"], key=lambda r: r["cost"]) is g["ce_pilot"] and min(g["harness"], key=lambda r: r["secs"]) is g["ce_pilot"]
         and g["top"]["fw"] == "CE",
         "'the Compound Engineering pick was the cheapest and fastest harness configuration, and Compound Engineering holds the top score'")
    need(g["lead_fws"] == {"CE", "MRV"}, "'the leading harness runs are a mix of both harnesses, either metareview or Compound Engineering'")
    need(g["harness_lead"] >= 10, "'the top of the leaderboard is all harness runs'")
    need(g["eff_best"]["verdict"] == "better" and g["eff_best"]["fw"] == "one-shot"
         and min(g["eb"][CE], g["eb"][MRV]) > g["eb"][VAN] > 0,
         "'the clearest gain was a one-shot prompt, and either harness at low effort still found more bugs'")
    need(sum(r["cost"] > 1 for r in g["effort"]) > len(g["effort"]) * 0.8, "'high effort reliably cost more'")
    need(g["low_fastest"] >= 0.9 * g["n_ladders"] and g["low_best_value"] > g["n_ladders"] / 2,
         "'low effort gave harnesses the best price/performance and was the fastest setting'")
    need(g["slow"]["medium"][0] > 5 * g["slow"]["medium"][1] and g["slow"]["high"][0] > 5 * g["slow"]["high"][1],
         "'above low effort the open-weight model is far slower than the closed model in the same harness'")
    need(abs(g["sel_recall_gap"]) < 0.02 and g["sel_f1_gap"] > 0.03,
         "'recall on the six matches the full benchmark closely, while harness F1 runs higher on the six'")
    need(g["sel_adjp_gap"] > 0 and g["pilot_sel"]["n_full"] >= 40 and g["pilot_sel"]["F1_t6"] > g["pilot_sel"]["F1_full"],
         "'harnesses were noisier on the rest of the benchmark, so their scores on the six run high'")
    need(g["n_eff"]["unresolved"] > len(g["effort"]) * 0.7,
         "'in most comparisons, high effort bought no measurable gain over medium'")


def render(template: str, facts: dict, data: dict) -> str:
    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name == "DATA_JSON":
            return json.dumps(data, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")
        if name not in facts:
            raise KeyError(f"template uses unknown fact {{{{{name}}}}}")
        return html.escape(facts[name], quote=True)

    return re.sub(r"\{\{(\w+)\}\}", sub, template)


def main() -> None:
    M, D = json.load(open(METRICS)), json.load(open(DATASET))
    facts, data, guards = compute(M, D)
    check_guards(guards)
    page = render(open(TEMPLATE, encoding="utf-8").read(), facts, data)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(page):,} bytes, {len(facts)} facts, "
          f"{len(data['cells'])} cells)")


if __name__ == "__main__":
    main()
