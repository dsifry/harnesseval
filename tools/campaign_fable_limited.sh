#!/bin/bash
# LIMITED fable run: top-6 PRs (sorted-URL order, deterministic) per cell across all 8 cells
# (vanilla med/high + CE low/med/high + mrv low/med/high; vanilla-low reused from 20260906 per locked spec).
# Expandable: raise TOPN to 20 and relaunch — the census re-picks the larger subset.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_fable.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
CONC=1  # one PR at a time within a cell: a mid-run session drain costs at most ONE in-flight attempt
MODEL=claude-fable-5-1
TOPN=6

missing_specs() {  # fw eff -> fill specs for the top-6 subset's PRs lacking a healthy run
  .venv/bin/python - "$1" "$2" "$TOPN" <<'PYEOF'
import json, glob, sys
from pathlib import Path
fw, eff, topn = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ".")
from harnesseval.dataset import martian
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        rows.append(pr["url"])
urls = sorted({u for u in rows})[:topn]  # the deterministic top-N subset
have = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if not s.get("url"): continue
    b = s.get("run_batch")
    if b != "20260910-mrv0120-manifold" and not (b == "20260906-fable51-vanilla-medhigh" and fw == "vanilla-engineered"): continue
    if (s.get("framework"), s.get("model"), s.get("effort")) != (fw, "claude-fable-5-1", eff): continue
    n = len(s.get("findings", [])); tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
    if tok and not s.get("error") and (n or tok <= 20000): have.add(s["url"])
missing = [u for u in urls if u not in have]
print(",".join(f"{fw}/claude-fable-5-1/{eff}/{u.rsplit('/', 1)[-1]}" for u in missing))
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

CELLS="vanilla-engineered/medium vanilla-engineered/high compound-realistic/low compound-realistic/medium compound-realistic/high metareview-realistic/low metareview-realistic/medium metareview-realistic/high"

log "LIMITED fable run: top-$TOPN PRs x 8 cells on the new account (expand: raise TOPN and relaunch)"
for ROUND in 1 2 3 4 5 6 7 8; do
  if ! claude_ok; then
    log "round $ROUND: capped at round start — waiting out the window; probing every 10 min"
    while ! claude_ok; do sleep 600; done
    log "round $ROUND: window open — starting cells"
  fi
  PIDS=""
  for cell in $CELLS; do
    fw="${cell%%/*}"; eff="${cell##*/}"
    SPECS=$(missing_specs "$fw" "$eff")
    if [ -z "$SPECS" ]; then log "round $ROUND: cell $fw/$eff top-$TOPN subset complete — skip"; continue; fi
    if ! claude_ok; then
      log "round $ROUND: capped at cell $fw/$eff — waiting out the window; probing every 10 min"
      while ! claude_ok; do sleep 600; done
      log "round $ROUND: window open — retrying cell $fw/$eff"
    fi
    N=$(echo "$SPECS" | tr ',' '\n' | grep -c .)
    log "round $ROUND: cell $fw/$MODEL/$eff — $N missing, running ONE PR AT A TIME (probe-gated between every run)"
    echo "$SPECS" | tr ',' '\n' | grep . | while IFS= read -r SPEC; do
      if ! claude_ok; then
        log "claude capped before $fw/$eff PR $SPEC — waiting out the window; probing every 10 min"
        while ! claude_ok; do sleep 600; done
        log "claude window open — resuming $fw/$eff"
      fi
      log "round $ROUND: $fw/$eff — running single PR $SPEC"
      bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks "$fw" \
        --models $MODEL --efforts "$eff" --mode cli --concurrency 1 \
        --run-batch $BATCH --skip-batch $BATCH \
        --fill "$SPEC" >> "logs/mx_campaign_fable_${fw}_${eff}.log" 2>&1
    done
    if ! claude_ok; then
      log "claude capped after cell $fw/$eff — waiting out the window; probing every 10 min"
      while ! claude_ok; do sleep 600; done
      log "claude window open — continuing"
    fi
  done
  DONE=1
  for cell in $CELLS; do
    fw="${cell%%/*}"; eff="${cell##*/}"
    [ -n "$(missing_specs "$fw" "$eff")" ] && DONE=0
  done
  [ "$DONE" -eq 1 ] && { log "all 8 fable cells complete on the top-$TOPN subset — done (expand: TOPN=20 + relaunch)"; exit 0; }
  log "round $ROUND finished — re-censusing"
done
log "limited fable run: 6 rounds exhausted — remaining subset gaps need a relaunch"
