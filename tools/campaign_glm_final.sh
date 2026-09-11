#!/bin/bash
# GLM legs — SINGLE sequential chain (the lesson of 2026-09-10: multiple concurrent
# GLM runners thrash the account's concurrency limit and starve every cell).
# Health-gated: waits for 2/3 clean probes before starting, so it self-launches when
# the backend stabilizes and stays paused while it's down.
set -u
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_final.log
log() { echo "$(date +%H:%M) $*" | tee -a "$LOG"; }
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env.bench
export HARNESS_KEY_BUDGETS=12,6
export HARNESS_LUNAROUTE_KEY_FILES=~/.config/harnesseval/keys.env.bench:~/.config/harnesseval/keys.env
BATCH=20260910-mrv0120-manifold

probe_up() {
  .venv/bin/python - <<'PYEOF'
import sys, os, asyncio
os.environ["HARNESS_KEYS_FILE"] = os.path.expanduser("~/.config/harnesseval/keys.env.bench")
sys.path.insert(0, ".")
from harnesseval import model_router
async def probe():
    ups = 0
    for i in (1, 2, 3):
        try:
            v, _, _, _ = await asyncio.wait_for(model_router.call_model_json(
                "glm-5.3-flash-background", "JSON only", 'Reply {"ok":true}', effort="low", max_tokens=32), timeout=90)
            if v.get("ok"): ups += 1
        except Exception:
            pass
    print(ups)
asyncio.run(probe())
PYEOF
}

log "health gate: waiting for 2/3 clean probes"
for i in $(seq 1 200); do
  UPS=$(probe_up)
  log "probe round $i: $UPS/3 clean"
  if [ "$UPS" -ge 2 ]; then log "backend stable — starting GLM legs"; break; fi
  sleep 300
done

PYCLEAN='
import json, glob, os, sys
model, eff = sys.argv[1], sys.argv[2]
bad = set()
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if (s.get("run_batch") == "20260910-mrv0120-manifold" and s.get("model") == model and s.get("effort") == eff):
        if len(s.get("findings", [])) == 0 and ((s.get("tokens_in", 0) or 0) + (s.get("tokens_out", 0) or 0)) > 0:
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
print(f"scrubbed {n} laundered registry entries")
'
missing_specs() {
  .venv/bin/python - "$1" "$2" <<'PYEOF'
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
        have[s.get("url")] = have.get(s.get("url"), False) or (not bad)
missing = sorted(u for u, ok in have.items() if not ok)
print(",".join(f"metareview-realistic/{model}/{eff}/{u.rsplit('/', 1)[-1]}" for u in missing), end="")
PYEOF
}

run_cell() {  # model effort
  local model=$1 eff=$2
  for try in 1 2 3 4 5; do
    log "cell $model/$eff attempt $try"
    .venv/bin/python -c "$PYCLEAN" "$model" "$eff"
    # conc 12 = full bench-key budget; overflow spills to key1's campaign share (HARNESS_KEY_BUDGETS)
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models $model --efforts $eff --mode api --concurrency 12 \
      --run-batch $BATCH --skip-batch $BATCH --fill "$(missing_specs "$model" "$eff")" >> logs/mx_campaign_${model}_${eff}.log 2>&1
    local LEFT; LEFT=$(missing_specs "$model" "$eff" | tr ',' '\n' | grep -c . || true)
    if [ -z "$LEFT" ] || [ "$LEFT" = "0" ]; then
      log "cell $model/$eff CLEAN (50/50 healthy)"; return 0
    fi
    log "cell $model/$eff missing $LEFT — next attempt refills"
  done
  log "cell $model/$eff FAILED after 5 attempts — missing: $(missing_specs "$model" "$eff" | tr ',' '\n' | wc -l | tr -d ' ')"
  return 1
}

# flash-high moved LAST (2026-09-11): the flash pool is wedged (1h+ hangs, 429s)
# while vision serves fine — don't let one wedged cell block the vision refills
run_cell glm-5.3-vision-background medium
run_cell glm-5.3-vision-background high
run_cell glm-5.3-flash-background high
log "GLM legs complete"
