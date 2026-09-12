#!/bin/bash
# usage: with_ceiling.sh <seconds> <command...>
# macOS lacks GNU timeout: run the command, kill it after N seconds (wedge watchdog).
CEIL=$1; shift
"$@" &
PID=$!
( sleep "$CEIL"; kill "$PID" 2>/dev/null ) &
WD=$!
wait "$PID"
RC=$?
kill "$WD" 2>/dev/null
exit $RC
