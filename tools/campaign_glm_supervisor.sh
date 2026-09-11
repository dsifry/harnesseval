#!/bin/bash
# GLM campaign supervisor: waits for the two orphan runners to finish their cells,
# then completes the remaining GLM cells (flash x3 + any vision stragglers).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_phase2_glm.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
BATCH=20260910-mrv0120-manifold

log "supervisor: waiting for orphan runners 66087 (vision-high) and 66309 (vision-medium)"
while ps -p 66087 >/dev/null 2>&1 || ps -p 66309 >/dev/null 2>&1; do sleep 60; done
log "supervisor: orphan runners finished"

PYCLEAN='
import json, glob, os, shutil, sys
model, eff = sys.argv[1], sys.argv[2]
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        if (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or s.get("error"):
            shutil.rmtree(os.path.dirname(f), ignore_errors=True)
            print("removed poison:", f)
'
poison_specs() {
  .venv/bin/python - "$1" "$2" <<'PYEOF'
import json, glob, sys
model, eff = sys.argv[1], sys.argv[2]
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        if (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or s.get("error"):
            print(f"metareview-realistic/{model}/{eff}/{(s.get('url') or '').rsplit('/', 1)[-1]}")
PYEOF
}

run_cell() {  # model effort
  local model=$1 eff=$2
  for try in 1 2 3 4 5; do
    log "supervisor: cell $model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode api --concurrency 5 \
      --run-batch $BATCH --skip-batch $BATCH >> logs/mx_campaign_${model}_${eff}.log 2>&1
    if .venv/bin/python -m harnesseval.validate --batch $BATCH >/dev/null 2>&1; then
      log "supervisor: cell $model/$eff CLEAN"; return 0
    fi
    local SPECS; SPECS=$(poison_specs "$model" "$eff")
    # only refill if the cell lacks a healthy run for some PR (dead duplicates are fine)
    NEED=$( .venv/bin/python - "$model" "$eff" <<'PYEOF'
import json, glob, sys
model, eff = sys.argv[1], sys.argv[2]
have = {}
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        bad = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or bool(s.get("error"))
        u = s.get("url")
        have[u] = have.get(u, False) or (not bad)
print(len([u for u, ok in have.items() if not ok]))
PYEOF
)
    if [ "$NEED" = "0" ]; then
      log "supervisor: cell $model/$eff effectively complete (healthy run for every PR; residue only)"; return 0
    fi
    log "supervisor: cell $model/$eff missing $NEED healthy PRs — cleaning and refilling"
    .venv/bin/python -c "$PYCLEAN" "$model" "$eff" 2>/dev/null || CELL_MODEL=$model CELL_EFF=$eff .venv/bin/python -c "$PYCLEAN"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode api --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH --fill "$(poison_specs "$model" "$eff" | tr '\n' ',')" >> logs/mx_campaign_${model}_${eff}.log 2>&1
  done
  log "supervisor: cell $model/$eff FAILED after 5 attempts"
  return 1
}

run_cell glm-5.3-vision-background medium
run_cell glm-5.3-vision-background high
run_cell glm-5.3-flash-background low
run_cell glm-5.3-flash-background medium
run_cell glm-5.3-flash-background high
log "supervisor: GLM legs complete"
