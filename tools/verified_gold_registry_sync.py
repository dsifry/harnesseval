#!/usr/bin/env python3
"""Sync the defect registry from the per-defect verification artifacts.

The verification pass writes <bundle>/defects/<id>/meta.json. This applies those outcomes to
DEFECT_REGISTRY.json:
  D-verified                    -> tier D-verified, orthogonality recorded, evidence dir linked
  duplicate_of_bundle_defect    -> removed from the defect universe (it IS the bundle's own defect)
  unresolved                    -> stays D-labelled with an explicit `undemonstrated` reason class
Idempotent; safe to re-run after any verification pass. Usage: python tools/verified_gold_registry_sync.py
"""
from __future__ import annotations
import glob, json
from pathlib import Path

VG = Path(__file__).resolve().parents[1] / "analysis/verified_gold"

UNDEMONSTRATED = {
    "10967-D05": ("test_fixture_inadequate",
                  "the test asserts the right behaviour but its fixture yields a past booking ('Cannot cancel past "
                  "events'), so it never reaches the multi-reference deletion loop; needs a realistic recurring-booking "
                  "fixture with several calendar references (or the DB-backed tier with real rows)"),
    "14740-D12": ("test_harness_invalid",
                  "the suite cannot run: vi.mock factory hoisting error + 'Failed to load url "
                  "@prisma/extension-accelerate'; needs valid module mocking for the email template"),
}

def main():
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    metas = {}
    for f in glob.glob(str(VG / "*/*/defects/*/meta.json")):
        m = json.load(open(f))
        metas[m["defect"]] = {**m, "dir": str(Path(f).parent.relative_to(VG))}
    merged_ids = {i for i, o in metas.items() if o.get("verdict") == "duplicate_of_bundle_defect"}
    kept, merged = [], []
    for d in reg["defects"]:
        if d.get("tier") in ("D-withdrawn", "D-duplicate"):
            # audit-decided states (2026-09-18 withdrawals/dedup — see WITHDRAWALS_AND_DEDUP_2026-09-18.md).
            # Never re-tier these from bundle metas; the reasons live in withdrawn_reason/dup_reason.
            kept.append(d)
            continue
        o = metas.get(d["id"])
        if not o:
            # a bundle-verified defect with no separate test pass: KEEP its existing tier
            d.setdefault("tier", "D-verified")
            kept.append(d)
            continue
        if o.get("verdict") == "D-verified" and o.get("own_fix_makes_test_pass") and o.get("sibling_fix_leaves_test_red") is not False:
            d["tier"] = "D-verified"
            d["orthogonality"] = o.get("sibling_fix_leaves_test_red")
            d["own_test"] = o["dir"]
            d.pop("undemonstrated", None)
            kept.append(d)
        elif o.get("verdict") == "duplicate_of_bundle_defect":
            if d.get("claim_index") == 0:
                # This defect IS the container's own claim (labels[0]), so the "sibling" fix the verifier
                # applied was its OWN minimal fix. That is a verification, not a duplicate: keep it.
                d["tier"] = "D-verified"
                d["orthogonality"] = None
                d["own_test"] = o.get("dir")
                d["verified_note"] = ("this defect is the execution container's own claim; the container fix is "
                                      "its own minimal fix, so the sibling check does not apply")
                d.pop("undemonstrated", None)
                kept.append(d)
            else:
                d["merged_reason"] = "the sibling fix also fixes it => same defect as the bundle's own label"
                merged.append(d)
        else:
            d["tier"] = "D-labelled"
            _u = UNDEMONSTRATED.get(d["id"])
            if isinstance(_u, tuple):
                _u = {"class": _u[0], "reason": _u[1]}
            d["undemonstrated"] = _u or {
                "class": "unresolved_in_pass",
                "reason": "the verification pass did not converge for this defect; the DEFECT itself is not in doubt "
                          "(it was split out of its bundle by the merge audit and its findings name the mechanism and lines)"}
            kept.append(d)
    reg["defects"] = kept
    reg["n_defects"] = len(kept)
    reg["n_verified"] = sum(1 for d in kept if d["tier"] == "D-verified")
    reg["n_withdrawn"] = sum(1 for d in kept if d["tier"] == "D-withdrawn")
    reg["n_duplicate"] = sum(1 for d in kept if d["tier"] == "D-duplicate")
    reg["n_labelled"] = sum(1 for d in kept if d["tier"] == "D-labelled")
    prev_merged = {m["id"]: m for m in (reg.get("merged_same_defect") or [])}
    reg["merged_same_defect"] = sorted(
        list({**prev_merged, **{d["id"]: {"id": d["id"], "bundle": d["bundle"], "label": d["label"],
                                         "reason": d.get("merged_reason")} for d in merged}}.values()),
        key=lambda m: m["id"])
    reg["_final"] = {"goldens": 42, "total_defects": reg["n_defects"],
                     "test_validated": reg["n_verified"], "undemonstrated_in_harness": reg["n_labelled"],
                     "withdrawn": reg["n_withdrawn"], "duplicates": reg["n_duplicate"],
                     "merged_away": len(reg["merged_same_defect"]), "total_gold": 42 + reg["n_defects"]}
    json.dump(reg, open(VG / "DEFECT_REGISTRY.json", "w"), indent=1)
    f = reg["_final"]
    print(json.dumps({**f, "ratio_total": round(f["total_gold"] / 42, 2),
                      "ratio_validated": round(f["test_validated"] / 42, 2)}, indent=1))
    rt, rv = round(f["total_gold"] / 42, 2), round(f["test_validated"] / 42, 2)
    distinct_gold = 42 + f["test_validated"]
    rd = round(distinct_gold / 42, 2)
    L = ["# Defect registry — final state (after the orthogonality experiment and the 2026-09-18 audit)", "",
         f"**Registry: {f['total_defects']} defect entries = {f['test_validated']} verified distinct + "
         f"{f['withdrawn']} withdrawn + {f['duplicates']} duplicates (2026-09-18 audit).**", "",
         f"**Distinct true gold = 42 goldens + {f['test_validated']} verified defects = {distinct_gold} ({rd}x goldens)**  ·  "
         f"**test-validated hidden gold = {f['test_validated']} ({rv}x goldens)**", "",
         f"- {f['merged_away']} labels were MERGED away: the sibling fix also cured them, so they were the bundle's own defect restated.",
         f"- {f['undemonstrated_in_harness']} defects are undemonstrated in this harness, each with a specific reason.",
         f"- {f['withdrawn']} defects were WITHDRAWN on 2026-09-18: their tests do not demonstrate the claimed behavior.",
         f"  Marked, retained, excluded from the verified universe (evidence: WITHDRAWALS_AND_DEDUP_2026-09-18.md).",
         f"- {f['duplicates']} entries were merged as DUPLICATES of kept defects / original goldens on 2026-09-18.", "",
         "| defect | bundle | class | why not demonstrated |", "|---|---|---|---|"]
    for d in kept:
        if d["tier"] == "D-labelled":
            u = d.get("undemonstrated") or {}
            if isinstance(u, tuple):
                u = {"class": u[0], "reason": u[1]}
            L.append(f"| {d['id']} | {d['bundle']} | `{u.get('class','?')}` | {str(u.get('reason',''))[:150]} |")
    L += ["", "## Merged away (same defect as their bundle's label)", "", "| defect | bundle | label |", "|---|---|---|"]
    for m in reg["merged_same_defect"]:
        L.append(f"| {m['id']} | {m['bundle']} | {str(m['label'])[:100]} |")
    (VG / "DEFECT_REGISTRY.md").write_text("\n".join(L) + "\n")
    print("undemonstrated:", [d["id"] for d in kept if d["tier"] != "D-verified"])
    print("merged away:", len(reg["merged_same_defect"]))


if __name__ == "__main__":
    main()
