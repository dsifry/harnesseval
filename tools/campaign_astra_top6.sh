#!/bin/bash
# Astra top-6 completion: the 5 remaining cells (compound-realistic x low/med/high + metareview-realistic x med/high
# for gpt-6-astra), targeting ONLY the severity-weight top-6 PRs (the HARNESS ordering — CAMPAIGN_GLOSSARY.md). ~11 runs.
# Mode: cli (codex OAuth — consumes codex credits, zero claude session).
# DRY RUN BY DEFAULT: pass DRY=0 for live. Sequential lane (user lane-discipline), codex probe-gated.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_astra_top6.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
DRY=${DRY:-1}
BATCH=20260910-mrv0120-manifold
MODEL=gpt-6-astra
[ "$DRY" = "0" ] && log "=== LIVE MODE — spends codex credits ===" || log "=== DRY RUN MODE — zero tokens ==="

missing_for() {  # fw eff -> missing top-6 PR urls
  .venv/bin/python - "$1" "$2" <<'PYEOF'
import json, glob, sys
from pathlib import Path
import sys as _s; _s.path.insert(0, ".")
from harnesseval.dataset import martian
fw, eff = sys.argv[1], sys.argv[2]
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
    if (s.get("model"), s.get("framework"), s.get("effort")) != ("gpt-6-astra", fw, eff): continue
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

codex_ok() {
  [ "$DRY" = "1" ] && return 0
  .venv/bin/python - <<'PYEOF'
import sys, asyncio
sys.path.insert(0, ".")
from harnesseval import cli_backends
async def t():
    try:
        text, _, _ = await asyncio.wait_for(
            cli_backends._codex_cli("gpt-5.6-sol", "low", "Reply with the single word ok"), timeout=60)
        sys.exit(0 if text.strip() else 1)
    except SystemExit: raise
    except Exception: sys.exit(1)
asyncio.run(t())
PYEOF
}

# cells: CE first (closest to complete), then mrv — cost order within cells is by PR order
CELLS="compound-realistic/low compound-realistic/medium compound-realistic/high metareview-realistic/medium metareview-realistic/high"

# ---- PHASE 1: census ----
log "phase 1: census of the 5 astra cells against the severity top-6"
TOTAL=0
for cell in $CELLS; do
  fw="${cell%%/*}"; eff="${cell##*/}"
  M=$(missing_for "$fw" "$eff")
  N=$(echo "$M" | grep -c . || true)
  TOTAL=$((TOTAL + N))
  log "  $MODEL $fw $eff: missing $N/6"
  if [ "$DRY" = "1" ]; then echo "$M" | while IFS= read -r u; do [ -n "$u" ] && log "    would run: $fw/$MODEL/$eff/$u"; done; fi
done
log "phase 1 result: $TOTAL runs needed across 5 cells"

# ---- PHASE 2: launch mechanics (zero tokens) ----
if [ "$DRY" = "1" ]; then
  PH2=$(.venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
    --frameworks compound-realistic --models $MODEL --efforts low --mode cli --concurrency 1 \
    --run-batch $BATCH --skip-batch $BATCH \
    --fill "compound-realistic/$MODEL/low/https://github.com/nonexistent/no-such-pr/999999" 2>&1 | grep -c "running 0 cells" || true)
  if [ "$PH2" = "1" ]; then
    log "phase 2 PASS: runner matched 0 cells on the no-match spec (zero tokens)"
  else
    log "phase 2 FAIL — DO NOT run live"; exit 1
  fi
  log "DRY RUN COMPLETE — live plan: sequential single-PR codex invocations, probe-gated, verifier-checked after every run"
  exit 0
fi

# ---- LIVE: sequential, probe-gated ----
RUN=0
while :; do
  DONE=1
  for cell in $CELLS; do
    fw="${cell%%/*}"; eff="${cell##*/}"
    URL=$(missing_for "$fw" "$eff" | head -1)
    [ -n "$URL" ] && DONE=0
    [ -z "$URL" ] && continue
    if ! codex_ok; then
      log "run $RUN: codex capped — waiting out the window; probing every 10 min"
      while ! codex_ok; do sleep 600; done
      log "run $RUN: codex window open — continuing"
    fi
    RUN=$((RUN + 1))
    log "run $RUN: $MODEL $fw $eff +1 PR (sequential codex lane)"
    bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
      --frameworks "$fw" --models $MODEL --efforts "$eff" --mode cli --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH \
      --fill "$fw/$MODEL/$eff/$URL" >> "logs/mx_campaign_astra_${fw}_${eff}.log" 2>&1
    log "run $RUN done — verifier: $(.venv/bin/python tools/verify_hitlist.py 2>/dev/null | head -1)"
  done
  [ "$DONE" -eq 1 ] && { log "ALL 5 astra cells complete on the severity top-6 — done"; exit 0; }
done
