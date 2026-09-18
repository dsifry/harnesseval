#!/usr/bin/env python3
"""Promote the verified hidden-gold DEFECT set to the PRIMARY analysis in the metrics artifact.

Adds analysis/final_report_metrics.json -> "true_gold_defects": the defect-level recall / F1' / adjusted
precision per cell, the harness-vs-vanilla and MRV-vs-CE comparisons, and the headline summary.

GUARD: every pre-existing top-level key must survive byte-identical (the artifact is sacrosanct). The tool
aborts rather than write if any frozen key changes.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MET = ROOT / "analysis/final_report_metrics.json"
DM = ROOT / "analysis/verified_gold/DEFECT_METRICS.json"
HARNESS = ("compound-realistic", "metareview-realistic")


def headline(block):
    cells = block["cells"]

    def cls(k):
        return k.split("|")[1]
    harness = {k: v for k, v in cells.items() if cls(k) in HARNESS}
    vanilla = {k: v for k, v in cells.items() if cls(k) == "vanilla-engineered"}
    out = {}
    for name, grp in (("harness", harness), ("vanilla", vanilla)):
        if not grp:
            continue
        brk, brv = max(grp.items(), key=lambda kv: kv[1]["recall"])
        bfk, bfv = max(grp.items(), key=lambda kv: kv[1]["F1p"])
        b2k, b2v = max(grp.items(), key=lambda kv: kv[1].get("F2p", 0))
        out[name] = {
            "best_recall": {"cell": brk, "F2p": brv.get("F2p"), **{k: brv[k] for k in ("recall", "F1p", "adjP", "TP", "den")}},
            "best_f1p": {"cell": bfk, "F2p": bfv.get("F2p"), **{k: bfv[k] for k in ("recall", "F1p", "adjP", "TP", "den")}},
            "best_f2p": {"cell": b2k, **{k: b2v[k] for k in ("recall", "F2p", "F1p", "adjP", "TP", "den")}},
        }
    if "harness" in out and "vanilla" in out:
        hr, vr = out["harness"]["best_recall"]["recall"], out["vanilla"]["best_recall"]["recall"]
        out["peak_recall_ratio_harness_over_vanilla"] = hr / vr if vr else None
        hf, vf = out["harness"]["best_f1p"]["F1p"], out["vanilla"]["best_f1p"]["F1p"]
        out["best_f1p_ratio_harness_over_vanilla"] = hf / vf if vf else None
        h2 = out["harness"]["best_f2p"]["F2p"]
        v2 = out["vanilla"]["best_f2p"]["F2p"]
        out["best_f2p_ratio_harness_over_vanilla"] = h2 / v2 if v2 else None
    return out


def main():
    met = json.load(open(MET))
    before = {k: json.dumps(v, sort_keys=True) for k, v in met.items() if k != "true_gold_defects"}
    dm = json.load(open(DM))
    for variant in ("verified", "reachable", "full"):
        if variant not in dm:
            continue
        dm[variant]["headline"] = headline(dm[variant])
        dm[variant]["definition"] = {
            "denominator": "42 Martian goldens + every verified hidden-gold defect in this set",
            "recall": "TP / denominator (cluster/PR-level bootstrap CI)",
            "F1p": "F1 with the nitpick-charged precision (adjP') - an EQUAL-weight, nitpick-averse lens; "
                   "it is volume-sensitive and can rank a terse cell above a higher-recall cell",
            "F2p": "F_beta with beta=2 (recall weighted 4:1) using adjP' - matches the campaign's declared cost "
                   "asymmetry (a missed bug costs more than a false alarm) and is the recommended composite",
            "adjP": "adjusted precision after adjudication (a reported finding counts only if the adjudicator "
                    "accepted it as a real defect)",
        }
    # per-PR counts so downstream panels can compute each cell's reachable ceiling on the true set
    reg = json.load(open(ROOT / "analysis/verified_gold/DEFECT_REGISTRY.json"))
    ds = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    from collections import Counter
    per_pr_slug = Counter(d["pr"] for d in reg["defects"])
    gold_pr = {u: v.get("goldens") for u, v in (met.get("expanded_gold_verified", {}).get("per_pr") or {}).items()}
    per_pr = {}
    for url, gold in gold_pr.items():          # gold_pr is keyed by the 6 campaign PR urls
        slug = url.rstrip("/").split("/")[-1]
        per_pr[url] = {"goldens": gold, "verified_defects": per_pr_slug.get(slug, 0)}
    dm["per_pr"] = per_pr
    met["true_gold_defects"] = dm
    met["true_gold_defects"]["role"] = ("PRIMARY true-gold analysis: the deduplicated verified hidden-gold "
                                       "defect set (see analysis/verified_gold/GOLD_DEFECT_CATALOG.md). "
                                       "supersedes the key-union levels in expanded_gold / expanded_gold_semantic / "
                                       "expanded_gold_verified, which are kept for provenance.")
    after = {k: json.dumps(v, sort_keys=True) for k, v in met.items() if k in before}
    changed = [k for k in before if before[k] != after.get(k)]
    if changed:
        print("ABORT: frozen keys would change:", changed, file=sys.stderr)
        sys.exit(2)
    json.dump(met, open(MET, "w"), indent=1)
    print("wrote true_gold_defects; frozen keys byte-identical:", len(before))
    print(json.dumps(met["true_gold_defects"]["verified"]["headline"], indent=1))


if __name__ == "__main__":
    main()
