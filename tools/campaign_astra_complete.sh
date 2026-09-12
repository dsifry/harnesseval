#!/bin/bash
# Astra completion phase: waits for the current astra script to finish (no overlap),
# then gates on codex health (the OAuth reset), and refills all 8 cells to 50/50.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_astra.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
CONC=6
MODEL=gpt-6-astra

log "completion phase: waiting for the first-pass script to exit (handoff)"
while tmux list-windows -t 0 2>/dev/null | grep -q " astra$"; do sleep 60; done
log "handoff complete — gating on codex health"

missing_specs() {
  .venv/bin/python - "$1" "$2" "$3" "$BATCH" <<'PYEOF'
import json, glob, sys
from pathlib import Path
fw, model, eff, batch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
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
    if s.get("run_batch") != batch or not s.get("url"): continue
    if (s.get("framework"), s.get("model"), s.get("effort")) != (fw, model, eff): continue
    n = len(s.get("findings", [])); tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
    if tok and not s.get("error") and (n or tok <= 20000): have.add(s["url"])
missing = [u for u in urls if u not in have]
print(",".join(f"{fw}/{model}/{eff}/{u.rsplit('/', 1)[-1]}" for u in missing))
PYEOF
}

codex_ok() {
  .venv/bin/python - <<'PYEOF'
import sys, asyncio
sys.path.insert(0, ".")
from harnesseval import cli_backends
async def t():
    try:
        text, _, _ = await asyncio.wait_for(cli_backends._codex_cli("gpt-5.6-sol", "low", "Reply with the single word ok"), timeout=60)
        sys.exit(0 if text.strip() else 1)
    except SystemExit: raise
    except Exception: sys.exit(1)
asyncio.run(t())
PYEOF
}

for round in 1 2 3 4 5 6; do
  TOTAL_MISSING=0
  PIDS=""
  for fw in vanilla-engineered compound-realistic metareview-realistic; do
    for eff in low medium high; do
      SPECS=$(missing_specs "$fw" "$MODEL" "$eff")
      [ -z "$SPECS" ] && continue
      N=$(echo "$SPECS" | tr ',' '\n' | grep -c .)
      TOTAL_MISSING=$((TOTAL_MISSING + N))
      log "round $round: launching $fw/$MODEL/$eff — missing $N"
      .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks "$fw" \
        --models $MODEL --efforts "$eff" --mode cli --concurrency $CONC \
        --run-batch $BATCH --skip-batch $BATCH \
        --fill "$SPECS" >> "logs/mx_campaign_astra_${fw}_${eff}.log" 2>&1 &
      PIDS="$PIDS $!"
    done
  done
  [ "$TOTAL_MISSING" -eq 0 ] && { log "ASTRA COMPLETE: all 8 cells at 50/50"; exit 0; }
  wait $PIDS
  log "round $round done — $TOTAL_MISSING were attempted; re-censusing"
  if ! codex_ok; then
    log "codex capped again — waiting for the next window (probing every 2 min)"
    while ! codex_ok; do sleep 120; done
  fi
done
log "max rounds reached — cells still incomplete; manual review"
