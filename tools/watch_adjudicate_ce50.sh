#!/bin/bash
# Adjudicate new compound-realistic glm-5.3-background low runs (batch 20260909-ce-bg50-lh) as they complete, k=1.
cd /Users/dsifry/Developer/harnesseval
BATCH=20260909-ce-bg50-lh
for i in $(seq 1 60); do
  .venv/bin/python -u readjudicate3.py --batch $BATCH --k 1 >> logs/rj3_ce_bg50_watch.log 2>&1
  st=$(.venv/bin/python - <<'PY'
import json, glob, os
runs = [f.replace("/summary.json","") for f in glob.glob("runs/*/summary.json")
        if (lambda s: s.get("run_batch")=="20260909-ce-bg50-lh" and s.get("framework")=="compound-realistic"
            and s.get("model")=="glm-5.3-background" and s.get("effort")=="low")(json.load(open(f)))]
adj = [d for d in runs if os.path.exists(d + "/readjudication3.json")]
print(f"PASS={len(runs)} ADJ={len(adj)}")
PY
)
  echo "$(date +%H:%M) loop$i: $st" >> logs/watch_ce50_status.log
  set -- $st; pass=$2; adj=$4
  runner=$(pgrep -f "run_model_matrix.*ce-bg50-lh" | wc -l | tr -d ' ')
  if [ "$pass" = "$adj" ] && [ "$pass" -ge 44 ] && [ "$runner" = "0" ]; then
    echo "$(date +%H:%M) COMPLETE: $st" >> logs/watch_ce50_status.log; break
  fi
  sleep 600
done
