#!/bin/bash
# Manifold campaign Phase 2: mrv-realistic regeneration with the 0.12.0 binary.
# Sequential (model x effort) cells with poison guard + --fill retry.
# CLI hosts (codex/claude) run the real binary via HARNESS_MRV_BIN; GLM runs api-direct
# (rc7 adapter — contract-parity verified with the binary 14/14, commit bf5fcb5).
# Retry design note: --skip-batch consults the registry, so it can NEVER refill cells the
# registry already counts as pass — retries must use --fill with explicit poisoned specs.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_phase2.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }

export HARNESS_MRV_BIN=~/Developer/metareview/bin/metareview   # v0.12.0
# Bench-key split: campaign processes route Lunaroute calls through the dedicated
# benchmark key (keys.env.bench); the default keys.env stays for interactive work.
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench

BATCH=20260910-mrv0120-manifold

# prints fill specs for poisoned cells of one (model, effort), one per line
poison_specs() {
  .venv/bin/python - "$1" "$2" <<'PYEOF'
import json, glob, sys
model, eff = sys.argv[1], sys.argv[2]
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        if (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or s.get("error"):
            pr = (s.get("url") or "").rsplit("/", 1)[-1]
            print(f"metareview-realistic/{model}/{eff}/{pr}")
PYEOF
}

# deletes the poisoned summaries of one (model, effort)
clean_poison() {
  .venv/bin/python - "$1" "$2" <<'PYEOF'
import json, glob, os, shutil, sys
model, eff = sys.argv[1], sys.argv[2]
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        if (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0) == 0 or s.get("error"):
            shutil.rmtree(os.path.dirname(f), ignore_errors=True)
            print("removed poison:", f)
PYEOF
}

run_cell() {  # model effort mode
  local model=$1 eff=$2 mode=$3
  local n=0
  for try in 1 2 3 4 5; do
    log "cell $model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode $mode --concurrency 2 \
      --run-batch $BATCH --skip-batch $BATCH >> logs/mx_campaign_${model}_${eff}.log 2>&1
    if .venv/bin/python -m harnesseval.validate --batch $BATCH >/dev/null 2>&1; then
      log "cell $model/$eff CLEAN"; return 0
    fi
    SPECS=$(poison_specs "$model" "$eff")
    if [ -z "$SPECS" ]; then
      log "cell $model/$eff validate failed with no poisoned summaries — inspect manually"; return 1
    fi
    log "cell $model/$eff POISONED ($(echo "$SPECS" | wc -l | tr -d ' ') cells) — cleaning and refilling"
    clean_poison "$model" "$eff"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode $mode --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH --fill "$(echo $SPECS | tr ' ' ',')" >> logs/mx_campaign_${model}_${eff}.log 2>&1
    if .venv/bin/python -m harnesseval.validate --batch $BATCH >/dev/null 2>&1; then
      log "cell $model/$eff CLEAN (after refill)"; return 0
    fi
  done
  log "cell $model/$eff FAILED after 5 attempts — specs: $(poison_specs "$model" "$eff" | tr '\n' ' ')"
  return 1
}

run_cell gpt-5.6-sol medium cli
run_cell gpt-5.6-sol high cli
run_cell gpt-5.6-terra low cli
run_cell gpt-5.6-terra medium cli
run_cell gpt-5.6-terra high cli
log "codex hosts done"
