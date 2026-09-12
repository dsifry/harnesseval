#!/bin/bash
# Credit-exhaustion guard for the astra run: when codex starts rejecting with
# limit/credit/usage errors repeatedly, STOP the astra runners and the completion
# loop (their retries would churn poison until the reset). The completion script
# is resumable after the reset (relaunch it; it re-censuses and refills).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_astra.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }

sig() {  # count limit-signature ERR lines in the astra logs' last 40 lines each
  cat logs/mx_campaign_astra_*.log 2>/dev/null | tail -200 \
    | grep -ciE "(usage limit|credit|limit reached|upgrade|rate.?limit.*exhaust|quota)"
}

STRIKES=0
while true; do
  C=$(sig)
  if [ "$C" -ge 3 ]; then
    STRIKES=$((STRIKES + 1))
  else
    STRIKES=0
  fi
  log "credit-watch: signature count $C, strikes $STRIKES"
  if [ "$STRIKES" -ge 2 ]; then
    log "STOP: credits exhausted — killing astra runners and the completion loop"
    tmux kill-window -t astracomplete 2>/dev/null
    pkill -f "run_model_matrix.*gpt-6-astra" 2>/dev/null
    log "STOPPED. after the reset: relaunch with 'tmux new-window -d -n astracomplete \"bash tools/campaign_astra_complete.sh\"' — it re-censuses and refills to 50/50"
    exit 0
  fi
  sleep 60
done
