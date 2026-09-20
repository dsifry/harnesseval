#!/usr/bin/env python
"""Print the most recent lunaroute-spy captures: each request paired with its response (or lack of one)."""
import json, sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
rows = []
with open("logs/lunaroute_spy.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
print("--- last %d spy captures ---" % n)
for r in rows[-n:]:
    if r.get("dir") == "req":
        print("  REQ  %s  cap=%s chars=%s" % (r.get("ts"), r.get("cap"), r.get("chars")))
    else:
        print("  RESP %s  status=%s chars=%s dur=%ss finish=%s tok=%s"
              % (r.get("ts"), r.get("status"), r.get("chars"), r.get("dur_s"),
                 r.get("finish"), r.get("completion_tok")))
reqs = [r for r in rows[-n:] if r.get("dir") == "req"]
resps = [r for r in rows[-n:] if r.get("dir") == "resp"]
print("  (in this window: %d reqs / %d resps -> %d unanswered)" % (len(reqs), len(resps), len(reqs) - len(resps)))
