#!/usr/bin/env python3
"""Partial-analysis tracker for batch 20260825-batch-083-fullmatrix (the definitive 4×4×4 matrix).

4 frameworks × 4 models × 4 efforts × 6 PRs = 384 cells total (331 new + 53 skipped).
Fuses the run registry (completed cells) with the live stdout log (in-flight cells).

Usage: uv run python bin/track_batch_083.py
"""
from __future__ import annotations
import json, re, sys, time, os, subprocess, random
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/dsifry/Developer/harnesseval")
BATCH = "20260825-batch-083-fullmatrix"
REG = ROOT / "runs" / "registry.jsonl"
OUT_LOG = Path("/tmp/batch_083_out.txt")
PID_FILE = Path("/tmp/batch_083_pid.txt")
TRACKER_MD = ROOT / "results" / "batch_083_TRACKER.md"
HISTORY = ROOT / "results" / "batch_083_history.jsonl"
TOTAL_CELLS = 384
CONCURRENCY = 3
FRAMEWORKS = ["vanilla-engineered", "metareview-realistic", "compound-realistic", "superpowers-realistic"]
MODELS = ["claude-opus-5", "gpt-5.6-sol", "claude-sonnet-5", "gpt-5.6-terra"]
EFFORTS = ["low", "medium", "high", "xhigh"]
# earlier batches for calibration (vanilla-engineered = control arm)
EARLIER_BATCHES = ["20260825-batch-082-v2-mrv-vanilla-opus-codex-48cells",
                   "20260824-101905-cli-144cells", "20260824-072840-cli-144cells"]
PRS = [
    ("11059", "calcom/cal.com#11059", 9), ("4", "discourse-graphite#4", 8),
    ("10", "discourse-graphite#10", 7), ("14740", "calcom/cal.com#14740", 6),
    ("8", "discourse-graphite#8", 6), ("10967", "calcom/cal.com#10967", 6),
]

def load_registry(batch):
    if not REG.exists(): return []
    out = []
    for line in REG.read_text().splitlines():
        if not line.strip(): continue
        try: e = json.loads(line)
        except: continue
        if e.get("run_batch") == batch: out.append(e)
    return out

def _dedup_latest(rows):
    """Latest run per (framework, model, effort, url) — fill-ins supersede originals."""
    latest = {}
    for r in rows:
        sp = r.get("summary_path")
        if not sp: continue
        try: s = json.load(open(sp))
        except: continue
        key = (r.get("framework"), r.get("model"), r.get("effort"), s.get("url",""))
        prev = latest.get(key)
        if prev is None or r.get("registered_at","") >= prev.get("registered_at",""):
            latest[key] = r
    return list(latest.values())

def _cell_key_full(r):
    sp = r.get("summary_path"); url = ""
    if sp:
        try: s = json.load(open(sp)); url = s.get("url","")
        except: pass
    return (r.get("framework"), r.get("model"), r.get("effort"), url)

START_RE = re.compile(r"^\[mx\] \[(\d+)/\d+\] (\S+) (\S+) (\S+) \.\.\.$")
DONE_RE  = re.compile(r"^\[mx\] \[(\d+)/\d+\] (\S+) (\S+) (\S+) TP=(\d+) FP=(\d+) FN=(\d+) rec=([\d.]+) adj_p=([\d.]+) incr_r=([\d.]+) real=(\d+) hal=(\d+) ([\d,]+)tok (\d+)s")
ERR_RE   = re.compile(r"^\[mx\] \[(\d+)/\d+\] (\S+) (\S+) (\S+) ERR (\d+)s: (.*)$")

def parse_log(path):
    cells = {}
    if not path.exists(): return cells
    for line in path.read_text().splitlines():
        m = START_RE.match(line)
        if m:
            i = int(m.group(1)); cells[i] = {"idx":i,"fw":m.group(2),"model":m.group(3),"effort":m.group(4),"status":"running"}
            continue
        m = DONE_RE.match(line)
        if m:
            i = int(m.group(1))
            cells[i] = {"idx":i,"fw":m.group(2),"model":m.group(3),"effort":m.group(4),"status":"done",
                        "tp":int(m.group(5)),"fp":int(m.group(6)),"fn":int(m.group(7)),
                        "recall":float(m.group(8)),"adj_p":float(m.group(9)),
                        "incr_r":float(m.group(10)),"real":int(m.group(11)),"hal":int(m.group(12)),
                        "tokens":int(m.group(13).replace(",","")),"wall_s":int(m.group(14))}
            continue
        m = ERR_RE.match(line)
        if m:
            i = int(m.group(1))
            cells[i] = {"idx":i,"fw":m.group(2),"model":m.group(3),"effort":m.group(4),"status":"fail",
                        "wall_s":int(m.group(5)),"error":m.group(6)[:160]}
    return cells

def process_status():
    pid = None
    if PID_FILE.exists():
        try: pid = int(PID_FILE.read_text().strip())
        except: pass
    running = False; etime = ""
    if pid:
        try:
            os.kill(pid, 0); running = True
            etime = subprocess.run(["ps","-o","etime=","-p",str(pid)], capture_output=True, text=True).stdout.strip()
        except: pass
    return {"running": running, "pid": pid, "etime": etime}

def agg(rows, keys):
    g = defaultdict(lambda: {"tp":0,"fp":0,"fn":0,"hal":0,"real":0,"tok_in":0,"tok_out":0,"wall":0.0,"n":0})
    for r in rows:
        m = r.get("metrics", {}) or {}
        k = tuple(r[k] for k in keys)
        b = g[k]
        b["tp"] += m.get("tp",0) or 0; b["fp"] += m.get("fp",0) or 0; b["fn"] += m.get("fn",0) or 0
        b["hal"] += m.get("n_hallucination",0) or 0; b["real"] += m.get("n_real_ungold",0) or 0
        b["tok_in"] += r.get("tokens_in",0) or 0; b["tok_out"] += r.get("tokens_out",0) or 0
        b["wall"] += r.get("wall_s",0) or 0; b["n"] += 1
    return g

def fmt_row(v):
    rec = v["tp"]/(v["tp"]+v["fn"]) if (v["tp"]+v["fn"]) else 0
    adjp = v["tp"]/(v["tp"]+v["hal"]) if (v["tp"]+v["hal"]) else 0
    incr = (v["tp"]+v["real"])/(v["tp"]+v["fn"]+v["real"]) if (v["tp"]+v["fn"]+v["real"]) else 0
    return rec, adjp, incr

# cross-batch calibration helpers (same as 082 tracker)
def _fw_cells_by_key(batch, framework, only_pass=True):
    out = {}
    for line in (REG.read_text().splitlines() if REG.exists() else []):
        if not line.strip(): continue
        try: e = json.loads(line)
        except: continue
        if e.get("run_batch") != batch or e.get("framework") != framework: continue
        if only_pass and e.get("status") != "pass": continue
        if e.get("model") not in MODELS or e.get("effort") not in EFFORTS: continue
        sp = e.get("summary_path")
        if not sp: continue
        try: s = json.load(open(sp))
        except: continue
        k = (e["model"], e["effort"], s.get("url","").rstrip("/").rsplit("/",1)[-1])
        m = e.get("metrics",{}) or {}
        out[k] = {"tp":m.get("tp",0) or 0,"fp":m.get("fp",0) or 0,"fn":m.get("fn",0) or 0,
                  "hal":m.get("n_hallucination",0) or 0,"real":m.get("n_real_ungold",0) or 0,
                  "tok_in":e.get("tokens_in",0) or 0,"tok_out":e.get("tokens_out",0) or 0}
    return out

def _calibrate_earlier(batch, cur_van_keys, cur_van_cells):
    random.seed(1)
    ev = _fw_cells_by_key(batch, "vanilla-engineered")
    matched = [k for k in cur_van_keys if k in ev]
    if not matched: return None
    earlier = [ev[k] for k in matched]; curm = [cur_van_cells[k] for k in matched]
    te = sum(c["tp"] for c in earlier); fe = sum(c["fn"] for c in earlier)
    tv = sum(c["tp"] for c in curm); fv = sum(c["fn"] for c in curm)
    re_ = te/(te+fe) if (te+fe) else 0; rv_ = tv/(tv+fv) if (tv+fv) else 0
    pairs = list(zip(earlier, curm)); bs = []
    for _ in range(2000):
        idx = [random.randrange(len(pairs)) for _ in range(len(pairs))]
        tpe = sum(pairs[i][0]["tp"] for i in idx); fne = sum(pairs[i][0]["fn"] for i in idx)
        tpv = sum(pairs[i][1]["tp"] for i in idx); fnv = sum(pairs[i][1]["fn"] for i in idx)
        bs.append((tpv/(tpv+fnv) if (tpv+fnv) else 0) - (tpe/(tpe+fne) if (tpe+fne) else 0))
    bs.sort()
    lo = bs[int(0.025*len(bs))]; hi = bs[int(0.975*len(bs))]
    return {"batch":batch,"matched_keys":matched,"n_matched":len(matched),
            "earlier_recall":re_,"v2_recall":rv_,"diff":rv_-re_,"ci_lo":lo,"ci_hi":hi,"calibrated":(lo<=0<=hi)}

def main():
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    reg = load_registry(BATCH)
    reg_latest = _dedup_latest(reg)
    log_cells = parse_log(OUT_LOG)
    ps = process_status()

    n_filled = len(reg) - len(reg_latest)
    eff_cells = len(reg_latest)
    pass_n = sum(1 for r in reg_latest if r["status"] == "pass")
    fail_n = sum(1 for r in reg_latest if r["status"] != "pass")
    log_done = sum(1 for c in log_cells.values() if c["status"] == "done")
    log_fail = sum(1 for c in log_cells.values() if c["status"] == "fail")
    log_finished = log_done + log_fail
    log_running = sum(1 for c in log_cells.values() if c["status"] == "running")
    in_flight = [c for c in log_cells.values() if c["status"] == "running"]

    walls = [c["wall_s"] for c in log_cells.values() if c["status"] in ("done","fail") and c.get("wall_s")]
    avg_wall = sum(walls)/len(walls) if walls else 0
    remaining = TOTAL_CELLS - 53 - log_finished  # 53 skipped, rest must run
    eta_s = (remaining * avg_wall / CONCURRENCY) if avg_wall else 0

    g_fme = agg(reg_latest, ["framework","model","effort"])
    g_fw = agg(reg_latest, ["framework"])
    g_model = agg(reg_latest, ["model"])
    g_eff = agg(reg_latest, ["effort"])

    pr_hits = defaultdict(lambda: {"n":0,"tp":0,"fn":0,"fp":0,"hal":0,"real":0})
    for r in reg_latest:
        sp = r.get("summary_path")
        if not sp: continue
        try: s = json.load(open(sp))
        except: continue
        num = s.get("url","").rstrip("/").rsplit("/",1)[-1]
        m = r.get("metrics",{}) or {}
        b = pr_hits[num]; b["n"] += 1; b["tp"] += m.get("tp",0) or 0; b["fn"] += m.get("fn",0) or 0
        b["fp"] += m.get("fp",0) or 0; b["hal"] += m.get("n_hallucination",0) or 0; b["real"] += m.get("n_real_ungold",0) or 0

    L = []
    L.append(f"# Batch 083 fullmatrix partial analysis — {now}")
    L.append("")
    L.append(f"**Batch:** `{BATCH}`")
    L.append("")
    L.append("Matrix: **6 PRs × 4 models × 4 efforts × 4 frameworks = 384 cells** (331 new + 53 skipped) · "
             "mode=cli (OAuth) · concurrency=3")
    L.append(f"**Models:** {', '.join(MODELS)}")
    L.append(f"**Efforts:** {', '.join(EFFORTS)}")
    L.append(f"**Frameworks:** {', '.join(FRAMEWORKS)}")
    L.append("Judges: cross-family (claude-* → gpt-5.2; gpt-* → claude-opus-4-5).")
    L.append("")
    st = "RUNNING" if ps["running"] else "FINISHED"
    L.append(f"**Status:** {st}" + (f"  ·  pid={ps['pid']}  ·  etime={ps['etime']}" if ps["running"] else ""))
    L.append("")
    L.append("## Progress")
    L.append("")
    L.append(f"- Cells finished in stdout log: **{log_finished}/331** (done={log_done}, fail={log_fail})")
    if n_filled > 0:
        L.append(f"- Runs registered: **{len(reg)}** (raw) → **{eff_cells}** effective after dedup · "
                 f"pass={pass_n}, fail={fail_n} · {n_filled} fill-in rerun(s) superseded")
    else:
        L.append(f"- Cells registered (effective): **{eff_cells}/384** (pass={pass_n}, fail={fail_n})")
    L.append(f"- In-flight right now: **{log_running}** cells")
    if in_flight:
        for c in in_flight[:6]:
            L.append(f"  - `[{c['idx']}]` {c['fw']} / {c['model']} / {c['effort']}")
        if len(in_flight) > 6: L.append(f"  - ... and {len(in_flight)-6} more")
    if avg_wall:
        L.append(f"- Avg wall per finished cell: **{avg_wall:.0f}s** · remaining {remaining} cells → ETA **~{eta_s/60:.0f} min** ({eta_s/3600:.1f}h)")
    L.append(f"- Tokens printed so far (log, done cells): {sum(c.get('tokens',0) for c in log_cells.values() if c['status']=='done'):,}")
    L.append("")
    pct = log_finished/max(331,1)
    bar = "█"*int(pct*40) + "░"*(40-int(pct*40))
    L.append(f"  `{bar}` {pct*100:.0f}%")
    L.append("")

    # aggregates per framework / model / effort
    def marginal_table(title, gmap, label):
        L.append(f"## {title} (completed cells)")
        L.append("")
        L.append(f"| {label} | cells | TP | FP | FN | recall | adj_p | incr_r | hidden gold | hal | tok |")
        L.append(f"|---|---|---|---|---|---|---|---|---|---|---|")
        for k in sorted(gmap):
            v = gmap[k]; rec,adjp,incr = fmt_row(v)
            L.append(f"| {k} | {v['n']} | {v['tp']} | {v['fp']} | {v['fn']} | {rec:.2f} | {adjp:.2f} | {incr:.2f} | {v['real']} | {v['hal']} | {v['tok_in']+v['tok_out']:,} |")
        L.append("")
    marginal_table("Aggregates per framework", g_fw, "framework")
    marginal_table("Aggregates per model", g_model, "model")
    marginal_table("Aggregates per effort", g_eff, "effort")

    # per (fw, model, effort) — the full grid
    L.append("## Aggregates per (framework × model × effort) — completed cells only")
    L.append("")
    L.append("| fw | model | effort | cells | TP | FN | recall | adj_p | incr_r | hidden gold | hal | tok |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for fw in FRAMEWORKS:
        for model in MODELS:
            for eff in EFFORTS:
                v = g_fme.get((fw, model, eff))
                if not v: continue
                rec,adjp,incr = fmt_row(v)
                L.append(f"| {fw} | {model} | {eff} | {v['n']}/6 | {v['tp']} | {v['fn']} | {rec:.2f} | {adjp:.2f} | {incr:.2f} | {v['real']} | {v['hal']} | {v['tok_in']+v['tok_out']:,} |")
    L.append("")

    # per-PR coverage
    L.append("## Per-PR coverage (completed cells so far)")
    L.append("")
    L.append("| PR | label | cells done | TP | FN | FP | hal | hidden gold | per-cell recall |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for num, label, _ in PRS:
        b = pr_hits.get(num)
        if not b:
            L.append(f"| {num} | {label} | 0/64 | — | — | — | — | — | — |"); continue
        rec = b["tp"]/(b["tp"]+b["fn"]) if (b["tp"]+b["fn"]) else 0
        L.append(f"| {num} | {label} | {b['n']}/64 | {b['tp']} | {b['fn']} | {b['fp']} | {b['hal']} | {b['real']} | {rec:.2f} |")
    L.append("")
    L.append("> Per-PR denominator is 64 cells = 4 frameworks × 4 models × 4 efforts.")
    L.append("")

    # cross-batch calibration
    cur_van = _fw_cells_by_key(BATCH, "vanilla-engineered")
    cur_van_keys = list(cur_van.keys())
    L.append("## Cross-batch calibration (vanilla-engineered = control arm)")
    L.append("")
    L.append("An earlier batch's compound/superpowers/mrv numbers are only comparable to 083 if vanilla-engineered "
             "in that batch is within margin of error of vanilla in 083 on matched (model×effort×PR) cells.")
    L.append("")
    L.append("| earlier batch | matched | earlier vanilla recall | 083 vanilla recall | Δ | 95% CI | calibrated? |")
    L.append("|---|---|---|---|---|---|---|")
    calib = []
    for b in EARLIER_BATCHES:
        res = _calibrate_earlier(b, cur_van_keys, cur_van)
        if res is None:
            L.append(f"| {b} | 0 | — | — | — | — | (no overlap) |"); continue
        calib.append(res)
        v = "✅ YES" if res["calibrated"] else "❌ NO"
        L.append(f"| {b} | {res['n_matched']} | {res['earlier_recall']:.3f} | {res['v2_recall']:.3f} | {res['diff']:+.3f} | [{res['ci_lo']:+.3f}, {res['ci_hi']:+.3f}] | {v} |")
    L.append("")

    # hidden gold × effort × framework (the key view)
    L.append("## Hidden gold & hallucinations by framework × effort (matched workload if calibrated)")
    L.append("")
    L.append("**Metrics:** `recall` = TP/(TP+FN). `hidden gold` = `n_real_ungold` = real bugs found NOT in golden set. "
             "`hallucinations` = `n_hallucination` = false positives adjudicated NOT real. `incr_recall` = (TP+hidden_gold)/(TP+FN+hidden_gold).")
    L.append("")
    L.append("### 083 batch (all completed cells, self-contained)")
    L.append("")
    L.append("| framework | effort | n | TP | FN | recall | hidden gold | /cell | incr_r | hal | /cell | tok |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    # aggregate per (fw, effort) across all models
    g_fe = defaultdict(lambda: {"tp":0,"fn":0,"real":0,"hal":0,"tok":0,"n":0})
    for r in reg_latest:
        m = r.get("metrics",{}) or {}
        k = (r.get("framework"), r.get("effort"))
        b = g_fe[k]
        b["tp"] += m.get("tp",0) or 0; b["fn"] += m.get("fn",0) or 0
        b["real"] += m.get("n_real_ungold",0) or 0; b["hal"] += m.get("n_hallucination",0) or 0
        b["tok"] += (r.get("tokens_in",0) or 0) + (r.get("tokens_out",0) or 0); b["n"] += 1
    for fw in FRAMEWORKS:
        for eff in EFFORTS:
            b = g_fe.get((fw, eff))
            if not b or b["n"] == 0: continue
            rec = b["tp"]/(b["tp"]+b["fn"]) if (b["tp"]+b["fn"]) else 0
            ir = (b["tp"]+b["real"])/(b["tp"]+b["fn"]+b["real"]) if (b["tp"]+b["fn"]+b["real"]) else 0
            hg = b["real"]/b["n"] if b["n"] else 0; hal = b["hal"]/b["n"] if b["n"] else 0
            L.append(f"| {fw} | {eff} | {b['n']} | {b['tp']} | {b['fn']} | {rec:.2f} | {b['real']} | {hg:.1f} | {ir:.2f} | {b['hal']} | {hal:.1f} | {b['tok']:,} |")
    L.append("")

    # notes & anomalies
    L.append("## Notes & anomalies")
    L.append("")
    fails = [r for r in reg_latest if r["status"] != "pass"]
    orig_fails = [r for r in reg if r["status"] != "pass"]
    filled_in = []
    if orig_fails:
        latest_pass_keys = {_cell_key_full(r) for r in reg_latest if r["status"] == "pass"}
        for r in orig_fails:
            if _cell_key_full(r) in latest_pass_keys: filled_in.append(r)
    log_fails = [c for c in log_cells.values() if c["status"] == "fail"]
    if filled_in:
        L.append(f"- 🔧 **{len(filled_in)} cell(s) originally errored, now FILLED IN**:")
        for r in filled_in:
            url = _cell_key_full(r)[-1] or ""
            L.append(f"  - {r['model']} / {r['effort']} / {r['framework']} (PR {url.rstrip('/').rsplit('/',1)[-1] or '?'}) — orig id={r['run_id']}")
    if log_fails:
        L.append(f"- ❌ **{len(log_fails)} cell(s) errored in the live log**:")
        for c in log_fails[:10]:
            L.append(f"  - `[{c['idx']}]` {c['fw']} / {c['model']} / {c['effort']} · {c.get('wall_s','?')}s · {c.get('error','')}")
        if len(log_fails) > 10: L.append(f"  - ... and {len(log_fails)-10} more")
    if fails:
        L.append(f"- ⚠️ {len(fails)} cell(s) still failing: " + ", ".join(f"{r['model']}/{r['effort']}/{r['framework']}" for r in fails[:10]))
    if not fails and not log_fails and not filled_in:
        L.append("- No anomalies detected so far.")
    L.append("")
    L.append("---")
    L.append(f"_Snapshot generated by `bin/track_batch_083.py` at {now}._")
    md = "\n".join(L)
    TRACKER_MD.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_MD.write_text(md)
    with HISTORY.open("a") as f: f.write(json.dumps({"ts":now,"running":ps["running"],"log_finished":log_finished,"eff_cells":eff_cells,"pass":pass_n,"fail":fail_n,"eta_min":eta_s/60 if avg_wall else None})+"\n")
    print(md)

if __name__ == "__main__":
    main()
