#!/bin/bash
# GLM top-6 finisher: the remaining 16 pairs — the 4 partial cells (flash CE-high 3, flash mrv-high 3,
# vision CE-high 1, vision mrv-medium 3) plus the held vision mrv-high (6, LAST — the degenerate-empty
# cell that needs the pool's good hours; by the time the first 10 land, we may be in them).
# Severity top-6 only (the HARNESS ordering — CAMPAIGN_GLOSSARY.md). Strictly sequential, one lane.
# DRY RUN BY DEFAULT: pass DRY=0 for live.
set -u
cd "$(dirname "$0")/.."
# FD headroom (2026-09-15): macOS soft limit is 256; a runner holding 6 concurrent SSL conns +
# lens/diff/result files can exhaust it, surfacing as "lenses: Connection error." (Errno 24 hit
# 45x historically). Raise for everything this script spawns.
ulimit -n 10240 2>/dev/null || true
LOG=logs/campaign_glm_top6_finish.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}
BATCH=20260910-mrv0120-manifold
export HARNESS_KEYS_FILE="${GLMFIN_KEYS_FILE:-$HOME/.config/harnesseval/keys.env.bench}"
export HARNESS_KEY_BUDGETS="${GLMFIN_KEY_BUDGETS:-12,6}"
# 900s: the ONLY successful landing tonight (flash mrv-high, 2026-09-15 01:41, 3129s wall) ran
# under 900s; vision lens calls are the longest (peer probe: 351s; failures at 2610-2908s). 600s
# was trialled briefly and reverted — it risks killing legitimate long vision calls before the
# gateway's ~600s wall resolves them. Fast-fail tuning belongs in the retry ladder, not here.
export HARNESS_LUNAROUTE_TIMEOUT_S=900
export HARNESS_LUNAROUTE_KEY_FILES="${GLMFIN_KEY_FILES:-$HOME/.config/harnesseval/keys.env.bench:$HOME/.config/harnesseval/keys.env}"
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
# GLMFIN_CELLS overrides the cell subset (e.g. flash-only tonight, vision-mrv cells held for the
# morning pool: night degenerate-empty mode hits vision mrv lens calls at ANY effort — 2026-09-14).
CELLS=${GLMFIN_CELLS:-"glm-5.3-vision-background/compound-realistic/high \
glm-5.3-vision-background/metareview-realistic/medium \
glm-5.3-flash-background/compound-realistic/high \
glm-5.3-flash-background/metareview-realistic/high \
glm-5.3-vision-background/metareview-realistic/high"}

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
NCELLS=$(echo "$CELLS" | wc -w | tr -d ' ')
log "phase 1 result: $TOTAL runs needed across $NCELLS cells"

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
    VER_BEFORE=$(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)
    bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
      --frameworks "$fw" --models "$model" --efforts "$eff" --mode api --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$fw/$model/$eff/$URL" >> "logs/mx_campaign_glmfinish_${fw}_${eff}.log" 2>&1
    RC=$?
    VER_AFTER=$(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)
    log "run $RUN done rc=$RC — verifier: $VER_AFTER"
    [ "$VER_BEFORE" = "$VER_AFTER" ] && log "run $RUN WARNING: verifier did not advance — degenerate or failed landing (see mx log)"
  done
  [ "$DONE" -eq 1 ] && { log "ALL 5 GLM cells complete on the severity top-6 — done"; exit 0; }
done
