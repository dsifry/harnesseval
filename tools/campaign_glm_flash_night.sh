#!/bin/bash
# Flash-only night lane: completes the two flash cells' top-6 pairs overnight (night-safe per
# evidence: flash runs healthy at all hours). Vision-mrv runs are deliberately EXCLUDED — they
# burn 68-min no-landings at night; the full finisher script handles them in the morning pool.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_flash_night.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
export HARNESS_KEY_BUDGETS=12,6
export HARNESS_LUNAROUTE_TIMEOUT_S=2400
export HARNESS_LUNAROUTE_KEY_FILES=~/.config/harnesseval/keys.env.bench:~/.config/harnesseval/keys.env
log "=== flash night lane: 2 cells, severity top-6 only ==="

missing_for() {
  .venv/bin/python - "$1" "$2" "$3" <<'PYEOF'
import json, glob, sys
sys.path.insert(0, ".")
from harnesseval.dataset import martian
model, fw, eff = sys.argv[1], sys.argv[2], sys.argv[3]
rows = []
for f in glob.glob(str(martian.GOLDEN_DIR) + "/*.json"):
    for pr in json.load(open(f)):
        cs = pr.get("comments", [])
        sev_w = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        rows.append((sum(sev_w.get(c.get("severity","Low"),1) for c in cs), len(cs), pr["url"]))
rows.sort(reverse=True)
top6 = [u for _,_,u in rows[:6]]
have = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("model"), s.get("framework"), s.get("effort")) != (model, fw, eff): continue
    if s.get("run_batch") != "20260910-mrv0120-manifold": continue
    tok = (s.get("tokens_in") or 0)+(s.get("tokens_out") or 0)
    n = len(s.get("findings", []))
    if s.get("error") or tok == 0 or (n == 0 and tok > 20000): continue
    have.add(s["url"])
for u in top6:
    if u not in have:
        print(u)
PYEOF
}

CELLS="glm-5.3-flash-background/compound-realistic/high glm-5.3-flash-background/metareview-realistic/high"
RUN=0
while :; do
  DONE=1
  for cell in $CELLS; do
    model="${cell%%/*}"; rest="${cell#*/}"; fw="${rest%/*}"; eff="${rest##*/}"
    URL=$(missing_for "$model" "$fw" "$eff" | head -1)
    [ -n "$URL" ] && DONE=0
    [ -z "$URL" ] && continue
    RUN=$((RUN + 1))
    log "run $RUN: $model $fw $eff +1 PR (flash night lane)"
    bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
      --frameworks "$fw" --models "$model" --efforts "$eff" --mode api --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$fw/$model/$eff/$URL" >> "logs/mx_glmflash_night_${fw}_${eff}.log" 2>&1
    log "run $RUN done — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
  done
  [ "$DONE" -eq 1 ] && { log "flash night lane complete — vision-mrv cells await the morning pool"; exit 0; }
done
