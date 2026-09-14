#!/bin/bash
# Night cutover: wait for run 5 (the first vision-mrv burn) to launch, kill the finisher
# window (cutting run 5's burn within seconds of launch), then start the flash-only night lane.
cd "$(dirname "$0")/.."
LOG=logs/campaign_glm_top6_finish.log
echo "$(date +%H:%M) cutover armed: watching for run 5" >> logs/campaign_glm_top6_finish.log
while ! grep -q "^..:.. run 5:" "$LOG" 2>/dev/null; do
  sleep 5
done
tmux kill-window -t glmfin 2>/dev/null
pkill -f "with_ceiling.*glm-5.3-vision" 2>/dev/null
pkill -f "run_model_matrix.*glm-5.3-vision" 2>/dev/null
sleep 2
echo "$(date +%H:%M) cutover: run 5 vision-mrv burn cut; flash night lane starting" >> "$LOG"
DRY=0 bash tools/campaign_glm_flash_night.sh
