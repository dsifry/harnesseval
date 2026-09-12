#!/usr/bin/env python3
"""Campaign dashboard — btop-style: frames, colors, block bars, two columns."""
import json, glob, os, sys, time
from collections import defaultdict

# width ground truth: tmux's pane_width — the tty itself can carry a stale client size
# (326 reported vs 170 visible observed), and $COLUMNS lies independently
import sys as _sys, subprocess as _sp
def _pane_size():
    if os.environ.get("TMUX"):
        r = _sp.run(["tmux", "display-message", "-p", "#{pane_width} #{pane_height}"],
                    capture_output=True, text=True)
        if r.returncode == 0:
            parts = r.stdout.split()
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[0]), int(parts[1])
    try:
        sz = os.get_terminal_size(_sys.stdout.fileno())
        return sz.columns, sz.lines
    except Exception:
        return 164, 46
W, H = _pane_size()
def _pane_width():
    if os.environ.get("TMUX"):
        r = _sp.run(["tmux", "display-message", "-p", "#{pane_width}"],
                    capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().isdigit():
            return int(r.stdout.strip())
    try:
        return os.get_terminal_size(_sys.stdout.fileno()).columns
    except Exception:
        return 164

G = "\033[38;5;114m"; Y = "\033[38;5;179m"; R = "\033[38;5;203m"
D = "\033[38;5;240m"; HD = "\033[38;5;250m"; X = "\033[0m"; BO = "\033[1m"

cells = defaultdict(lambda: {"healthy": set(), "poison": 0, "tp": 0, "fn": 0, "hal": 0, "times": []})
for f in glob.glob("runs/*/summary.json"):
    try:
        s = json.load(open(f))
    except Exception:
        continue
    if s.get("run_batch") != "20260910-mrv0120-manifold" or not s.get("url"):
        continue
    key = (s.get("framework"), s.get("model"), s.get("effort"))
    n_find = len(s.get("findings", []))
    tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
    bad = tok == 0 or bool(s.get("error")) or (n_find == 0 and tok > 20000)
    c = cells[key]
    if not bad:
        c["healthy"].add(s["url"])
        c["tp"] += s.get("tp", 0) or 0
        c["fn"] += s.get("fn", 0) or 0
        c["hal"] += s.get("n_hallucination", 0) or 0
        try:
            c["times"].append(os.path.getmtime(f))
        except OSError:
            pass
    else:
        c["poison"] += 1

fw_short = {"metareview-realistic": "mrv", "compound-realistic": "CE", "vanilla-engineered": "van"}
m_short = {"gpt-5.6-sol": "sol", "gpt-5.6-terra": "terra", "claude-opus-5": "opus",
           "claude-sonnet-5": "sonnet", "glm-5.3-vision-background": "glm-vis",
           "glm-5.3-flash-background": "glm-flash"}
eff_order = {"low": 0, "medium": 1, "high": 2}
keys = sorted(cells.keys(), key=lambda k: (fw_short.get(k[0], k[0]), m_short.get(k[1], k[1]), eff_order.get(k[2], 9)))

import subprocess, re
runners, active_keys = [], set()
try:
    res = subprocess.run(["pgrep", "-f", "run_model_matrix"], capture_output=True, text=True)
    for pid in res.stdout.split():
        try:
            cmd = open(f"/proc/{pid}/cmdline").read().replace("\0", " ")
        except Exception:
            cmd = subprocess.run(["ps", "-ww", "-p", pid, "-o", "command="], capture_output=True, text=True).stdout  # -ww: no truncation
        m = re.search(r"(?:--)?frameworks (\S+) (?:--)?models (\S+) (?:--)?efforts (\S+)", cmd)
        if m:
            _fw = fw_short.get(m.group(1), m.group(1))
            runners.append(f"{_fw} {m_short.get(m.group(2), m.group(2))} {m.group(3)}")
            active_keys.add((m.group(1), m.group(2), m.group(3)))
except Exception:
    pass

NOW = time.time()
def eta_str(c, n, active):
    # expected time to 50/50: recent 30-min completion rate first, cell-span average as fallback
    if n >= 50:
        return "", None
    if not active:
        return " —", None
    recent = [t for t in c["times"] if t > NOW - 1800]
    if len(recent) >= 2:
        rate = len(recent) / 30.0  # runs per minute over the last half hour
    elif len(c["times"]) >= 2:
        rate = len(c["times"]) / max(1.0, (max(c["times"]) - min(c["times"])) / 60.0)
    else:
        return " ?", None  # active but not enough history to estimate
    mins = (50 - n) / max(rate, 1e-9)
    if mins >= 100:
        return f" {int(mins // 60)}h{int(mins % 60):02d}", mins
    return f" {int(mins):02d}:{int((mins % 1) * 60):02d}", mins

def fmt_mins(mins):
    if mins >= 100:
        return f"{int(mins // 60)}h{int(mins % 60):02d}"
    return f"{int(mins):02d}:{int((mins % 1) * 60):02d}"

def fmt_signed(mins):
    sign = "-" if mins < 0 else ""
    return sign + fmt_mins(abs(mins))

rows = []
total = 0
for fw, m, e in keys:
    c = cells[(fw, m, e)]
    n = len(c["healthy"])
    total += n
    rows.append((f"{fw_short.get(fw,fw)} {m_short.get(m,m)} {e}", n,
                 c["tp"] / max(1, c["tp"] + c["fn"]),
                 c["tp"] / max(1, c["tp"] + c["hal"]), c["poison"]))

def frame_line(ch="─"):
    return f"{D}{'┌' + ch * (W - 3) + '┐'}{X}"

import re as _re
def pad(s, w):
    s = _re.sub(r"\033\[[0-9;]*m", "", s)  # strip ALL ANSI — the cursor's cyan was missing
                                           # from the old list, shortening padded cursor rows
    return s + " " * max(0, w - len(s))

C = "\033[38;5;33m"  # blue cursor: marks the in-flight cell at the fill frontier
TY = "\033[38;5;220m"  # saturated yellow for trend glyphs (179 is too pale to read as yellow)
def cell_panel(name, n, rec, ap, poison, w, active=False):
    filled = n * (w - 40) // 50
    empty = (w - 40) - filled
    color = G if n >= 50 else (R if n == 0 else Y)
    cursor = ""
    if n < 50 and active and empty > 0:
        empty -= 1
        cursor = C + "▓" + D  # the rightmost slot is being worked on right now
    bar = color + "█" * filled + D + "░" * empty + cursor + X
    line1 = f"{X}{name:<22s} {bar} {n:>3}/50"
    line2 = f"{D}rec {rec:.2f}  adjP {ap:.2f}  ✗{poison:<3d}{X}"
    return [pad(line1, w - 1), pad(line2, w - 1)]

colw = (W - 5) // 2
half = (len(rows) + 1) // 2
left, right = rows[:half], rows[half:]
right += [None] * (half - len(right))

import unicodedata
def vlen(s):
    s = _re.sub(r"\033\[[0-9;]*m", "", s)
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)

def pad(s, w):
    return s + " " * max(0, w - vlen(s))

def clip(s, w):
    if vlen(s) <= w:
        return s
    acc, out = 0, []
    for ch in _re.sub(r"(\033\[[0-9;]*m)", "", s):  # crude: strip color on clip
        pass
    plain = _re.sub(r"\033\[[0-9;]*m", "", s)
    return plain[: w - 1] + "…"

VW = W - 1  # stay one char under the pane width: exact-width lines double-wrap
print("\033[2J\033[H", end="")  # clear + home every refresh — no scrolling residue
out = [f"{D}┌{'─' * (VW - 2)}┐{X}"]
title = f" MANIFOLD CAMPAIGN — {time.strftime('%a %H:%M:%S')} — batch 20260910-mrv0120-manifold "
out.append(f"{D}│{X}{BO}{HD}{pad(title, VW - 2)}{X}{D}│{X}")
PL = (VW - 3) // 2   # left panel width  (between the │ separators)
PR = VW - 3 - PL     # right panel width — identical math, no drift
out.append(f"{D}│{'─' * PL}┬{'─' * PR}│{X}")

def panel(row, w, active, eta="", trend="", last_mins=None, pace=None):
    name, n, rec, ap, poison = row
    barw = 50  # one slot per PR — the cursor sits exactly at run n+1 (user spec:
               # "leftmost 12 green, 13th next to it"); pane-derived widths broke 1:1
    filled = n
    empty = barw - filled
    color = G if n >= 50 else (R if n == 0 else Y)
    # the in-flight cell sits immediately AFTER the last completed cell, not at the
    # bar's right edge — it marks the frontier of the fill. The cursor REPLACES the
    # last empty slot (adding it made cursor rows 51 wide and shifted their columns).
    _has_cursor = n < 50 and active and empty > 0
    if _has_cursor:
        empty -= 1
    cursor = f"{C}▓{D}" if _has_cursor else ""
    suffix = eta
    if last_mins is not None:
        mins, inflight = last_mins[0], last_mins[1]
        ld = fmt_mins(mins)
        es = eta.strip()
        if inflight:
            rem = 50 - n
            pace0 = last_mins[4] if len(last_mins) > 4 else None
            if pace0 is not None:
                # countdown from the estimate FROZEN at pass start (last completed pass's
                # realized pace x targeted runs) minus elapsed. Ticks down every refresh,
                # goes negative on overrun; the pace only updates when the pass COMPLETES,
                # from its actual duration (never re-based mid-pass).
                n_t = last_mins[2] or rem
                est = fmt_signed(pace0 * n_t - mins)
                suffix = f" {ld} elapsed/{rem} left/{est} est"
            else:
                suffix = f" {ld} elapsed/{rem} left/? est"
        elif n >= 50:
            suffix = f" {ld} last"  # complete cell: pass history, nothing left to estimate
        else:
            suffix = f" {ld}/{es}" if es and es != "—" else f" {ld}/No ETA"
    l1 = pad(f"{name:<22s} {color}{'█' * filled}{cursor}{D}{'░' * empty}{X} {n:>3}/50{Y}{suffix}{X}", w)
    f1v = 2 * rec * ap / max(rec + ap, 1e-9)
    _pace = f"{HD}  ·  {fmt_mins(pace)} per run{X}" if pace else ""
    l2 = pad(f"{HD}rec {rec:.2f}  adjP {ap:.2f}  F1 {f1v:.2f}{trend}{D}  ✗{poison:<3d}{X}{_pace}", w)
    return [l1, l2]

def is_active(row):
    # exact match on all three: framework, model, effort — a vision runner must not
    # light the flash cell, and a sol runner must not light both mrv and CE sol
    toks = row[0].split()
    return any(fw_short.get(k[0]) == toks[0] and m_short.get(k[1]) == toks[1] and k[2] == toks[2]
               for k in active_keys)

half = (len(rows) + 1) // 2
left, right = rows[:half], rows[half:]
right += [None] * (half - len(right))
eta_by_name = {r[0]: eta_str(cells[(k)], r[1], is_active(r)) for r, k in
               [(r, key) for r, key in zip(rows, keys)]}

# last completed fill-pass wall clock per cell, across ALL fill sources:
# sweeper (refilling -> refill pass done), CE chains (filling -> done/still missing), GLM chain (attempt N -> next event)
def last_pass_minutes():
    import re as _re3
    out = {}
    import collections as _col
collections = _col
    d_min = lambda a, b: (b - a) if b >= a else (b - a + 1440)
    FW_ALIAS = {"CE": "compound-realistic", "mrv": "metareview-realistic", "van": "vanilla-engineered"}
    def name_for(fw, model, eff):
        fw = FW_ALIAS.get(fw, fw)
        return f"{fw_short.get(fw, fw)} {m_short.get(model, model)} {eff}"
    completed = {}  # name -> (duration, landed) of the last COMPLETED pass (avg-per-run fallback)
    pass_seq = collections.defaultdict(list)  # name -> [(start, end, n_target)] for landed computation
    def emit(start_min, key, done_min, n_target):
        d = done_min - start_min
        if d < 0: d += 1440  # midnight wrap
        out[name_for(*key)] = (d, False, n_target, start_min, None)
        pass_seq[name_for(*key)].append((start_min, done_min, n_target))
    # landed runs per pass = targeted minus the NEXT pass's target for the same cell
    # (a pass targeting 3 that leaves 1 missing landed 2 — dividing by 3 inflated the pace)
    for _nm, seq in pass_seq.items():
        seq.sort()
        for i, (s0, s1, n_t) in enumerate(seq):
            if n_t is None:
                continue  # glm chain passes have no targeted count — no landed basis
            landed = n_t
            if i + 1 < len(seq):
                landed = max(1, n_t - seq[i + 1][2])
            rate = d_min(s0, s1) / max(1, landed)
            if rate >= 0.25:  # >= 15s per landed run
                completed[_nm] = (d_min(s0, s1), landed)
    for path, kind in [("logs/campaign_final_refill.log", "sweep"),
                       ("logs/campaign_ce_codex.log", "chain"),
                       ("logs/campaign_ce_claude.log", "chain"),
                       ("logs/campaign_glm_final.log", "glm")]:
        pend = None
        try:
            for ln in open(path, errors="replace"):
                m = _re3.match(r"^(\d{2}):(\d{2})\s+(.*)", ln)
                if not m: continue
                t = int(m.group(1)) * 60 + int(m.group(2))
                msg = m.group(3)
                if kind == "sweep":
                    ms = _re3.match(r"cell (\S+)/(\S+)/(\S+) — refilling (\d+)", msg)
                    md = _re3.match(r"cell (\S+)/(\S+)/(\S+) refill pass done", msg)
                    if ms:
                        _nm = name_for(*ms.groups()[:3])
                        _p0 = (completed[_nm][0] / completed[_nm][1]) if _nm in completed and completed[_nm][1] else None
                        pend = (t, (ms.group(1), ms.group(2), ms.group(3)), int(ms.group(4)), _p0)
                    elif md and pend and pend[1] == (md.group(1), md.group(2), md.group(3)):
                        emit(pend[0], pend[1], t, pend[2]); pend = None
                elif kind == "chain":
                    ms = _re3.match(r"cell (\S+)/(\S+)/(\S+) filling (\d+) missing", msg)
                    md = _re3.match(r"cell (\S+)/(\S+)/(\S+) (?:done|still missing)", msg)
                    if ms:
                        _nm = name_for(*ms.groups()[:3])
                        _p0 = (completed[_nm][0] / completed[_nm][1]) if _nm in completed and completed[_nm][1] else None
                        pend = (t, (ms.group(1), ms.group(2), ms.group(3)), int(ms.group(4)), _p0)
                    elif md and pend and pend[1] == (md.group(1), md.group(2), md.group(3)):
                        emit(pend[0], pend[1], t, pend[2]); pend = None
                else:  # glm chain: "cell model/eff attempt N" (mrv implied; 3-part also tolerated)
                    ma = _re3.match(r"cell (\S+)/(\S+)/(\S+) attempt", msg) or _re3.match(r"cell (\S+)/(\S+) attempt", msg)
                    if ma:
                        key = (ma.group(1), ma.group(2), ma.group(3)) if ma.lastindex == 3 else ("metareview-realistic", ma.group(1), ma.group(2))
                        _nm = name_for(*key)
                        _p0 = (completed[_nm][0] / completed[_nm][1]) if _nm in completed and completed[_nm][1] else None
                        if pend and pend[1] != key:
                            emit(pend[0], pend[1], t, None)
                        pend = (t, key, None, _p0)
        except OSError:
            pass
    # in-flight passes: report elapsed-so-far for cells with no completed pass yet
    for path, kind in [("logs/campaign_final_refill.log", "sweep"),
                       ("logs/campaign_ce_codex.log", "chain"),
                       ("logs/campaign_ce_claude.log", "chain"),
                       ("logs/campaign_glm_final.log", "glm")]:
        pend = None
        try:
            for ln in open(path, errors="replace"):
                m = _re3.match(r"^(\d{2}):(\d{2})\s+(.*)", ln)
                if not m: continue
                t = int(m.group(1)) * 60 + int(m.group(2))
                msg = m.group(3)
                if kind == "sweep":
                    ms = _re3.match(r"cell (\S+)/(\S+)/(\S+) — refilling (\d+)", msg)
                    md = _re3.match(r"cell (\S+)/(\S+)/(\S+) refill pass done", msg)
                    if ms:
                        _nm = name_for(*ms.groups()[:3])
                        _c = completed.get(_nm)
                        _p0 = (_c[0] / _c[1]) if _c and _c[1] else None
                        pend = (t, (ms.group(1), ms.group(2), ms.group(3)), int(ms.group(4)), _p0)
                    elif md: pend = None
                elif kind == "chain":
                    ms = _re3.match(r"cell (\S+)/(\S+)/(\S+) filling (\d+) missing", msg)
                    md = _re3.match(r"cell (\S+)/(\S+)/(\S+) (?:done|still missing)", msg)
                    if ms:
                        _nm = name_for(*ms.groups()[:3])
                        _c = completed.get(_nm)
                        _p0 = (_c[0] / _c[1]) if _c and _c[1] else None
                        pend = (t, (ms.group(1), ms.group(2), ms.group(3)), int(ms.group(4)), _p0)
                    elif md: pend = None
                else:
                    ma = _re3.match(r"cell (\S+)/(\S+)/(\S+) attempt", msg) or _re3.match(r"cell (\S+)/(\S+) attempt", msg)
                    if ma:
                        key = (ma.group(1), ma.group(2), ma.group(3)) if ma.lastindex == 3 else ("metareview-realistic", ma.group(1), ma.group(2))
                        _nm = name_for(*key)
                        _c = completed.get(_nm)
                        _p0 = (_c[0] / _c[1]) if _c and _c[1] else None
                        pend = (t, key, None, _p0)
        except OSError:
            pass
        if pend:
            name = name_for(*pend[1])
            _lt = time.localtime(NOW)
            now_s = _lt.tm_hour * 3600 + _lt.tm_min * 60 + _lt.tm_sec
            d = ((now_s - pend[0] * 60) % 86400) / 60.0  # elapsed in float minutes (ticks every refresh)
            cand = (d, True, pend[2], pend[0], pend[3])  # pend[3] = pace basis frozen at pass start
            # the most RECENT pass wins: a live in-flight pass must not be hidden by a
            # stale completed entry from a dead chain's log (sonnet-high 02:00 bug)
            if name not in out or cand[3] > out[name][3]:
                out[name] = cand
    return out, completed
last_pass, last_completed = last_pass_minutes()

def pace_by_name_factory():
    def pace_for(name, n):
        # every pace must pass the plausibility filter (>= 15s per run) — fast-fail
        # sweeps are failure artifacts, not paces (the 00:02-per-run lesson)
        def plausible(rate):
            return rate is not None and rate >= 0.25  # minutes per run
        e = last_pass.get(name)
        if e and len(e) > 4 and e[4] is not None and plausible(e[4]):
            return e[4]  # in-flight: the pace basis the running estimate is built on
        if e and not e[1] and e[2]:
            rate = e[0] / e[2]  # completed pass: realized pace (actual duration / actual runs)
            if plausible(rate):
                return rate
        if name in last_completed and last_completed[name][1]:
            d0, n0 = last_completed[name]
            rate = d0 / n0
            if plausible(rate):
                return rate
        return None
    return pace_for
pace_for = pace_by_name_factory()

# F1 trend vs the previous poll (state persisted across refreshes in /tmp)
STATE = "/tmp/campaign_f1_state.json"
f1 = lambda rec, ap: 2 * rec * ap / max(rec + ap, 1e-9)
try:
    prev_state = json.load(open(STATE))
    # format guard: older states stored [rec, ap] lists — discard incompatible entries
    prev_state = {k: v for k, v in prev_state.items()
                  if isinstance(v, dict) and "quiet" in v and "n_last" in v} if isinstance(prev_state, dict) else {}
except Exception:
    prev_state = {}
trend_by_name = {}
new_state = {}
for name, n, rec, ap, poison in rows:
    f1c = f1(rec, ap)
    st = prev_state.get(name)
    if st is None:
        trend_by_name[name] = f"{D}.{X}"        # no baseline yet (first poll only)
        new_state[name] = {"n_last": n, "quiet": [rec, ap], "t": ""}
    elif n == st["n_last"]:
        # settled this poll: the batch finished — the settled value becomes the new
        # pre-batch baseline for the NEXT batch; the arrow persists until then
        trend_by_name[name] = "" if n >= 50 else (st.get("t") or f"{D}.{X}")
        new_state[name] = {"n_last": n, "quiet": [rec, ap], "t": st.get("t", "")}
    else:
        # batch in flight: compare vs the SETTLED pre-batch value — never the 15s-ago slice
        d = f1c - f1(*st["quiet"])
        if d > 1e-12:
            t = f"{G}▲{X}"
        elif d < -1e-12:
            t = f"{R}▼{X}"
        else:
            t = st.get("t") or f"{TY}-{X}"
        trend_by_name[name] = t
        # quiet stays PUT while the batch lands — the whole batch is measured against it
        new_state[name] = {"n_last": n, "quiet": st["quiet"], "t": t}
try:
    json.dump(new_state, open(STATE, "w"))
except Exception:
    pass
for i in range(half):
    lp = panel(left[i], PL, is_active(left[i]), eta_by_name.get(left[i][0], ("", None))[0], trend_by_name.get(left[i][0], ""), last_pass.get(left[i][0]), pace_for(left[i][0], left[i][1])) if i < len(left) else [pad("", PL), pad("", PL)]
    rp = panel(right[i], PR, is_active(right[i]), eta_by_name.get(right[i][0], ("", None))[0], trend_by_name.get(right[i][0], ""), last_pass.get(right[i][0]), pace_for(right[i][0], right[i][1])) if right[i] else [pad("", PR), pad("", PR)]
    out.append(f"{D}│{X}{lp[0]}{D}│{X}{rp[0]}{D}│{X}")
    out.append(f"{D}│{X}{lp[1]}{D}│{X}{rp[1]}{D}│{X}")
out.append(f"{D}└{'─' * PL}┴{'─' * PR}┘{X}")
_etas = [(eta_by_name.get(r[0], ("", None))[1], r[0]) for r in rows]
_overall = max((e for e in _etas if e[0] is not None), default=None)
_suffix = f"   {BO}overall eta ~{fmt_mins(_overall[0])}{X} {D}(bottleneck: {_overall[1]}){X}" if _overall else ""
out.append(f"  {BO}TOTAL healthy runs: {G}{total}{X}   {D}residue = dead runs with healthy siblings (harmless){X}{_suffix}")
rc = "  ".join(sorted(set(runners))) or "none"
out.append(f"  {BO}runners:{X} {clip(rc, VW - 12)}")
out.append(f"  {BO}▓{X} = actively refilling")

# ── recent events panel: merged, timestamped tails of the campaign logs ──
import re as _re2
SOURCES = [  # (file, tag, color)
    ("logs/campaign_final_refill.log", "refill", Y),
    ("logs/campaign_glm_final.log",    "glm",    C),
    ("logs/campaign_ce_codex.log",     "ce-codex", G),
    ("logs/campaign_ce_claude.log",    "ce-claude", G),
    ("logs/campaign_stream2.log",      "s2",     G),
    ("logs/campaign_phase2.log",       "phase2", D),
]
events = []
for path, tag, col in SOURCES:
    try:
        lines = open(path, errors="replace").read().splitlines()
        mtime = os.path.getmtime(path)
        day = time.strftime("%m-%d", time.localtime(mtime))
    except OSError:
        continue
    # walk BACKWARD from the newest line (its date = the file's mtime); each time an
    # older line has a LATER hh:mm than the line after it, we crossed midnight going back
    prev_ts = None
    for ln in reversed(lines[-400:]):
        m = _re2.match(r"^(\d{2}:\d{2})\s+(.*)", ln)
        if not m:
            continue
        ts = m.group(1)
        if prev_ts and ts > prev_ts:  # backward walk, but hh:mm jumped forward -> midnight crossed
            day = time.strftime("%m-%d", time.localtime(os.path.getmtime(path) - 86400))
        prev_ts = ts
        events.append((f"{day} {ts}", ts, tag, col, m.group(2)))
# mx logs carry no timestamps — stamp their last lines with the file's mtime so
# per-run starts/completions show up in the panel (the campaign's real heartbeat)
import glob as _glob
for _p in sorted(_glob.glob("logs/mx_campaign_*.log"), key=os.path.getmtime, reverse=True)[:12]:
    try:
        _mt = os.path.getmtime(_p)
        if _mt < time.time() - 3600:
            continue  # only logs touched in the last hour
        _day = time.strftime("%m-%d", time.localtime(_mt))
        _name = os.path.basename(_p).replace("mx_campaign_", "").replace(".log", "")
        for _ln in open(_p, errors="replace").read().splitlines()[-3:]:
            if not _ln.strip():
                continue
            _hm = time.strftime("%H:%M", time.localtime(_mt))
            _bad = ("ERR" in _ln or "fail" in _ln.lower() or "POISON" in _ln)
            _col = R if _bad else HD
            events.append((f"{_day} {_hm}", _hm, _name[:14], _col, _ln.replace("[mx] ", "").strip()[:96]))
    except OSError:
        pass
events.sort(key=lambda e: e[0])
BAD = ("fail", "err ", "error", "poison", "timeout")
GOOD = ("clean", "done", "complete", "stable", "refill pass done")
LOGN = max(3, min(14, H - 2 - (len(out) + 4)))  # fit the pane: panels never scroll
out.append(f"{D}├{'─' * (PL)}┴{'─' * PR}┤{X}")
out.append(f"{D}│{X}{BO}{HD}{pad(' RECENT EVENTS — newest last', VW - 2)}{X}{D}│{X}")
for _, ts, tag, col, msg in events[-LOGN:]:
    lc = R if any(b in msg.lower() for b in BAD) else (G if any(g in msg.lower() for g in GOOD) else HD)
    out.append(f"{D}│{X}{pad(f'{D}{ts}{X} {col}[{tag}]{X} {lc}{msg[:VW - 16]}{X}', VW - 2)}{X}{D}│{X}")
out.append(f"{D}└{'─' * (VW - 2)}┘{X}")

# ── key-pool utilization panel: aggregated from the router's ledger ──
import json as _json2
_kagg = {}
_live = {}   # key -> in-flight right now (start events minus end events, file is append-ordered)
try:
    for _ln in open("logs/key_usage.jsonl", errors="replace"):
        try:
            _r = _json2.loads(_ln)
        except Exception:
            continue
        if _r.get("ts", 0) < time.time() - 86400:  # last 24h
            continue
        _k = _r.get("key", 9)
        if _r.get("ev") == "start":
            _live[_k] = _live.get(_k, 0) + 1
            continue
        _a = _kagg.setdefault(_k, {"ok": 0, "fail": 0, "s": 0.0, "in": 0, "out": 0, "cached": 0, "models": {}})
        if _r.get("ok"): _a["ok"] += 1
        else: _a["fail"] += 1
        _a["s"] += _r.get("s", 0) or 0
        _a["in"] += _r.get("in", 0); _a["out"] += _r.get("out", 0); _a["cached"] += _r.get("cached", 0)
        _a["models"][_r.get("model", "?")] = _a["models"].get(_r.get("model", "?"), 0) + 1
        _live[_k] = max(0, _live.get(_k, 0) - 1)  # an end closes its start
        # concurrency tracking: each completed record occupied [ts-s, ts]
        _kagg.setdefault("__intervals__", {}).setdefault(_k, []).append(
            (_r["ts"] - (_r.get("s", 0) or 0), _r["ts"]))
except OSError:
    pass
_intervals = _kagg.pop("__intervals__", {})
# budgets must match the chains' HARNESS_KEY_BUDGETS export: bench 12, interactive 6
# (the interactive key reserves a lane for interactive use)
BUDGETS = [12, 6]

def _conc_stats(ivs, window_s=3600.0, budget=12):
    """(now_inflight, peak, avg, util%) over the trailing window from busy intervals."""
    now = time.time()
    now_n = sum(1 for s0, s1 in ivs if s0 <= now < s1)
    pts = []
    for s0, s1 in ivs:
        if s1 < now - window_s: continue
        pts.append((max(s0, now - window_s), 1)); pts.append((min(s1, now), -1))
    pts.sort()
    peak = cur = 0; busy = 0.0; last_t = now - window_s
    for t, dv in pts:
        busy += cur * (t - last_t); last_t = t
        cur = max(0, cur + dv); peak = max(peak, cur)
    busy += cur * (now - last_t)
    avg = busy / window_s
    return now_n, peak, avg, 100.0 * avg / budget  # true share of this key's budget
if _kagg:
    out.append(f"{D}├{'─' * (VW - 2)}┤{X}")
    out.append(f"{D}│{X}{BO}{HD}{pad(' KEY POOL — 24h utilization (key0 = bench file, key1 = interactive file)', VW - 2)}{X}{D}│{X}")
    _tot_n = 0; _tot_util = 0.0
    _merged = [iv for _k in sorted(_kagg) for iv in _intervals.get(_k, [])]
    _pn, _ppeak, _pavg, _putil = _conc_stats(_merged, budget=sum(BUDGETS))
    for _k in sorted(_kagg):
        _a = _kagg[_k]
        _ms = ", ".join(f"{_m}×{_c}" for _m, _c in sorted(_a["models"].items()))
        _b = BUDGETS[_k] if _k < len(BUDGETS) else 12
        _now = _live.get(_k, 0)  # live in-flight from start/end events (sees long calls)
        _, _peak, _avg, _util = _conc_stats(_intervals.get(_k, []), budget=_b)
        _tot_n += _now; _tot_util += _util
        _row = (f"key{_k}: {_a['ok']}ok/{_a['fail']}fail  now {_now}/{_b}  peak {_peak}  "
                f"avg {_avg:.1f} ({_util:.0f}% of budget)  in {_a['in']:,} (cached {_a['cached']:,})  out {_a['out']:,}")
        out.append(f"{D}│{X}{pad(_row, VW - 2)}{X}{D}│{X}")
        _mr = ", ".join(f"{_m}×{_c}" for _m, _c in sorted(_a["models"].items()))
        out.append(f"{D}│{X}{pad(f'      models: {_mr}', VW - 2)}{X}{D}│{X}")
    out.append(f"{D}│{X}{pad(f'POOL: {_tot_n} in flight now (budget {sum(BUDGETS)}) · peak {_ppeak} · avg {_pavg:.1f} · utilization {_putil:.0f}% — headroom {100 - _putil:.0f}%', VW - 2)}{X}{D}│{X}")
    out.append(f"{D}└{'─' * (VW - 2)}┘{X}")

# btop-style panel draw: address absolute rows, clear each line to EOL, clear below.
# The upper (cells) panel is never overwritten because every row is addressed explicitly
# and the total block is sized to fit the pane.
buf = ["\033[H"]  # no full clear — in-place redraw avoids the 15s flicker; trailing \033[J handles shrinkage
for i, line in enumerate(out, start=1):
    if i > H - 1:
        break
    buf.append(f"\033[{i};1H{line}\033[K")
buf.append(f"\033[{min(len(out) + 1, H)};1H\033[J")
sys.stdout.write("".join(buf) + "\n")
sys.stdout.flush()
