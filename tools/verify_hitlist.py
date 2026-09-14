#!/usr/bin/env python
"""Verify manifold_top6_hitlist.csv: for each (model, framework, effort, pr_url) row,
report whether a healthy run exists in the campaign batch. Usage:
  .venv/bin/python tools/verify_hitlist.py [--verbose]
Exit 0 if every row is done; else exit 1 and list what remains."""
import csv, json, glob, sys

have = set()
BATCHES = ("20260910-mrv0120-manifold", "20260906-fable51-vanilla-low", "20260906-fable51-vanilla-medhigh")
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    # ERA RULE (user, 2026-09-13): vanilla-engineered pairs accept healthy runs from ANY era
    # (no metareview binary involved); mrv/compound pairs require the current campaign batch
    # (pre-0.12 binaries are instrument-confounded).
    if s.get("framework") != "vanilla-engineered" and s.get("run_batch") not in BATCHES: continue
    tok = (s.get("tokens_in") or 0) + (s.get("tokens_out") or 0)
    if s.get("error") or tok == 0: continue
    n = len(s.get("findings", []))
    if not (n or tok <= 20000): continue
    have.add((s.get("model"), s.get("framework"), s.get("effort"), s.get("url")))

rows = list(csv.DictReader(open("manifold_top6_hitlist.csv")))
remaining = [r for r in rows if (r["model"], r["framework"], r["effort"], r["pr_url"]) not in have]
done = len(rows) - len(remaining)
print(f"hitlist: {len(rows)} rows — {done} done, {len(remaining)} remaining")
if "--verbose" in sys.argv or remaining:
    from collections import Counter
    c = Counter((r["model"], r["framework"], r["effort"], r["mode"]) for r in remaining)
    for (m, fw, ef, mode), n in sorted(c.items()):
        print(f"REMAINING {m} {fw} {ef} (mode={mode}): {n}")
sys.exit(1 if remaining else 0)
