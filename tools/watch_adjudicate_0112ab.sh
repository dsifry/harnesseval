#!/bin/bash
cd /Users/dsifry/Developer/harnesseval
for i in $(seq 1 40); do
  .venv/bin/python -u readjudicate3.py --batch 20260909-mrv0112-ab2 --k 1 >> logs/rj3_0112ab_watch.log 2>&1
  n=$(ls runs/*/readjudication3.json 2>/dev/null | wc -l | tr -d ' ')
  runner=$(ps aux | grep '[r]un_model_matrix.*0112-ab' | grep -c python)
  pass=$(.venv/bin/python -c "
import json, glob
print(sum(1 for f in glob.glob('runs/*/summary.json') if json.load(open(f)).get('run_batch')=='20260909-mrv0112-ab2'))")
  adj=$(.venv/bin/python -c "
import json, glob, os
print(sum(1 for f in glob.glob('runs/*/summary.json')
          if json.load(open(f)).get('run_batch')=='20260909-mrv0112-ab2'
          and (json.load(open(f)).get('n_hallucination',0)+json.load(open(f)).get('n_real_ungold',0))==0
          or os.path.exists(f.replace('summary.json','readjudication3.json')))")
)
  echo "$(date +%H:%M) loop$i: PASS=$pass ADJ=$adj runner=$runner" >> logs/watch_0112ab_status.log
  if [ "$runner" = "0" ] && [ "$pass" = "$adj" ] && [ "$pass" -ge 17 ]; then echo COMPLETE >> logs/watch_0112ab_status.log; break; fi
  sleep 420
done
