#!/bin/bash
# Campaign dashboard — near-real-time view of the manifold campaign.
# Run:  watch -n 10 -c bash tools/campaign_dashboard.sh
cd "$(dirname "$0")/.."
clear
echo "MANIFOLD CAMPAIGN DASHBOARD — $(date '+%a %H:%M:%S')"
echo "batch: 20260910-mrv0120-manifold"
echo
.venv/bin/python <<'PYEOF'
import json, glob, os, time
from collections import defaultdict

cells = defaultdict(lambda: {"healthy": set(), "poison": 0, "tp": 0, "fn": 0, "hal": 0})
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
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
           "claude-sonnet-5": "sonnet", "claude-fable-5-1": "fable", "gpt-6-astra": "astra",
           "glm-5.3-vision-background": "glm-vis", "glm-5.3-flash-background": "glm-flash"}
order = sorted(cells.keys())
print(f"{'cell':26s} {'healthy':>9} {'rec':>5} {'adjP':>5} {'residue':>7}")
print("-" * 58)
total_healthy = 0
for key in order:
    fw, m, e = key
    c = cells[key]
    n = len(c["healthy"])
    total_healthy += n
    rec = c["tp"] / max(1, c["tp"] + c["fn"])
    ap = c["tp"] / max(1, c["tp"] + c["hal"])
    bar = "#" * (n // 2) + ("·" * ((50 - n) // 2) if n < 50 else "")
    print(f"{fw_short.get(fw, fw)+' '+m_short.get(m, m)+' '+e:26s} {n:>4}/50 {bar:26s} {rec:>5.2f} {ap:>5.2f} {c['poison']:>7}")
print("-" * 58)
print(f"healthy runs total: {total_healthy}")
PYEOF
echo
echo "=== live runners:"
for p in $(pgrep -f "run_model_matrix"); do ps -p $p -o command= 2>/dev/null | grep -oE "models [a-z0-9.-]+ efforts [a-z]+"; done | sort | uniq -c
echo
echo "=== last chain events:"
tail -1 logs/campaign_phase2.log 2>/dev/null | sed 's/^/  codex: /'
tail -1 logs/campaign_glm_final.log 2>/dev/null | sed 's/^/  glm-final: /'
tail -1 logs/campaign_stream2.log 2>/dev/null | sed 's/^/  stream2: /'
tail -1 logs/campaign_ce_claude.log 2>/dev/null | sed 's/^/  CE-claude: /'
tail -1 logs/campaign_ce_codex.log 2>/dev/null | sed 's/^/  CE-codex: /'
echo
.venv/bin/python -m harnesseval.validate --batch 20260910-mrv0120-manifold 2>&1 | head -1 | sed 's/^/validate: /'
