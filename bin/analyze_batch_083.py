#!/usr/bin/env python3
"""Rolling analysis for batch 20260825-batch-083-fullmatrix (the definitive 4x4x4 matrix).

4 frameworks x 4 models x 4 efforts x 6 PRs = 384 cells (331 new + 53 skipped).
Fuses the run registry (completed cells) + live stdout log (in-flight) + per-run
summary.json (accurate per-model token & $ breakdown).

Reports: recall, (raw + adjudicated) precision, hidden gold, hallucinations, token
spend, REPORTED $ (real Anthropic billing w/ cache; GPT=0 via OAuth) and IMPLIED $
(= reported + GPT at estimated per-token rates), cross-batch comparison vs the
predecessor batches, and a linear extrapolation of total batch spend.

Usage: uv run python bin/analyze_batch_083.py
"""
from __future__ import annotations
import json, re, os, subprocess, time, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/dsifry/Developer/harnesseval")
BATCH = "20260825-batch-083-fullmatrix"
REG = ROOT / "runs" / "registry.jsonl"
OUT_LOG = Path("/tmp/batch_083_out.txt")
PID_FILE = Path("/tmp/batch_083_pid.txt")
ANALYSIS_MD = ROOT / "results" / "batch_083_ANALYSIS.md"
HISTORY = ROOT / "results" / "batch_083_analysis_history.jsonl"
TOTAL_CELLS = 384
NEW_CELLS = 331
CONCURRENCY = 3
FRAMEWORKS = ["vanilla-engineered", "metareview-realistic", "compound-realistic", "superpowers-realistic"]
MODELS = ["claude-opus-5", "gpt-5.6-sol", "claude-sonnet-5", "gpt-5.6-terra"]
EFFORTS = ["low", "medium", "high", "xhigh"]
PRS = [
    ("11059", "calcom/cal.com#11059", 9), ("4", "discourse-graphite#4", 8),
    ("10", "discourse-graphite#10", 7), ("14740", "calcom/cal.com#14740", 6),
    ("8", "discourse-graphite#8", 6), ("10967", "calcom/cal.com#10967", 6),
]
PR_BY_NUM = {n: (l, g) for n, l, g in PRS}
EARLIER_BATCHES = [
    ("20260825-batch-082-v2-mrv-vanilla-opus-codex-48cells", "082-v2 (48c, direct predecessor)"),
    ("20260824-101905-cli-144cells", "0824-1019 (144c)"),
    ("20260824-072840-cli-144cells", "0824-0728 (144c)"),
]

# --- Pricing (pinned 2026-08-22) -------------------------------------------------
# Anthropic: we use the ACTUAL reported cost_usd from per_model_usage (real billing
# with cache discounts) -- validated to reconcile exactly with the pinned table for
# haiku, and opus/sonnet use the same provider-reported number (no estimation).
# GPT models report $0 via OAuth/subscription, so their TRUE marginal cost is hidden;
# IMPLIED $ applies the ESTIMATED per-1M-token rates below (UNVERIFIED, clearly labeled).
GPT_EST_RATE = {  # per 1M tokens, ESTIMATED, pinned 2026-08-22
    "gpt-5.6-sol":   {"in": 1.25, "out": 10.00},
    "gpt-5.6-terra": {"in": 2.50, "out": 20.00},
    "gpt-5.2":       {"in": 1.25, "out": 10.00},
    # gpt-6-astra: fetched from platform.openai.com/docs/pricing STANDARD tier on 2026-09-06
    # (in $10.00 / cached $1.00 / out $12.50 per 1M). Note: the 2026-08-22 sol/terra pins above
    # do not match the current page (sol standard is now $4.00 in / $5.00 out) -- historical
    # cells keep their original pin for consistency; astra uses its own dated pin.
    "gpt-6-astra":   {"in": 10.00, "out": 12.50},
}
ANTHRO_MODELS = {"claude-opus-5", "claude-sonnet-5", "claude-opus-4-5-20251101",
                 "claude-haiku-4-5-20251001", "claude-opus-4-8", "claude-fable-5",
                 "claude-sonnet-4-5-20250929"}

def gpt_implied_cost(pmu: dict) -> float:
    """Implied $ for GPT models from per_model_usage tokens at ESTIMATED rates."""
    tot = 0.0
    for m, u in (pmu or {}).items():
        r = GPT_EST_RATE.get(m)
        if not r:
            continue
        tot += (u.get("input_tokens", 0) * r["in"] + u.get("output_tokens", 0) * r["out"]
                + u.get("reasoning_output_tokens", 0) * r["out"]) / 1e6
    return tot

def reported_cost(pmu: dict) -> float:
    return sum((u.get("cost_usd", 0) or 0) for u in (pmu or {}).values())

# --- Registry / summaries -------------------------------------------------------
def load_registry(batch):
    if not REG.exists():
        return []
    out = []
    for line in REG.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("run_batch") == batch:
            out.append(e)
    return out

def _url_of(r):
    sp = r.get("summary_path")
    if not sp:
        return ""
    try:
        return (json.load(open(sp))).get("url", "")
    except Exception:
        return ""

def _cell_key(r, url=None):
    if url is None:
        url = _url_of(r)
    return (r.get("framework"), r.get("model"), r.get("effort"), url)

def dedup_latest(rows):
    latest = {}
    for r in rows:
        sp = r.get("summary_path")
        if not sp or r.get("status") != "pass":
            continue
        key = _cell_key(r)
        prev = latest.get(key)
        if prev is None or r.get("registered_at", "") >= prev.get("registered_at", ""):
            latest[key] = r
    return list(latest.values())

def cell_metrics(r):
    """Load summary.json -> dict with metrics + accurate tokens/$ from per_model_usage."""
    sp = r.get("summary_path")
    base = {"tp": 0, "fp": 0, "fn": 0, "precision": 0.0, "recall": 0.0,
            "adj_p": 0.0, "incr_r": 0.0, "real": 0, "hal": 0,
            "tok_in": 0, "tok_out": 0, "tok": 0, "rep_usd": 0.0, "imp_usd": 0.0,
            "wall_s": r.get("wall_s", 0) or 0, "pmu": {}, "url": _url_of(r),
            "framework": r.get("framework"), "model": r.get("model"), "effort": r.get("effort")}
    if not sp or not Path(sp).exists():
        # fallback to registry fields
        m = r.get("metrics", {}) or {}
        base.update({"tp": m.get("tp",0),"fp": m.get("fp",0),"fn": m.get("fn",0),
                     "precision": m.get("precision",0),"recall": m.get("recall",0),
                     "adj_p": m.get("adjudicated_precision",0),"incr_r": m.get("incremental_recall",0),
                     "real": m.get("n_real_ungold",0),"hal": m.get("n_hallucination",0),
                     "tok_in": r.get("tokens_in",0) or 0,"tok_out": r.get("tokens_out",0) or 0,
                     "tok": (r.get("tokens_in",0) or 0)+(r.get("tokens_out",0) or 0),
                     "rep_usd": r.get("cost_usd",0) or 0})
        base["imp_usd"] = base["rep_usd"]
        return base
    try:
        s = json.load(open(sp))
    except Exception:
        return base
    m = s.get("metrics", {}) or {}
    if not m and "tp" in s:
        m = s
    pmu = s.get("per_model_usage", {}) or {}
    tok_in = sum(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                 + u.get("cache_creation_input_tokens", 0) for u in pmu.values()) or s.get("tokens_in", 0)
    tok_out = sum(u.get("output_tokens", 0) + u.get("reasoning_output_tokens", 0) for u in pmu.values()) or s.get("tokens_out", 0)
    rep = reported_cost(pmu) or (s.get("total_cost_usd", 0) or 0)
    imp = rep + gpt_implied_cost(pmu)
    base.update({
        "tp": m.get("tp", 0), "fp": m.get("fp", 0), "fn": m.get("fn", 0),
        "precision": m.get("precision", 0.0), "recall": m.get("recall", 0.0),
        "adj_p": m.get("adjudicated_precision", 0.0), "incr_r": m.get("incremental_recall", 0.0),
        "real": m.get("n_real_ungold", 0), "hal": m.get("n_hallucination", 0),
        "tok_in": tok_in, "tok_out": tok_out, "tok": tok_in + tok_out,
        "rep_usd": rep, "imp_usd": imp, "pmu": pmu,
        "wall_s": s.get("wall_s", r.get("wall_s", 0)) or 0,
        "url": s.get("url", ""),
    })
    return base

# --- Live stdout log parsing ----------------------------------------------------
START_RE = re.compile(r"^\[mx\] \[(\d+)/\d+\] (\S+) (\S+) (\S+) \.\.\.$")
DONE_RE = re.compile(r"^\[mx\] \[(\d+)/\d+\] (\S+) (\S+) (\S+) TP=(\d+) FP=(\d+) FN=(\d+) rec=([\d.]+) adj_p=([\d.]+) incr_r=([\d.]+) real=(\d+) hal=(\d+) ([\d,]+)tok (\d+)s")
ERR_RE = re.compile(r"^\[mx\] \[(\d+)/\d+\] (\S+) (\S+) (\S+) ERR (\d+)s: (.*)$")

def parse_log(path):
    cells = {}
    if not path.exists():
        return cells, 0
    tok_done = 0
    for line in path.read_text().splitlines():
        m = START_RE.match(line)
        if m:
            i = int(m.group(1)); cells[i] = {"idx": i, "fw": m.group(2), "model": m.group(3), "effort": m.group(4), "status": "running"}
            continue
        m = DONE_RE.match(line)
        if m:
            i = int(m.group(1))
            cells[i] = {"idx": i, "fw": m.group(2), "model": m.group(3), "effort": m.group(4), "status": "done",
                        "tp": int(m.group(5)), "fp": int(m.group(6)), "fn": int(m.group(7)),
                        "recall": float(m.group(8)), "adj_p": float(m.group(9)), "incr_r": float(m.group(10)),
                        "real": int(m.group(11)), "hal": int(m.group(12)), "tok": int(m.group(13).replace(",", "")),
                        "wall_s": int(m.group(14))}
            tok_done += cells[i]["tok"]
            continue
        m = ERR_RE.match(line)
        if m:
            i = int(m.group(1))
            cells[i] = {"idx": i, "fw": m.group(2), "model": m.group(3), "effort": m.group(4), "status": "fail",
                        "wall_s": int(m.group(5)), "error": m.group(6)}
    return cells, tok_done

def proc_status():
    running, pid, etime = False, None, ""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            running = (pid and subprocess.run(["kill", "-0", str(pid)], capture_output=True).returncode == 0)
            if running:
                ps = subprocess.run(["ps", "-o", "etime=", "-p", str(pid)], capture_output=True, text=True)
                etime = ps.stdout.strip()
        except Exception:
            pass
    return {"running": running, "pid": pid, "etime": etime}

# --- Aggregation helpers -------------------------------------------------------
def agg(cells):
    n = len(cells)
    if n == 0:
        return None
    tp = sum(c["tp"] for c in cells); fp = sum(c["fp"] for c in cells); fn = sum(c["fn"] for c in cells)
    real = sum(c["real"] for c in cells); hal = sum(c["hal"] for c in cells)
    tok = sum(c["tok"] for c in cells); rep = sum(c["rep_usd"] for c in cells); imp = sum(c["imp_usd"] for c in cells)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    ir = (tp + real) / (tp + fn + real) if (tp + fn + real) else 0.0
    return {"n": n, "tp": tp, "fp": fp, "fn": fn, "prec": prec, "recall": rec, "adj_p": sum(c["adj_p"] for c in cells) / n,
            "incr_r": ir, "real": real, "hal": hal, "tok": tok, "rep": rep, "imp": imp,
            "real_cell": real / n, "hal_cell": hal / n, "tok_cell": tok / n, "rep_cell": rep / n, "imp_cell": imp / n}

def fmt_money(x):
    return f"${x:,.2f}" if x >= 1 else f"${x:.4f}"

def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ps = proc_status()
    reg = load_registry(BATCH)
    reg_latest = dedup_latest(reg)
    cells = [cell_metrics(r) for r in reg_latest]
    cells = [c for c in cells if c["tp"] + c["fp"] + c["fn"] > 0 or c["recall"] > 0 or c["incr_r"] > 0]
    log_cells, log_tok_done = parse_log(OUT_LOG)
    log_done = [c for c in log_cells.values() if c["status"] == "done"]
    log_fail = [c for c in log_cells.values() if c["status"] == "fail"]
    log_running = [c for c in log_cells.values() if c["status"] == "running"]
    eff_cells = len(cells)
    n_done_log = len(log_done)
    avg_wall = (sum(c["wall_s"] for c in log_done) / len(log_done)) if log_done else 0
    remaining = max(0, NEW_CELLS - n_done_log)
    eta_s = (remaining / CONCURRENCY) * avg_wall if avg_wall else 0
    eta_min = eta_s / 60

    L = []
    L.append(f"# Batch 083 fullmatrix — rolling analysis · {now}")
    L.append("")
    status = 'RUNNING' if ps['running'] else 'FINISHED/DEAD'
    pidpart = ''
    if ps['running']:
        pidpart = ' · pid=' + str(ps['pid']) + ' · etime=' + str(ps['etime'])
    L.append('**Batch:** `' + BATCH + '` · status: **' + status + '**' + pidpart)
    L.append(f"Matrix: **6 PRs × 4 models × 4 efforts × 4 frameworks = {TOTAL_CELLS} cells** "
             f"({NEW_CELLS} new + {TOTAL_CELLS-NEW_CELLS} skipped) · concurrency={CONCURRENCY} · mode=cli (OAuth)")
    L.append(f"Models: {', '.join(MODELS)} · Efforts: {', '.join(EFFORTS)} · Frameworks: {', '.join(FRAMEWORKS)}")
    L.append("")
    L.append("## Progress")
    L.append("")
    pct = n_done_log / NEW_CELLS * 100 if NEW_CELLS else 0
    bar_len = 40; filled = int(bar_len * pct / 100)
    L.append(f"- Cells finished in stdout log: **{n_done_log}/{NEW_CELLS}** (fail={len(log_fail)})")
    L.append(f"- Cells registered (effective, deduped): **{eff_cells}/{TOTAL_CELLS}**")
    L.append(f"- In-flight right now: **{len(log_running)}** cells" +
             (": " + ", ".join(f"`[{c['idx']}]` {c['fw']}/{c['model']}/{c['effort']}" for c in log_running) if log_running else ""))
    L.append(f"- Avg wall per finished cell: **{avg_wall:.0f}s** · remaining {remaining} cells → ETA **~{eta_min:.0f} min** ({eta_min/60:.1f}h)")
    L.append(f"- Log tokens (done cells): {log_tok_done:,}")
    L.append("")
    L.append(f"  `{'█'*filled}{'░'*(bar_len-filled)}` {pct:.1f}%")
    L.append("")

    # ---- Overall totals ----
    tot = agg(cells) if cells else None
    if tot:
        L.append("## Overall (completed cells so far)")
        L.append("")
        L.append(f"- **Recall** {tot['recall']:.3f} · **Precision (raw)** {tot['prec']:.3f} · **Adjudicated precision** {tot['adj_p']:.3f} · **Incremental recall** {tot['incr_r']:.3f}")
        L.append(f"- **Hidden gold** {tot['real']} ({tot['real_cell']:.1f}/cell) · **Hallucinations** {tot['hal']} ({tot['hal_cell']:.1f}/cell)")
        L.append(f"- **Tokens** {tot['tok']:,} ({tot['tok_cell']:,.0f}/cell)")
        L.append(f"- **Reported $** {fmt_money(tot['rep'])} ({fmt_money(tot['rep_cell'])}/cell) — real Anthropic billing w/ cache; GPT=$0 via OAuth")
        L.append(f"- **Implied $ (est.)** {fmt_money(tot['imp'])} ({fmt_money(tot['imp_cell'])}/cell) — adds GPT at estimated per-token rates")
        L.append("")

    # ---- per framework ----
    L.append("## Per framework (completed cells)")
    L.append("")
    L.append("| framework | n | TP | FP | FN | recall | prec | adj_p | incr_r | hidden | /cell | hal | /cell | tok | rep$ | imp$ |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for fw in FRAMEWORKS:
        b = agg([c for c in cells if reg_fw(c) == fw])
        if not b: continue
        L.append(f"| {fw} | {b['n']} | {b['tp']} | {b['fp']} | {b['fn']} | {b['recall']:.2f} | {b['prec']:.2f} | {b['adj_p']:.2f} | {b['incr_r']:.2f} | {b['real']} | {b['real_cell']:.1f} | {b['hal']} | {b['hal_cell']:.1f} | {b['tok']:,} | {fmt_money(b['rep'])} | {fmt_money(b['imp'])} |")
    L.append("")

    # ---- per model ----
    L.append("## Per model (completed cells)")
    L.append("")
    L.append("| model | n | TP | FP | FN | recall | prec | adj_p | incr_r | hidden | /cell | hal | /cell | tok | rep$ | imp$ | imp$/cell |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for mdl in MODELS:
        b = agg([c for c in cells if reg_model(c) == mdl])
        if not b: continue
        L.append(f"| `{mdl}` | {b['n']} | {b['tp']} | {b['fp']} | {b['fn']} | {b['recall']:.2f} | {b['prec']:.2f} | {b['adj_p']:.2f} | {b['incr_r']:.2f} | {b['real']} | {b['real_cell']:.1f} | {b['hal']} | {b['hal_cell']:.1f} | {b['tok']:,} | {fmt_money(b['rep'])} | {fmt_money(b['imp'])} | {fmt_money(b['imp_cell'])} |")
    L.append("")

    # ---- per effort ----
    L.append("## Per effort (completed cells)")
    L.append("")
    L.append("| effort | n | TP | FP | FN | recall | prec | adj_p | incr_r | hidden | /cell | hal | /cell | tok | rep$ | imp$ |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for eff in EFFORTS:
        b = agg([c for c in cells if reg_effort(c) == eff])
        if not b: continue
        L.append(f"| {eff} | {b['n']} | {b['tp']} | {b['fp']} | {b['fn']} | {b['recall']:.2f} | {b['prec']:.2f} | {b['adj_p']:.2f} | {b['incr_r']:.2f} | {b['real']} | {b['real_cell']:.1f} | {b['hal']} | {b['hal_cell']:.1f} | {b['tok']:,} | {fmt_money(b['rep'])} | {fmt_money(b['imp'])} |")
    L.append("")

    # ---- per (fw x model x effort) grid (completed) ----
    L.append("## Per framework × model × effort (completed cells)")
    L.append("")
    L.append("| fw | model | effort | n/6 | TP | FN | recall | adj_p | incr_r | hidden | hal | tok | imp$ |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    g = defaultdict(list)
    for c in cells:
        g[(reg_fw(c), reg_model(c), reg_effort(c))].append(c)
    for fw in FRAMEWORKS:
        for mdl in MODELS:
            for eff in EFFORTS:
                cs = g.get((fw, mdl, eff))
                if not cs: continue
                b = agg(cs)
                L.append(f"| {fw} | `{mdl}` | {eff} | {b['n']}/6 | {b['tp']} | {b['fn']} | {b['recall']:.2f} | {b['adj_p']:.2f} | {b['incr_r']:.2f} | {b['real']} | {b['hal']} | {b['tok']:,} | {fmt_money(b['imp'])} |")
    L.append("")

    # ---- $ breakdown by provider model (per_model_usage) ----
    L.append("## Spend breakdown by provider model (per_model_usage, completed cells)")
    L.append("")
    L.append("| provider model | n_cells | input tok | cache_read | cache_write | output tok | reasoning | reported $ | implied $ |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    pmu_tot = defaultdict(lambda: {"n": 0, "in": 0, "cr": 0, "cw": 0, "out": 0, "reason": 0, "rep": 0.0})
    for c in cells:
        for m, u in (c.get("pmu") or {}).items():
            b = pmu_tot[m]
            b["n"] += 1; b["in"] += u.get("input_tokens", 0) or 0
            b["cr"] += u.get("cache_read_input_tokens", 0) or 0
            b["cw"] += u.get("cache_creation_input_tokens", 0) or 0
            b["out"] += u.get("output_tokens", 0) or 0
            b["reason"] += u.get("reasoning_output_tokens", 0) or 0
            b["rep"] += u.get("cost_usd", 0) or 0
    rep_grand = 0.0; imp_grand = 0.0
    for m in sorted(pmu_tot, key=lambda x: -pmu_tot[x]["rep"]):
        b = pmu_tot[m]
        r = GPT_EST_RATE.get(m)
        imp = (b["rep"] + ((b["in"] * r["in"] + (b["out"] + b["reason"]) * r["out"]) / 1e6)) if r else b["rep"]
        rep_grand += b["rep"]; imp_grand += imp
        kind = "Anthropic (real)" if m in ANTHRO_MODELS else "GPT (est.)"
        L.append(f"| {m} {kind} | {b['n']} | {b['in']:,} | {b['cr']:,} | {b['cw']:,} | {b['out']:,} | {b['reason']:,} | {fmt_money(b['rep'])} | {fmt_money(imp)} |")
    L.append(f"| **TOTAL** | — | — | — | — | — | — | **{fmt_money(rep_grand)}** | **{fmt_money(imp_grand)}** |")
    L.append("")
    L.append(f"> **Reported $** = real Anthropic `cost_usd` (cache-discounted billing); GPT models report **$0** via OAuth/subscription so reported $ **understates** true cost. "
             f"**Implied $** adds GPT at *estimated* per-token rates (pinned 2026-08-22, **unverified**): "
             + "; ".join(f"{m} in ${r['in']}/out ${r['out']} per 1M" for m, r in GPT_EST_RATE.items()) + ".")
    L.append("")

    # ---- per-PR coverage ----
    L.append("## Per-PR coverage (completed cells)")
    L.append("")
    L.append("| PR | label | cells done | TP | FN | FP | hidden | hal | recall | tok | imp$ |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for num, label, gold in PRS:
        cs = [c for c in cells if c["url"].rstrip("/").rsplit("/", 1)[-1] == num]
        b = agg(cs) if cs else None
        if b:
            L.append(f"| {num} | {label} | {b['n']}/64 | {b['tp']} | {b['fn']} | {b['fp']} | {b['real']} | {b['hal']} | {b['recall']:.2f} | {b['tok']:,} | {fmt_money(b['imp'])} |")
        else:
            L.append(f"| {num} | {label} | 0/64 | — | — | — | — | — | — | — | — |")
    L.append("")

    # ---- cross-batch comparison ----
    def earlier_cells(batch):
        rows = load_registry(batch)
        rows = dedup_latest(rows)
        out = []
        for r in rows:
            c = cell_metrics(r)
            if c["tp"] + c["fp"] + c["fn"] > 0 or c["incr_r"] > 0:
                out.append(c)
        return out

    cur_keys = {_cell_key_from_metrics(c) for c in cells}
    L.append("## Cross-batch comparison (matched cells on framework×model×effort×PR)")
    L.append("")
    L.append("Each earlier batch is compared to 083 **only on cells present in both** (matched keys). "
             "Deltas are 083 − earlier; positive recall Δ = 083 improved. "
             "`vanilla-engineered` is the control arm — if 083 vanilla recall ≈ earlier vanilla recall on matched cells, "
             "the other frameworks are comparable.")
    L.append("")
    L.append("| earlier batch | matched | earlier recall | 083 recall | Δrec | earlier adj_p | 083 adj_p | Δadj_p | earlier hidden/cell | 083 hidden/cell | earlier hal/cell | 083 hal/cell | earlier imp$/cell | 083 imp$/cell |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for bname, blabel in EARLIER_BATCHES:
        ec = earlier_cells(bname)
        ekeys = {_cell_key_from_metrics(c) for c in ec}
        matched = cur_keys & ekeys
        if not matched:
            L.append(f"| {blabel} | 0 | — | — | — | — | — | — | — | — | — | — | — | — |")
            continue
        ec_m = [c for c in ec if _cell_key_from_metrics(c) in matched]
        cur_m = [c for c in cells if _cell_key_from_metrics(c) in matched]
        be = agg(ec_m); bv = agg(cur_m)
        L.append(f"| {blabel} | {len(matched)} | {be['recall']:.3f} | {bv['recall']:.3f} | {bv['recall']-be['recall']:+.3f} | "
                 f"{be['adj_p']:.3f} | {bv['adj_p']:.3f} | {bv['adj_p']-be['adj_p']:+.3f} | "
                 f"{be['real_cell']:.1f} | {bv['real_cell']:.1f} | {be['hal_cell']:.1f} | {bv['hal_cell']:.1f} | "
                 f"{fmt_money(be['imp_cell'])} | {fmt_money(bv['imp_cell'])} |")
    L.append("")

    # ---- extrapolation ----
    L.append("## Spend extrapolation (linear, to full 384-cell matrix)")
    L.append("")
    if tot and eff_cells > 0:
        frac = eff_cells / TOTAL_CELLS
        proj_tok = tot["tok"] / frac
        proj_rep = tot["rep"] / frac
        proj_imp = tot["imp"] / frac
        # also per-cell on the NEW cells only basis
        L.append(f"- Completed {eff_cells}/{TOTAL_CELLS} cells ({frac*100:.1f}%). At current per-cell rates:")
        L.append(f"- Projected **tokens** (all 384): {proj_tok:,.0f}")
        L.append(f"- Projected **reported $** (all 384): {fmt_money(proj_rep)} — Anthropic real billing; GPT $0")
        L.append(f"- Projected **implied $** (all 384): {fmt_money(proj_imp)} — incl. GPT at estimated rates")
        L.append(f"- Spend rate so far: {fmt_money(tot['imp'])} implied over {eff_cells} cells")
        L.append("")
        L.append("> ⚠ Extrapolation is linear and early (N small). Frameworks with heavy orchestrator+cache "
                 "(metareview-realistic, compound-realistic on claude-opus-5) dominate cost; if those cells are "
                 "under-represented in the completed set, the projection underestimates; if over-represented, it overestimates.")
        L.append("")

    # ---- anomalies ----
    L.append("## Notes & anomalies")
    L.append("")
    orig_fails = [r for r in reg if r.get("status") != "pass"]
    filled_in = []
    if orig_fails:
        latest_pass_keys = {_cell_key(r) for r in dedup_latest(reg)}
        for r in orig_fails:
            if _cell_key(r) in latest_pass_keys:
                filled_in.append(r)
    notes = []
    if filled_in:
        notes.append(f"- 🔧 {len(filled_in)} cell(s) originally errored, now FILLED IN (latest wins).")
    if log_fail:
        notes.append(f"- ❌ {len(log_fail)} cell(s) errored in the live log: " +
                     ", ".join(f"`[{c['idx']}]` {c['fw']}/{c['model']}/{c['effort']} ({c.get('wall_s','?')}s)" for c in log_fail[:8]))
    # degenerate / outlier cells
    deg = [c for c in cells if c["tp"] + c["fp"] == 0 and c["fn"] > 0]
    if deg:
        notes.append(f"- ⚠ {len(deg)} degenerate cell(s) (0 findings, recall collapse): " +
                     ", ".join(f"{reg_model(c)}/{reg_effort(c)}/{reg_fw(c)} PR{c['url'].rstrip('/').rsplit('/',1)[-1]}" for c in deg[:8]))
    hi_tok = sorted(cells, key=lambda c: -c["tok"])[:3]
    if hi_tok and hi_tok[0]["tok"] > 1_000_000:
        notes.append("- 💸 highest-token cells so far: " + ", ".join(
            f"{reg_model(c)}/{reg_effort(c)}/{reg_fw(c)} {c['tok']:,}tok {fmt_money(c['imp_usd'])}" for c in hi_tok))
    if not notes and not log_fail:
        notes.append("- No anomalies detected so far.")
    L.extend(notes if notes else ["- No anomalies detected so far."])
    L.append("")
    L.append("---")
    L.append(f"_Generated by `bin/analyze_batch_083.py` at {now}._")
    md = "\n".join(L)
    ANALYSIS_MD.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_MD.write_text(md)
    # append compact history
    snap = {"ts": now, "running": ps["running"], "done_log": n_done_log, "eff_cells": eff_cells,
            "recall": round(tot["recall"], 4) if tot else None,
            "adj_p": round(tot["adj_p"], 4) if tot else None,
            "incr_r": round(tot["incr_r"], 4) if tot else None,
            "hidden": tot["real"] if tot else 0, "hal": tot["hal"] if tot else 0,
            "tok": tot["tok"] if tot else 0,
            "rep_usd": round(tot["rep"], 4) if tot else 0,
            "imp_usd": round(tot["imp"], 4) if tot else 0,
            "proj_imp_usd": round((tot["imp"] / (eff_cells / TOTAL_CELLS)), 2) if tot and eff_cells else 0,
            "eta_min": round(eta_min, 1)}
    with HISTORY.open("a") as f:
        f.write(json.dumps(snap) + "\n")
    print(md)

# helpers to read dimension off a metrics dict (cell_metrics attaches fw/model/effort)
def reg_fw(c):
    return c.get("framework")
def reg_model(c):
    return c.get("model")
def reg_effort(c):
    return c.get("effort")

def _cell_key_from_metrics(c):
    return (c.get("framework"), c.get("model"), c.get("effort"), c.get("url", ""))

if __name__ == "__main__":
    main()
