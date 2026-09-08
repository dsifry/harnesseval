#!/usr/bin/env python3
"""Quick directional comparison: new mrv 0.11.0 cell vs old mrv baseline vs ce, same cell.

Usage: .venv/bin/python analysis/quick_compare.py [--rj]   # --rj: include readjudication3 v3 counts
Baseline sources: batch 20260906-glm53-top6 (old mrv low = v2-adjudicated; ce low).
New: batch 20260908-mrv011-glm53-low (adapter with Runtime-reliability + binary v0.11.0).
"""
import json, glob, os, sys, collections

NEW_BATCH = "20260908-mrv011-glm53-low"
OLD_BATCH = "20260906-glm53-top6"
MODEL, EFFORT = "glm-5.3-background", "low"

def runs_in(batch, framework):
    out = {}
    for mf in glob.glob("runs/*/manifest.json"):
        try: m = json.load(open(mf))
        except Exception: continue
        if m.get("run_batch") != batch or m.get("framework") != framework: continue
        if m.get("model") != MODEL or m.get("status") != "pass": continue
        # GLM: manifest effort low==report low
        if m.get("effort") != EFFORT: continue
        d = os.path.dirname(mf)
        try:
            s = json.load(open(os.path.join(d, "summary.json")))
        except Exception: continue
        if s.get("url"): out[s["url"]] = (d, s, m)
    return out

def cell_stats(runs, use_rj):
    n = len(runs)
    if not n: return None
    rec = hid = hal = find = 0
    for url, (d, s, m) in runs.items():
        gm = [x for x in s.get("per_golden_matches", []) if x.get("matched_candidate")]
        rec += len(gm) / max(1, s.get("n_golden", 1))
        find += s.get("n_findings", 0)
        rj = os.path.join(d, "readjudication3.json")
        if use_rj and os.path.exists(rj):
            try:
                c = json.load(open(rj))["corrected"]
                hid += c.get("n_bug_ungold", 0); hal += c.get("n_true_hallucination", 0)
                continue
            except Exception: pass
        hid += s.get("n_real_ungold", 0); hal += s.get("n_hallucination", 0)
    return dict(n=n, rec=rec/n, findings=find/n, hid=hid/n, hal=hal/n)

def main():
    use_rj = "--rj" in sys.argv
    new = runs_in(NEW_BATCH, "metareview-realistic")
    old = runs_in(OLD_BATCH, "metareview-realistic")
    ce  = runs_in(OLD_BATCH, "compound-realistic")
    rows = [("mrv 0.11.0 (new, this run)", new), ("mrv 0.10.1 baseline (same cell)", old),
            ("ce baseline (same cell)", ce)]
    print(f"cell: {MODEL} x {EFFORT}   (rj={'v3 readjudication' if use_rj else 'run-time adjudication'})")
    print(f"{'':32s} {'n':>3s} {'rec':>5s} {'find/PR':>8s} {'hid/PR':>7s} {'hal/PR':>7s}")
    for name, runs in rows:
        st = cell_stats(runs, use_rj)
        if not st: print(f"{name:32s}  (no runs yet)"); continue
        print(f"{name:32s} {st['n']:3d} {st['rec']:5.2f} {st['findings']:8.1f} {st['hid']:7.1f} {st['hal']:7.1f}")

    # acceptance findings checklist (textual presence in the new runs' findings)
    CHECKS = [
        ("1 destroyRecord no .catch", ["destroyrecord", ".catch"]),
        ("2 port saved/stripped on lookup", ["port"]),
        ("3 cmd_tuples dead guard", ["cmd_tuples"]),
        ("4 pagination race / offset", ["offset", "race"]),
        ("5 silent partial success usernames", ["username"]),
        ("6 sync-mode schema mismatch", ["sync", "schema"]),
        ("7 routes without actions", ["resource", "action"]),
        ("8 Office365 interface mismatch", ["office365", "updateevent"]),
    ]
    print("\nacceptance-finding presence (textual, any of the new runs):")
    texts = []
    for url, (d, s, m) in new.items():
        texts += [f["issue_text"] for f in s.get("findings", [])]
    low = " || ".join(texts).lower()
    for name, kws in CHECKS:
        hit = any(k.lower() in low for k in kws)
        print(f"  [{'x' if hit else ' '}] {name}")

if __name__ == "__main__":
    main()
