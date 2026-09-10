#!/bin/bash
# Campaign Phase 2 (GLM legs): api-direct mrv cells on the BENCH key.
# Runs in parallel with the codex chain (different resource: Lunaroute vs local CLI).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_phase2_glm.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench

PYCLEAN='
import json, glob, os, shutil
model, eff = os.environ.get("CELL_MODEL"), os.environ.get("CELL_EFF")
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        if (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or s.get("error"):
            shutil.rmtree(os.path.dirname(f), ignore_errors=True)
            print("removed poison:", f)
'

run_cell() {  # model effort
  local model=$1 eff=$2
  local batch="20260910-mrv0120-manifold"
  for try in 1 2 3; do
    log "cell $model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode api --concurrency 3 \
      --run-batch $batch --skip-batch $batch >> logs/mx_campaign_${model}_${eff}.log 2>&1
    if .venv/bin/python -m harnesseval.validate --batch $batch >/dev/null 2>&1; then
      log "cell $model/$eff CLEAN"; return 0
    fi
    log "cell $model/$eff POISONED — cleaning and retrying"
    CELL_MODEL=$model CELL_EFF=$eff .venv/bin/python -c "$PYCLEAN"
  done
  log "cell $model/$eff FAILED after 3 attempts"
  return 1
}

export CELL_MODEL=glm-5.3-vision-background CELL_EFF=low;      run_cell glm-5.3-vision-background low
export CELL_MODEL=glm-5.3-vision-background CELL_EFF=medium;   run_cell glm-5.3-vision-background medium
export CELL_MODEL=glm-5.3-vision-background CELL_EFF=high;     run_cell glm-5.3-vision-background high
log "glm vision cells done"
export CELL_MODEL=glm-5.3-flash-background CELL_EFF=low;       run_cell glm-5.3-flash-background low
export CELL_MODEL=glm-5.3-flash-background CELL_EFF=medium;    run_cell glm-5.3-flash-background medium
export CELL_MODEL=glm-5.3-flash-background CELL_EFF=high;      run_cell glm-5.3-flash-background high
log "glm flash cells done — GLM legs complete"
