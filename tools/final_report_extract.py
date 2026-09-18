#!/usr/bin/env python3
"""FINAL REPORT extractor — builds analysis/final_report_dataset.json.

Extracts, for every healthy scored run of the §8 apples-to-apples surface
(8 models x 3 frameworks x 3 efforts, era rule applied, health rule applied),
the per-run quantities needed by REPORT_FINAL.md:

  recall side   : tp / fn (frozen matcher, judge.py) + per-profile TP/FN
                  (Strict/Core/All) derived from summary.json per_golden_matches
                  (each entry carries the golden's category; matched entries have
                  a matched_candidate)
  precision side: in-run adjudication counts (n_true_hallucination /
                  n_bug_ungold / n_important_non_bug / n_unresolved — v2 three-way,
                  or v1-era fields flagged as such) AND readjudication3.json
                  verdicts (v3.1 clustered, k=1) where the file exists
  cost side     : per_model_usage token split (fresh input / cached read /
                  cache write / output incl. reasoning), reported cost_usd,
                  wall_ms
  provenance    : run_batch, registered_at (manifest.json), judges, run_id

Selection rule for the matrix (one run per (model, framework, effort, url)):
  healthy scored runs only; prefer batch 20260910-mrv0120-manifold, then
  20260906-fable51-vanilla-{low,medhigh}, then 20260906-glm53-top6,
  then 20260906-gpt6astra-vanilla-{low,medhigh}, then 20260825-batch-083-fullmatrix,
  then anything else; within a tier, newest registered_at wins.

Health rule (handoff §5.5): no error, tokens>0, and (findings or tokens<=20000).
Scored rule (added by this tool): summary has integer tp and fn keys.
Era rule (handoff §5.2): vanilla-engineered accepts any batch; compound/metareview
must be in {20260910-mrv0120-manifold, 20260906-fable51-vanilla-low,
20260906-fable51-vanilla-medhigh} (the last two are vanilla-only in practice).

Usage: .venv/bin/python tools/final_report_extract.py
"""
import json, glob, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from readjudicate3 import normalize_for_cluster  # same normalization rj3 clusters use

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_TIER = {
    "20260910-mrv0120-manifold": 0,
    "20260906-fable51-vanilla-low": 1,
    "20260906-fable51-vanilla-medhigh": 1,
    "20260906-glm53-top6": 2,
    "20260906-glm53-smoke": 2,
    "20260906-gpt6astra-vanilla-low": 3,
    "20260906-gpt6astra-vanilla-medhigh": 3,
    "20260825-batch-083-fullmatrix": 4,
}
MODELS = ["claude-fable-5-1", "gpt-6-astra", "gpt-5.6-sol", "claude-opus-5",
          "glm-5.3-vision-background", "gpt-5.6-terra", "claude-sonnet-5",
          "glm-5.3-flash-background"]
FRAMEWORKS = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
EFFORTS = ["low", "medium", "high"]
SEV_W = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
PROFILE = {
    "Strict": {"bug", "security", "concurrency", "data", "api"},
    "Core": {"bug", "security", "concurrency", "data", "api", "perf", "test_gap", "doc_defect"},
    "All": None,  # all categories
}

# --- golden set: severity weights + the top-6 -------------------------------
pr_golden = {}
for f in (glob.glob(f"{ROOT}/analysis/inputs/golden_comments/*.json")
              or glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json")):
    for e in json.load(open(f)):
        cs = e["comments"]
        pr_golden[e["url"]] = {
            "sev_weight": sum(SEV_W.get(c["severity"], 0) for c in cs),
            "n_comments": len(cs),
            "categories": sorted(c["category"] for c in cs),
        }
top6 = sorted(pr_golden, key=lambda u: (-pr_golden[u]["sev_weight"], -pr_golden[u]["n_comments"]))[:6]

if not pr_golden:
    raise SystemExit(
        "FATAL: the benchmark golden set is empty, so no recall number can be computed.\n"
        "  Expected analysis/inputs/golden_comments/*.json (vendored) or\n"
        "  third_party/code-review-benchmark/offline/golden_comments/*.json (upstream checkout).\n"
        "  Refusing to write a degenerate dataset - see analysis/inputs/golden_comments/README.md."
    )

# --- run extraction -----------------------------------------------------------
def health_ok(s):
    tok = (s.get("tokens_in") or 0) + (s.get("tokens_out") or 0)
    if s.get("error") or tok == 0:
        return False
    if not (len(s.get("findings", []) or []) or tok <= 20000):
        return False
    return True

def scored(s):
    return isinstance(s.get("tp"), int) and isinstance(s.get("fn"), int)

LEGACY_MODELS = ["glm-5.3-background", "glm-5.2-vision-flex", "kimi-k3", "gpt-5.2",
                  "claude-opus-4-5-20251101"]  # out-of-matrix rows, capability-floor aside only

def extract(f, models=MODELS):
    rid = f.split("/")[-2]
    s = json.load(open(f))
    fw = s.get("framework")
    # ERA RULE (handoff §5.2): compound/metareview pairs must come from the CURRENT
    # campaign batch (pre-0.12 binaries are instrument-confounded); vanilla may reuse
    # healthy runs from ANY batch/era.
    if fw in ("compound-realistic", "metareview-realistic"):
        if s.get("run_batch") != "20260910-mrv0120-manifold":
            return None
    elif fw != "vanilla-engineered":
        return None  # superpowers etc. are out of the §8 matrix
    if not health_ok(s) or not scored(s):
        return None
    if s.get("model") not in models or s.get("effort") not in EFFORTS + ["xhigh"]:
        return None
    # per-profile TP/FN from per_golden_matches
    prof = {}
    pgm = s.get("per_golden_matches") or []
    # identities of the goldens the official matcher credited (for the §10c double-count
    # correction: a golden found officially AND via a golden-overlapping cluster must be
    # counted once)
    matched_goldens = [g.get("golden_comment") for g in pgm if g.get("matched_candidate")]
    for name, cats in PROFILE.items():
        tp_p = fn_p = 0
        for g in pgm:
            if cats is not None and g.get("category") not in cats:
                continue
            if g.get("matched_candidate"):
                tp_p += 1
            else:
                fn_p += 1
        prof[name] = {"tp": tp_p, "fn": fn_p}
    # token split
    fresh_in = cached_in = cache_w = out_tok = 0
    pmu_cost = 0.0
    for u in (s.get("per_model_usage") or {}).values():
        fresh_in += u.get("input_tokens", 0) or 0
        cached_in += u.get("cache_read_input_tokens", 0) or 0
        cache_w += u.get("cache_creation_input_tokens", 0) or 0
        out_tok += (u.get("output_tokens", 0) or 0) + (u.get("reasoning_output_tokens", 0) or 0)
        pmu_cost += u.get("cost_usd", 0) or 0
    pmu_missing = (fresh_in + cached_in + cache_w + out_tok) == 0
    if pmu_missing:  # GLM harness runs store only aggregate in/out — conservative
        # fallback: all input priced at the fresh rate (ignores the cheaper cached rate,
        # so metered $ for these cells is an UPPER bound for the input side)
        fresh_in = s.get("tokens_in") or 0
        out_tok = s.get("tokens_out") or 0
    # in-run adjudication counts (v2 if present; v1 fallback flagged)
    v2 = "n_true_hallucination" in s
    inrun = {
        "instrument": "v2" if v2 else "v1",
        "hal": (s.get("n_true_hallucination") if v2 else s.get("n_hallucination")) or 0,
        "bug": (s.get("n_bug_ungold") if v2 else s.get("n_real_ungold")) or 0,
        "imp": (s.get("n_important_non_bug") if v2 else 0) or 0,
        "unres": (s.get("n_unresolved") if v2 else 0) or 0,
    }
    # rj3 verdicts (v3.1 clustered, k=1 per campaign lock)
    rj3 = None
    p = f"runs/{rid}/readjudication3.json"
    if os.path.exists(p):
        try:
            r = json.load(open(p))
            recs = r.get("records") or []
            h = b = i = u2 = 0
            for rec in recs:
                v = (rec.get("new_verdict") or "").lower()
                if v == "hallucination":
                    h += 1
                elif v == "bug":
                    b += 1
                elif v == "important_non_bug":
                    i += 1
                elif v == "unresolved":
                    u2 += 1
            rj3 = {"hal": h, "bug": b, "imp": i, "unres": u2,
                   "adjudicator_version": r.get("adjudicator_version"),
                   "judge": r.get("adjudicating_judge") or (json.load(open(f)).get("adjudicating_judge"))}
            # confirmed-bug texts from rj3 records (v3.1): the strongest instrument.
            # BUGFIX 2026-09-17: these were previously lost — the rj3 dict never carried
            # `records`, so rj3-adjudicated runs contributed ZERO texts to the union.
            # All 143 rj3 runs on the top-6 PRs (mostly vanilla cells) were silently
            # excluded; 706 rj3-confirmed bugs missing from the §10 union.
            bugtexts_rj3 = [normalize_for_cluster(rec.get("issue_text") or "")
                            for rec in recs if (rec.get("new_verdict") or "").lower() == "bug"]
        except Exception:
            rj3 = None
    try:
        ts = json.load(open(f"runs/{rid}/manifest.json")).get("registered_at") or ""
    except Exception:
        ts = ""
    # confirmed-bug texts (hidden-gold candidates) for the cross-run union:
    # rj3 'bug' verdicts if the run was re-adjudicated, else in-run 'real_but_ungold'
    bugtexts = []
    if rj3:
        bugtexts = bugtexts_rj3
    else:
        for rec in (s.get("adjudication_records") or []):
            if (rec.get("primary_judge_verdict") or "") == "real_but_ungold":
                bugtexts.append(normalize_for_cluster(rec.get("issue_text") or ""))
    return {
        "run_id": rid, "url": s.get("url"), "model": s["model"], "framework": fw,
        "effort": s["effort"], "batch": s.get("run_batch"),
        "tier": BATCH_TIER.get(s.get("run_batch"), 9),
        "ts": ts,
        "judge": s.get("primary_judge"), "adj_judge": s.get("adjudicating_judge"),
        "tp": s["tp"], "fn": s["fn"], "fp": s.get("fp") or 0,
        "n_findings": len(s.get("findings") or []),
        "prof": prof, "matched_goldens": matched_goldens, "inrun": inrun, "rj3": rj3,
        "fresh_in": fresh_in, "cached_in": cached_in, "cache_w": cache_w,
        "out_tok": out_tok, "pmu_cost_usd": pmu_cost, "pmu_missing": pmu_missing,
        "tokens_in": s.get("tokens_in") or 0, "tokens_out": s.get("tokens_out") or 0,
        "wall_ms": s.get("wall_ms") or 0,
        "bugtexts": bugtexts,
    }

runs = []
legacy = []
for f in glob.glob(f"{ROOT}/runs/*/summary.json"):
    for bucket, models in ((runs, MODELS), (legacy, LEGACY_MODELS)):
        try:
            r = extract(f, models)
        except Exception:
            r = None
        if r:
            bucket.append(r)
            break

# --- one run per (model, framework, effort, url) ------------------------------
best = {}
n_avail = defaultdict(int)
for r in runs:
    k = (r["model"], r["framework"], r["effort"], r["url"])
    n_avail[k[:3]] += 0  # placeholder (kept for clarity)
    # prefer LOWER tier (0 = current campaign batch), then NEWER ts; key sorts so that
    # "greater" = "preferred": (-tier, ts) makes tier 0 dominate and ts break ties.
    key = (-r["tier"], r["ts"])
    if k not in best or key > (-best[k]["tier"], best[k]["ts"]):
        best[k] = r

selected = list(best.values())

# coverage: healthy scored PRs per cell (selected basis and all-healthy basis)
cov_sel = defaultdict(set)
cov_all = defaultdict(set)
for r in runs:
    cov_all[(r["model"], r["framework"], r["effort"])].add(r["url"])
for r in selected:
    cov_sel[(r["model"], r["framework"], r["effort"])].add(r["url"])

out = {
    "top6": top6,
    "pr_golden": pr_golden,
    "selected_runs": selected,
    "all_healthy_runs": runs,   # every healthy scored run incl. duplicates: feeds the union
    "legacy_runs": legacy,
    "coverage_selected": {f"{m}|{fw}|{e}": sorted(v) for (m, fw, e), v in cov_sel.items()},
    "coverage_all_healthy": {f"{m}|{fw}|{e}": sorted(v) for (m, fw, e), v in cov_all.items()},
}
os.makedirs(f"{ROOT}/analysis", exist_ok=True)
with open(f"{ROOT}/analysis/final_report_dataset.json", "w") as fh:
    json.dump(out, fh)

print(f"extracted {len(runs)} healthy scored runs; selected {len(selected)} (one per cell x PR)")
print("top-6:", *top6, sep="\n  ")
print("coverage (selected / all-healthy):")
for m in MODELS:
    for fw in FRAMEWORKS:
        for e in EFFORTS:
            a = cov_sel.get((m, fw, e), set())
            b = cov_all.get((m, fw, e), set())
            t6a = len(a & set(top6)); t6b = len(b & set(top6))
            print(f"  {m:28s} {fw:20s} {e:6s} sel {len(a):2d}/50 (top6 {t6a}/6)  all {len(b):2d}/50 (top6 {t6b}/6)")
