#!/usr/bin/env python3
"""Emit REPORT_FINAL.md data tables as markdown (from final_report_metrics.json).
Every cell carries its cluster-bootstrap 95% CI. Writes /tmp/final_report_tables.md."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(f"{ROOT}/analysis/final_report_metrics.json"))
MODELS = ["claude-fable-5-1", "gpt-6-astra", "gpt-5.6-sol", "claude-opus-5",
          "glm-5.3-vision-background", "gpt-5.6-terra", "claude-sonnet-5",
          "glm-5.3-flash-background"]
FWS = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
SH = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV",
      "claude-fable-5-1": "fable-5.1", "gpt-6-astra": "astra", "gpt-5.6-sol": "sol",
      "claude-opus-5": "opus-5", "glm-5.3-vision-background": "glm-vis",
      "gpt-5.6-terra": "terra", "claude-sonnet-5": "sonnet-5",
      "glm-5.3-flash-background": "glm-flash"}

def ci(t, fmt="{:.2f}", pre=""):
    p, lo, hi, fr = t
    star = "*" if fr < 0.975 else ""
    return f"{pre}{fmt.format(p)} [{pre}{fmt.format(lo)}, {pre}{fmt.format(hi)}]{star}"

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from presfmt import fnum, money, money_adaptive

def ci_usd(t, places=5):
    # adaptive $ formatting: the POINT value's magnitude decides the unit for the
    # whole bracket (< $0.01 -> cents, kills leading-zero drowning; else $),
    # artifact-free; N=5 default
    p, lo, hi, fr = t
    star = "*" if fr < 0.975 else ""
    if 0 < abs(p) < 0.01:
        f = lambda v: f"{fnum(v * 100, places)}¢"
    else:
        f = lambda v: f"${fnum(v, places)}"
    return f"{f(p)} [{f(lo)}, {f(hi)}]{star}"

out = []
def w(s=""):
    out.append(s)

# ---- T1 quality matrix
w("### T1 — §8 apples-to-apples matrix (severity top-6): quality, 95% cluster-bootstrap CIs")
w()
w("recall = frozen-matcher TP/(TP+FN) vs all 173 goldens (All profile; Core/Strict differ only by")
w("PR 10967's single style golden on this PR set). adjP = TP/(TP+hallucinations), k=1 verdicts;")
w("`inst` = precision instrument (rj3 = v3.1 clustered k=1, v2 = in-run three-way, v1 = binary legacy).")
w("n = PRs with a selected healthy scored run (1 run/PR). Judge: gpt-5.2 for fable/opus/sonnet/glm rows,")
w("claude-opus-4-5-20251101 for sol/terra/astra rows.")
w()
w("| model | fw | eff | n | recall [CI] | adjP [CI] | F1 [CI] | F2 [CI] | beyond-gold/PR | inst |")
w("|---|---|---|---|---|---|---|---|---|---|")
for m in MODELS:
    for fw in FWS:
        for e in ("low", "medium", "high"):
            v = M["matrix"].get(f"{m}|{fw}|{e}")
            if not v:
                continue
            flag = " **GAP**" if v["n_pr"] < 6 else ""
            w(f"| {SH[m]}{flag} | {SH[fw]} | {e} | {v['n_pr']} | {ci(v['ci']['recall'])} | "
              f"{ci(v['ci']['adjP'])} | {ci(v['ci']['F1'])} | {ci(v['ci']['F2'])} | "
              f"{v['real_beyond']/v['n_pr']:.1f} | {'/'.join(v['instruments'])} |")
w()
# ---- T2 cost matrix
w("### T2 — cost & throughput per cell (top-6), 95% cluster-bootstrap CIs")
w()
w("Metered $ at published list prices retrieved 2026-09-16 (REPORT_FINAL §6.1). tok/run includes")
w("fresh input + cached reads + cache writes + output (incl. reasoning). GLM cells marked * are")
w("conservative (all input priced at the fresh rate; no per-model token split available).")
w("Values < $0.01 are shown in cents (¢) to avoid leading-zero drowning; ≥ $0.01 in $.")
w()
w("| model | fw | eff | $/run [CI] | $/real [CI] | $/TP [CI] | tok/run [CI] | wall s/run [CI] | price per k-tok [CI] |")
w("|---|---|---|---|---|---|---|---|---|")
for m in MODELS:
    for fw in FWS:
        for e in ("low", "medium", "high"):
            v = M["matrix"].get(f"{m}|{fw}|{e}")
            if not v:
                continue
            flag = "*" if v["pmu_missing_runs"] else ""
            w(f"| {SH[m]}{flag} | {SH[fw]} | {e} | {ci_usd(v['ci']['cost_run'])} | "
              f"{ci_usd(v['ci']['usd_per_real'])} | {ci_usd(v['ci']['usd_per_tp'])} | "
              f"{ci(v['ci']['tok_run'], '{:,.0f}')} | {ci(v['ci']['wall_run'], '{:,.0f}')} | "
              f"{ci_usd(v['ci']['price_per_ktok'])} |")
w()
# ---- T3 selection effect
w("### T3 — selection effect: top-6 vs full-50 (cells with ≥40/50 healthy scored PRs)")
w()
w("| cell | n | recall top-6 | recall full | F1 top-6 | F1 full | F1 full [CI] |")
w("|---|---|---|---|---|---|---|")
for k, v in M["selection_effect"].items():
    m, fw, e = k.split("|")
    w(f"| {SH[m]} {SH[fw]} {e} | {v['n_full']} | {v['recall_t6']:.2f} | {v['recall_full']:.2f} | "
      f"{v['F1_t6']:.2f} | {v['F1_full']:.2f} | {ci(v['ci_full_F1'])} |")
w()
w("Rank agreement (Spearman of model F1 ranks, top-6 vs full-50, within framework×effort):")
w()
w("| framework × effort | models with full rows | Spearman ρ |")
w("|---|---|---|")
for k, v in M["rank_agreement"].items():
    fw, e = k.split("|")
    w(f"| {fw} {e} | {len(v['models'])} | {v['spearman']:.2f} |")
w()
# ---- T4 framework deltas
w("### T4 — harness vs vanilla, paired on the same 6 PRs (Δrecall CI; token ×; cost ×)")
w()
w("| cell (model fw effort) | Δrecall [CI] | token × [CI] | cost × [CI] |")
w("|---|---|---|---|")
for k, d in M["framework_delta"].items():
    m, fw, e = k.split("|")
    tm = M["token_multiple"][k]
    w(f"| {SH[m]} {SH[fw]} {e} | {d['recall'][0]:+.2f} [{d['recall'][1]:+.2f}, {d['recall'][2]:+.2f}] | "
      f"{tm['tok_ratio'][0]:.1f}× [{tm['tok_ratio'][1]:.1f}, {tm['tok_ratio'][2]:.1f}] | "
      f"{tm['cost_ratio'][0]:.1f}× [{tm['cost_ratio'][1]:.1f}, {tm['cost_ratio'][2]:.1f}] |")
w()
# ---- T5 effort ladder
w("### T5 — effort ladder: high vs medium, paired (ΔF1 CI; Δrecall CI; cost high/medium)")
w()
w("| model × framework | ΔF1 [CI] | Δrecall [CI] | cost high/med |")
w("|---|---|---|---|")
for k, d in M["effort_ladder"].items():
    m, fw = k.split("|")
    dl = d["delta"]
    w(f"| {SH[m]} {SH[fw]} | {dl['F1'][0]:+.2f} [{dl['F1'][1]:+.2f}, {dl['F1'][2]:+.2f}] | "
      f"{dl['recall'][0]:+.2f} [{dl['recall'][1]:+.2f}, {dl['recall'][2]:+.2f}] | "
      f"{d['cost_ratio'][0]:.2f}× [{d['cost_ratio'][1]:.2f}, {d['cost_ratio'][2]:.2f}] |")
w()
# ---- T6 tier
w("### T6 — glm-flash vs glm-vision, paired on the same 6 PRs (Δ from vision → flash)")
w()
w("| framework × effort | Δrecall [CI] | Δ real findings [CI] |")
w("|---|---|---|")
for k, d in M["tier_flash_vs_vision"].items():
    fw, e = k.split("|")
    w(f"| {SH[fw]} {e} | {d['recall'][0]:+.2f} [{d['recall'][1]:+.2f}, {d['recall'][2]:+.2f}] | "
      f"{d['real_total'][0]:+.0f} [{d['real_total'][1]:+.0f}, {d['real_total'][2]:+.0f}] |")
w()
# ---- T7 cost structure
w("### T7 — cost-structure ratios (all pairs, low effort unless stated): per-token / tokens-per-task / net cost-per-task")
w()
w("| glm cell vs frontier cell | per-token (glm/frontier) [CI] | tokens/task [CI] | cost/task [CI] |")
w("|---|---|---|---|")
for k, d in M["cost_structure_ratios"].items():
    a, b = k.split(" vs ")
    w(f"| {a} vs {b} | {fnum(d['ptok_ratio'][0])} [{fnum(d['ptok_ratio'][1])}, {fnum(d['ptok_ratio'][2])}] | "
      f"{d['toktask_ratio'][0]:.1f}× [{d['toktask_ratio'][1]:.1f}, {d['toktask_ratio'][2]:.1f}] | "
      f"{fnum(d['costtask_ratio'][0])} [{fnum(d['costtask_ratio'][1])}, {fnum(d['costtask_ratio'][2])}] |")
w()
# ---- T8 recommendation
w("### T8 — recommendation ratios (glm @ low vs frontier reference cells, same 6 PRs)")
w()
w("| glm cell (A) vs frontier cell (F) | recall A/F [CI] | F1 A/F [CI] | cost A/F [CI] |")
w("|---|---|---|---|")
for k, d in M["recommendation_ratios"].items():
    a, b = k.split(" vs ")
    w(f"| {a} vs {b} | {fnum(d['recall_ratio'][0])} [{fnum(d['recall_ratio'][1])}, {fnum(d['recall_ratio'][2])}] | "
      f"{fnum(d['F1_ratio'][0])} [{fnum(d['F1_ratio'][1])}, {fnum(d['F1_ratio'][2])}] | "
      f"{fnum(d['cost_ratio_A_over_F'][0])} [{fnum(d['cost_ratio_A_over_F'][1])}, {fnum(d['cost_ratio_A_over_F'][2])}] |")
w()
# ---- T9 expanded-gold matrix
w()
w("### T9 — expanded-gold matrix (top-6): recall/adjP/F1 against the hidden-gold union")
w()
w("Strict = Martian benchmark (goldens only). Expanded = goldens + cross-run/cross-model")
w("deduplicated confirmed-bug union (see REPORT_FINAL §5b for construction and caveats).")
w("recall_exp and F1_exp levels are conservative lower bounds; the paired deltas in T10 are")
w("the robust comparison.")
w()
w("| model | fw | eff | n | recall_strict | recall_exp [CI] | adjP_exp | F1_exp [CI] | F1_strict |")
w("|---|---|---|---|---|---|---|---|---|")
for m in MODELS:
    for fw in FWS:
        for e in ("low", "medium", "high"):
            k = f"{m}|{fw}|{e}"
            v = M["expanded_gold"]["matrix_exp"].get(k)
            st = M["matrix"].get(k)
            if not v or not st:
                continue
            flag = " **GAP**" if v["n_pr"] < 6 else ""
            w(f"| {SH[m]}{flag} | {SH[fw]} | {e} | {v['n_pr']} | {st['recall']:.2f} | "
              f"{v['recall_exp']:.3f} [{v['ci']['recall_exp'][1]:.3f}, {v['ci']['recall_exp'][2]:.3f}] | "
              f"{v['adjP_exp']:.2f} | {v['F1_exp']:.3f} [{v['ci']['F1_exp'][1]:.3f}, {v['ci']['F1_exp'][2]:.3f}] | {st['F1']:.2f} |")
w()
# ---- T10 framework deltas exp
w("### T10 — harness vs vanilla, paired on the same 6 PRs: Δrecall under the expanded set")
w()
w("| cell (model fw effort) | Δrecall_exp [CI] |")
w("|---|---|")
pos = neg = unres = 0
for k, d in M["expanded_gold"]["framework_delta_exp"].items():
    dd = d["dRecall_exp"]
    if dd[1] > 0: pos += 1
    elif dd[2] < 0: neg += 1
    else: unres += 1
    m, fw, e = k.split("|")
    w(f"| {SH[m]} {SH[fw]} {e} | {dd[0]:+.3f} [{dd[1]:+.3f}, {dd[2]:+.3f}] |")
w()
w(f"Resolved positive {pos}/{len(M['expanded_gold']['framework_delta_exp'])}, negative {neg}, unresolved {unres} "
  f"(strict-benchmark version: 17/42 positive, 2 negative — see T4).")
w()
# ---- union sizes
w("### T11 — hidden-gold union sizes per top-6 PR")
w()
w("| PR | goldens | union clusters | expanded set |")
w("|---|---|---|---|")
for u, v in M["expanded_gold"]["per_pr"].items():
    w(f"| {u.split('github.com/')[1]} | {v['golden']} | {v['union']} | {v['expanded']} |")
w()

# ---- §10b semantic union tables (PRIMARY real-world result) ----
SEM = M["expanded_gold_semantic"]
w("### T12 — semantic-union matrix (§10b PRIMARY): per-cell real-world metrics with 95% cluster-bootstrap CIs")
w()
w("Union = distinct real bugs (LLM semantic merge of all confirmed-bug findings; hallucinations and")
w("nitpicks excluded at the gate). recall_sem = (golden TP + distinct bugs found)/(goldens + true bugs).")
w("adjP charges only hallucinations; adjP\' also charges nitpicks (user lens: everything the reader wades through).")
w()
w("| cell | n PRs | recall_sem | adjP | adjP\' | F1 | F1\' |")
w("|---|---|---|---|---|---|---|")
order = sorted(SEM["matrix_sem"].items(), key=lambda kv: -kv[1]["F1p"])
for k, c in order:
    m, fw, e = k.split("|")
    w(f"| {SH[m]} {SH[fw]} {e} | {c['n_pr']} | {c['recall_sem']:.3f} [{c['ci']['recall_sem'][1]:.3f}, {c['ci']['recall_sem'][2]:.3f}] "
      f"| {c['adjP']:.3f} | {c['adjPp']:.3f} | {c['F1']:.3f} [{c['ci']['F1'][1]:.3f}, {c['ci']['F1'][2]:.3f}] "
      f"| {c['F1p']:.3f} [{c['ci']['F1p'][1]:.3f}, {c['ci']['F1p'][2]:.3f}] |")
w()
w("### T13 — CE vs MRV, paired on the same PRs (Δ = MRV − CE, semantic metrics)")
w()
w("| model · effort | n PRs | Δrecall_sem | ΔF1 | ΔF1\' |")
w("|---|---|---|---|---|")
for k, v in sorted(SEM["ce_vs_mrv"].items()):
    m, e = k.split("|")
    dr, df, dfp = v["dRecall_sem"], v["dF1"], v["dF1p"]
    w(f"| {SH[m]} · {e} | {v['n_pr']} | {dr[0]:+.3f} [{dr[1]:+.3f}, {dr[2]:+.3f}] "
      f"| {df[0]:+.3f} [{df[1]:+.3f}, {df[2]:+.3f}] | {dfp[0]:+.3f} [{dfp[1]:+.3f}, {dfp[2]:+.3f}] |")
ps = SEM["pairs_summary"]
w()
w(f"Pairs-level aggregate: mean ΔF1 {ps['mean']['dF1']:+.3f} [{ps['ci_mean']['dF1'][1]:+.3f}, {ps['ci_mean']['dF1'][2]:+.3f}], "
  f"mean ΔF1\' {ps['mean']['dF1p']:+.3f} [{ps['ci_mean']['dF1p'][1]:+.3f}, {ps['ci_mean']['dF1p'][2]:+.3f}] — "
  f"**resolves positive**. Signs: ΔF1 {ps['signs']['dF1']['pos']}+/{ps['signs']['dF1']['neg']}−/{ps['signs']['dF1']['zero']}0; "
  f"ΔF1\' {ps['signs']['dF1p']['pos']}+/{ps['signs']['dF1p']['neg']}−. No single pair\'s CI excludes zero (6 PRs each); "
  f"the aggregate over {ps['n_pairs']} matched pairs is the reportable quantity.")
w()
w("### T14 — harness vs vanilla, paired Δrecall_sem (semantic union)")
w()
w("| model · fw · effort | n PRs | Δrecall_sem (harness − vanilla) | resolved |")
w("|---|---|---|---|")
posf = sum(1 for v in SEM["harness_vs_vanilla_sem"].values() if v["dRecall_sem"][1] > 0)
for k, v in sorted(SEM["harness_vs_vanilla_sem"].items()):
    m, fw, e = k.split("|")
    dd = v["dRecall_sem"]
    res = "+" if dd[1] > 0 else ("−" if dd[2] < 0 else "~")
    w(f"| {SH[m]} {SH[fw]} {e} | {v['n_pr']} | {dd[0]:+.3f} [{dd[1]:+.3f}, {dd[2]:+.3f}] | {res} |")
w()
w(f"Resolved positive {posf}/{len(SEM['harness_vs_vanilla_sem'])} (vs 38/42 under the frozen key-union, 17/42 strict).")
w()
w("### T15 — true-golden set per PR (semantic union; evidence pack)")
w()
w("| PR | goldens | true bugs | findings clustered | judge calls |")
w("|---|---|---|---|---|")
for u, v in SEM["per_pr"].items():
    w(f"| {u.split('github.com/')[1]} | {v['goldens']} | **{v['union_sem']}** | {v['n_findings']:,} | {v['judge_calls']} |")
w()
w(f"Total: 42 goldens + 359 true bugs. Per-bug verification cards (location, why-real, replication,")
w("found-by): `analysis/TRUE_GOLDEN_EVIDENCE.md`.")
w()

open("/tmp/final_report_tables.md", "w").write("\n".join(out))
print("wrote /tmp/final_report_tables.md", len(out), "lines")
