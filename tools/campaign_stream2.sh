#!/bin/bash
# Lunaroute stream 2 (INTERACTIVE key): CE + vanilla GLM completion cells.
# Stream 1 (bench key, campaign_glm_final.sh) owns the mrv GLM legs; this stream owns
# the additive completion blocks. One manager per stream; no cell overlap.
# Trade-off (owner-approved): interactive API calls share this key's quota with the
# stream — throttle concurrency if interactivity degrades.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_stream2.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
# NOTE: default keys.env (the interactive key) — HARNESS_KEYS_FILE is deliberately NOT set.

run_cell() {  # fw model eff
  local fw=$1 model=$2 eff=$3
  for try in 1 2 3; do
    log "cell $fw/$model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks $fw \
      --models $model --efforts $eff --mode api --concurrency 3 \
      --run-batch $BATCH --skip-batch $BATCH >> logs/mx_campaign_s2_${fw}_${model}_${eff}.log 2>&1
    local LEFT
    LEFT=$( .venv/bin/python - "$fw" "$model" "$eff" <<'PYEOF'
import json, glob, sys
fw, model, eff = sys.argv[1], sys.argv[2], sys.argv[3]
have = {}
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("framework") == fw and s.get("model") == model and s.get("effort") == eff and s.get("url")):
        n_find = len(s.get("findings", []))
        tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
        bad = tok == 0 or bool(s.get("error")) or (n_find == 0 and tok > 20000)
        have[s.get("url")] = have.get(s.get("url"), False) or (not bad)
print(len([u for u, ok in have.items() if not ok]))
PYEOF
)
    if [ "$LEFT" = "0" ]; then log "cell $fw/$model/$eff CLEAN (50/50)"; return 0; fi
    log "cell $fw/$model/$eff missing $LEFT — retrying sweep (attempt $try)"
  done
  log "cell $fw/$model/$eff FAILED after 3 attempts"
  return 1
}

# CE GLM completion (the two largest gaps)
run_cell compound-realistic glm-5.3-vision-background low
run_cell compound-realistic glm-5.3-vision-background medium
run_cell compound-realistic glm-5.3-vision-background high
run_cell compound-realistic glm-5.3-flash-background low
run_cell compound-realistic glm-5.3-flash-background medium
run_cell compound-realistic glm-5.3-flash-background high
log "stream 2: CE GLM complete"

# vanilla GLM completion
run_cell vanilla-engineered glm-5.3-vision-background low
run_cell vanilla-engineered glm-5.3-vision-background medium
run_cell vanilla-engineered glm-5.3-vision-background high
run_cell vanilla-engineered glm-5.3-flash-background low
run_cell vanilla-engineered glm-5.3-flash-background medium
run_cell vanilla-engineered glm-5.3-flash-background high
log "stream 2: vanilla GLM complete — stream 2 done"
