#!/usr/bin/env python3
"""Post-pass: audit the base-run verdicts against the stored logs.

`defect_present_before_pr` means the test also failed at the pre-PR commit. That is only a sound
conclusion if it failed on the SAME asserted behaviour. A test authored against head APIs can fail
at base for unrelated reasons (renamed/absent symbol, TypeError, transform error) — those bundles
are `base_not_comparable`, not pre-existing defects.

This pass never deletes anything: it rewrites meta.json with the refined verdict and keeps the
previous verdict + the evidence line under meta["reclassified"].

Usage: .venv/bin/python tools/verified_gold_reclassify.py [--dry-run]
"""
from __future__ import annotations
import argparse, glob, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ASSERT = re.compile(r"AssertionError:.*?(expected .*?to be .*?)(?:\s*//|$)", re.S)
ERRTYPE = re.compile(r"\b(TypeError|ReferenceError|SyntaxError|Transform failed|Failed to load url|Cannot find module|is not a function|Cannot read propert)")


def sig(log: str):
    m = ASSERT.search(log)
    if m:
        return ("assert", re.sub(r"\s+", " ", m.group(1))[:160])
    m2 = ERRTYPE.search(log)
    if m2:
        return ("error", m2.group(1))
    if re.search(r"Test Files\s+1 passed", log):
        return ("pass", "")
    return ("other", "")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    changed = []
    for mf in sorted(glob.glob(str(ROOT / "analysis/verified_gold/*/B*/meta.json"))):
        meta = json.loads(Path(mf).read_text())
        v = meta.get("verdict")
        if v not in {"defect_present_before_pr", "confirmed_regression"}:
            continue
        b = Path(mf).parent / "logs"
        base = (b / "base.log").read_text() if (b / "base.log").exists() else ""
        head = (b / "head.log").read_text() if (b / "head.log").exists() else ""
        bs, hs = sig(base), sig(head)
        new = v
        if bs[0] == "error" and hs[0] == "assert":
            new = "base_not_comparable"          # base failed for an API/compile reason, not the claim
        elif bs[0] == "other" and hs[0] == "assert":
            new = "base_not_comparable"
        if new != v:
            meta["reclassified"] = {"from": v, "to": new,
                                    "base_signal": bs, "head_signal": hs,
                                    "reason": "base run failed for a different reason than the claimed behaviour"}
            meta["verdict"] = new
            if not a.dry_run:
                Path(mf).write_text(json.dumps(meta, indent=1))
            changed.append((meta.get("bug_id"), v, new))
    print(f"reclassified: {len(changed)}")
    for bid, old, new in changed:
        print(f"  {bid}: {old} -> {new}")
    if a.dry_run:
        print("(dry run — nothing written)")


if __name__ == "__main__":
    main()
