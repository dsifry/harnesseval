#!/bin/bash
# Expanded astra run: gpt-6-astra (Codex CLI slug) across vanilla/CE/mrv x low/medium/high.
# vanilla-low is NOT re-run: the original astra vanilla-low runs are reused per the locked spec.
# Codex OAuth cap resets ~3h from 2026-09-11 18:40 PDT — health-gated: bursts at max width when codex opens.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_astra.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
CONC=8
MODEL=gpt-6-astra

missing_specs() {  # fw model eff -> per-PR fill specs for PRs lacking a healthy run
  .venv/bin/python - "$1" "$2" "$3" "$BATCH" <<'PYEOF'
import json, glob, sys, os
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

log "expanded astra run: $MODEL across vanilla/CE/mrv x low/med/high (vanilla-low reused, not re-run)"
while ! codex_ok; do
  log "gate: codex capped — waiting for the reset (probing every 2 min)"
  sleep 120
done
log "codex open — bursting: all 8 cells concurrently, OAuth CLI, conc $CONC each"

PIDS=""
for fw in vanilla-engineered compound-realistic metareview-realistic; do
  for eff in low medium high; do
    SPECS=$(missing_specs "$fw" "$MODEL" "$eff")
    if [ -z "$SPECS" ]; then log "cell $fw/$MODEL/$eff complete — skip"; continue; fi
    N=$(echo "$SPECS" | tr ',' '\n' | grep -c .)
    log "launching cell $fw/$MODEL/$eff — filling $N (background)"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks "$fw" \
      --models $MODEL --efforts "$eff" --mode cli --concurrency $CONC \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$SPECS" >> "logs/mx_campaign_astra_${fw}_${eff}.log" 2>&1 &
    PIDS="$PIDS $!"
  done
done
wait $PIDS
log "all first passes done — retry passes for cells still missing"

PIDS=""
for fw in vanilla-engineered compound-realistic metareview-realistic; do
  for eff in low medium high; do
    SPECS2=$(missing_specs "$fw" "$MODEL" "$eff")
    [ -z "$SPECS2" ] && { log "cell $fw/$MODEL/$eff complete"; continue; }
    N2=$(echo "$SPECS2" | tr ',' '\n' | grep -c .)
    log "launching retry cell $fw/$MODEL/$eff — missing $N2 (background)"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks "$fw" \
      --models $MODEL --efforts "$eff" --mode cli --concurrency $CONC \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$SPECS2" >> "logs/mx_campaign_astra_${fw}_${eff}.log" 2>&1 &
    PIDS="$PIDS $!"
  done
done
wait $PIDS
log "expanded astra run complete"
