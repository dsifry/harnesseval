#!/usr/bin/env python3
"""§10d — per-cell metrics computed at the DEFECT level (not the bundle level).

Inputs: DEFECT_REGISTRY.json (tiered defects), DEFECT_ASSIGN.json (finding -> defect id),
analysis/final_report_dataset.json (runs), analysis/final_report_metrics.json (golden counts).

For each selected run:
  defects hit       = distinct defect ids among its findings (from the assignment map)
  tp                = golden TP (official matcher) + defects hit
  denominator (PR)  = goldens(PR) + defects(PR)
Variants retain the frozen defect universes. Legacy adjP/adjP' and bug-only F2
retain their original judgments. F2' uses accepted advisory credit and unsupported
finding penalties from the common re-adjudication, excluding verified bug hits.

Writes analysis/verified_gold/DEFECT_METRICS.{json,md}. CIs: cluster bootstrap B=10000, seed 20260916,
rng = SEED+5 (a fresh stream; nothing frozen is touched).

Usage: .venv/bin/python tools/verified_gold_defect_metrics.py
"""
from __future__ import annotations
import glob, hashlib, json
from collections import defaultdict
from pathlib import Path

import numpy as np
from report_quality import advisory_f2, SENSITIVITY_WEIGHTS
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readjudicate3 import normalize_for_cluster
from tools.advisory_scoring_policy import advisory_evidence

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"
SEED = 20260916
B = 10000


def sha(t):
    return hashlib.sha1(t.encode()).hexdigest()[:16]


def scored_advisory_counts(evidence, assignments, admitted_bug_ids):
    """Apply the selected bug universe before counting non-bug outcomes."""
    counts = dict(advisories=0, penalties=0, below_threshold=0, uncredited_bugs=0)
    fields = {"accepted": "advisories", "penalty": "penalties", "unresolved": "below_threshold", "below_scoring_threshold": "below_threshold",
              "excluded_bug": "uncredited_bugs"}
    for group in evidence["records"]:
        ids = {assignments.get(sha(normalize_for_cluster(src["issue_text"]))) for src in group["sources"]}
        if ids & admitted_bug_ids:
            continue
        field = fields.get(group["decision"])
        if field:
            counts[field] += 1
    counts["unresolved"] = counts["below_threshold"]  # Legacy schema alias, not processing status.
    return counts


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
    # Defects that at least one finding anywhere was assigned to, restricted to the D-verified universe.
    # (Post-2026-09-18 audit: withdrawn/duplicate tiers must never inflate a denominator or a credit --
    #  see analysis/verified_gold/WITHDRAWALS_AND_DEDUP_2026-09-18.md. The never-reported count below is
    #  computed dynamically; it is no longer the historical "13".)
    reported_ids = {d for _pr, m in assign.items() for _h, d in m.items()
                    if d in valid_ids and tier.get(d) == "D-verified"}
    n_never_reported = sum(1 for i in valid_ids if tier.get(i) == "D-verified" and i not in reported_ids)

    sel = {(r["model"], r["framework"], r["effort"], r["url"]): r for r in D["selected_runs"]}
    try:
        M = json.load(open(ROOT / "analysis/final_report_metrics.json"))
    except FileNotFoundError:
        M = {}
    MODELS = M["mods"] if "mods" in M else sorted({r["model"] for r in D["selected_runs"]})
    FWS = ["vanilla-engineered", "compound-realistic", "metareview-realistic"]
    EFFS = ["low", "medium", "high"]
    rng = np.random.default_rng(SEED + 5)

    def eff_instrument(r):
        """Where this run's hal/imp counts actually come from: the v3.1 re-adjudication when present,
        else the in-run adjudicator. 'v1' means the binary instrument with NO important_non_bug
        category, so a nitpick count of 0 from a v1 run is structurally unmeasured, not observed."""
        return "rj3" if r.get("rj3") else (r.get("inrun") or {}).get("instrument") or "unknown"

    grid_runs = [r for r in D["selected_runs"] if r["url"] in top6 and r["model"] in MODELS and r["framework"] in FWS and r["effort"] in EFFS]
    evidence = {r["run_id"]: advisory_evidence(ROOT, r) for r in grid_runs}
    pending = [rid for rid, ev in evidence.items() if ev.get("advisory_run_status") == "pending"]
    if pending:
        raise RuntimeError(f"Advisory scoring evidence not ready for {len(pending)} selected reviews (base export or policy-specific deduplication pending); refusing mixed/zero-filled scoring")
    # A finding credited to a verified defect cannot also earn an advisory bonus.
    # Apply the frozen bug assignment, independent of any later classifier label.
    for r in grid_runs:
        ev = evidence[r["run_id"]]
        amap = assign.get(slug[r["url"]], {})
        for group in ev["records"]:
            ids = {amap.get(sha(normalize_for_cluster(src["issue_text"]))) for src in group["sources"]}
            verified = sorted(d for d in ids if d and tier.get(d)=="D-verified")
            if verified:
                group["verified_bug_ids"] = verified
            if verified and group["decision"] in ("accepted", "penalty", "unresolved", "below_scoring_threshold"):
                group["classifier_decision_before_bug_guard"] = group["decision"]
                group["decision"] = "excluded_verified_bug"
        ev["accepted_count"] = sum(g["decision"]=="accepted" for g in ev["records"])
        ev["penalty_count"] = sum(g["decision"]=="penalty" for g in ev["records"])
        ev["below_threshold_count"] = sum(g["decision"] in ("unresolved", "below_scoring_threshold") for g in ev["records"])
        ev["unresolved_count"] = ev["below_threshold_count"]  # Legacy alias.
        ev["uncredited_bug_count"] = sum(g["decision"]=="excluded_bug" and not g.get("verified_bug_ids") for g in ev["records"])

    def run_row(r, variant):
        pr = slug.get(r["url"], r["url"].rstrip("/").split("/")[-1])
        amap = assign.get(pr, {})
        own = set()
        for t in (r.get("bugtexts") or []):
            did = amap.get(sha(t))
            if not did or did not in valid_ids:      # merged-away defects no longer count
                continue
            if variant == "verified" and tier.get(did) != "D-verified":
                continue            # withdrawn (2026-09-18 audit) and duplicate-tier defects are never credited
            if variant == "reachable" and did not in reported_ids:
                continue
            own.add(did)
        tot = len(by_pr_defects.get(pr, []))
        if variant == "verified":
            tot = sum(1 for d in by_pr_defects.get(pr, []) if d["tier"] == "D-verified")
        elif variant == "reachable":
            tot = sum(1 for d in by_pr_defects.get(pr, []) if d["id"] in reported_ids)
        v = r["rj3"] or r["inrun"]
        ev = evidence[r["run_id"]]
        admitted = valid_ids if variant == "full" else {d for d in valid_ids if tier.get(d) == "D-verified"}
        return {"tp": r["tp"] + len(own), "den": goldens[pr] + tot, "hal": v["hal"], "imp": v["imp"],
                **scored_advisory_counts(ev, amap, admitted)}

    def vec(S):
        t, d, h, im = S[:, :, 0].sum(axis=1), S[:, :, 1].sum(axis=1), S[:, :, 2].sum(axis=1), S[:, :, 3].sum(axis=1)
        rec = np.where(d > 0, t / np.where(d > 0, d, 1), 0)
        adj = np.where(t + h > 0, t / np.where(t + h > 0, t + h, 1), 0)
        adjp = np.where(t + h + im > 0, t / np.where(t + h + im > 0, t + h + im, 1), 0)
        f1 = np.where(rec + adj > 0, 2 * rec * adj / np.where(rec + adj > 0, rec + adj, 1), 0)
        f1p = np.where(rec + adjp > 0, 2 * rec * adjp / np.where(rec + adjp > 0, rec + adjp, 1), 0)
        # F2 remains bug-only. F2p adds independently classified useful-advisory credit.
        f2 = np.where(4 * adj + rec > 0, 5 * rec * adj / np.where(4 * adj + rec > 0, 4 * adj + rec, 1), 0)
        f2p = advisory_f2(t, d, S[:, :, 4].sum(axis=1), S[:, :, 5].sum(axis=1))
        return rec, adj, adjp, f1, f1p, f2, f2p

    def pt(X):
        t, d, h, im = float(X[:, 0].sum()), float(X[:, 1].sum()), float(X[:, 2].sum()), float(X[:, 3].sum())
        rec = t / d if d else 0
        adj = t / (t + h) if (t + h) else 0
        adjp = t / (t + h + im) if (t + h + im) else 0
        f1 = 2 * rec * adj / (rec + adj) if rec + adj else 0
        f1p = 2 * rec * adjp / (rec + adjp) if rec + adjp else 0
        f2 = 5 * rec * adj / (4 * adj + rec) if (4 * adj + rec) else 0
        f2p = float(advisory_f2(t, d, X[:, 4].sum(), X[:, 5].sum()))
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
                    run_infos = [run_row(sel[(m, fw, e, u)], variant) for u in urls]
                    rows = np.array([[info[k] for k in ("tp", "den", "hal", "imp", "advisories", "penalties")] for info in run_infos], dtype=float)
                    unresolved = sum(info["unresolved"] for info in run_infos)
                    insts = sorted({eff_instrument(sel[(m, fw, e, u)]) for u in urls})
                    n = len(rows)
                    idx = rng.integers(0, n, size=(B, n))
                    S = rows[idx]
                    rec, adj, adjp, f1, f1p, f2, f2p = vec(S)
                    p = pt(rows)
                    adv_rows = [evidence[sel[(m, fw, e, u)]["run_id"]] for u in urls]
                    legacy_draws = 5*S[:,:,0].sum(axis=1)/(4*S[:,:,1].sum(axis=1)+S[:,:,0].sum(axis=1)+S[:,:,2].sum(axis=1)+S[:,:,3].sum(axis=1))
                    legacy = 5*rows[:,0].sum()/(4*rows[:,1].sum()+rows[:,0].sum()+rows[:,2].sum()+rows[:,3].sum())
                    sensitivity = {}
                    for weight in SENSITIVITY_WEIGHTS:
                        draws = advisory_f2(S[:,:,0].sum(axis=1), S[:,:,1].sum(axis=1), S[:,:,4].sum(axis=1), S[:,:,5].sum(axis=1), weight)
                        sensitivity[str(weight)] = [float(advisory_f2(rows[:,0].sum(), rows[:,1].sum(), rows[:,4].sum(), rows[:,5].sum(), weight)), float(np.percentile(draws,2.5)), float(np.percentile(draws,97.5))]
                    common_without_bonus = float(advisory_f2(rows[:,0].sum(), rows[:,1].sum(), 0, rows[:,5].sum()))
                    cells[f"{m}|{fw}|{e}"] = {
                        "advisory_count": int(rows[:,4].sum()), "penalty_count": int(rows[:,5].sum()),
                        "advisory_measured": all(ev["measured"] for ev in adv_rows),
                        "advisory_instruments": sorted({ev.get("advisory_instrument") or ev.get("instrument", "saved-original-or-rj3") for ev in adv_rows}),
                        "advisory_below_threshold": unresolved,
                        "advisory_unresolved": unresolved,  # Legacy alias.
                        "advisory_uncredited_bugs": sum(info["uncredited_bugs"] for info in run_infos),
                        "F2p_legacy": float(legacy), "F2p_sensitivity": sensitivity,
                        "F2p_without_advisory_bonus": common_without_bonus,
                        "F2p_advisory_bonus_lift": float(p[6]) - common_without_bonus,
                        "F2p_unresolved_bounds": [float(advisory_f2(rows[:,0].sum(), rows[:,1].sum(), rows[:,4].sum(), rows[:,5].sum()+unresolved)), float(advisory_f2(rows[:,0].sum(), rows[:,1].sum(), rows[:,4].sum()+unresolved, rows[:,5].sum()))],
                        "per_pr": [{"url": u, "counts": rows[i].tolist(), "advisory_measured": adv_rows[i]["measured"], "below_threshold": run_infos[i]["below_threshold"], "unresolved": run_infos[i]["unresolved"], "uncredited_bugs": run_infos[i]["uncredited_bugs"]} for i,u in enumerate(urls)],
                        "n_pr": n, "TP": int(rows[:, 0].sum()), "den": int(rows[:, 1].sum()),
                        "recall": p[0], "adjP": p[1], "adjPp": p[2], "F1": p[3], "F1p": p[4],
                        "F2": p[5], "F2p": p[6], "instruments": insts,
                        "ci": {"recall": (float(p[0]), float(np.percentile(rec, 2.5)), float(np.percentile(rec, 97.5)), 1.0),
                               "F1": (float(p[3]), float(np.percentile(f1, 2.5)), float(np.percentile(f1, 97.5)), 1.0),
                               "F1p": (float(p[4]), float(np.percentile(f1p, 2.5)), float(np.percentile(f1p, 97.5)), 1.0),
                               "F2": (float(p[5]), float(np.percentile(f2, 2.5)), float(np.percentile(f2, 97.5)), 1.0),
                               "F2p_legacy": (float(legacy), float(np.percentile(legacy_draws,2.5)), float(np.percentile(legacy_draws,97.5)), 1.0),
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
                    return np.array([[run_row(sel[(cell[0], cell[1], cell[2], u)], variant)[k] for k in ("tp", "den", "hal", "imp", "advisories", "penalties")] for u in urls], dtype=float)
                Xa, Xb = R(A), R(Bc)
                n = len(urls)
                idx = rng.integers(0, n, size=(B, n))
                ra, _, _, f1a, f1pa, f2a, f2pa = vec(Xa[idx])
                rb, _, _, f1b, f1pb, f2b, f2pb = vec(Xb[idx])
                pa, pb = pt(Xa), pt(Xb)
                pairs[f"{m}|{e}"] = {"n_pr": n,
                    "dRecall": (float(pb[0] - pa[0]), float(np.percentile(rb - ra, 2.5)), float(np.percentile(rb - ra, 97.5))),
                    "dF1p": (float(pb[4] - pa[4]), float(np.percentile(f1pb - f1pa, 2.5)), float(np.percentile(f1pb - f1pa, 97.5))),
                    "advisory_measured": all(evidence[sel[(m, fw, e, u)]["run_id"]]["measured"] for fw in (A[1], Bc[1]) for u in urls),
                    "dF2p": (float(pb[6] - pa[6]), float(np.percentile(f2pb - f2pa, 2.5)), float(np.percentile(f2pb - f2pa, 97.5)))}
        out[variant] = {"cells": cells, "pairs": pairs,
                        "totals": {"TP": sum(c["TP"] for c in cells.values()), "den": sum(c["den"] for c in cells.values())}}
    (VG / "ADVISORY_EVIDENCE.json").write_text(json.dumps({"definition": "Accepted important_non_bug judgments supply advisory credit; hallucination judgments supply unsupported-finding penalties. The common top-six pass reuses audited verified-bug assignments and uses the existing readjudicate3 classifier for the remaining unmatched channels. The active pass is identified by advisory_readjudication/active_pass.json; its manifest freezes grouping, inputs and judge settings. The separately versioned active_scoring_policy.json selects advisory credit at confidence >= 0.70 and unsupported/style penalties at >= 0.80. Classified findings below the applicable scoring threshold receive neither credit nor penalty; raw categories and confidence are preserved. Advisory identities require policy-specific deduplication. Verified bug assignments take precedence, preventing double credit or contradictory penalties. Below-threshold classifications are reported separately. Historical JSON keys containing unresolved are compatibility aliases, not a processing status. The older advisory reference ceiling covers only PR4/10 of the current six and is not an advisory-recall denominator.", "weight": 1.0, "runs": evidence}, indent=1))
    (VG / "DEFECT_METRICS.json").write_text(json.dumps(out, indent=1))

    n_verified_now = sum(1 for d in reg['defects'] if d['tier'] == 'D-verified')
    L = ["# §10d — defect-level metrics (per-run matching at the individual-bug unit)", "",
         "Denominators are computed from the registry (see _final in analysis/verified_gold/DEFECT_REGISTRY.json): "
         f"verified = 42 goldens + every D-verified defect ({n_verified_now} after the 2026-09-18 "
         "withdrawal/dedup audit — 3 withdrawn, 2 merged; see WITHDRAWALS_AND_DEDUP_2026-09-18.md); "
         f"reachable = 42 + only those D-verified defects that some run actually reported ({n_never_reported} "
         f"verified defect{' is' if n_never_reported == 1 else 's are'} reported by no run and cap recall for everyone); "
         "full = 42 + all registry defects. The assignment map covers every finding (null = no clear match; see "
         "DEFECT_ASSIGN.md and DEFECT_ASSIGN_AUDIT.json). Legacy non-bug burden counts from cells whose instruments include "
         "'v1' are structurally unmeasured (the binary instrument has no important_non_bug category), not observed zeros. "
         "F2′=(5T+A)/(4D+T+A+H), with accepted advisory credit A and effective unsupported findings H. "
         "F2p_legacy retains the former penalty-based score. Missing advisory coverage makes F2′ incomplete. "
         "recall = (golden TP + distinct defects hit) / denominator; legacy adjP charges original hallucination judgments, and legacy adjP' also charges original important_non_bug judgments.", ""]
    for variant in ("verified", "reachable", "full"):
        L += [f"## variant: {variant}", "", "| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' | instruments |", "|---|---|---|---|---|---|---|---|---|---|"]
        for k, c in sorted(out[variant]["cells"].items(), key=lambda kv: -kv[1]["F1p"]):
            m, fw, e = k.split("|")
            L.append(f"| {m} · {fw} · {e} | {c['n_pr']} | {c['recall']:.3f} [{c['ci']['recall'][1]:.3f}, {c['ci']['recall'][2]:.3f}] "
                     f"| {c['adjP']:.3f} | {c['adjPp']:.3f} | {c['F1']:.3f} | {c['F1p']:.3f} | {c['F2']:.3f} | {c['F2p']:.3f} | {'/'.join(c.get('instruments') or [])} |")
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
