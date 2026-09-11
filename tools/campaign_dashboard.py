#!/usr/bin/env python3
"""Campaign dashboard — btop-style: frames, colors, block bars, two columns."""
import json, glob, os, sys, time
from collections import defaultdict

# width ground truth: tmux's pane_width — the tty itself can carry a stale client size
# (326 reported vs 170 visible observed), and $COLUMNS lies independently
import sys as _sys, subprocess as _sp
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
W = _pane_width()
G = "\033[38;5;114m"; Y = "\033[38;5;179m"; R = "\033[38;5;203m"
D = "\033[38;5;240m"; HD = "\033[38;5;250m"; X = "\033[0m"; BO = "\033[1m"

cells = defaultdict(lambda: {"healthy": set(), "poison": 0, "tp": 0, "fn": 0, "hal": 0})
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

C = "\033[38;5;51m"  # cyan cursor: marks the rightmost dot of actively-refilling cells
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

def panel(row, w, active):
    name, n, rec, ap, poison = row
    barw = w - 40
    filled = n * barw // 50
    empty = barw - filled
    color = G if n >= 50 else (R if n == 0 else Y)
    cursor = ""
    if n < 50 and active and empty > 0:
        empty -= 1
        cursor = C + "▓" + D
    l1 = pad(f"{name:<22s} {color}{'█' * filled}{D}{'░' * empty}{cursor}{X} {n:>3}/50", w)
    l2 = pad(f"{D}rec {rec:.2f}  adjP {ap:.2f}  ✗{poison:<3d}{X}", w)
    return [l1, l2]

def is_active(row):
    toks = row[0].split()
    eff = toks[-1]
    return any(k[1] and eff == k[2] and (k[1].split("-")[0] in row[0] or m_short.get(k[1], "") in row[0]) for k in active_keys)

half = (len(rows) + 1) // 2
left, right = rows[:half], rows[half:]
right += [None] * (half - len(right))
for i in range(half):
    lp = panel(left[i], PL, is_active(left[i])) if i < len(left) else [pad("", PL), pad("", PL)]
    rp = panel(right[i], PR, is_active(right[i])) if right[i] else [pad("", PR), pad("", PR)]
    out.append(f"{D}│{X}{lp[0]}{D}│{X}{rp[0]}{D}│{X}")
    out.append(f"{D}│{X}{lp[1]}{D}│{X}{rp[1]}{D}│{X}")
out.append(f"{D}└{'─' * PL}┴{'─' * PR}┘{X}")
out.append(f"  {BO}TOTAL healthy runs: {G}{total}{X}   {D}residue = dead runs with healthy siblings (harmless){X}")
rc = "  ".join(sorted(set(runners))) or "none"
out.append(f"  {BO}runners:{X} {clip(rc, VW - 12)}")
out.append(f"  {BO}▓{X} = actively refilling")

for line in out:
    print(line)
