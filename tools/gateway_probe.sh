#!/bin/bash
# cheap serving probe: tiny request, 20s cap. Prints "SERVED <ms>ms" or "STALE".
cd "$(dirname "$0")/.."
K1=$(grep HARNESS_LUNAROUTE_API_KEY ~/.config/harnesseval/keys.env | cut -d= -f2)
T0=$(python3 -c 'import time; print(int(time.time()*1000))')
R=$(curl -s -m 20 -X POST https://gw.lunaroute.com/v1/chat/completions \
  -H "Content-Type: application/json" -H "Authorization: Bearer $K1" \
  -d '{"model":"glm-5.3-flash-background","messages":[{"role":"user","content":"reply with the single word ok"}],"max_completion_tokens":512}')
if echo "$R" | grep -q '"choices"'; then
  T1=$(python3 -c 'import time; print(int(time.time()*1000))')
  echo "SERVED $((T1-T0))ms"
else
  echo "STALE"
fi
