#!/usr/bin/env python3
"""Promote the verified hidden-gold DEFECT set to the PRIMARY analysis in the metrics artifact.

Adds analysis/final_report_metrics.json -> "true_gold_defects": the defect-level recall / F1' / adjusted
precision per cell, the harness-vs-vanilla and MRV-vs-CE comparisons, and the headline summary.

GUARD: every pre-existing top-level key must survive byte-identical (the artifact is sacrosanct). The tool
aborts rather than write if any frozen key changes.
"""
from __future__ import annotations
import json, sys
import numpy as np
from report_quality import advisory_f2, SENSITIVITY_WEIGHTS
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MET = ROOT / "analysis/final_report_metrics.json"
DM = ROOT / "analysis/verified_gold/DEFECT_METRICS.json"
HARNESS = ("compound-realistic", "metareview-realistic")


def headline(block):
    cells = {k:v for k,v in block["cells"].items() if v["n_pr"] == 6}

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
        b2k, b2v = max(((k,v) for k,v in grp.items() if v.get("advisory_measured")), key=lambda kv: kv[1].get("F2p", 0))
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


def matched_framework_means(cells):
    frameworks = ("vanilla-engineered", "compound-realistic", "metareview-realistic")
    groups = {fw: {(k.split("|")[0], k.split("|")[2]): v for k, v in cells.items()
                   if k.split("|")[1] == fw} for fw in frameworks}
    shared = set.intersection(*(set(group) for group in groups.values()))
    return {fw: {"n": len(shared), "mean_F2p": sum(group[key]["F2p"] for key in sorted(shared)) / len(shared)}
            for fw, group in groups.items()} if shared else {}


def advisory_summary(block):
    cells = {k:v for k,v in block["cells"].items() if v["n_pr"]==6 and v["advisory_measured"]}
    rng = np.random.default_rng(20260919)
    def compare(ak,bk):
        a,b=cells[ak],cells[bk]
        ar={r["url"]:r["counts"] for r in a["per_pr"]};br={r["url"]:r["counts"] for r in b["per_pr"]}
        urls=sorted(set(ar)&set(br));A=np.array([ar[u] for u in urls]);B=np.array([br[u] for u in urls])
        ix=rng.integers(0,len(urls),size=(10000,len(urls)))
        aa=A[ix].sum(axis=1);bb=B[ix].sum(axis=1)
        da=advisory_f2(aa[:,0],aa[:,1],aa[:,4],aa[:,5]);db=advisory_f2(bb[:,0],bb[:,1],bb[:,4],bb[:,5])
        diff=db-da;ratio=np.divide(db,da,out=np.zeros_like(db),where=da>0)
        return {"a":ak,"b":bk,"delta":[b["F2p"]-a["F2p"],float(np.percentile(diff,2.5)),float(np.percentile(diff,97.5))],"ratio":[b["F2p"]/a["F2p"],float(np.percentile(ratio,2.5)),float(np.percentile(ratio,97.5))]}
    framework=matched_framework_means(cells)
    ranking=sorted(cells,key=lambda k:-cells[k]["F2p"])
    h=block["headline"];pairs={"best_harness_vs_vanilla":compare(h["vanilla"]["best_f2p"]["cell"],h["harness"]["best_f2p"]["cell"])}
    for model in ("glm-5.3-vision-background","glm-5.3-flash-background"):
        for effort in ("low","medium","high"):
            a=f"{model}|compound-realistic|{effort}";b=f"{model}|metareview-realistic|{effort}"
            if a in cells and b in cells:pairs[model+"|"+effort]=compare(a,b)
    return {"definition":"F2prime_advisory_v1: (5T+alpha*A)/(4D+T+alpha*A+H), alpha=1; complete, advisory-measured cells only for rankings", "n_eligible":len(cells),"excluded":[k for k,v in block["cells"].items() if v["n_pr"]==6 and not v["advisory_measured"]],"ranking":ranking,"framework_means":framework,"comparisons":pairs,"sensitivity_rankings":{str(w):sorted(cells,key=lambda k:-cells[k]["F2p_sensitivity"][str(w)][0]) for w in SENSITIVITY_WEIGHTS}}


def derived_numbers(dm_var, M, ROOT):
    """Persist the comparison numbers that the report cites but no single artifact stored:
    harness-vs-vanilla paired deltas, ensemble coverage / blind tail, and the best cell's misses."""
    import hashlib
    VG = ROOT / "analysis/verified_gold"
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    assign = json.load(open(VG / "DEFECT_ASSIGN.json"))
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))

    def sha(t):
        return hashlib.sha1(t.encode()).hexdigest()[:16]

    # The verified universe ONLY: withdrawn (2026-09-18 audit) and duplicate-tier defects must not
    # inflate the union coverage, the best-cell counts, or any denominator. See
    # analysis/verified_gold/WITHDRAWALS_AND_DEDUP_2026-09-18.md.
    valid = {d["id"] for d in reg["defects"] if d.get("tier") == "D-verified"}
    # the 66 complete cells (all six PRs) - the same basis the recall / F2' metrics use. Partial-coverage
    # cells in the same block are excluded so that the union and the per-cell metrics cannot disagree.
    cells = {k: v for k, v in dm_var["cells"].items() if v.get("n_pr") == 6}
    sel = {(r["model"], r["framework"], r["effort"], r["url"]): r for r in D["selected_runs"]}
    slug = {u: u.rstrip("/").split("/")[-1] for u in M["expanded_gold"]["per_pr"]}
    # Derive the denominators instead of hardcoding them: goldens from the expanded-gold per-PR golden
    # counts (sums to 42 for the six campaign PRs), defects from the verified registry universe.
    goldens_den = sum((M["expanded_gold"]["per_pr"].get(u) or {}).get("golden") or 0 for u in slug)
    defects_den = len(valid)
    den = goldens_den + defects_den

    hits = {}
    for c in cells:
        m, fw, e = c.split("|")
        G, Dp = set(), set()
        for u, pr in slug.items():
            r = sel.get((m, fw, e, u))
            if not r:
                continue
            for g in (r.get("matched_goldens") or []):
                G.add(g)
            mm = assign.get(pr, {})
            for t in (r.get("bugtexts") or []):
                d = mm.get(sha(t))
                if d and d in valid:
                    Dp.add(d)
        hits[c] = (G, Dp)

    allG = set().union(*[g for g, _ in hits.values()])
    allD = set().union(*[d for _, d in hits.values()])
    harG = set().union(*[g for k, (g, _) in hits.items() if k.split("|")[1] != "vanilla-engineered"])
    harD = set().union(*[d for k, (_, d) in hits.items() if k.split("|")[1] != "vanilla-engineered"])
    bestk = max(hits, key=lambda k: len(hits[k][0]) + len(hits[k][1]))
    bg, bd = hits[bestk]
    others = set()
    for k, (g, d) in hits.items():
        if k != bestk:
            others |= (g | d)
    missed = (allG | allD) - (bg | bd)

    hv = []
    for k, c in cells.items():
        m, fw, e = k.split("|")
        if fw == "vanilla-engineered":
            continue
        vk = f"{m}|vanilla-engineered|{e}"
        if vk in cells:
            hv.append((c["recall"] - cells[vk]["recall"], c["F1p"] - cells[vk]["F1p"]))
    n = len(hv)
    return {
        "coverage": {
            "all_cells": len(allG) + len(allD), "harness_cells_only": len(harG) + len(harD),
            "den": den, "goldens": len(allG), "goldens_den": goldens_den, "defects": len(allD), "defects_den": defects_den,
            "unfound_total": den - (len(allG) + len(allD)),
            "unfound_goldens": goldens_den - len(allG), "unfound_defects": defects_den - len(allD),
            "note": "union over the 66 complete cells (all six PRs); a golden counts once matched by any cell, a "
                    "defect once its finding text is assigned to it by any cell. Basis chosen to match the "
                    "recall/F2' per-cell metrics.",
        },
        "best_cell": {"cell": bestk, "found": len(bg) + len(bd), "den": den,
                      "misses_within_reach": len(missed), "misses_found_by_another_cell": len(missed & others)},
        "harness_vs_vanilla": {
            "n_pairs": n, "n_positive_recall": sum(1 for a, _ in hv if a > 0),
            "mean_dRecall": (sum(a for a, _ in hv) / n) if n else None,
            "n_positive_F1p": sum(1 for _, b in hv if b > 0),
            "mean_dF1p": (sum(b for _, b in hv) / n) if n else None,
            "note": "matched model*effort pairs, harness cell minus its same-model/effort vanilla cell, "
                    "on the true golden set",
        },
        "mrv_vs_ce": {
            "n_pairs": len(dm_var["pairs"]),
            "mean_dF2p": (sum(v["dF2p"][0] for v in dm_var["pairs"].values()) / len(dm_var["pairs"])) if dm_var["pairs"] else None,
            "mean_dRecall": (sum(v["dRecall"][0] for v in dm_var["pairs"].values()) / len(dm_var["pairs"])) if dm_var["pairs"] else None,
            "n_positive_F2p_point": sum(1 for v in dm_var["pairs"].values() if v["dF2p"][0] > 0),
            "n_resolved_F2p_95": sum(1 for v in dm_var["pairs"].values() if v["dF2p"][1] > 0),
        },
    }


def main():
    met = json.load(open(MET))
    before = {k: json.dumps(v, sort_keys=True) for k, v in met.items() if k != "true_gold_defects"}
    dm = json.load(open(DM))
    for variant in ("verified", "reachable", "full"):
        if variant not in dm:
            continue
        dm[variant]["headline"] = headline(dm[variant])
        dm[variant]["advisory_summary"] = advisory_summary(dm[variant])
        dm[variant]["derived"] = derived_numbers(dm[variant], met, ROOT)
        dm[variant]["definition"] = {
            "denominator": "42 Martian goldens + every verified hidden-gold defect in this set",
            "recall": "TP / denominator (cluster/PR-level bootstrap CI)",
            "F1p": "F1 with the nitpick-charged precision (adjP') - an EQUAL-weight, nitpick-averse lens; "
                   "it is volume-sensitive and can rank a terse cell above a higher-recall cell",
            "F2p": "Advisory-augmented F2: (5T+A)/(4D+T+A+H). T verified bugs; D bug denominator; "
                   "A accepted saved useful advisories, full-channel merge; H effective unsupported claims including style/vague. "
                   "Advisory weight 1 is a declared preference (sensitivity 0.5/2); not measured developer utility. "
                   "F2p_legacy preserves former non-bug penalty. Incomplete advisory measurement excluded from rankings.",
            "adjP": "adjusted precision after adjudication (a reported finding counts only if the adjudicator "
                    "accepted it as a real defect)",
        }
    # per-PR counts so downstream panels can compute each cell's reachable ceiling on the true set
    reg = json.load(open(ROOT / "analysis/verified_gold/DEFECT_REGISTRY.json"))
    ds = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    from collections import Counter
    per_pr_slug = Counter(d["pr"] for d in reg["defects"] if d.get("tier") == "D-verified")
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
