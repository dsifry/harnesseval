#!/usr/bin/env python3
"""Aggregate the key-usage ledger (logs/key_usage.jsonl): per key — calls, models,
wall minutes, tokens in/out/cached. Optional --hours N window (default all)."""
#!/usr/bin/env python3
import json, sys, time, collections
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "logs/key_usage.jsonl"
hours = float(sys.argv[sys.argv.index("--hours") + 1]) if "--hours" in sys.argv else None
cutoff = time.time() - hours * 3600 if hours else 0
KEY_NAMES = {0: "primary (HARNESS_KEYS_FILE)", 1: "extra-1"}
agg = collections.defaultdict(lambda: {"calls": 0, "fails": 0, "secs": 0.0, "in": 0, "out": 0, "cached": 0,
                                       "models": collections.Counter()})
if not path.exists():
    print("no ledger at", path); sys.exit(0)
for line in path.read_text(errors="replace").splitlines():
    try: r = json.loads(line)
    except Exception: continue
    if r.get("ts", 0) < cutoff: continue
    a = agg[r.get("key", "?")]
    a["calls" if r.get("ok") else "fails"] += 1
    a["secs"] += r.get("s", 0) or 0
    a["in"] += r.get("in", 0); a["out"] += r.get("out", 0); a["cached"] += r.get("cached", 0)
    a["models"][r.get("model", "?")] += 1
for k in sorted(agg):
    a = agg[k]
    name = KEY_NAMES.get(k, f"extra-{k}")
    models = ", ".join(f"{m}×{c}" for m, c in a["models"].most_common(4))
    print(f"key[{k}] {name}")
    print(f"  calls {a['calls']} ok / {a['fails']} failed   wall {a['secs']/3600:.2f}h")
    print(f"  tokens in {a['in']:,} (cached {a['cached']:,})  out {a['out']:,}")
    print(f"  models: {models}")
