#!/bin/bash
# GLM full 50-PR matrix lane: fills every missing (framework x model x effort x PR) cell for the
# two GLM rows, SKIPPING cells that already have HEALTHY evidence (--skip-batch, which since the
# 2026-09-15 "THIRD FIX" requires no-error + tokens>0 before locking a cell out).
#
# Why now (2026-09-15): streaming (default ON in model_router) removed the gateway wedge and the
# lens pool is 4-wide, so runs complete in ~20-40 min instead of failing. ~250 cells were missing
# across these six cells before this lane.
#
# DRY RUN BY DEFAULT: pass DRY=0 for live.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_fullmatrix.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}
BATCH=20260910-mrv0120-manifold
[ "$DRY" = "0" ] && log "=== LIVE: GLM full-matrix fill ===" || log "=== DRY RUN ==="

ulimit -n 10240 2>/dev/null || true
export HARNESS_KEYS_FILE="${GLMFULL_KEYS_FILE:-$HOME/.config/harnesseval/keys.env.bench}"
export HARNESS_KEY_BUDGETS="${GLMFULL_KEY_BUDGETS:-12,6}"
export HARNESS_LUNAROUTE_TIMEOUT_S=900
export HARNESS_LUNAROUTE_KEY_FILES="${GLMFULL_KEY_FILES:-$HOME/.config/harnesseval/keys.env.bench:$HOME/.config/harnesseval/keys.env}"

ARGS=(--prs 50
      --frameworks compound-realistic,metareview-realistic
      --models glm-5.3-flash-background,glm-5.3-vision-background
      --efforts low,medium,high
      --mode api --concurrency 1
      --run-batch "$BATCH" --skip-batch "$BATCH")

if [ "$DRY" = "1" ]; then
  # no-token assertion: a deliberately impossible fill spec must match 0 cells
  .venv/bin/python -u -m harnesseval.run_model_matrix "${ARGS[@]}" \
    --fill "compound-realistic/glm-5.3-flash-background/high/https://github.com/nonexistent/no-such-pr/999999" \
    2>&1 | grep -E "total skip set|running [0-9]+ cells" | tail -3
  log "DRY: above must show 'running 0 cells' — then relaunch with DRY=0"
  exit 0
fi

log "launching full-matrix fill (sequential, lens pool 4, streaming on)"
.venv/bin/python -u -m harnesseval.run_model_matrix "${ARGS[@]}" >> "logs/mx_glm_fullmatrix_run.log" 2>&1
log "full-matrix lane exited rc=$? — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
