#!/bin/bash
# Adjudicate new mrv-0.11.1 bg-low runs as they complete, k=1 for learning turnaround.
cd /Users/dsifry/Developer/harnesseval
BATCH=20260908-mrv0111-bg-lh
for i in $(seq 1 60); do
  .venv/bin/python -u readjudicate3.py --batch $BATCH --k 1 >> logs/rj3_mrv_bg50_watch.log 2>&1
  st=$(.venv/bin/python - <<'PY'
import json, glob, os
runs = [f.replace("/summary.json","") for f in glob.glob("runs/*/summary.json")
        if (lambda s: s.get("run_batch")=="20260908-mrv0111-bg-lh" and s.get("framework")=="metareview-realistic"
            and s.get("model")=="glm-5.3-background" and s.get("effort")=="low")(json.load(open(f)))]
adj = [d for d in runs if os.path.exists(d + "/readjudication3.json")]
runner_alive = os.path.exists("/proc") # placeholder, replaced below
print(f"PASS={len(runs)} ADJ={len(adj)}")
PY
)
  echo "$(date +%H:%M) loop$i: $st" >> logs/watch_mrv50_status.log
  set -- $st; pass=$2; adj=$4
  runner=$(pgrep -f "run_model_matrix.*mrv0111-bg-lh" | wc -l | tr -d ' ')
  if [ "$pass" = "$adj" ] && [ "$pass" -ge 44 ] && [ "$runner" = "0" ]; then
    echo "$(date +%H:%M) COMPLETE: $st" >> logs/watch_mrv50_status.log; break
  fi
  sleep 600
done
