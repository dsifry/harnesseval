"""Definitive interaction analysis for batch 083 — tests two hypotheses:

H2a: harnesses (mrv/compound) always beat vanilla-engineered at the equivalent effort level.
H2b: harnesses often beat vanilla even at vanilla's HIGHER effort levels (harness-at-E vs vanilla-at-E+1).
H1:  the real wins are harness + cheap model + low effort (cost-efficiency frontier).

Aggregates the full 384-cell matrix (latest run per cell across v2 + 083 batches).
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/dsifry/Developer/harnesseval")
REG = ROOT / "runs" / "registry.jsonl"
FRAMEWORKS = ["vanilla-engineered", "metareview-realistic", "compound-realistic", "superpowers-realistic"]
MODELS = ["claude-opus-5", "gpt-5.6-sol", "claude-sonnet-5", "gpt-5.6-terra"]
EFFORTS = ["low", "medium", "high", "xhigh"]
EFF_RANK = {"low": 0, "medium": 1, "high": 2, "xhigh": 3}

# load latest run per (fw, model, effort, url) across both batches
latest = {}
for line in REG.read_text().splitlines():
    e = json.loads(line)
    if e.get("run_batch") not in ("20260825-batch-083-fullmatrix", "20260825-batch-082-v2-mrv-vanilla-opus-codex-48cells"):
        continue
    sp = e.get("summary_path")
    if not sp:
        continue
    try:
        s = json.load(open(sp))
    except Exception:
        continue
    key = (e["framework"], e["model"], e["effort"], s.get("url", ""))
    prev = latest.get(key)
    if prev is None or e.get("registered_at", "") >= prev.get("registered_at", ""):
        latest[key] = e

assert len(latest) == 384, f"expected 384 cells, got {len(latest)}"

# build per-cell aggregates: (fw, model, effort) -> {tp, fn, fp, hal, real, tok, n, per_pr: {pr: {tp,fn,...}}}
def cell_agg(fw, model, effort):
    b = {"tp": 0, "fn": 0, "fp": 0, "hal": 0, "real": 0, "tok": 0, "n": 0, "per_pr": {}}
    for (f, m, e, url), r in latest.items():
        if f == fw and m == model and e == effort and r["status"] == "pass":
            mt = r.get("metrics", {}) or {}
            pr = url.rstrip("/").rsplit("/", 1)[-1]
            b["tp"] += mt.get("tp", 0) or 0
            b["fn"] += mt.get("fn", 0) or 0
            b["fp"] += mt.get("fp", 0) or 0
            b["hal"] += mt.get("n_hallucination", 0) or 0
            b["real"] += mt.get("n_real_ungold", 0) or 0
            b["tok"] += (r.get("tokens_in", 0) or 0) + (r.get("tokens_out", 0) or 0)
            b["n"] += 1
            b["per_pr"][pr] = {"tp": mt.get("tp", 0) or 0, "fn": mt.get("fn", 0) or 0,
                               "fp": mt.get("fp", 0) or 0, "hal": mt.get("n_hallucination", 0) or 0,
                               "real": mt.get("n_real_ungold", 0) or 0}
    return b

def rec(b): return b["tp"] / (b["tp"] + b["fn"]) if (b["tp"] + b["fn"]) else 0
def adjp(b): return b["tp"] / (b["tp"] + b["hal"]) if (b["tp"] + b["hal"]) else 0
def incr(b): return (b["tp"] + b["real"]) / (b["tp"] + b["fn"] + b["real"]) if (b["tp"] + b["fn"] + b["real"]) else 0

# precompute all 64 cells
CELL = {(fw, m, e): cell_agg(fw, m, e) for fw in FRAMEWORKS for m in MODELS for e in EFFORTS}

print("=" * 90)
print("ANALYSIS 1: Full framework × model × effort grid (64 cells, pooled over 6 PRs each)")
print("=" * 90)
print(f"{'fw':22s} {'model':16s} {'eff':6s} {'rec':>5} {'adj_p':>6} {'incr_r':>6} {'hidGold':>7} {'hal':>5} {'tok(M)':>8}")
for fw in FRAMEWORKS:
    for m in MODELS:
        for e in EFFORTS:
            b = CELL[(fw, m, e)]
            if b["n"] == 0: continue
            print(f"{fw:22s} {m:16s} {e:6s} {rec(b):5.2f} {adjp(b):6.2f} {incr(b):6.2f} {b['real']:>7} {b['hal']:>5} {b['tok']/1e6:8.1f}")

print()
print("=" * 90)
print("ANALYSIS 2 (H2a): Harness vs vanilla at EQUIVALENT effort — per (model × effort) aggregate")
print("  For each (model, effort): does harness recall/hidden-gold/incr_r beat vanilla? (pooled over 6 PRs)")
print("=" * 90)
print(f"{'model':16s} {'eff':6s} | {'van rec':>7} {'mrv rec':>7} {'cmp rec':>7} | {'van hid':>7} {'mrv hid':>7} {'cmp hid':>7} | {'mrv>van':>7} {'cmp>van':>7}")
h2a_mrv_wins = 0; h2a_cmp_wins = 0; h2a_total = 0
for m in MODELS:
    for e in EFFORTS:
        v = CELL[("vanilla-engineered", m, e)]
        mr = CELL[("metareview-realistic", m, e)]
        cp = CELL[("compound-realistic", m, e)]
        mrv_beats = rec(mr) > rec(v)
        cmp_beats = rec(cp) > rec(v)
        h2a_total += 1
        h2a_mrv_wins += mrv_beats
        h2a_cmp_wins += cmp_beats
        flag_m = "✓" if mrv_beats else "✗"
        flag_c = "✓" if cmp_beats else "✗"
        print(f"{m:16s} {e:6s} | {rec(v):7.2f} {rec(mr):7.2f} {rec(cp):7.2f} | {v['real']:>7} {mr['real']:>7} {cp['real']:>7} | {flag_m:>7} {flag_c:>7}")
print(f"\n→ mrv beats vanilla on recall in {h2a_mrv_wins}/{h2a_total} (model×effort) cells")
print(f"→ compound beats vanilla on recall in {h2a_cmp_wins}/{h2a_total} (model×effort) cells")

print()
print("=" * 90)
print("ANALYSIS 3 (H2a strict): PR-PAIRED win rate — per (model, effort, PR) does harness TP ≥ vanilla TP?")
print("  96 paired comparisons per harness (4 models × 4 efforts × 6 PRs). Tests 'ALWAYS beat'.")
print("=" * 90)
for harness in ["metareview-realistic", "compound-realistic"]:
    wins = ties = losses = 0
    rec_wins = 0
    for m in MODELS:
        for e in EFFORTS:
            v = CELL[("vanilla-engineered", m, e)]
            h = CELL[(harness, m, e)]
            for pr in v["per_pr"]:
                vt = v["per_pr"][pr]["tp"]; ht = h["per_pr"].get(pr, {}).get("tp", 0)
                if ht > vt: wins += 1
                elif ht == vt: ties += 1
                else: losses += 1
    total = wins + ties + losses
    print(f"  {harness:22s}: wins={wins} ties={ties} losses={losses} (of {total}) → beat or tie on {wins+ties}/{total} ({(wins+ties)/total*100:.0f}%)")

print()
print("=" * 90)
print("ANALYSIS 4 (H2b): Harness-at-E vs vanilla-at-(E+1) — does harness at LOWER effort beat vanilla cranked HIGHER?")
print("  For each model: mrv/compound at effort E vs vanilla at next-higher effort (pooled recall).")
print("=" * 90)
print(f"{'model':16s} {'harness@E':24s} {'van@E+1':24s} {'h rec':>6} {'v rec':>6} {'beat?':>6}")
h2b_mrv = 0; h2b_cmp = 0; h2b_total = 0
for m in MODELS:
    for i, e in enumerate(EFFORTS[:-1]):  # low, medium, high (each vs the next)
        e2 = EFFORTS[i + 1]
        for harness, cnt in [("metareview-realistic", "h2b_mrv"), ("compound-realistic", "h2b_cmp")]:
            h = CELL[(harness, m, e)]
            v = CELL[("vanilla-engineered", m, e2)]
            beats = rec(h) > rec(v)
            h2b_total += 1
            if harness == "metareview-realistic": h2b_mrv += beats
            else: h2b_cmp += beats
            print(f"{m:16s} {harness[:10]+'@'+e:24s} {'vanilla@'+e2:24s} {rec(h):6.2f} {rec(v):6.2f} {'✓' if beats else '✗':>6}")
print(f"\n→ mrv at effort E beats vanilla at E+1 in {h2b_mrv}/{h2b_total} cases")
print(f"→ compound at effort E beats vanilla at E+1 in {h2b_cmp}/{h2b_total} cases")

print()
print("=" * 90)
print("ANALYSIS 5 (H1): Cost-efficiency — recall & hidden-gold PER MILLION TOKENS, by cell")
print("  Sorted by recall/Mtok (the 'bang per buck' view). Top 15.")
print("=" * 90)
rows = []
for fw in FRAMEWORKS:
    for m in MODELS:
        for e in EFFORTS:
            b = CELL[(fw, m, e)]
            if b["n"] == 0 or b["tok"] == 0: continue
            rows.append({
                "fw": fw, "model": m, "eff": e,
                "rec": rec(b), "adjp": adjp(b), "incr": incr(b),
                "real": b["real"], "hal": b["hal"], "tok": b["tok"],
                "rec_per_mtok": rec(b) / (b["tok"] / 1e6),
                "hg_per_mtok": b["real"] / (b["tok"] / 1e6),
                "incr_per_mtok": incr(b) / (b["tok"] / 1e6),
            })
print(f"\n--- Top 15 by RECALL per million tokens ---")
print(f"{'fw':22s} {'model':16s} {'eff':6s} {'rec':>5} {'rec/Mtok':>9} {'hidGold':>7} {'adj_p':>6} {'tok(M)':>8}")
for r in sorted(rows, key=lambda x: -x["rec_per_mtok"])[:15]:
    print(f"{r['fw']:22s} {r['model']:16s} {r['eff']:6s} {r['rec']:5.2f} {r['rec_per_mtok']:9.3f} {r['real']:>7} {r['adjp']:6.2f} {r['tok']/1e6:8.1f}")
print(f"\n--- Top 15 by HIDDEN GOLD per million tokens ---")
print(f"{'fw':22s} {'model':16s} {'eff':6s} {'hidGold':>7} {'hg/Mtok':>8} {'rec':>5} {'adj_p':>6} {'tok(M)':>8}")
for r in sorted(rows, key=lambda x: -x["hg_per_mtok"])[:15]:
    print(f"{r['fw']:22s} {r['model']:16s} {r['eff']:6s} {r['real']:>7} {r['hg_per_mtok']:8.2f} {r['rec']:5.2f} {r['adjp']:6.2f} {r['tok']/1e6:8.1f}")

# Pareto frontier: (recall, -tok) — cells not dominated on both recall and cost
print(f"\n--- PARETO FRONTIER (recall vs cost: high recall, low tok, non-dominated) ---")
pareto = []
for r in rows:
    dominated = any(o["rec"] >= r["rec"] and o["tok"] <= r["tok"] and (o["rec"] > r["rec"] or o["tok"] < r["tok"]) for o in rows)
    if not dominated:
        pareto.append(r)
print(f"{'fw':22s} {'model':16s} {'eff':6s} {'rec':>5} {'hidGold':>7} {'adj_p':>6} {'tok(M)':>8}")
for r in sorted(pareto, key=lambda x: x["tok"]):
    print(f"{r['fw']:22s} {r['model']:16s} {r['eff']:6s} {r['rec']:5.2f} {r['real']:>7} {r['adjp']:6.2f} {r['tok']/1e6:8.1f}")

print()
print("=" * 90)
print("ANALYSIS 6 (H1 direct): cheap+harness+low  vs  expensive+vanilla+high")
print("  Does (mrv/compound × gpt/sonnet × low/medium) match or beat (vanilla × opus-5 × high/xhigh)?")
print("=" * 90)
# the "expensive vanilla" reference cells
exp_van = [("vanilla-engineered", "claude-opus-5", "high"), ("vanilla-engineered", "claude-opus-5", "xhigh")]
# the "cheap harness" candidates
cheap_harness = [(fw, m, e) for fw in ["metareview-realistic", "compound-realistic"]
                for m in ["gpt-5.6-sol", "gpt-5.6-terra", "claude-sonnet-5"]
                for e in ["low", "medium"]]
print(f"\nReference (expensive vanilla):")
for k in exp_van:
    b = CELL[k]
    print(f"  {k[0]}/{k[1]}/{k[2]}: rec={rec(b):.2f} hidGold={b['real']} adj_p={adjp(b):.2f} tok={b['tok']/1e6:.1f}M")
print(f"\nCheap+harness cells that BEAT or MATCH expensive vanilla on recall AND cost less:")
print(f"{'fw':22s} {'model':16s} {'eff':6s} {'rec':>5} {'hidGold':>7} {'adj_p':>6} {'tok(M)':>8} {'vs van@high':>11} {'vs van@xhigh':>12}")
ref_h = CELL[exp_van[0]]; ref_x = CELL[exp_van[1]]
for k in cheap_harness:
    b = CELL[k]
    vs_h = "beats" if rec(b) >= rec(ref_h) and b["tok"] < ref_h["tok"] else "—"
    vs_x = "beats" if rec(b) >= rec(ref_x) and b["tok"] < ref_x["tok"] else "—"
    print(f"{k[0]:22s} {k[1]:16s} {k[2]:6s} {rec(b):5.2f} {b['real']:>7} {adjp(b):6.2f} {b['tok']/1e6:8.1f} {vs_h:>11} {vs_x:>12}")
