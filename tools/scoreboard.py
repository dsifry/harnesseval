#!/usr/bin/env python
"""Campaign scoreboard: per-cell recall, adjusted precision, and F1(adjP, recall).

Reads run summaries plus their readjudication3.json verdicts (rj3 output).
  recall = TP / (TP + FN)                       (frozen golden matcher)
  adjP   = TP / (TP + hallucinations)           (rj3-corrected precision)
  F1     = 2 * recall * adjP / (recall + adjP)  (harmonic mean of the honest pair)
  beyond-gold = rj3 verdicts of bug + important_non_bug (real findings outside gold)

Usage: tools/scoreboard.py --batch B [--model M] [--rj-since "YYYY-MM-DD HH:MM"]
By default a run's rj3 file is used regardless of age; --rj-since restricts to
rj3 files written after a cutoff (to snapshot one readjudication pass).
"""
import argparse, json, glob, os, time
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--batch", required=True)
ap.add_argument("--model", default=None)
ap.add_argument("--rj-since", default=None, help="only use readjudication3.json newer than this, e.g. '2026-09-11 21:50'")
args = ap.parse_args()

cutoff = time.mktime(time.strptime(args.rj_since, "%Y-%m-%d %H:%M")) if args.rj_since else 0

cells = defaultdict(lambda: {"runs": 0, "tp": 0, "fn": 0, "fp": 0, "hal": 0, "real": 0})
for f in glob.glob("runs/*/summary.json"):
    try:
        s = json.load(open(f))
    except Exception:
        continue
    if s.get("run_batch") != args.batch or not s.get("url"):
        continue
    if args.model and s.get("model") != args.model:
        continue
    rid = f.split("/")[1]
    rj_path = f"runs/{rid}/readjudication3.json"
    if not os.path.exists(rj_path) or os.path.getmtime(rj_path) < cutoff:
        continue
    try:
        rj = json.load(open(rj_path))
    except Exception:
        continue
    key = (s.get("framework", "?"), s.get("model", "?"), s.get("effort"))
    c = cells[key]
    c["runs"] += 1
    c["tp"] += s.get("tp", 0) or 0
    c["fn"] += s.get("fn", 0) or 0
    c["fp"] += s.get("fp", 0) or 0
    for r in (rj.get("records") or rj.get("corrected") or []):
        v = (r.get("new_verdict") or "").lower()
        if v == "hallucination":
            c["hal"] += 1
        elif v in ("bug", "important_non_bug"):
            c["real"] += 1

hdr = f"{'framework':<22} {'model':<24} {'eff':<7} {'runs':>4} {'TP':>4} {'FN':>4} {'rec':>5} {'adjP':>5} {'F1':>5} {'hal':>4} {'beyond':>6}"
print(hdr)
print("-" * len(hdr))
tot = defaultdict(int)
for k in sorted(cells):
    c = cells[k]
    rec = c["tp"] / max(1, c["tp"] + c["fn"])
    adjp = c["tp"] / max(1, c["tp"] + c["hal"])
    f1 = 2 * rec * adjp / max(1e-9, rec + adjp)
    print(f"{k[0]:<22} {k[1]:<24} {k[2]:<7} {c['runs']:>4} {c['tp']:>4} {c['fn']:>4} {rec:>5.2f} {adjp:>5.2f} {f1:>5.2f} {c['hal']:>4} {c['real']:>6}")
    for f in ("runs", "tp", "fn", "hal", "real"):
        tot[f] += c[f]
rec = tot["tp"] / max(1, tot["tp"] + tot["fn"])
adjp = tot["tp"] / max(1, tot["tp"] + tot["hal"])
f1 = 2 * rec * adjp / max(1e-9, rec + adjp)
print("-" * len(hdr))
print(f"{'TOTAL':<54} {tot['runs']:>4} {tot['tp']:>4} {tot['fn']:>4} {rec:>5.2f} {adjp:>5.2f} {f1:>5.2f} {tot['hal']:>4} {tot['real']:>6}")
