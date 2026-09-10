#!/bin/bash
# Manifold campaign Phase 2: mrv-realistic regeneration with the 0.12.0 binary.
# Sequential (model × effort) cells, each with poison guard + retry, per MANIFOLD_RERUN_PLAN.md.
# CLI hosts (codex/claude) run the real binary via HARNESS_MRV_BIN; GLM runs api-direct
# (rc7 adapter — contract-parity verified with the binary 14/14, commit bf5fcb5).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_phase2.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }

export HARNESS_MRV_BIN=~/Developer/metareview/bin/metareview   # v0.12.0
# Bench-key split: campaign processes route Lunaroute calls through the dedicated
# benchmark key (keys.env.bench); the default keys.env stays for interactive work.
# The loader reads HARNESS_KEYS_FILE only when invoked in API mode and passes values
# directly to the SDKs — nothing leaks into os.environ globally.
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench

run_cell() {  # fw model effort mode prs
  local fw=$1 model=$2 eff=$3 mode=$4 prs=$5
  local batch="20260910-mrv0120-manifold"
  for try in 1 2 3; do
    log "cell $fw/$model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs $prs --frameworks $fw \
      --models $model --efforts $eff --mode $mode --concurrency 2 \
      --run-batch $batch --skip-batch $batch >> logs/mx_campaign_${model}_${eff}.log 2>&1
    if .venv/bin/python -m harnesseval.validate --batch $batch >/dev/null 2>&1; then
      log "cell $fw/$model/$eff CLEAN"; return 0
    fi
    log "cell $fw/$model/$eff POISONED — cleaning and retrying"
    .venv/bin/python - <<'EOF'
import json, glob, os, shutil
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == os.environ.get("CELL_MODEL")
            and s.get("effort") == os.environ.get("CELL_EFF")):
        if (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or s.get("error"):
            shutil.rmtree(os.path.dirname(f), ignore_errors=True)
            print("removed poison:", f)
EOF
  done
  log "cell $fw/$model/$eff FAILED after 3 attempts"
  return 1
}

# Order: codex hosts first (slowest, most valuable — extends the acceptance cell), then claude, then GLM api cells.
export CELL_MODEL=gpt-5.6-sol CELL_EFF=low;       run_cell metareview-realistic gpt-5.6-sol low cli 50
export CELL_MODEL=gpt-5.6-sol CELL_EFF=medium;    run_cell metareview-realistic gpt-5.6-sol medium cli 50
export CELL_MODEL=gpt-5.6-sol CELL_EFF=high;      run_cell metareview-realistic gpt-5.6-sol high cli 50
export CELL_MODEL=gpt-5.6-terra CELL_EFF=low;     run_cell metareview-realistic gpt-5.6-terra low cli 50
export CELL_MODEL=gpt-5.6-terra CELL_EFF=medium;  run_cell metareview-realistic gpt-5.6-terra medium cli 50
export CELL_MODEL=gpt-5.6-terra CELL_EFF=high;    run_cell metareview-realistic gpt-5.6-terra high cli 50
log "codex hosts done"
