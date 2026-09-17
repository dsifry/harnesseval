#!/bin/bash
# GLM VANILLA full-matrix fill: glm-5.3-flash-background + glm-5.3-vision-background,
# vanilla-engineered, efforts low/medium/high, all 50 PRs minus the 6 top-6-era PRs already
# covered (~44 remaining per effort => ~264 cells).
#
# Context (2026-09-15): vanilla coverage for glm was top-6-only (6/50 exactly), inherited from
# the 20260906-glm53-top6 baseline batches. The hero models (sol/terra/astra) have full 50/50
# vanilla coverage; this lane brings glm to parity. Opus/sonnet vanilla intentionally HELD.
#
# --skip-batch skips any cell with HEALTHY evidence, so the 6 already-done PRs are not redone.
# DRY RUN BY DEFAULT: pass DRY=0 for live.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_vanilla_full.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}
BATCH=20260910-mrv0120-manifold
[ "$DRY" = "0" ] && log "=== LIVE: GLM vanilla full-matrix fill ===" || log "=== DRY RUN ==="

ulimit -n 10240 2>/dev/null || true
export HARNESS_KEYS_FILE="${GLMVAN_KEYS_FILE:-$HOME/.config/harnesseval/keys.env.bench}"
export HARNESS_KEY_BUDGETS="${GLMVAN_KEY_BUDGETS:-12,6}"
export HARNESS_LUNAROUTE_TIMEOUT_S=900
export HARNESS_LUNAROUTE_KEY_FILES="${GLMVAN_KEY_FILES:-$HOME/.config/harnesseval/keys.env.bench:$HOME/.config/harnesseval/keys.env}"

ARGS=(--prs 50
      --frameworks vanilla-engineered
      --models glm-5.3-flash-background,glm-5.3-vision-background
      --efforts low,medium,high
      --mode api --concurrency 1
      --run-batch "$BATCH" --skip-batch "$BATCH")

if [ "$DRY" = "1" ]; then
  .venv/bin/python -u -m harnesseval.run_model_matrix "${ARGS[@]}" \
    --fill "vanilla-engineered/glm-5.3-flash-background/high/https://github.com/nonexistent/no-such-pr/999999" \
    2>&1 | grep -E "total skip set|running [0-9]+ cells" | tail -3
  log "DRY: above must show 'running 0 cells' — then relaunch with DRY=0"
  exit 0
fi

log "launching vanilla fill (sequential, streaming on)"
.venv/bin/python -u -m harnesseval.run_model_matrix "${ARGS[@]}" >> "logs/mx_glm_vanilla_full_run.log" 2>&1
log "vanilla lane exited rc=$? — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
