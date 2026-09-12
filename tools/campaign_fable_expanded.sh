#!/bin/bash
# Expanded fable run: claude-fable-5-1 (Claude OAuth CLI) across vanilla/CE/mrv x med/high + CE/mrv x low.
# vanilla-low is NOT re-run: the 20260906-fable51-vanilla-low batch (50/50) is reused per the locked spec.
# Claude OAuth limits reset at noon PT (2026-09-12 12:00); 5-hour session windows may stall mid-run —
# the probe gate + per-round re-census ride the windows. Not in a rush: conc 4, sequential rounds.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_fable.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
CONC=4
MODEL=claude-fable-5-1

missing_specs() {
  .venv/bin/python - "$1" "$2" "$3" "$BATCH" <<'PYEOF'
import json, glob, sys, os
from pathlib import Path
fw, model, eff, batch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
cap = int(sys.argv[5]) if len(sys.argv) > 5 else 0  # if set: fixed sample = first N urls of the full sorted list
sys.path.insert(0, ".")
from harnesseval.dataset import martian
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        rows.append(pr["url"])
urls = sorted({u for u in rows})
have = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if not s.get("url"): continue
    b = s.get("run_batch")
    if b != batch and not (b == "20260906-fable51-vanilla-medhigh" and fw == "vanilla-engineered"): continue
    if (s.get("framework"), s.get("model"), s.get("effort")) != (fw, model, eff): continue
    n = len(s.get("findings", [])); tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
    if tok and not s.get("error") and (n or tok <= 20000): have.add(s["url"])
sample = urls[:cap] if cap else urls
missing = [u for u in sample if u not in have]
print(",".join(f"{fw}/{model}/{eff}/{u.rsplit('/', 1)[-1]}" for u in missing))
PYEOF
}

claude_ok() {
  .venv/bin/python - <<'PYEOF'
import sys, asyncio
sys.path.insert(0, ".")
from harnesseval import cli_backends
async def t():
    try:
        text, _, _ = await asyncio.wait_for(
            cli_backends._claude_cli("claude-fable-5-1", "low", "Reply with the single word ok"), timeout=90)
        sys.exit(0 if text.strip() else 1)
    except SystemExit: raise
    except Exception: sys.exit(1)
asyncio.run(t())
PYEOF
}

CELLS="vanilla-engineered/medium vanilla-engineered/high compound-realistic/medium compound-realistic/high metareview-realistic/medium metareview-realistic/high"

log "expanded fable run: $MODEL across 8 cells (vanilla-low reused from 20260906-fable51-vanilla-low per locked spec)"
for ROUND in 1 2 3 4 5 6 7 8; do
  PIDS=""
  LAUNCHED=0
  for cell in $CELLS; do
    fw="${cell%%/*}"; eff="${cell##*/}"
    if [ "$fw" = "vanilla-engineered" ]; then CAPARG=""; else CAPARG="6"; fi
    SPECS=$(missing_specs "$fw" "$MODEL" "$eff" $CAPARG)
    if [ -z "$SPECS" ]; then log "round $ROUND: cell $fw/$eff complete — skip"; continue; fi
    if ! claude_ok; then log "round $ROUND: claude capped — waiting out the window (probe every 10 min)"; break; fi
    N=$(echo "$SPECS" | tr ',' '\n' | grep -c .)
    log "round $ROUND: launching cell $fw/$MODEL/$eff — filling $N (conc $CONC)"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks "$fw" \
      --models $MODEL --efforts "$eff" --mode cli --concurrency $CONC \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$SPECS" >> "logs/mx_campaign_fable_${fw}_${eff}.log" 2>&1 &
    PIDS="$PIDS $!"
    LAUNCHED=$((LAUNCHED + 1))
  done
  [ -z "$PIDS" ] && { log "round $ROUND: nothing to launch"; if [ "$LAUNCHED" -eq 0 ]; then ALLDONE=1; fi; }
  # done check: all cells complete?
  DONE=1
  for cell in $CELLS; do
    fw="${cell%%/*}"; eff="${cell##*/}"
    if [ "$fw" = "vanilla-engineered" ]; then CAPARG=""; else CAPARG="6"; fi
    [ -n "$(missing_specs "$fw" "$MODEL" "$eff" $CAPARG)" ] && DONE=0
  done
  [ "$DONE" -eq 1 ] && { log "all 8 fable cells complete — done"; exit 0; }
  [ -n "$PIDS" ] && wait $PIDS
  log "round $ROUND finished — re-censusing"
  if ! claude_ok; then
    log "claude capped after round $ROUND — waiting for the window (noon PT reset backstop); probing every 10 min"
    while ! claude_ok; do sleep 600; done
    log "claude window open — continuing"
  fi
done
log "fable run: 8 rounds exhausted — remaining gaps need a relaunch"
