#!/bin/bash
# usage: with_ceiling.sh <seconds> <command...>
# macOS lacks GNU timeout. ADAPTIVE WATCHDOG (2026-09-14, user directive: "reset the hung
# socket timers when tokens are flowing — much longer overall timeout"):
#   - every 5 min, sample the target's socket bytes (nettop) and the key-usage ledger mtime
#   - ANY movement (bytes delta OR ledger write) resets the inactivity timer
#   - kill only after 45 consecutive minutes of TOTAL freeze (no bytes, no ledger writes)
#   - hard cap: 2x the stated ceiling, unconditional
#   - lstart identity guard: never kills a recycled PID
# Motivation: a 3h dumb ceiling killed a live, token-flowing 14740 vision-medium run unbanked.
CEIL=$1; shift
LOG=logs/key_usage.jsonl
"$@" &
PID=$!
START=$(ps -o lstart= -p "$PID" 2>/dev/null | sed 's/^ *//')
[ -z "$START" ] && { wait "$PID"; exit $?; }
LAST_BYTES=$(nettop -p "$PID" -x -l 1 2>/dev/null | awk '{rx+=$4; tx+=$6} END {print rx+tx+0}')
LAST_LEDGER=$(stat -f '%m' "$LOG" 2>/dev/null || echo 0)
BORN=$(date +%s)
HARD=$((BORN + 2 * CEIL))
(
  QUIET=0
  while :; do
    sleep 300
    [ "$(ps -o lstart= -p "$PID" 2>/dev/null | sed 's/^ *//')" != "$START" ] && exit 0
    NOW=$(date +%s)
    [ "$NOW" -ge "$HARD" ] && { kill "$PID" 2>/dev/null; exit 0; }
    CUR=$(nettop -p "$PID" -x -l 1 2>/dev/null | awk '{rx+=$4; tx+=$6} END {print rx+tx+0}')
    CUR_LEDGER=$(stat -f '%m' "$LOG" 2>/dev/null || echo 0)
    if [ "$CUR" = "$LAST_BYTES" ] && [ "$CUR_LEDGER" = "$LAST_LEDGER" ]; then
      QUIET=$((QUIET + 300))
    else
      QUIET=0
    fi
    LAST_BYTES=$CUR; LAST_LEDGER=$CUR_LEDGER
    [ "$QUIET" -ge 2700 ] && { kill "$PID" 2>/dev/null; exit 0; }
  done
) &
WD=$!
wait "$PID"
RC=$?
kill "$WD" 2>/dev/null
pkill -P "$WD" 2>/dev/null
exit $RC
