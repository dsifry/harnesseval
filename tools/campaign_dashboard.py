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
            cmd = subprocess.run(["ps", "-p", pid, "-o", "command="], capture_output=True, text=True).stdout
        m = re.search(r"(?:--)?frameworks (\S+) (?:--)?models (\S+) (?:--)?efforts (\S+)", cmd)
        if m:
            runners.append(f"{m.group(2)} {m.group(3)}")
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

def panel(row, w, active, eta="", trend="", last_mins=None):
    name, n, rec, ap, poison = row
    barw = 50  # one slot per PR — the cursor sits exactly at run n+1 (user spec:
               # "leftmost 12 green, 13th next to it"); pane-derived widths broke 1:1
    filled = n
    empty = barw - filled
    color = G if n >= 50 else (R if n == 0 else Y)
    # the in-flight cell sits immediately AFTER the last completed cell, not at the
    # bar's right edge — it marks the frontier of the fill
    cursor = f"{C}▓{D}" if (n < 50 and active and empty > 0) else ""
    suffix = eta
    if last_mins is not None:
        ld = fmt_mins(last_mins)
        es = eta.strip()
        suffix = f" {ld}/{es}" if es and es != "—" else f" {ld}/No ETA"
    l1 = pad(f"{name:<22s} {color}{'█' * filled}{cursor}{D}{'░' * empty}{X} {n:>3}/50{Y}{suffix}{X}", w)
    f1v = 2 * rec * ap / max(rec + ap, 1e-9)
    l2 = pad(f"{HD}rec {rec:.2f}  adjP {ap:.2f}  F1 {f1v:.2f}{trend}{D}  ✗{poison:<3d}{X}", w)
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

# last completed refill-pass wall clock per cell, from the sweeper log
def last_pass_minutes():
    import re as _re3
    out = {}
    pend = None
    try:
        for ln in open("logs/campaign_final_refill.log", errors="replace"):
            m = _re3.match(r"^(\d{2}):(\d{2}) cell (\S+)/ (\S+)", ln)
            m_start = _re3.match(r"^(\d{2}):(\d{2}) cell (\S+)/(\S+)/(\S+) — refilling", ln)
            m_done = _re3.match(r"^(\d{2}):(\d{2}) cell (\S+)/(\S+)/(\S+) refill pass done", ln)
            if m_start:
                pend = (int(m_start.group(1)) * 60 + int(m_start.group(2)),
                        (m_start.group(3), m_start.group(4), m_start.group(5)))
            elif m_done and pend and pend[1] == (m_done.group(3), m_done.group(4), m_done.group(5)):
                d = (int(m_done.group(1)) * 60 + int(m_done.group(2))) - pend[0]
                if d < 0: d += 1440  # midnight wrap
                name = f"{fw_short.get(pend[1][0], pend[1][0])} {m_short.get(pend[1][1], pend[1][1])} {pend[1][2]}"
                out[name] = d
                pend = None
    except OSError:
        pass
    return out
last_pass = last_pass_minutes()

# F1 trend vs the previous poll (state persisted across refreshes in /tmp)
STATE = "/tmp/campaign_f1_state.json"
f1 = lambda rec, ap: 2 * rec * ap / max(rec + ap, 1e-9)
try:
    prev_state = json.load(open(STATE))
except Exception:
    prev_state = {}
trend_by_name = {}
new_state = {}
for name, n, rec, ap, poison in rows:
    f1c = f1(rec, ap)
    st = prev_state.get(name)
    if st is None:
        trend_by_name[name] = f"{D}.{X}"        # no baseline yet (first poll)
        new_state[name] = {"n": n, "f1": [rec, ap]}
    elif n == st["n"]:
        trend_by_name[name] = f"{Y}-{X}"        # no results landed since the baseline: flat
        new_state[name] = st                    # keep the pre-batch baseline (arrows persist)
    else:
        d = f1c - f1(*st["f1"])                 # results landed: compare vs where we were before them
        if abs(d) < 0.005:
            trend_by_name[name] = f"{Y}-{X}"
        elif d > 0:
            trend_by_name[name] = f"{G}▲{X}"
        else:
            trend_by_name[name] = f"{R}▼{X}"
        new_state[name] = {"n": n, "f1": [rec, ap]}  # ratchet the baseline to now
try:
    json.dump(new_state, open(STATE, "w"))
except Exception:
    pass
for i in range(half):
    lp = panel(left[i], PL, is_active(left[i]), eta_by_name.get(left[i][0], ("", None))[0], trend_by_name.get(left[i][0], ""), last_pass.get(left[i][0])) if i < len(left) else [pad("", PL), pad("", PL)]
    rp = panel(right[i], PR, is_active(right[i]), eta_by_name.get(right[i][0], ("", None))[0], trend_by_name.get(right[i][0], ""), last_pass.get(right[i][0])) if right[i] else [pad("", PR), pad("", PR)]
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
        day = time.strftime("%m-%d", time.localtime(os.path.getmtime(path)))
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
