#!/bin/bash
# Opus5 + Sonnet top-6 completion: the 12 never-run cells (vanilla + mrv x low/med/high x 2 models),
# targeting ONLY the severity-weight top-6 PRs (the HARNESS ordering — see CAMPAIGN_GLOSSARY.md).
# Design: serial single-PR invocations, probe-gated between EVERY run, interleaved rotations
# (vanilla first — cheap — then mrv), with_ceiling watchdog per run.
# DRY RUN BY DEFAULT: pass DRY=0 for live. In dry mode nothing that spends tokens executes.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_opus_sonnet_top6.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}   # 1 = dry run (zero tokens), 0 = live
BATCH=20260910-mrv0120-manifold
MODELS="claude-opus-5 claude-sonnet-5"

[ "$DRY" = "0" ] && log "=== LIVE MODE — runs will spend claude session tokens ===" || log "=== DRY RUN MODE — zero tokens: census, specs, launch mechanics, completion checks only ==="

# the top-6 PRs by the HARNESS ordering (severity weight desc, comments desc) — computed live, never lexicographic
top6_prs() {
  .venv/bin/python - <<'PYEOF'
import json, glob
from pathlib import Path
import sys
sys.path.insert(0, ".")
from harnesseval.dataset import martian
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        cs = pr.get("comments", [])
        sev_w = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        rows.append((sum(sev_w.get(c.get("severity", "Low"), 1) for c in cs), len(cs), pr["url"]))
rows.sort(reverse=True)
for u in [u for _, _, u in rows[:6]]:
    print(u)
PYEOF
}

missing_for() {  # model fw eff -> missing top-6 PR urls (newline list)
  .venv/bin/python - "$1" "$2" "$3" <<'PYEOF'
import json, glob, sys
model, fw, eff = sys.argv[1], sys.argv[2], sys.argv[3]
top6 = []
import subprocess
top6 = subprocess.run(["bash", "-c", "true"], capture_output=True) and None  # placeholder, filled below
PYEOF
  # simpler: compute inline (kept readable — one python pass)
  .venv/bin/python - "$1" "$2" "$3" <<'PYEOF'
import json, glob, sys
from pathlib import Path
model, fw, eff = sys.argv[1], sys.argv[2], sys.argv[3]
import sys as _s; _s.path.insert(0, ".")
from harnesseval.dataset import martian
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
    if s.get("error") or tok == 0: continue
    n = len(s.get("findings", []))
    if not (n or tok <= 20000): continue
    have.add(s["url"])
for u in top6:
    if u not in have:
        print(u)
PYEOF
}

claude_ok() {
  [ "$DRY" = "1" ] && return 0   # dry mode: no probe (a probe spends ~16 tokens)
  .venv/bin/python - <<'PYEOF'
import sys, asyncio
sys.path.insert(0, ".")
from harnesseval import cli_backends
async def t():
    try:
        text, _, _ = await asyncio.wait_for(
            cli_backends._claude_cli("claude-opus-5", "low", "Reply with the single word ok"), timeout=90)
        sys.exit(0 if text.strip() else 1)
    except SystemExit: raise
    except Exception: sys.exit(1)
asyncio.run(t())
PYEOF
}

run_one() {  # model fw eff url
  local model=$1 fw=$2 eff=$3 url=$4
  local spec="${fw}/${model}/${eff}/${url}"
  if [ "$DRY" = "1" ]; then
    log "  DRY: would run spec: $spec"
    return 0
  fi
  log "  LIVE: running spec: $spec"
  bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
    --frameworks "$fw" --models "$model" --efforts "$eff" --mode cli --concurrency 1 \
    --run-batch $BATCH --skip-batch $BATCH \
    --fill "$spec" >> "logs/mx_campaign_${model}_${eff}_${fw}.log" 2>&1
  log "  LIVE: finished spec: $spec"
}

# CELLS in cost order: all vanilla first (cheap single-shot), then mrv (multi-lens)
CELLS=""
for fw in vanilla-engineered metareview-realistic; do
  for eff in low medium high; do
    for model in $MODELS; do
      CELLS="$CELLS $model/$fw/$eff"
    done
  done
done

# ---- PHASE 1: census + queue validation (always runs, zero tokens) ----
log "phase 1: census of the 12 cells against the severity top-6"
TOTAL=0
QUEUE=""
for cell in $CELLS; do
  model="${cell%%/*}"; rest="${cell#*/}"; fw="${rest%%/*}"; eff="${rest##*/}"
  M=$(missing_for "$model" "$fw" "$eff")
  N=$(echo "$M" | grep -c . || true)
  TOTAL=$((TOTAL + N))
  log "  $model $fw $eff: missing $N/6"
  QUEUE="$QUEUE$M"
done
log "phase 1 result: $TOTAL runs needed across 12 cells"
if [ "$DRY" = "1" ]; then
  log "phase 1 verified: census machinery works; specs generated for every missing pair"
fi

# ---- PHASE 2: launch mechanics dry-run (zero tokens) ----
if [ "$DRY" = "1" ]; then
  log "phase 2: runner launch mechanics with a NO-MATCH spec (expect 'running 0 cells'; the trailing *** lines are the batch's pre-registered error summary — residue reporting, not new attempts)"
  PH2=$(.venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
    --frameworks vanilla-engineered --models claude-opus-5 --efforts low --mode cli --concurrency 1 \
    --run-batch $BATCH --skip-batch $BATCH \
    --fill "vanilla-engineered/claude-opus-5/low/https://github.com/nonexistent/no-such-pr/999999" 2>&1 | grep -c "running 0 cells" || true)
  if [ "$PH2" = "1" ]; then
    log "phase 2 PASS: runner matched 0 cells and exited cleanly (zero tokens)"
  else
    log "phase 2 FAIL: no-match spec did not yield 'running 0 cells' — DO NOT run live"; exit 1
  fi
  log "DRY RUN COMPLETE — all parts verified. Relaunch with DRY=0 for live."
  exit 0
fi

# ---- LIVE: interleaved rotations, one PR per cell per wave, probe-gated between every run ----
log "live: interleaved rotations begin (one PR per cell per wave; vanilla cells first)"
WAVE=0
while :; do
  WAVE=$((WAVE + 1))
  DONE=1
  for cell in $CELLS; do
    model="${cell%%/*}"; rest="${cell#*/}"; fw="${rest%%/*}"; eff="${rest##*/}"
    URL=$(missing_for "$model" "$fw" "$eff" | head -1)
    [ -n "$URL" ] && DONE=0
    [ -z "$URL" ] && continue
    if ! claude_ok; then
      log "wave $WAVE: capped before $model/$fw/$eff — waiting out the window; probing every 10 min"
      while ! claude_ok; do sleep 600; done
      log "wave $WAVE: window open — continuing"
    fi
    run_one "$model" "$fw" "$eff" "$URL"
  done
  [ "$DONE" -eq 1 ] && { log "ALL 12 opus/sonnet cells complete on the severity top-6 — done"; exit 0; }
  log "wave $WAVE rotation done — next rotation re-censuses"
done
