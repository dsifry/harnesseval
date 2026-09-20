#!/bin/bash
# Campaign Phase 2.5: CE (compound-realistic) cell completion to full-50, ADDITIVE —
# existing healthy runs are kept, only PRs lacking a healthy run get filled.
# This leg: claude-host CE cells (opus, sonnet) — claude CLI, parallel-safe with the
# codex chain (different CLI/provider) and the GLM supervisor (different resource).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_ce_claude.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
export HARNESS_MRV_BIN=~/Developer/metareview/bin/metareview
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
BATCH=20260910-mrv0120-manifold

missing_specs() {  # model effort -> fill specs for PRs lacking a healthy CE run
  .venv/bin/python - "$1" "$2" <<'PYEOF'
import json, glob, sys
model, eff = sys.argv[1], sys.argv[2]
# the full 50-PR url set, from the golden data ordering the runner uses
rows = []
for f in glob.glob(str(__import__("pathlib").Path(__import__("harnesseval.dataset", fromlist=["martian"]).martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        rows.append(pr["url"])
urls = sorted({u for u in rows})
have = {}
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("framework") == "compound-realistic" and s.get("model") == model and s.get("effort") == eff and s.get("url")):
        n_find = len(s.get("findings", []))
        tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
        bad = tok == 0 or bool(s.get("error")) or (n_find == 0 and tok > 20000)
        have[s.get("url")] = have.get(s.get("url"), False) or (not bad)
missing = [u for u in urls if not have.get(u, False)]
print(",".join(f"compound-realistic/{model}/{eff}/{u.rsplit('/', 1)[-1]}" for u in missing), end="")
PYEOF
}

run_cell() {  # model effort
  local model=$1 eff=$2
  local SPECS; SPECS=$(missing_specs "$model" "$eff")
  if [ -z "$SPECS" ]; then log "cell CE/$model/$eff already complete"; return 0; fi
  local N; N=$(echo "$SPECS" | tr ',' '\n' | wc -l | tr -d ' ')
  log "cell CE/$model/$eff filling $N missing PRs"
  .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks compound-realistic \
    --models $model --efforts $eff --mode cli --concurrency 2 \
    --run-batch $BATCH --skip-batch $BATCH --fill "$SPECS" >> logs/mx_campaign_ce_${model}_${eff}.log 2>&1
  local LEFT; LEFT=$(missing_specs "$model" "$eff" | tr ',' '\n' | grep -c . || true)
  if [ "$LEFT" = "0" ] || [ -z "$LEFT" ]; then
    log "cell CE/$model/$eff CLEAN (50/50)"; return 0
  fi
  log "cell CE/$model/$eff still missing $LEFT — one more fill pass"
  .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks compound-realistic \
    --models $model --efforts $eff --mode cli --concurrency 1 \
    --run-batch $BATCH --skip-batch $BATCH --fill "$(missing_specs "$model" "$eff")" >> logs/mx_campaign_ce_${model}_${eff}.log 2>&1
  log "cell CE/$model/$eff done (remaining: $(missing_specs "$model" "$eff" | tr ',' '\n' | grep -c . || echo 0))"
}

run_cell claude-opus-5 low
run_cell claude-opus-5 medium
run_cell claude-opus-5 high
run_cell claude-sonnet-5 low
run_cell claude-sonnet-5 medium
run_cell claude-sonnet-5 high
log "CE claude-host completion done"
