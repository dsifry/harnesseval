#!/bin/bash
cd /Users/dsifry/Developer/harnesseval
for i in $(seq 1 40); do
  .venv/bin/python -u readjudicate3.py --batch 20260909-mrv0112-ab2 --k 1 >> logs/rj3_0112ab2_watch.log 2>&1
  runner=$(ps aux | grep '[r]un_model_matrix.*0112-ab2' | grep -c python)
  st=$(.venv/bin/python -c "
import json, glob, os
runs = [f for f in glob.glob('runs/*/summary.json') if json.load(open(f)).get('run_batch')=='20260909-mrv0112-ab2']
adj = [f for f in runs if os.path.exists(f.replace('summary.json','readjudication3.json'))
       or (json.load(open(f)).get('n_hallucination',0)+json.load(open(f)).get('n_real_ungold',0))==0]
print(f'PASS={len(runs)} ADJ={len(adj)}')")
  echo "$(date +%H:%M) loop$i: $st" >> logs/watch_0112ab2_status.log
  set -- $st; pass=$2; adj=$4
  if [ "$runner" = "0" ] && [ "$pass" = "$adj" ] && [ "$pass" -ge 17 ]; then echo COMPLETE >> logs/watch_0112ab2_status.log; break; fi
  sleep 420
done
