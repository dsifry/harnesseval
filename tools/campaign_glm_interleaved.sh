#!/bin/bash
# INTERLEAVED GLM fill: breadth-first across all incomplete glm cells.
# Each wave picks the K cells with the most missing runs and advances each by ONE PR
# (single-PR runner, conc 1 per cell, K cells in parallel). Cells stay near lock-step,
# so at any moment every cell has comparable fill — matched-PR comparisons at any cutoff.
# K=3: the vision pool negative-scales past ~3-wide (measured 2026-09-11/12).
# Single manager for ALL glm cells (chain + sweeper glm roles merged here).
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_interleaved.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
BATCH=20260910-mrv0120-manifold
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
export HARNESS_KEY_BUDGETS=12,6
export HARNESS_LUNAROUTE_TIMEOUT_S=2400
export HARNESS_LUNAROUTE_KEY_FILES=~/.config/harnesseval/keys.env.bench:~/.config/harnesseval/keys.env
K=1  # single run at a time (user, 2026-09-12): concentrate pool service on one run so it completes — 3-wide spreads burst capacity and feeds the degenerate marathon mode

PYCLEAN='
import json, glob, os, sys
model, fw = sys.argv[1], sys.argv[2]
bad = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("framework") == fw):
        if len(s.get("findings", [])) == 0 and ((s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)) > 20000:
            bad.add(os.path.abspath(f))
rows, n = [], 0
for line in open("runs/registry.jsonl"):
    try: r = json.loads(line)
    except Exception: rows.append(line.rstrip("\n")); continue
    sp = os.path.abspath(r.get("summary_path") or "")
    if r.get("status") == "pass" and sp in bad:
        r["status"] = "fail"; n += 1
    rows.append(json.dumps(r))
open("runs/registry.jsonl", "w").write("\n".join(rows) + "\n")
print(f"scrubbed {n}")
'

# prints lines: "fw|model|eff|N_MISSING" for incomplete cells, sorted most-missing-first
census() {
  .venv/bin/python - <<'PYEOF'
import json, glob
from pathlib import Path
import sys
sys.path.insert(0, ".")
from harnesseval.dataset import martian
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        rows.append(pr["url"])
urls = set(rows)
cells = [
    ("metareview-realistic", "glm-5.3-vision-background", "medium"),
    # HELD overnight (2026-09-12 23:15): mrv glm vision-high routes lens calls through the claude CLI
    # (futile cc_cli_limit fast-fails while fable owns the account; routing investigation pending).
    # Restore by re-adding: ("metareview-realistic", "glm-5.3-vision-background", "high"),
    ("metareview-realistic", "glm-5.3-flash-background", "high"),
    ("compound-realistic", "glm-5.3-vision-background", "medium"),
    ("compound-realistic", "glm-5.3-vision-background", "high"),
    ("compound-realistic", "glm-5.3-flash-background", "medium"),
    ("compound-realistic", "glm-5.3-flash-background", "high"),
]
out = []
for fw, model, eff in cells:
    have = set()
    for f in glob.glob("runs/*/summary.json"):
        try: s = json.load(open(f))
        except Exception: continue
        if (s.get("run_batch") == "20260910-mrv0120-manifold" and (s.get("framework"), s.get("model"), s.get("effort")) == (fw, model, eff) and s.get("url")):
            tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
            n = len(s.get("findings", []))
            if tok and not s.get("error") and (n or tok <= 20000): have.add(s["url"])
    miss = len(urls) - len(have)
    if miss: out.append((miss, fw, model, eff))
for miss, fw, model, eff in sorted(out, reverse=True):
    print(f"{fw}|{model}|{eff}|{miss}")
PYEOF
}

next_spec() {  # fw model eff -> first missing PR's fill spec
  .venv/bin/python - "$1" "$2" "$3" <<'PYEOF'
import json, glob, sys
from pathlib import Path
fw, model, eff = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, ".")
from harnesseval.dataset import martian
rows = []
for f in glob.glob(str(Path(martian.GOLDEN_DIR) / "*.json")):
    for pr in json.load(open(f)):
        rows.append(pr["url"])
urls = sorted(set(rows))
have = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and (s.get("framework"), s.get("model"), s.get("effort")) == (fw, model, eff) and s.get("url")):
        tok = (s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)
        n = len(s.get("findings", []))
        if tok and not s.get("error") and (n or tok <= 20000): have.add(s["url"])
missing = [u for u in urls if u not in have]
if missing:
    print(f"{fw}/{model}/{eff}/{missing[0]}")  # full URL as substring suffix — bare PR number matched many URLs (11-PR bug)
PYEOF
}

WAVE=0
log "INTERLEAVED GLM fill: breadth-first, K=$K most-behind cells advance one PR per wave"
while true; do
  CENSUS=$(census)
  [ -z "$CENSUS" ] && { log "ALL glm cells 50/50 — interleaved fill complete"; exit 0; }
  WAVE=$((WAVE + 1))
  TOTAL=$(echo "$CENSUS" | awk -F'|' '{s+=$4} END {print s}')
  log "wave $WAVE: $(echo "$CENSUS" | wc -l | tr -d ' ') cells, $TOTAL total missing — advancing top $K:"
  PIDS=""
  # bash 3.2-safe: no mapfile; herestring + while-read keeps runners as direct children (waitable)
  TOP=$(census | head -n "$K")
  while IFS='|' read -r fw model eff miss; do
    [ -z "$fw" ] && continue
    .venv/bin/python -c "$PYCLEAN" "$model" "$fw" >/dev/null 2>&1
    SPEC=$(next_spec "$fw" "$model" "$eff")
    [ -z "$SPEC" ] && continue
    log "  wave $WAVE: $fw/$eff +1 PR ($miss missing)"
    bash tools/with_ceiling.sh 10800 .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 \
      --frameworks "$fw" --models "$model" --efforts "$eff" --mode api --concurrency 1 \
      --run-batch $BATCH --skip-batch $BATCH --fill "$SPEC" \
      >> "logs/mx_campaign_${model}_${eff}.log" 2>&1 &
    PIDS="$PIDS $!"
  done <<< "$TOP"
  # wedge self-heal: kill only if 45 min elapsed SINCE WAVE LAUNCH and the ledger shows nothing since then
  # (the first version measured raw ledger age — after one wedge it burned every fresh wave instantly)
  WAVE_T0=$(date +%s)
  LEDGER_AT_LAUNCH=$(stat -f %m logs/key_usage.jsonl)
  while :; do
    ALIVE=0
    for p in $PIDS; do kill -0 "$p" 2>/dev/null && ALIVE=1; done
    [ "$ALIVE" = "0" ] && break
    ELAPSED=$(( $(date +%s) - WAVE_T0 ))
    NOW_LEDGER=$(stat -f %m logs/key_usage.jsonl)
    if [ "$ELAPSED" -gt 2700 ] && [ "$NOW_LEDGER" -le "$LEDGER_AT_LAUNCH" ]; then
      log "wave $WAVE: no ledger activity since launch (${ELAPSED}s) — killing wedged runners, wave ends"
      for p in $PIDS; do kill "$p" 2>/dev/null; done
      break
    fi
    sleep 60
  done
  for p in $PIDS; do wait "$p" 2>/dev/null; done
  log "wave $WAVE done — breathing 60s before re-census"
  sleep 60
done
