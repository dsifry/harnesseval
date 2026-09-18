#!/usr/bin/env python3
"""§10d — per-cell metrics computed at the DEFECT level (not the bundle level).

Inputs: DEFECT_REGISTRY.json (145 defects, tiered), DEFECT_ASSIGN.json (finding -> defect id),
analysis/final_report_dataset.json (runs), analysis/final_report_metrics.json (golden counts).

For each selected run:
  defects hit       = distinct defect ids among its findings (from the assignment map)
  tp                = golden TP (official matcher) + defects hit
  denominator (PR)  = goldens(PR) + defects(PR)
Two variants: 'verified' (denominator = goldens + D-verified only, the strict floor) and
'full' (goldens + all registry defects). adjP charges hallucinations; adjP' also charges nitpicks.

Writes analysis/verified_gold/DEFECT_METRICS.{json,md}. CIs: cluster bootstrap B=10000, seed 20260916,
rng = SEED+5 (a fresh stream; nothing frozen is touched).

Usage: .venv/bin/python tools/verified_gold_defect_metrics.py
"""
from __future__ import annotations
import glob, hashlib, json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"
SEED = 20260916
B = 10000


def sha(t):
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def main():
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    assign = json.load(open(VG / "DEFECT_ASSIGN.json"))
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    # The six-PR list and the per-PR golden counts come from the DATASET (produced by final_report_extract.py)
    # rather than from the generated final_report_metrics.json. That file is written by final_report_compute.py,
    # whose §10d step consumes THIS tool's DEFECT_METRICS.json - so reading the dataset here breaks the cycle and
    # lets the whole chain be rebuilt from scratch in one pass. (Values are identical: n_comments per PR is the
    # golden count, and the top-6 ordering key is the same sev_weight/n_comments sort used by the extractor.)
    _pg = D["pr_golden"]
    top6 = sorted(_pg, key=lambda u: (-_pg[u]["sev_weight"], -_pg[u]["n_comments"]))[:6]
    goldens = {u.rstrip("/").split("/")[-1]: _pg[u]["n_comments"] for u in top6}
    slug = {u: u.rstrip("/").split("/")[-1] for u in top6}
    by_pr_defects = defaultdict(list)
    for d in reg["defects"]:
        by_pr_defects[d["pr"]].append(d)
    tier = {}
    for d in reg["defects"]:
        tier[d["id"]] = d["tier"]
    valid_ids = set(tier)
    # defects that at least one finding anywhere was assigned to. 13 of the verified defects were surfaced by
    # the AUDIT (merge-audit label lists / under-count triage) and were never reported by any run, so no cell
    # can score them; recall against them is structurally capped. Reported as a separate 'reachable' variant.
    reported_ids = {d for _pr, m in assign.items() for _h, d in m.items() if d in valid_ids}

    sel = {(r["model"], r["framework"], r["effort"], r["url"]): r for r in D["selected_runs"]}
    try:
        M = json.load(open(ROOT / "analysis/final_report_metrics.json"))
    except FileNotFoundError:
        M = {}
    MODELS = M["mods"] if "mods" in M else sorted({r["model"] for r in D["selected_runs"]})
    FWS = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
    EFFS = ["low", "medium", "high"]
    rng = np.random.default_rng(SEED + 5)

    def run_row(r, variant):
        pr = slug.get(r["url"], r["url"].rstrip("/").split("/")[-1])
        amap = assign.get(pr, {})
        own = set()
        for t in (r.get("bugtexts") or []):
            did = amap.get(sha(t))
            if not did or did not in valid_ids:      # merged-away defects no longer count
                continue
            if variant == "verified" and tier.get(did) != "D-verified":
                continue
            if variant == "reachable" and did not in reported_ids:
                continue
            own.add(did)
        tot = len(by_pr_defects.get(pr, []))
        if variant == "verified":
            tot = sum(1 for d in by_pr_defects.get(pr, []) if d["tier"] == "D-verified")
        elif variant == "reachable":
            tot = sum(1 for d in by_pr_defects.get(pr, []) if d["id"] in reported_ids)
        v = r["rj3"] or r["inrun"]
        return {"tp": r["tp"] + len(own), "den": goldens[pr] + tot, "hal": v["hal"], "imp": v["imp"]}

    def vec(S):
        t, d, h, im = S[:, :, 0].sum(axis=1), S[:, :, 1].sum(axis=1), S[:, :, 2].sum(axis=1), S[:, :, 3].sum(axis=1)
        rec = np.where(d > 0, t / np.where(d > 0, d, 1), 0)
        adj = np.where(t + h > 0, t / np.where(t + h > 0, t + h, 1), 0)
        adjp = np.where(t + h + im > 0, t / np.where(t + h + im > 0, t + h + im, 1), 0)
        f1 = np.where(rec + adj > 0, 2 * rec * adj / np.where(rec + adj > 0, rec + adj, 1), 0)
        f1p = np.where(rec + adjp > 0, 2 * rec * adjp / np.where(rec + adjp > 0, rec + adjp, 1), 0)
        # F_beta with beta=2 (recall weighted 4:1 - the campaign's declared cost asymmetry:
        # a missed bug costs more than a false alarm). F1' contradicts that preference.
        f2 = np.where(4 * adj + rec > 0, 5 * rec * adj / np.where(4 * adj + rec > 0, 4 * adj + rec, 1), 0)
        f2p = np.where(4 * adjp + rec > 0, 5 * rec * adjp / np.where(4 * adjp + rec > 0, 4 * adjp + rec, 1), 0)
        return rec, adj, adjp, f1, f1p, f2, f2p

    def pt(X):
        t, d, h, im = float(X[:, 0].sum()), float(X[:, 1].sum()), float(X[:, 2].sum()), float(X[:, 3].sum())
        rec = t / d if d else 0
        adj = t / (t + h) if (t + h) else 0
        adjp = t / (t + h + im) if (t + h + im) else 0
        f1 = 2 * rec * adj / (rec + adj) if rec + adj else 0
        f1p = 2 * rec * adjp / (rec + adjp) if rec + adjp else 0
        f2 = 5 * rec * adj / (4 * adj + rec) if (4 * adj + rec) else 0
        f2p = 5 * rec * adjp / (4 * adjp + rec) if (4 * adjp + rec) else 0
        return rec, adj, adjp, f1, f1p, f2, f2p

    out = {}
    for variant in ("verified", "reachable", "full"):
        cells = {}
        for m in MODELS:
            for fw in FWS:
                for e in EFFS:
                    urls = [u for u in top6 if (m, fw, e, u) in sel]
                    if not urls:
                        continue
                    rows = np.array([[run_row(sel[(m, fw, e, u)], variant)[k] for k in ("tp", "den", "hal", "imp")] for u in urls], dtype=float)
                    n = len(rows)
                    idx = rng.integers(0, n, size=(B, n))
                    S = rows[idx]
                    rec, adj, adjp, f1, f1p, f2, f2p = vec(S)
                    p = pt(rows)
                    cells[f"{m}|{fw}|{e}"] = {
                        "n_pr": n, "TP": int(rows[:, 0].sum()), "den": int(rows[:, 1].sum()),
                        "recall": p[0], "adjP": p[1], "adjPp": p[2], "F1": p[3], "F1p": p[4],
                        "F2": p[5], "F2p": p[6],
                        "ci": {"recall": (float(p[0]), float(np.percentile(rec, 2.5)), float(np.percentile(rec, 97.5)), 1.0),
                               "F1": (float(p[3]), float(np.percentile(f1, 2.5)), float(np.percentile(f1, 97.5)), 1.0),
                               "F1p": (float(p[4]), float(np.percentile(f1p, 2.5)), float(np.percentile(f1p, 97.5)), 1.0),
                               "F2": (float(p[5]), float(np.percentile(f2, 2.5)), float(np.percentile(f2, 97.5)), 1.0),
                               "F2p": (float(p[6]), float(np.percentile(f2p, 2.5)), float(np.percentile(f2p, 97.5)), 1.0)},
                    }
        # pairs
        pairs = {}
        for m in MODELS:
            for e in EFFS:
                A, Bc = (m, "compound-realistic", e), (m, "metareview-realistic", e)
                urls = [u for u in top6 if (m, A[1], e, u) in sel and (m, Bc[1], e, u) in sel]
                if len(urls) < 2:
                    continue
                def R(cell):
                    return np.array([[run_row(sel[(cell[0], cell[1], cell[2], u)], variant)[k] for k in ("tp", "den", "hal", "imp")] for u in urls], dtype=float)
                Xa, Xb = R(A), R(Bc)
                n = len(urls)
                idx = rng.integers(0, n, size=(B, n))
                ra, _, _, f1a, f1pa, f2a, f2pa = vec(Xa[idx])
                rb, _, _, f1b, f1pb, f2b, f2pb = vec(Xb[idx])
                pa, pb = pt(Xa), pt(Xb)
                pairs[f"{m}|{e}"] = {"n_pr": n,
                    "dRecall": (float(pb[0] - pa[0]), float(np.percentile(rb - ra, 2.5)), float(np.percentile(rb - ra, 97.5))),
                    "dF1p": (float(pb[4] - pa[4]), float(np.percentile(f1pb - f1pa, 2.5)), float(np.percentile(f1pb - f1pa, 97.5))),
                    "dF2p": (float(pb[6] - pa[6]), float(np.percentile(f2pb - f2pa, 2.5)), float(np.percentile(f2pb - f2pa, 97.5)))}
        out[variant] = {"cells": cells, "pairs": pairs,
                        "totals": {"TP": sum(c["TP"] for c in cells.values()), "den": sum(c["den"] for c in cells.values())}}
    (VG / "DEFECT_METRICS.json").write_text(json.dumps(out, indent=1))

    L = ["# §10d — defect-level metrics (per-run matching at the individual-bug unit)", "",
         "Denominators are computed from the registry (see _final in analysis/verified_gold/DEFECT_REGISTRY.json): "
         "verified = 42 goldens + every D-verified defect; reachable = 42 + only those defects that some run "
         "actually reported (13 were audit-surfaced and no run ever reported them, so they cap recall for "
         "everyone); full = 42 + all registry defects. "
         "recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also nitpicks.", ""]
    for variant in ("verified", "reachable", "full"):
        L += [f"## variant: {variant}", "", "| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' |", "|---|---|---|---|---|---|---|"]
        for k, c in sorted(out[variant]["cells"].items(), key=lambda kv: -kv[1]["F1p"]):
            m, fw, e = k.split("|")
            L.append(f"| {m} · {fw} · {e} | {c['n_pr']} | {c['recall']:.3f} [{c['ci']['recall'][1]:.3f}, {c['ci']['recall'][2]:.3f}] "
                     f"| {c['adjP']:.3f} | {c['adjPp']:.3f} | {c['F1']:.3f} | {c['F1p']:.3f} | {c['F2']:.3f} | {c['F2p']:.3f} |")
        pos = sum(1 for v in out[variant]["pairs"].values() if v["dF1p"][1] > 0)
        _p = out[variant]['pairs']
        _p2 = sum(1 for v in _p.values() if v['dF2p'][1] > 0)
        L += ["", f"MRV-vs-CE on ΔF1': {pos}/{len(_p)} pairs resolve positive (CI lower bound > 0). "
                  f"On ΔF2' (our evaluator): {_p2}/{len(_p)}. Point estimates: "
                  f"{sum(1 for v in _p.values() if v['dF1p'][0] > 0)}/{len(_p)} positive on ΔF1', "
                  f"{sum(1 for v in _p.values() if v['dF2p'][0] > 0)}/{len(_p)} on ΔF2'.", ""]
    (VG / "DEFECT_METRICS.md").write_text("\n".join(L) + "\n")
    for variant in ("verified", "reachable", "full"):
        top = sorted(out[variant]["cells"].items(), key=lambda kv: -kv[1]["F1p"])[:5]
        print(f"[{variant}] top cells by F1':")
        for k, c in top:
            print(f"   {k:58s} recall {c['recall']:.3f} [{c['ci']['recall'][1]:.3f},{c['ci']['recall'][2]:.3f}] F1' {c['F1p']:.3f}")
        print(f"[{variant}] totals: TP {out[variant]['totals']['TP']} / den {out[variant]['totals']['den']}")


if __name__ == "__main__":
    main()
