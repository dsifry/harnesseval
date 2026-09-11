#!/usr/bin/env python3
"""Campaign dashboard — btop-style: frames, colors, block bars, two columns."""
import json, glob, os, sys, time
from collections import defaultdict

# query the tty directly — shutil.get_terminal_size trusts $COLUMNS, which the tmux
# environment can set to a value unrelated to the actual pane width (318 vs 171 observed)
import sys as _sys
try:
    W = os.get_terminal_size(_sys.stdout.fileno()).columns
except Exception:
    W = 164
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
    return f"{D}{'┌' + ch * (W - 2) + '┐'}{X}"

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

colw = (W - 4) // 2
half = (len(rows) + 1) // 2
left, right = rows[:half], rows[half:]
right += [None] * (half - len(right))

out = [frame_line()]
title = f" MANIFOLD CAMPAIGN — {time.strftime('%a %H:%M:%S')} — batch 20260910-mrv0120-manifold "
out.append(f"{D}│{BO}{HD}{pad(title, W - 2)}{X}{D}│{X}")
out.append(f"{D}{'│' + '─' * (colw) + '┬' + '─' * (W - 4 - colw) + '│'}{X}")
def is_active(row):
    # row name: "<fwshort> <mshort> <eff>" — match against active (fw, model, eff) keys
    toks = row[0].split()
    eff = toks[-1]
    return any(k[1] and eff == k[2] and (k[1].split("-")[0] in row[0] or m_short.get(k[1], "") in row[0]) for k in active_keys)
for i in range(half):
    l = cell_panel(*left[i], w=colw, active=is_active(left[i])) if i < len(left) else [pad("", colw - 1), pad("", colw - 1)]
    r = right[i] if i < len(right) else None
    rr = cell_panel(*r, w=W - 4 - colw, active=is_active(r)) if r else [pad("", W - 3 - colw), pad("", W - 3 - colw)]
    out.append(f"{D}│{X}{l[0]}{D}│{X}{rr[0]}{D}│{X}")
    out.append(f"{D}│{X}{l[1]}{D}│{X}{rr[1]}{D}│{X}")
out.append(f"{D}{'└' + '─' * colw + '┴' + '─' * (W - 4 - colw) + '┘'}{X}")
out.append(f"  {BO}TOTAL healthy runs: {G}{total}{X}   {D}residue = dead runs with healthy siblings (harmless){X}")

# footer: runners + last events
rc = "  ".join(sorted(set(runners))) or "none"
out.append(f"  {BO}runners:{X} {rc}   {BO}▓{X} = actively refilling")

for line in out:
    print(line[:W] if "\033" not in line else line)
