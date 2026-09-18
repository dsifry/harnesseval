#!/usr/bin/env python3
"""Merge duplicate defect ids in the registry after an independent duplicate review.

Input: a JSON file with {"groups": [["4-D03","4-D04"], ...], "reason_map": {...}} — each group is a set
of defect ids that a reviewer judged to be the SAME underlying defect. The first id in a group is kept
(prefer the one with the richer evidence); the others are marked merged_duplicate_of and removed from
the defect universe (they would be a double count of the total gold).

Then re-runs the registry sync and the defect-level metrics.

Usage: .venv/bin/python tools/verified_gold_merge_defects.py --groups '{"groups":[["4-D03","4-D04"]]}'
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", default=None, help="JSON with a 'groups' list of defect-id lists")
    ap.add_argument("--file", default=None, help="or a path to such a JSON file")
    a = ap.parse_args()
    if not a.file and not a.groups:
        ap.error("pass --groups or --file")
    data = json.load(open(a.file)) if a.file else json.loads(a.groups)
    groups = data.get("groups") or []
    reasons = data.get("reasons") or {}

    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    by_id = {d["id"]: d for d in reg["defects"]}
    drop, log = set(), []
    for g in groups:
        keep = g[0]
        for other in g[1:]:
            if other in by_id and keep in by_id:
                drop.add(other)
                log.append({"kept": keep, "merged": other,
                            "reason": reasons.get(other) or reasons.get(f"{keep}|{other}") or
                                      "independent duplicate review: same underlying defect",
                            "kept_label": by_id[keep]["label"], "merged_label": by_id[other]["label"]})
    reg["defects"] = [d for d in reg["defects"] if d["id"] not in drop]
    reg.setdefault("merged_duplicates", []).extend(log)
    json.dump(reg, open(VG / "DEFECT_REGISTRY.json", "w"), indent=1)
    print(f"merged {len(drop)} duplicate defect(s) away; registry now has {len(reg['defects'])}")
    for l in log:
        print(f"  {l['merged']} -> {l['kept']}: {l['reason'][:100]}")
    subprocess.run([sys.executable, str(ROOT / "tools/verified_gold_registry_sync.py")], check=False)
    subprocess.run([sys.executable, str(ROOT / "tools/verified_gold_defect_metrics.py")], check=False)


if __name__ == "__main__":
    main()
