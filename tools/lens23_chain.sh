#!/bin/bash
# Chain: wait for glm-5.3-vision-background to return, then run the two
# rename-equivalence confirmation runs (lens2, lens3) of the rc7 config.
cd /Users/dsifry/Developer/harnesseval
SPECS=$(python3 -c "
import json, glob
nums = sorted({json.load(open(f))['url'].rstrip('/').rsplit('/',1)[-1] for f in glob.glob('analysis/advisory_ceiling/*.json')}, key=lambda x: int(x) if x.isdigit() else 0)
print(','.join(f'metareview-realistic/glm-5.3-vision-background/low/{n}' for n in nums))")

log() { echo "$(date +%H:%M) $*" >> logs/lens_chain_status.log; }
log "chain started; probing vision-background availability"

# 1. wait for the backend (probe every 5 min, up to 24h)
ok=0
for i in $(seq 1 288); do
  if python3 - <<'PY'
import asyncio, sys
sys.path.insert(0, ".")
from harnesseval.model_router import call_model
async def m():
    try:
        await asyncio.wait_for(call_model("glm-5.3-vision-background", system="t", user="OK", effort="low", max_tokens=5), 60)
        return True
    except Exception:
        return False
print("OK" if asyncio.run(m()) else "DOWN")
PY
  then ok=1; log "backend UP after $i probes"; break; fi
  sleep 300
done
[ "$ok" = "0" ] && { log "backend never returned in 24h — aborting chain"; exit 1; }

run_until_real() {
  local batch=$1 log=$2 tries=0
  while :; do
    tries=$((tries+1))
    .venv/bin/python -u -m harnesseval.run_model_matrix --prs 50 --frameworks metareview-realistic \
      --models glm-5.3-vision-background --efforts low --mode api --concurrency 4 \
      --run-batch $batch --fill "$SPECS" >> $log 2>&1 &
    local pid=$!
    log "$batch runner launched (pid $pid, attempt $tries)"
    wait $pid
    # guard: a real run consumes tokens; 0 tokens = backend was down, cells are empty poison
    tok=$(grep -o 'tok$\|[0-9]*tok' $log | grep -o '^[0-9]*' | tail -1)
    if [ "${tok:-0}" -gt 0 ]; then log "$batch produced ${tok} tokens — real run"; return 0; fi
    log "$batch produced 0 tokens (backend down) — cleaning poisoned runs, waiting for backend"
    python3 - <<PY
import json, glob, os, shutil
for f in glob.glob("runs/*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    if s.get("run_batch") == "$batch": shutil.rmtree(os.path.dirname(f))
PY
    until python3 - <<'PY'
import asyncio, sys
sys.path.insert(0, ".")
from harnesseval.model_router import call_model
async def m():
    try:
        await asyncio.wait_for(call_model("glm-5.3-vision-background", system="t", user="OK", effort="low", max_tokens=5), 60)
        return True
    except Exception:
        return False
print("OK" if asyncio.run(m()) else "DOWN")
PY
    do sleep 300; done
    log "backend back — retrying $batch"
    [ $tries -ge 5 ] && { log "$batch failed 5 attempts — aborting"; return 1; }
  done
}

run_until_real 20260909-mrv0112-lens2 logs/mx_mrv0112_lens2.log
nohup tools/watch_adjudicate_lens2.sh > /dev/null 2>&1 &
run_until_real 20260909-mrv0112-lens3 logs/mx_mrv0112_lens3.log
nohup tools/watch_adjudicate_lens3.sh > /dev/null 2>&1 &

# wait for both adjudications to converge
for i in $(seq 1 60); do
  st=$(python3 - <<'PY'
import json, glob, os
out = []
for b in ("20260909-mrv0112-lens2", "20260909-mrv0112-lens3"):
    runs = [f for f in glob.glob("runs/*/summary.json") if json.load(open(f)).get("run_batch") == b]
    adj = [f for f in runs if os.path.exists(f.replace("summary.json", "readjudication3.json"))
           or (json.load(open(f)).get("n_hallucination", 0) + json.load(open(f)).get("n_real_ungold", 0)) == 0]
    out.append(f"{b}:{len(adj)}/{len(runs)}")
print(" ".join(out))
PY
)
  log "adjudication: $st"
  set -- $st
  if [ "${1#*:}" = "${1#*:}" ] && [ "${1#*:}" = "${2#*:}" ]; then log "COMPLETE"; break; fi
  sleep 420
done
log "chain done"
