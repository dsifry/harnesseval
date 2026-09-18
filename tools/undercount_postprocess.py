#!/usr/bin/env python3
"""Post-process the under-count candidates after the defect verifier runs.

The verifier's orthogonality step asks: "does the container's fix also cure this candidate?" For a candidate
that IS the container's own claim (labels[0]) the container's fix is its OWN fix, so that check is
meaningless and its MERGED verdict must be reclassified as verified. For a candidate that is a genuinely
secondary claim, MERGED is a real duplicate and is merged into the container's primary defect.

Idempotent; run any number of times.
"""
from __future__ import annotations
import glob, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"


def toks(x): return set(re.findall(r"[a-z0-9]+", x.lower()))
def jac(a, b): return len(toks(a) & toks(b)) / max(1, len(toks(a) | toks(b)))


def main():
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    by_id = {d["id"]: d for d in reg["defects"]}
    to_merge, reclassified, still = [], [], []
    for d in reg["defects"]:
        if d.get("tier") != "D-labelled":
            continue
        mv = glob.glob(str(VG / "**" / "defects" / d["id"] / "meta.json"), recursive=True)
        if not mv:
            still.append((d["id"], "no meta yet")); continue
        m = json.load(open(mv[0]))
        v = m.get("verdict")
        if v == "D-verified":
            continue
        if v == "duplicate_of_bundle_defect":
            cm = json.load(open(Path(d["evidence_dir"]) / "meta.json"))
            labels = (cm.get("multi_defect") or {}).get("labels") or []
            # authoritative: the audit claim index this candidate was created from (0 = the container's own claim)
            if d.get("claim_index") == 0:
                # this candidate IS the container's own claim -> the container fix is its own fix
                m["verdict"] = "D-verified"
                m["sibling_fix_leaves_test_red"] = None
                m["note"] = ("reclassified: this defect IS the container's own claim (labels[0]), so the "
                             "container's fix is its own minimal fix; the sibling check does not apply")
                json.dump(m, open(mv[0], "w"), indent=1)
                reclassified.append((d["id"], labels[0][:70]))
                continue
            prim = max([x for x in reg["defects"] if x["bundle"] == d["bundle"] and x["pr"] == d["pr"]],
                       key=lambda x: jac(x["label"], labels[0]) if labels else 0)
            if prim["id"] != d["id"]:
                to_merge.append((d["id"], prim["id"], prim["label"][:80]))
                continue
        still.append((d["id"], v))
    print("reclassified as verified (own-claim candidates):")
    for i, l in reclassified: print(f"   {i}  <- {l}")
    print("genuine duplicates to merge:")
    for a, b, l in to_merge: print(f"   {a} -> {b}  ({l})")
    print("still pending/unresolved:", still)
    if to_merge:
        groups = {"groups": [[b, a] for a, b, _ in to_merge],
                  "reasons": {a: f"the container's fix also cures this candidate's test -> same defect as {b}"
                              for a, b, _ in to_merge}}
        Path("/tmp/undercount_merges.json").write_text(json.dumps(groups))
        subprocess.run([sys.executable, str(ROOT / "tools/verified_gold_merge_defects.py"),
                        "--file", "/tmp/undercount_merges.json"], check=False)


if __name__ == "__main__":
    main()
