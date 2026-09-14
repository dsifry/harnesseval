#!/bin/bash
# GLM vision vanilla top-6 completion: the 3 never-run cells (vanilla-engineered x low/med/high x glm-5.3-vision-background),
# targeting ONLY the severity-weight top-6 PRs (the HARNESS ordering — CAMPAIGN_GLOSSARY.md). 18 runs.
# Mode: api (lunaroute) — consumes NO claude/codex session capacity.
# DRY RUN BY DEFAULT: pass DRY=0 for live.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glmvan_prep.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}
BATCH=20260910-mrv0120-manifold
MODEL=glm-5.3-vision-background
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
export HARNESS_KEY_BUDGETS=12,6
export HARNESS_LUNAROUTE_TIMEOUT_S=2400
export HARNESS_LUNAROUTE_KEY_FILES=~/.config/harnesseval/keys.env.bench:~/.config/harnesseval/keys.env
[ "$DRY" = "0" ] && log "=== LIVE MODE ===" || log "=== DRY RUN MODE — zero tokens ==="

missing_for() {  # eff -> missing top-6 PR urls
  .venv/bin/python - "$1" <<'PYEOF'
import json, glob, sys
from pathlib import Path
import sys as _s; _s.path.insert(0, ".")
from harnesseval.dataset import martian
eff = sys.argv[1]
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
    if (s.get("model"), s.get("framework"), s.get("effort")) != ("glm-5.3-vision-background", "vanilla-engineered", eff): continue
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

# ---- PHASE 1: census ----
log "phase 1: census of the 3 glm-vision vanilla cells against the severity top-6"
TOTAL=0
for eff in low medium high; do
  M=$(missing_for "$eff")
  N=$(echo "$M" | grep -c . || true)
  TOTAL=$((TOTAL + N))
  log "  $MODEL vanilla $eff: missing $N/6"
  if [ "$DRY" = "1" ]; then echo "$M" | while IFS= read -r u; do [ -n "$u" ] && log "    would run: vanilla-engineered/$MODEL/$eff/$u"; done; fi
done
log "phase 1 result: $TOTAL runs needed across 3 cells"

# ---- PHASE 2: launch mechanics (zero tokens) ----
if [ "$DRY" = "1" ]; then
  PH2=$(.venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
    --frameworks vanilla-engineered --models $MODEL --efforts low --mode api --concurrency 1 \
    --run-batch $BATCH --skip-batch $BATCH \
    --fill "vanilla-engineered/$MODEL/low/https://github.com/nonexistent/no-such-pr/999999" 2>&1 | grep -c "running 0 cells" || true)
  if [ "$PH2" = "1" ]; then
    log "phase 2 PASS: runner matched 0 cells on the no-match spec (zero tokens)"
  else
    log "phase 2 FAIL — DO NOT run live"; exit 1
  fi
  log "DRY RUN COMPLETE — live plan: STRICTLY SEQUENTIAL single-PR api runs (one lane; the vision pool has a fixed lane count), verifier-checked after every run"
  exit 0
fi

# ---- LIVE: paced waves ----
WAVE=0
while :; do
  WAVE=$((WAVE + 1))
  DONE=1
  PIDS=""
  for eff in low medium high; do
    URL=$(missing_for "$eff" | head -1)
    [ -n "$URL" ] && DONE=0
    [ -z "$URL" ] && continue
    log "run $WAVE: $MODEL vanilla $eff +1 PR (SEQUENTIAL — one lane, no parallelism: the vision pool has a fixed number of lanes)"
    bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
      --frameworks vanilla-engineered --models $MODEL --efforts "$eff" --mode api --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "vanilla-engineered/$MODEL/$eff/$URL" >> "logs/mx_campaign_glmvan_${eff}.log" 2>&1
    log "run $WAVE done — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
  done
  log "wave $WAVE done — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
done
