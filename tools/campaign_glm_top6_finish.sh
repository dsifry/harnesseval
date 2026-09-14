#!/bin/bash
# GLM top-6 finisher: the remaining 16 pairs — the 4 partial cells (flash CE-high 3, flash mrv-high 3,
# vision CE-high 1, vision mrv-medium 3) plus the held vision mrv-high (6, LAST — the degenerate-empty
# cell that needs the pool's good hours; by the time the first 10 land, we may be in them).
# Severity top-6 only (the HARNESS ordering — CAMPAIGN_GLOSSARY.md). Strictly sequential, one lane.
# DRY RUN BY DEFAULT: pass DRY=0 for live.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_top6_finish.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}
BATCH=20260910-mrv0120-manifold
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
export HARNESS_KEY_BUDGETS=12,6
export HARNESS_LUNAROUTE_TIMEOUT_S=2400
export HARNESS_LUNAROUTE_KEY_FILES=~/.config/harnesseval/keys.env.bench:~/.config/harnesseval/keys.env
[ "$DRY" = "0" ] && log "=== LIVE MODE — sequential lunaroute lane ===" || log "=== DRY RUN MODE — zero tokens ==="

missing_for() {  # model fw eff -> missing top-6 PR urls
  .venv/bin/python - "$1" "$2" "$3" <<'PYEOF'
import json, glob, sys
from pathlib import Path
import sys as _s; _s.path.insert(0, ".")
from harnesseval.dataset import martian
model, fw, eff = sys.argv[1], sys.argv[2], sys.argv[3]
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        cs = pr.get("comments", [])
        sev_w = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        rows.append((sum(sev_w.get(c.get("severity", "Low"), 1) for c in cs), len(cs), pr["url"]))
rows.sort(reverse=True)
top6 = [u for _, _, u in rows[:6]]
have = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("model"), s.get("framework"), s.get("effort")) != (model, fw, eff): continue
    if s.get("run_batch") != "20260910-mrv0120-manifold": continue
    tok = (s.get("tokens_in") or 0) + (s.get("tokens_out") or 0)
    n = len(s.get("findings", []))
    if s.get("error") or tok == 0 or (n == 0 and tok > 20000): continue
    have.add(s["url"])
for u in top6:
    if u not in have:
        print(u)
PYEOF
}

# deterministic cell order: partials first (cheapest/closest first), held cell LAST
CELLS="glm-5.3-vision-background/compound-realistic/high \
glm-5.3-vision-background/metareview-realistic/medium \
glm-5.3-flash-background/compound-realistic/high \
glm-5.3-flash-background/metareview-realistic/high \
glm-5.3-vision-background/metareview-realistic/high"

# ---- PHASE 1: census ----
log "phase 1: census of the 5 remaining GLM cells against the severity top-6"
TOTAL=0
for cell in $CELLS; do
  model="${cell%%/*}"; rest="${cell#*/}"; fw="${rest%/*}"; eff="${rest##*/}"
  M=$(missing_for "$model" "$fw" "$eff")
  N=$(echo "$M" | grep -c . || true)
  TOTAL=$((TOTAL + N))
  log "  $model $fw $eff: missing $N/6"
  if [ "$DRY" = "1" ]; then echo "$M" | while IFS= read -r u; do [ -n "$u" ] && log "    would run: $fw/$model/$eff/$u"; done; fi
done
log "phase 1 result: $TOTAL runs needed across 5 cells"

# ---- PHASE 2: launch mechanics (zero tokens) ----
if [ "$DRY" = "1" ]; then
  PH2=$(.venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
    --frameworks compound-realistic --models glm-5.3-flash-background --efforts high --mode api --concurrency 1 \
    --run-batch $BATCH --skip-batch $BATCH \
    --fill "compound-realistic/glm-5.3-flash-background/high/https://github.com/nonexistent/no-such-pr/999999" 2>&1 | grep -c "running 0 cells" || true)
  if [ "$PH2" = "1" ]; then
    log "phase 2 PASS: runner matched 0 cells on the no-match spec (zero tokens)"
  else
    log "phase 2 FAIL — DO NOT run live"; exit 1
  fi
  log "DRY RUN COMPLETE — live plan: strictly sequential single-PR api runs, verifier after every run, held cell last"
  exit 0
fi

# ---- LIVE: strictly sequential, one lane ----
RUN=0
while :; do
  DONE=1
  for cell in $CELLS; do
    model="${cell%%/*}"; rest="${cell#*/}"; fw="${rest%/*}"; eff="${rest##*/}"
    URL=$(missing_for "$model" "$fw" "$eff" | head -1)
    [ -n "$URL" ] && DONE=0
    [ -z "$URL" ] && continue
    RUN=$((RUN + 1))
    log "run $RUN: $model $fw $eff +1 PR (sequential lane)"
    bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
      --frameworks "$fw" --models "$model" --efforts "$eff" --mode api --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$fw/$model/$eff/$URL" >> "logs/mx_campaign_glmfinish_${fw}_${eff}.log" 2>&1
    log "run $RUN done — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
  done
  [ "$DONE" -eq 1 ] && { log "ALL 5 GLM cells complete on the severity top-6 — done"; exit 0; }
done
