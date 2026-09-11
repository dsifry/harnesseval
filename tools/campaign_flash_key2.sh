#!/bin/bash
# Flash cells on the ORIGINAL (interactive) key — the bench key's lanes are saturated
# (owner authorized dual-key use 2026-09-10). Runs in parallel with the vision supervisor.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_phase2_glm.log
log() { echo "$(date +%H:%M) [flash-key2] $*" | tee -a "$LOG"; }
unset HARNESS_KEYS_FILE   # default keys.env = the original interactive key
BATCH=20260910-mrv0120-manifold

run_cell() {  # model effort
  local model=$1 eff=$2
  for try in 1 2 3 4 5; do
    log "cell $model/$eff attempt $try"
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode api --concurrency 3 \
      --run-batch $BATCH --skip-batch $BATCH >> logs/mx_campaign_${model}_${eff}.log 2>&1
    if [ "$( .venv/bin/python - "$model" "$eff" <<'PYEOF'
import json, glob, sys
model, eff = sys.argv[1], sys.argv[2]
have = {}
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        n_find = len(s.get("findings", []))
        tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
        bad = tok == 0 or bool(s.get("error")) or (n_find == 0 and tok > 20000)
        u = s.get("url")
        have[u] = have.get(u, False) or (not bad)
print(len([u for u, ok in have.items() if not ok]))
PYEOF
)" = "0" ]; then
      log "cell $model/$eff CLEAN (healthy run for every PR)"; return 0
    fi
    log "cell $model/$eff incomplete — next attempt re-runs the missing cells"
  done
  log "cell $model/$eff FAILED after 5 attempts"
  return 1
}

run_cell glm-5.3-flash-background medium
run_cell glm-5.3-flash-background high
log "flash legs complete (original key)"
