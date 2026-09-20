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
  local CELLCHECK MISSING_N FILL_SPECS
  for try in 1 2 3 4 5; do
    log "cell $model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode $mode --concurrency 2 \
      --run-batch $BATCH --skip-batch $BATCH >> logs/mx_campaign_${model}_${eff}.log 2>&1
    CELLCHECK=$( .venv/bin/python - "$model" "$eff" <<'PYCHECK'
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
missing = [u for u, ok in have.items() if not ok]
print(len(missing))
print(",".join(f"metareview-realistic/{model}/{eff}/{u.rsplit('/',1)[-1]}" for u in missing), end="")
PYCHECK
)
    MISSING_N=$(echo "$CELLCHECK" | head -1)
    FILL_SPECS=$(echo "$CELLCHECK" | tail -1)
    if [ "$MISSING_N" = "0" ]; then
      log "cell $model/$eff CLEAN (healthy run for every PR)"; return 0
    fi
    log "cell $model/$eff missing $MISSING_N healthy PRs — refilling exactly those (concurrency 1)"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode $mode --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH --fill "$FILL_SPECS" >> logs/mx_campaign_${model}_${eff}.log 2>&1
  done
  log "cell $model/$eff FAILED after 5 attempts — missing: $MISSING_N"
  return 1
}

run_cell gpt-5.6-sol medium cli
run_cell gpt-5.6-sol high cli
run_cell gpt-5.6-terra low cli
run_cell gpt-5.6-terra medium cli
run_cell gpt-5.6-terra high cli
log "codex hosts done"
