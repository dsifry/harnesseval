#!/bin/bash
# Final campaign refill sweeper — loops over every campaign cell and fills whatever
# is still missing, one pass per round, until all cells are 50/50 or maxed rounds.
# Launch AFTER the CE/GLM chains drain (single sweeper — the one-manager lesson).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_final_refill.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
export HARNESS_KEY_BUDGETS=12,6
export HARNESS_LUNAROUTE_TIMEOUT_S=2400  # queue headroom: longest observed drain 1778s, ceiling gives peak-hour margin
export HARNESS_LUNAROUTE_KEY_FILES=~/.config/harnesseval/keys.env.bench:~/.config/harnesseval/keys.env
MAX_ROUNDS=6

missing_specs() {  # fw model eff -> comma-sep fw/model/eff/url-suffix for PRs lacking a healthy run
  .venv/bin/python - "$1" "$2" "$3" "$BATCH" <<'PYEOF'
import json, glob, sys, os
from pathlib import Path
fw, model, eff, batch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, ".")
from harnesseval.dataset import martian
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        rows.append(pr["url"])
urls = sorted({u for u in rows})
have = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if s.get("run_batch") != batch or not s.get("url"):
        continue
    if (s.get("framework"), s.get("model"), s.get("effort")) != (fw, model, eff):
        continue
    n_find = len(s.get("findings", []))
    tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
    if tok and not s.get("error") and (n_find or tok <= 20000):
        have.add(s["url"])
missing = [u for u in urls if u not in have]
print(",".join(f"{fw}/{model}/{eff}/{u.rsplit('/', 1)[-1]}" for u in missing))
PYEOF
}

cli_ok() {  # cheap OAuth probe before burning a cell's attempts against a capped CLI
  case "$2" in
    glm-*) return 0 ;;  # api models: the GLM chain has its own gate
  esac
  .venv/bin/python - "$2" <<'PYEOF'
import sys, asyncio
sys.path.insert(0, '.')
from harnesseval import cli_backends
model = sys.argv[1]
async def t():
    try:
        if model.startswith("gpt"):
            fn = cli_backends._codex_cli
        else:
            fn = cli_backends._claude_cli
        text, _, _ = await fn(model, 'low', 'Reply with the single word ok')
        sys.exit(0 if text.strip() else 1)
    except SystemExit: raise
    except Exception: sys.exit(1)
asyncio.run(t())
PYEOF
}

for round in $(seq 1 $MAX_ROUNDS); do
  log "=== refill round $round"
  INCOMPLETE=0
  for fw in compound-realistic metareview-realistic vanilla-engineered; do
    for model in claude-opus-5 claude-sonnet-5 gpt-5.6-sol gpt-5.6-terra glm-5.3-vision-background glm-5.3-flash-background; do
      for eff in low medium high; do
        # ownership split: the GLM chain (window glmfinal) owns the mrv glm cells;
        # the sweeper owns CE/vanilla glm cells + everything else. Two managers on
        # one cell = duplicate runs + 429 thrash (2026-09-11 collision, caught live).
        if [ "$fw" = "metareview-realistic" ] && [ "$model" = "glm-5.3-vision-background" -o "$model" = "glm-5.3-flash-background" ]; then
          continue
        fi
        SPECS=$(missing_specs "$fw" "$model" "$eff")
        [ -z "$SPECS" ] && continue
        N=$(echo "$SPECS" | tr ',' '\n' | wc -l | tr -d ' ')
        INCOMPLETE=$((INCOMPLETE + 1))
        if ! cli_ok "$fw" "$model"; then
          log "cell $fw/$model/$eff — SKIPPED this round: CLI probe failed (rate-cap guard, prevents attempt storm)"
          continue
        fi
        log "cell $fw/$model/$eff — refilling $N"
        # CLI-hosted premium models (claude/gpt slugs) run via the CLI (OAuth); GLM via the API
        case "$model" in
          glm-*) MODE=api; CONC=2 ;;  # vision pool negative-scales past 2-wide (measured)
          *)     MODE=cli; CONC=3 ;;
        esac
        HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench \
          .venv/bin/python -m harnesseval.run_model_matrix --prs 50 \
          --frameworks "$fw" --models "$model" --efforts "$eff" --mode "$MODE" \
          --concurrency $CONC --run-batch $BATCH --skip-batch $BATCH \
          --fill "$SPECS" >> "logs/mx_campaign_${model}_${eff}.log" 2>&1
        log "cell $fw/$model/$eff refill pass done"
      done
    done
  done
  [ "$INCOMPLETE" -eq 0 ] && { log "ALL CELLS COMPLETE (50/50)"; exit 0; }
  sleep 120
done
log "max rounds reached — cells still incomplete; check dashboard"
