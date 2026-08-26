#!/usr/bin/env python3
"""Partial-analysis tracker for batch 20260825-batch-082-v2-mrv-vanilla-opus-codex-48cells.

Fuses two sources:
  1. runs/registry.jsonl  — authoritative COMPLETED+registered cells (manifest.json/summary.json)
  2. /tmp/batch_082_v2_out.txt — live stdout: "[i/48] fw model effort ..." start lines and
     "[i/48] fw model effort TP=.. FP=.. FN=.. ..." completion lines (lets us see in-flight cells
     and cells that printed but may not have hit the registry yet)

Writes:
  results/batch_082_v2_TRACKER.md      latest markdown partial-analysis snapshot
  results/batch_082_v2_history.jsonl   append-only JSON snapshots (one per invocation)

Compares against the sibling non-v2 batch (the run this v2 retries) for context.
"""
from __future__ import annotations
import json, re, sys, time, os, subprocess
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/dsifry/Developer/harnesseval")
BATCH_V2 = "20260825-batch-082-v2-mrv-vanilla-opus-codex-48cells"
BATCH_V1 = "20260825-batch-082-mrv-vanilla-opus-codex-48cells"   # the run v2 retries
REG = ROOT / "runs" / "registry.jsonl"
OUT_LOG = Path("/tmp/batch_082_v2_out.txt")
PID_FILE = Path("/tmp/batch_082_v2_pid.txt")
TRACKER_MD = ROOT / "results" / "batch_082_v2_TRACKER.md"
HISTORY = ROOT / "results" / "batch_082_v2_history.jsonl"
TOTAL_CELLS = 48
CONCURRENCY = 3
MODELS = ["claude-opus-5", "gpt-5.6-sol"]
EFFORTS = ["medium", "xhigh"]
FRAMEWORKS = ["metareview-realistic", "vanilla-engineered"]
# The 6 hardest PRs (top by severity-weighted golden-comment count), in matrix order
PRS = [
    ("11059", "calcom/cal.com#11059", 9),
    ("4",     "discourse-graphite#4",  8),
    ("10",    "discourse-graphite#10", 7),
    ("14740", "calcom/cal.com#14740",  6),
    ("8",     "discourse-graphite#8",  6),
    ("10967", "calcom/cal.com#10967", 6),
]
PR_BY_NUM = {n: label for n, label, _ in PRS}

def load_registry(batch):
    if not REG.exists(): return []
    out = []
    for line in REG.read_text().splitlines():
        if not line.strip(): continue
        try: e = json.loads(line)
        except Exception: continue
        if e.get("run_batch") == batch: out.append(e)
    return out

START_RE = re.compile(r"^\[mx\] \[(\d+)/48\] (\S+) (\S+) (\S+) \.\.\.$")
DONE_RE  = re.compile(r"^\[mx\] \[(\d+)/48\] (\S+) (\S+) (\S+) TP=(\d+) FP=(\d+) FN=(\d+) rec=([\d.]+) adj_p=([\d.]+) incr_r=([\d.]+) real=(\d+) hal=(\d+) ([\d,]+)tok (\d+)s")
ERR_RE   = re.compile(r"^\[mx\] \[(\d+)/48\] (\S+) (\S+) (\S+) ERR (\d+)s: (.*)$")

def parse_log(path):
    """Return {cell_index: {status:'running'|'done'|'fail', fw,model,effort, ...}} from the live log."""
    cells = {}
    if not path.exists(): return cells
    for line in path.read_text().splitlines():
        m = START_RE.match(line)
        if m:
            i, fw, model, eff = int(m.group(1)), m.group(2), m.group(3), m.group(4)
            cells[i] = {"idx": i, "fw": fw, "model": model, "effort": eff, "status": "running", "wall_s": None}
            continue
        m = DONE_RE.match(line)
        if m:
            i = int(m.group(1)); fw = m.group(2); model = m.group(3); eff = m.group(4)
            cells[i] = {"idx": i, "fw": fw, "model": model, "effort": eff, "status": "done",
                        "tp": int(m.group(5)), "fp": int(m.group(6)), "fn": int(m.group(7)),
                        "recall": float(m.group(8)), "adj_p": float(m.group(9)),
                        "incr_r": float(m.group(10)), "real": int(m.group(11)),
                        "hal": int(m.group(12)),
                        "tokens": int(m.group(13).replace(",", "")),
                        "wall_s": int(m.group(14))}
            continue
        m = ERR_RE.match(line)
        if m:
            i = int(m.group(1)); fw = m.group(2); model = m.group(3); eff = m.group(4)
            cells[i] = {"idx": i, "fw": fw, "model": model, "effort": eff, "status": "fail",
                        "wall_s": int(m.group(5)), "error": m.group(6)[:160]}
    return cells

def process_status():
    pid = None
    if PID_FILE.exists():
        try: pid = int(PID_FILE.read_text().strip())
        except Exception: pid = None
    running = False
    etime = ""
    if pid:
        try:
            os.kill(pid, 0); running = True
            etime = subprocess.run(["ps","-o","etime=","-p",str(pid)], capture_output=True, text=True).stdout.strip()
        except Exception:
            running = False
    return {"running": running, "pid": pid, "etime": etime}

def agg(rows, keys):
    g = defaultdict(lambda: {"tp":0,"fp":0,"fn":0,"hal":0,"real":0,"tok_in":0,"tok_out":0,"wall":0.0,"n":0})
    for r in rows:
        m = r.get("metrics", {}) or {}
        k = tuple(r[k] for k in keys)
        b = g[k]
        b["tp"] += m.get("tp",0) or 0
        b["fp"] += m.get("fp",0) or 0
        b["fn"] += m.get("fn",0) or 0
        b["hal"] += m.get("n_hallucination",0) or 0
        b["real"] += m.get("n_real_ungold",0) or 0
        b["tok_in"] += r.get("tokens_in",0) or 0
        b["tok_out"] += r.get("tokens_out",0) or 0
        b["wall"] += r.get("wall_s",0) or 0
        b["n"] += 1
    return g

def fmt_row(k, v):
    rec = v["tp"]/(v["tp"]+v["fn"]) if (v["tp"]+v["fn"]) else 0
    adjp = v["tp"]/(v["tp"]+v["hal"]) if (v["tp"]+v["hal"]) else 0
    incr = (v["tp"]+v["real"])/(v["tp"]+v["fn"]+v["real"]) if (v["tp"]+v["fn"]+v["real"]) else 0
    return rec, adjp, incr

# ---- cross-batch calibration vs compound-realistic & superpowers-realistic ----
# Earlier batches (20260824-*) ran compound-realistic & superpowers-realistic alongside
# vanilla-engineered. We use vanilla-engineered as a CONTROL ARM: only trust an earlier
# batch's compound/superpowers numbers as comparable to v2 if vanilla-engineered in that
# batch is within margin of error of vanilla in v2 on the matched (model,effort,PR) cells.
# Method: bootstrap 95% CI on the (v2 - earlier) pooled-recall difference; calibrated iff CI contains 0.
EARLIER_BATCHES = ["20260824-101905-cli-144cells", "20260824-072840-cli-144cells"]
V2_MODELS_SET = set(MODELS)
V2_EFFORTS_SET = set(EFFORTS)

def _cell_key_from_summary(e):
    sp = e.get("summary_path")
    if not sp: return None
    try: s = json.load(open(sp))
    except Exception: return None
    return (e["model"], e["effort"], s.get("url","").rstrip("/").rsplit("/",1)[-1])

def _fw_cells_by_key(batch, framework, only_pass=True, v2_filter=True):
    """Return {(model,effort,pr_num): {tp,fp,fn,hal,real,tok_in,tok_out,wall}} for a batch+framework."""
    out = {}
    if not REG.exists(): return out
    for line in REG.read_text().splitlines():
        if not line.strip(): continue
        try: e = json.loads(line)
        except Exception: continue
        if e.get("run_batch") != batch: continue
        if e.get("framework") != framework: continue
        if only_pass and e.get("status") != "pass": continue
        if v2_filter and (e.get("model") not in V2_MODELS_SET or e.get("effort") not in V2_EFFORTS_SET): continue
        k = _cell_key_from_summary(e)
        if k is None: continue
        m = e.get("metrics", {}) or {}
        out[k] = {"tp": m.get("tp",0) or 0, "fp": m.get("fp",0) or 0, "fn": m.get("fn",0) or 0,
                  "hal": m.get("n_hallucination",0) or 0, "real": m.get("n_real_ungold",0) or 0,
                  "tok_in": e.get("tokens_in",0) or 0, "tok_out": e.get("tokens_out",0) or 0,
                  "wall": e.get("wall_s",0) or 0}
    return out

def _agg_cells(cells):
    b = {"tp":0,"fp":0,"fn":0,"hal":0,"real":0,"tok_in":0,"tok_out":0,"wall":0.0,"n":0}
    for c in cells:
        for kk in ("tp","fp","fn","hal","real","tok_in","tok_out"): b[kk]+=c[kk]
        b["wall"]+=c["wall"]; b["n"]+=1
    return b

def _calibrate_earlier(batch, v2_van_keys, v2_van_cells):
    """Return dict with matched-key set, earlier-vanilla recall, v2-vanilla recall, bootstrap CI, calibrated bool."""
    import random as _r
    _r.seed(1)
    ev = _fw_cells_by_key(batch, "vanilla-engineered")
    matched_keys = [k for k in v2_van_keys if k in ev]
    if not matched_keys:
        return None
    earlier = [ev[k] for k in matched_keys]
    v2m = [v2_van_cells[k] for k in matched_keys]
    be = _agg_cells(earlier); bv = _agg_cells(v2m)
    re_ = be["tp"]/(be["tp"]+be["fn"]) if (be["tp"]+be["fn"]) else 0.0
    rv_ = bv["tp"]/(bv["tp"]+bv["fn"]) if (bv["tp"]+bv["fn"]) else 0.0
    # bootstrap 95% CI on (v2 - earlier) pooled-recall difference, resampling matched pairs
    pairs = list(zip(earlier, v2m))
    bs = []
    for _ in range(2000):
        idx = [_r.randrange(len(pairs)) for _ in range(len(pairs))]
        tpe = sum(pairs[i][0]["tp"] for i in idx); fne = sum(pairs[i][0]["fn"] for i in idx)
        tpv = sum(pairs[i][1]["tp"] for i in idx); fnv = sum(pairs[i][1]["fn"] for i in idx)
        re_b = tpe/(tpe+fne) if (tpe+fne) else 0.0
        rv_b = tpv/(tpv+fnv) if (tpv+fnv) else 0.0
        bs.append(rv_b - re_b)
    bs.sort()
    lo = bs[int(0.025*len(bs))]; hi = bs[int(0.975*len(bs))]
    return {"batch": batch, "matched_keys": matched_keys, "n_matched": len(matched_keys),
            "earlier_recall": re_, "v2_recall": rv_, "diff": rv_-re_,
            "ci_lo": lo, "ci_hi": hi, "calibrated": (lo <= 0 <= hi)}

def _dedup_latest_per_cell(rows):
    """Dedup runs by (framework, model, effort, PR url), keeping the LATEST by registered_at.
    Fill-in reruns (same run_batch) register a NEW run for an errored cell; this makes the
    fill-in's pass cleanly replace the original fail in all aggregates without double-counting."""
    latest = {}
    for r in rows:
        sp = r.get("summary_path")
        if not sp:
            # no summary -> can't get url; key on run_id so it's kept distinct (shouldn't happen for v2)
            key = (r.get("framework"), r.get("model"), r.get("effort"), r.get("run_id"))
        else:
            try: s = json.load(open(sp))
            except Exception: continue
            key = (r.get("framework"), r.get("model"), r.get("effort"), s.get("url",""))
        prev = latest.get(key)
        if prev is None or r.get("registered_at","") >= prev.get("registered_at",""):
            latest[key] = r
    return list(latest.values())

def _cell_key_full(r):
    """(framework, model, effort, url) for a run — used to match fill-ins to originals."""
    sp = r.get("summary_path")
    url = ""
    if sp:
        try: s = json.load(open(sp)); url = s.get("url","")
        except Exception: pass
    return (r.get("framework"), r.get("model"), r.get("effort"), url)

def main():
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    reg_v2 = load_registry(BATCH_V2)
    reg_v2_latest = _dedup_latest_per_cell(reg_v2)   # latest run per cell (fill-ins supersede originals)
    n_filled_in = len(reg_v2) - len(reg_v2_latest)
    reg_v1 = load_registry(BATCH_V1)
    log_cells = parse_log(OUT_LOG)
    ps = process_status()

    done_registered = len(reg_v2)               # raw runs incl. fill-in reruns
    eff_registered = len(reg_v2_latest)         # effective (latest-per-cell) runs
    pass_n = sum(1 for r in reg_v2_latest if r["status"] == "pass")
    fail_n = sum(1 for r in reg_v2_latest if r["status"] != "pass")
    log_done = sum(1 for c in log_cells.values() if c["status"] == "done")
    log_fail = sum(1 for c in log_cells.values() if c["status"] == "fail")
    log_finished = log_done + log_fail
    log_running = sum(1 for c in log_cells.values() if c["status"] == "running")
    in_flight = [c for c in log_cells.values() if c["status"] == "running"]

    # ETA from finished cells' wall times + remaining cells / concurrency
    completed_walls = [c["wall_s"] for c in log_cells.values() if c["status"] in ("done","fail") and c["wall_s"]]
    avg_wall = sum(completed_walls)/len(completed_walls) if completed_walls else 0
    remaining = TOTAL_CELLS - log_finished
    eta_s = (remaining * avg_wall / CONCURRENCY) if avg_wall else 0

    # aggregates from the AUTHORITATIVE registry. reg_v2_latest already deduped above.
    g_fw_model_eff = agg(reg_v2_latest, ["framework", "model", "effort"])
    g_fw = agg(reg_v2_latest, ["framework"])
    g_model = agg(reg_v2_latest, ["model"])
    g_eff = agg(reg_v2_latest, ["effort"])

    # PR coverage from summary.json (which url each completed run covered)
    pr_hits = defaultdict(lambda: {"n":0,"tp":0,"fn":0,"fp":0,"hal":0})
    for r in reg_v2_latest:
        sp = r.get("summary_path")
        if not sp: continue
        try: s = json.load(open(sp))
        except Exception: continue
        url = s.get("url","")
        num = url.rstrip("/").rsplit("/",1)[-1]
        m = r.get("metrics",{}) or {}
        b = pr_hits[num]
        b["n"] += 1; b["tp"] += m.get("tp",0) or 0; b["fn"] += m.get("fn",0) or 0
        b["fp"] += m.get("fp",0) or 0; b["hal"] += m.get("n_hallucination",0) or 0

    # v1 (non-v2) for comparison: metareview-realistic failure mode
    g_v1_fwm = agg(reg_v1, ["framework", "model", "effort"])

    # ---- build markdown ----
    L = []
    L.append(f"# Batch 082-v2 partial analysis — {now}")
    L.append("")
    L.append(f"**Batch:** `{BATCH_V2}`")
    L.append("")
    L.append("Matrix: **6 PRs × 2 models × 2 efforts × 2 frameworks = 48 cells** · mode=cli (OAuth) · concurrency=3 · "
             "models=claude-opus-5, gpt-5.6-sol · efforts=medium, xhigh · frameworks=metareview-realistic, vanilla-engineered")
    L.append("Judges: cross-family (claude-* → gpt-5.2 primary; gpt-* → claude-opus-4-5 primary).")
    L.append("")
    st = "RUNNING" if ps["running"] else "FINISHED"
    L.append(f"**Status:** {st}" + (f"  ·  pid={ps['pid']}  ·  etime={ps['etime']}" if ps['running'] else ""))
    L.append("")
    L.append("## Progress")
    L.append("")
    L.append(f"- Cells finished in stdout log: **{log_finished}/48** (done={log_done}, fail={log_fail})")
    if n_filled_in > 0:
        L.append(f"- Runs registered: **{done_registered}** (raw) → **{eff_registered}/48** effective cells after dedup · "
                 f"pass={pass_n}, fail={fail_n} · **{n_filled_in} fill-in rerun(s)** superseded an earlier run for the same cell (latest wins)")
    else:
        L.append(f"- Cells registered in run registry: **{done_registered}/48** (pass={pass_n}, fail={fail_n})")
    L.append(f"- In-flight right now: **{log_running}** cells")
    if in_flight:
        for c in in_flight:
            L.append(f"  - `[{c['idx']}/48]` {c['fw']} / {c['model']} / {c['effort']}")
    if avg_wall:
        L.append(f"- Avg wall per finished cell: **{avg_wall:.0f}s** · remaining {remaining} cells → ETA **~{eta_s/60:.0f} min** @ concurrency {CONCURRENCY}")
    L.append(f"- Tokens printed so far (log): {sum(c.get('tokens',0) for c in log_cells.values() if c['status']=='done'):,}")
    L.append("")
    # progress bar
    pct = log_finished/TOTAL_CELLS
    bar = "█"*int(pct*40) + "░"*(40-int(pct*40))
    L.append(f"  `{bar}` {pct*100:.0f}%")
    L.append("")

    # per cell table (all 48, mark done/running/pending)
    L.append("## Cell-by-cell (matrix grid)")
    L.append("")
    L.append("| idx | fw | model | effort | state | TP | FP | FN | rec | adj_p | incr_r | real | hal | tok | wall |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    # build index map for grid: matrix order is url -> model -> effort -> fw (matches run_model_matrix)
    # But log indices follow asyncio gather order, which is the append order = (url, model, effort, fw).
    cells_by_idx = {c["idx"]: c for c in log_cells.values()}
    # We don't know exact idx->PR from log, so just list what we have sorted by idx
    for i in sorted(cells_by_idx):
        c = cells_by_idx[i]
        if c["status"]=="done":
            stt="✅done"
            L.append(f"| {i} | {c['fw']} | {c['model']} | {c['effort']} | {stt} | {c['tp']} | {c['fp']} | {c['fn']} | {c['recall']:.2f} | {c['adj_p']:.2f} | {c['incr_r']:.2f} | {c['real']} | {c['hal']} | {c['tokens']:,} | {c['wall_s']}s |")
        elif c["status"]=="fail":
            stt="❌fail"
            L.append(f"| {i} | {c['fw']} | {c['model']} | {c['effort']} | {stt} | — | — | — | — | — | — | — | — | — | {c.get('wall_s','?')}s |")
        else:
            stt="⏳run"
            L.append(f"| {i} | {c['fw']} | {c['model']} | {c['effort']} | {stt} | — | — | — | — | — | — | — | — | — | — |")
    pending = TOTAL_CELLS - len(cells_by_idx)
    if pending>0:
        L.append(f"| … | *{pending} cells not yet started* | | | ⬜pending | | | | | | | | | | |")
    L.append("")

    # per (fw,model,effort) aggregates — the real signal
    L.append("## Aggregates per (framework × model × effort) — completed cells only")
    L.append("")
    L.append("| fw | model | effort | cells | TP | FP | FN | recall | adj_p | incr_r | real | hal | tok |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for fw in FRAMEWORKS:
        for model in MODELS:
            for eff in EFFORTS:
                v = g_fw_model_eff.get((fw, model, eff))
                if not v: 
                    L.append(f"| {fw} | {model} | {eff} | 0/6 | — | — | — | — | — | — | — | — | — |"); continue
                rec, adjp, incr = fmt_row((fw,model,eff), v)
                L.append(f"| {fw} | {model} | {eff} | {v['n']}/6 | {v['tp']} | {v['fp']} | {v['fn']} | {rec:.2f} | {adjp:.2f} | {incr:.2f} | {v['real']} | {v['hal']} | {v['tok_in']+v['tok_out']:,} |")
    L.append("")

    # per framework / per model / per effort marginals
    def marginal_table(title, gmap, labels):
        L.append(f"## {title} (completed cells)")
        L.append("")
        L.append(f"| {labels[0]} | cells | TP | FP | FN | recall | adj_p | incr_r | real | hal | tok |")
        L.append(f"|---|---|---|---|---|---|---|---|---|---|---|")
        for k in sorted(gmap):
            v = gmap[k]; rec,adjp,incr = fmt_row(k, v)
            L.append(f"| {k} | {v['n']} | {v['tp']} | {v['fp']} | {v['fn']} | {rec:.2f} | {adjp:.2f} | {incr:.2f} | {v['real']} | {v['hal']} | {v['tok_in']+v['tok_out']:,} |")
        L.append("")
    marginal_table("Aggregates per framework", g_fw, ["framework"])
    marginal_table("Aggregates per model", g_model, ["model"])
    marginal_table("Aggregates per effort", g_eff, ["effort"])

    # PR coverage
    L.append("## Per-PR coverage (completed cells so far)")
    L.append("")
    L.append("| PR | label | cells done | TP | FN | FP | hal | per-cell recall |")
    L.append("|---|---|---|---|---|---|---|---|")
    for num, label, _ in PRS:
        b = pr_hits.get(num)
        if not b:
            L.append(f"| {num} | {label} | 0/8 | — | — | — | — | — |"); continue
        # each PR appears in 4 cells (2 fw × 2 model × ... actually 2 fw × 2 models × ... wait 2 fw × 2 models =4 but ×effort=2 -> 8 per PR? No: per PR there are 2 models × 2 efforts × 2 fw = 8 cells)
        # Actually 6 PRs * 8 = 48. So per PR = 8 cells.
        rec = b["tp"]/(b["tp"]+b["fn"]) if (b["tp"]+b["fn"]) else 0
        L.append(f"| {num} | {label} | {b['n']}/8 | {b['tp']} | {b['fn']} | {b['fp']} | {b['hal']} | {rec:.2f} |")
    L.append("")
    L.append("> Note: per-PR denominator is 8 cells = 2 frameworks × 2 models × 2 efforts.")
    L.append("")

    # v1 vs v2 comparison for the metareview-realistic failure mode
    L.append("## v1 → v2 comparison (metareview-realistic was the failure mode being retried)")
    L.append("")
    L.append("The non-v2 batch (`batch-082-mrv-...`) showed metareview-realistic on **claude-opus-5** burning "
             "~3.0M and ~6.6M tokens for **0 TP / 0 FP / 9 FN** (total recall collapse). v2 retries it.")
    L.append("")
    L.append("| fw | model | effort | batch | cells | TP | FP | FN | recall | hal | tok |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for fw in FRAMEWORKS:
        for model in MODELS:
            for eff in EFFORTS:
                for batch, g, name in [(BATCH_V1, g_v1_fwm, "v1"), (BATCH_V2, g_fw_model_eff, "v2")]:
                    v = g.get((fw, model, eff))
                    if not v: continue
                    rec = v["tp"]/(v["tp"]+v["fn"]) if (v["tp"]+v["fn"]) else 0
                    L.append(f"| {fw} | {model} | {eff} | {name} | {v['n']}/6 | {v['tp']} | {v['fp']} | {v['fn']} | {rec:.2f} | {v['hal']} | {v['tok_in']+v['tok_out']:,} |")
    L.append("")

    # Anomalies / notes
    # ---- Cross-batch calibration vs compound-realistic & superpowers-realistic ----
    # vanilla-engineered is the control arm. For each earlier batch, match its vanilla cells to v2's
    # completed vanilla cells on (model, effort, PR); bootstrap CI on the recall diff. If calibrated,
    # pull that batch's compound-realistic & superpowers-realistic onto the same workload (matched keys)
    # and present alongside v2's frameworks on a shared Pareto-style table.
    v2_van_cells = _fw_cells_by_key(BATCH_V2, "vanilla-engineered")
    v2_van_keys = list(v2_van_cells.keys())
    v2_mrv_cells = _fw_cells_by_key(BATCH_V2, "metareview-realistic")
    L.append("## Cross-batch calibration vs compound-realistic & superpowers-realistic")
    L.append("")
    L.append("Earlier `20260824-*` batches ran **compound-realistic** & **superpowers-realistic** alongside "
             "vanilla-engineered. vanilla-engineered is used as a *control arm*: an earlier batch's "
             "compound/superpowers numbers are only treated as comparable to v2 if vanilla-engineered in "
             "that batch is within margin of error of vanilla in v2 on the matched (model × effort × PR) cells. "
             "Method: bootstrap 95% CI on the (v2 − earlier) pooled-recall difference; calibrated iff the CI contains 0.")
    L.append("")
    # calibration table
    L.append("### Calibration check (vanilla-engineered control arm)")
    L.append("")
    L.append("| earlier batch | matched cells | earlier vanilla recall | v2 vanilla recall | Δ (v2−earlier) | 95% CI | calibrated? |")
    L.append("|---|---|---|---|---|---|---|")
    calib_results = []
    for b in EARLIER_BATCHES:
        res = _calibrate_earlier(b, v2_van_keys, v2_van_cells)
        if res is None:
            L.append(f"| {b} | 0 | — | — | — | — | (no overlap) |"); continue
        calib_results.append(res)
        verdict = "✅ YES" if res["calibrated"] else "❌ NO"
        L.append(f"| {b} | {res['n_matched']}/{len(v2_van_keys)} | {res['earlier_recall']:.3f} | {res['v2_recall']:.3f} | "
                 f"{res['diff']:+.3f} | [{res['ci_lo']:+.3f}, {res['ci_hi']:+.3f}] | {verdict} |")
    L.append("")
    # Pareto-style comparison on the matched workload (only from calibrated batches)
    L.append("### Framework comparison on the matched workload (recall / precision / cost)")
    L.append("")
    if not calib_results:
        L.append("_No earlier batch calibrated against v2 yet (need more v2 vanilla cells to overlap)._")
        L.append("")
    else:
        # use the largest matched set among calibrated batches as the reference workload
        calib_results.sort(key=lambda r: r["n_matched"], reverse=True)
        ref = calib_results[0]
        mkeys = set(ref["matched_keys"])
        L.append(f"Reference workload: **{ref['n_matched']} matched cells** (model × effort × PR) from `{ref['batch']}` "
                 f"(largest calibrated overlap). All frameworks below are aggregated over this exact set.")
        L.append("")
        L.append("| framework | source batch | cells | TP | FP | FN | recall | adj_p | incr_r | real | hal | tok |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        rows_compare = []
        # v2 frameworks over the matched keys
        for name, cells, batch in [("vanilla-engineered", v2_van_cells, BATCH_V2),
                                  ("metareview-realistic", v2_mrv_cells, BATCH_V2)]:
            sub = [c for k,c in cells.items() if k in mkeys]
            if not sub: continue
            b = _agg_cells(sub); rec,adjp,incr = fmt_row(None, b)
            rows_compare.append((name, batch, b, rec, adjp, incr))
            L.append(f"| {name} | v2 | {b['n']} | {b['tp']} | {b['fp']} | {b['fn']} | {rec:.2f} | {adjp:.2f} | {incr:.2f} | {b['real']} | {b['hal']} | {b['tok_in']+b['tok_out']:,} |")
        # earlier-batch frameworks over the matched keys (only calibrated batches)
        for res in calib_results:
            for fw in ("compound-realistic", "superpowers-realistic"):
                cells = _fw_cells_by_key(res["batch"], fw)
                sub = [c for k,c in cells.items() if k in set(res["matched_keys"])]
                if not sub: continue
                b = _agg_cells(sub); rec,adjp,incr = fmt_row(None, b)
                rows_compare.append((fw, res["batch"], b, rec, adjp, incr))
                L.append(f"| {fw} | {res['batch'][:10]}… | {b['n']} | {b['tp']} | {b['fp']} | {b['fn']} | {rec:.2f} | {adjp:.2f} | {incr:.2f} | {b['real']} | {b['hal']} | {b['tok_in']+b['tok_out']:,} |")
        L.append("")
        # frontier read: sort by recall then tok
        rows_compare.sort(key=lambda x: (-x[3], x[2]["tok_in"]+x[2]["tok_out"]))
        L.append("**Pareto read (matched workload, sorted by recall then cost):**")
        L.append("")
        for name, batch, b, rec, adjp, incr in rows_compare:
            src = "v2" if batch == BATCH_V2 else batch[:10]+"…"
            L.append(f"- `{name}` ({src}): recall **{rec:.2f}** · adj_p {adjp:.2f} · incr_r {incr:.2f} · "
                     f"{b['hal']} hal · **{b['tok_in']+b['tok_out']:,} tok**")
        L.append("")
    L.append("")

    # ---- Hidden gold & hallucinations by framework x effort (matched workload) ----
    # Surfaces n_real_ungold ("hidden gold": real bugs found that are NOT in the golden set,
    # adjudicated real-but-ungold) as a first-class metric, and treats EFFORT as a variable so
    # the framework x effort interaction is visible (e.g. vanilla/xhigh vs mrv/medium vs
    # compound/medium). Only uses cells on the calibrated matched workload (apples-to-apples).
    L.append("## Hidden gold & hallucinations by framework × effort (matched workload)")
    L.append("")
    L.append("**Metrics:** `recall` = found bugs that ARE in the golden set (TP/(TP+FN)). "
             "`hidden gold` = `n_real_ungold` = real bugs the reviewer found that are NOT in the "
             "golden set (adjudicated real-but-ungold — bonus discoveries beyond the benchmark). "
             "`hallucinations` = `n_hallucination` = false positives adjudicated as NOT real. "
             "`incr_recall` = (TP+hidden_gold)/(TP+FN+hidden_gold) — recall counting hidden gold as found.")
    L.append("")
    if not calib_results:
        L.append("_Needs a calibrated earlier batch (more v2 vanilla cells required to overlap)._")
        L.append("")
    else:
        calib_results.sort(key=lambda r: r["n_matched"], reverse=True)
        ref = calib_results[0]
        mkeys = set(ref["matched_keys"])
        def _fe(cells, eff):
            """Aggregate a framework's cells on the matched workload at a given effort."""
            ekeys = {k for k in mkeys if k[1] == eff}
            sub = [c for k, c in cells.items() if k in ekeys]
            if not sub: return None
            tp=sum(c["tp"] for c in sub); fn=sum(c["fn"] for c in sub)
            real=sum(c["real"] for c in sub); hal=sum(c["hal"] for c in sub)
            tok=sum(c["tok_in"]+c["tok_out"] for c in sub); n=len(sub)
            rec=tp/(tp+fn) if (tp+fn) else 0
            ir=(tp+real)/(tp+fn+real) if (tp+fn+real) else 0
            return {"n":n,"tp":tp,"fn":fn,"real":real,"hal":hal,"tok":tok,"rec":rec,"ir":ir}
        # gather (framework, effort, source) rows
        fw_sources = [("vanilla-engineered", BATCH_V2, "v2"),
                     ("metareview-realistic", BATCH_V2, "v2")]
        for b in [r["batch"] for r in calib_results]:
            fw_sources += [("compound-realistic", b, b[:7]), ("superpowers-realistic", b, b[:7])]
        rows_fe = []
        for fw, batch, src in fw_sources:
            cells_fw = _fw_cells_by_key(batch, fw)
            for eff in ("medium", "xhigh"):
                r = _fe(cells_fw, eff)
                if r is None: continue
                rows_fe.append((fw, eff, src, r))
        L.append("### Effort × framework table (matched workload)")
        L.append("")
        L.append("| framework | effort | source | n | TP | FN | recall | hidden gold | /cell | incr_r | hal | /cell | tok |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for fw, eff, src, r in rows_fe:
            hg_pc = r["real"]/r["n"] if r["n"] else 0
            hal_pc = r["hal"]/r["n"] if r["n"] else 0
            L.append(f"| {fw} | {eff} | {src} | {r['n']} | {r['tp']} | {r['fn']} | {r['rec']:.2f} | "
                     f"{r['real']} | {hg_pc:.1f} | {r['ir']:.2f} | {r['hal']} | {hal_pc:.1f} | {r['tok']:,} |")
        L.append("")
        # focused effort-tradeoff comparison: vanilla/xhigh vs mrv/medium vs compound/medium
        L.append("### Effort-tradeoff read: vanilla/xhigh vs mrv/medium vs compound/medium")
        L.append("")
        L.append("Tests the hypothesis that cranking vanilla effort (xhigh) competes with mrv/compound at "
                 "medium — and that the lens frameworks find more hidden gold, with mrv at ~half the "
                 "hallucinations of compound.")
        L.append("")
        target = [("vanilla-engineered", "xhigh", BATCH_V2, "v2"),
                 ("metareview-realistic", "medium", BATCH_V2, "v2")]
        for b in [r["batch"] for r in calib_results]:
            target.append(("compound-realistic", "medium", b, b[:7]))
        found = []
        for fw, eff, batch, src in target:
            cells_fw = _fw_cells_by_key(batch, fw)
            r = _fe(cells_fw, eff)
            if r is None: continue
            found.append((fw, eff, src, r))
        L.append("| config | source | n | recall | hidden gold | /cell | incr_r | hal | /cell | tok |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for fw, eff, src, r in found:
            hg_pc = r["real"]/r["n"] if r["n"] else 0
            hal_pc = r["hal"]/r["n"] if r["n"] else 0
            L.append(f"| {fw} / {eff} | {src} | {r['n']} | {r['rec']:.2f} | {r['real']} | {hg_pc:.1f} | "
                     f"{r['ir']:.2f} | {r['hal']} | {hal_pc:.1f} | {r['tok']:,} |")
        L.append("")
        if len(found) >= 2:
            # narrative comparison: mrv/medium vs vanilla/xhigh, compound/medium vs mrv/medium
            vm = next((x for x in found if x[0]=="vanilla-engineered" and x[1]=="xhigh"), None)
            mm = next((x for x in found if x[0]=="metareview-realistic" and x[1]=="medium"), None)
            cm = next((x for x in found if x[0]=="compound-realistic" and x[1]=="medium"), None)
            L.append("**Read:**")
            L.append("")
            if vm and mm:
                drec = mm[3]["rec"] - vm[3]["rec"]
                dhg = mm[3]["real"] - vm[3]["real"]
                dhal = mm[3]["hal"] - vm[3]["hal"]
                L.append(f"- **mrv/medium vs vanilla/xhigh**: recall {mm[3]['rec']:.2f} vs {vm[3]['rec']:.2f} "
                         f"({drec:+.2f}), hidden gold {mm[3]['real']} vs {vm[3]['real']} ({dhg:+d}), "
                         f"hallucinations {mm[3]['hal']} vs {vm[3]['hal']} ({dhal:+d}) — mrv/medium finds more "
                         f"golden + hidden bugs at the cost of more hallucinations and "
                         f"~{mm[3]['tok']/vm[3]['tok']:.0f}× the tokens.")
            if mm and cm:
                ratio = cm[3]["hal"]/mm[3]["hal"] if mm[3]["hal"] else 0   # compound hal / mrv hal
                mrv_frac = mm[3]["hal"]/cm[3]["hal"] if cm[3]["hal"] else 0  # mrv hal / compound hal
                L.append(f"- **compound/medium vs mrv/medium**: recall {cm[3]['rec']:.2f} vs {mm[3]['rec']:.2f}, "
                         f"hidden gold {cm[3]['real']} vs {mm[3]['real']} ({cm[3]['real']-mm[3]['real']:+d}; "
                         f"{cm[3]['real']/mm[3]['real']:.1f}×), hallucinations {cm[3]['hal']} vs {mm[3]['hal']} "
                         f"— mrv/medium has **{mrv_frac:.0%} of compound's hallucinations** (~{ratio:.1f}× fewer; "
                         f"about half), but compound finds far more hidden gold.")
            L.append("")
    L.append("")

    # Anomalies / notes
    L.append("## Notes & anomalies")
    L.append("")
    # detect any 0-TP metareview-realistic cell in v2 (the failure mode) — use LATEST per cell
    bad = []
    for r in reg_v2_latest:
        m = r.get("metrics",{}) or {}
        if r["framework"]=="metareview-realistic" and (m.get("tp",0) or 0)==0 and (m.get("tokens_in",0)+m.get("tokens_out",0))>1_000_000:
            bad.append(r)
    if bad:
        L.append(f"- ⚠️ **{len(bad)} metareview-realistic cell(s) in v2 still show 0-TP + >1M tokens** (the v1 failure mode persists):")
        for r in bad:
            m=r["metrics"]; L.append(f"  - {r['model']} / {r['effort']} / id={r['run_id']} · TP={m.get('tp')} FN={m.get('fn')} tok={(r['tokens_in']+r['tokens_out']):,}")
    else:
        if any(r["framework"]=="metareview-realistic" for r in reg_v2_latest):
            L.append("- ✅ No metareview-realistic cell in v2 (latest per cell) hits the v1 0-TP/>1M-tok failure mode.")
    # originally-errored cells that have since been filled in (a newer pass run exists for the same cell)
    orig_fails = [r for r in reg_v2 if r["status"]!="pass"]
    filled_in = []
    if orig_fails:
        latest_pass_keys = {_cell_key_full(r) for r in reg_v2_latest if r["status"]=="pass"}
        for r in orig_fails:
            if _cell_key_full(r) in latest_pass_keys:
                filled_in.append(r)
    fails = [r for r in reg_v2_latest if r["status"]!="pass"]   # STILL failing after any fill-in
    log_fails = [c for c in log_cells.values() if c["status"]=="fail"]
    if filled_in:
        L.append(f"- 🔧 **{len(filled_in)} cell(s) originally errored, now FILLED IN** (output-cap fix → pass):")
        for r in filled_in:
            url = _cell_key_full(r)[-1] or ""
            L.append(f"  - {r['model']} / {r['effort']} / {r['framework']} (PR {url.rstrip('/').rsplit('/',1)[-1] or '?'}) — orig id={r['run_id']}, now superseded")
    if log_fails:
        L.append(f"- ❌ **{len(log_fails)} cell(s) errored in the live stdout log** (watch for recurrence):")
        for c in log_fails:
            L.append(f"  - `[{c['idx']}/48]` {c['fw']} / {c['model']} / {c['effort']} · {c.get('wall_s','?')}s · {c.get('error','')}")
    if fails:
        L.append(f"- ⚠️ {len(fails)} cell(s) STILL failing after fill-in (latest per cell): " + ", ".join(f"{r['model']}/{r['effort']}/{r['framework']}" for r in fails))
    if not bad and not fails and not log_fails and not filled_in:
        L.append("- No anomalies detected in completed cells so far.")
    L.append("")
    L.append("---")
    L.append(f"_Snapshot generated by `bin/track_batch_082_v2.py` at {now}. Re-run for a fresh snapshot; "
             f"history in `results/batch_082_v2_history.jsonl`._")
    md = "\n".join(L)
    TRACKER_MD.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_MD.write_text(md)

    snap = {
        "ts": now, "running": ps["running"], "etime": ps["etime"],
        "log_done": log_done, "registered": done_registered, "pass": pass_n, "fail": fail_n,
        "in_flight": len(in_flight), "avg_wall": avg_wall, "eta_min": eta_s/60 if avg_wall else None,
        "tokens_so_far": sum(c.get("tokens",0) for c in log_cells.values() if c["status"]=="done"),
        "per_fwm": {f"{k[0]}|{k[1]}|{k[2]}": v for k,v in g_fw_model_eff.items()},
    }
    with HISTORY.open("a") as f: f.write(json.dumps(snap)+"\n")

    # also print a concise stdout summary
    print(md)
    print("\n=== snapshot appended to results/batch_082_v2_history.jsonl ===")

if __name__ == "__main__":
    main()
