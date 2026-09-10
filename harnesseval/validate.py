"""Batch poison validation.

A 'poisoned' cell is one whose summary.json looks complete but carries no real
signal: an error field, or zero tokens (tokens_in + tokens_out == 0). These arise
from backend outages and from deterministic failures like the GLM output-cap 400
('Could not finish the message because max_tokens or model output limit was
reached'). They must NEVER be silently aggregated: analysis scripts that score a
batch must first validate it, or the batch's numbers are quietly understated
(observed live: lens3 scored with two empty cells).

Usage (CLI):
    python -m harnesseval.validate --batch 20260909-mrv0112-lens3
Exit code 1 if any poisoned cell exists, with the exact --fill specs to repair.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys


def scan_batch(batch: str) -> tuple[list[dict], list[dict]]:
    """Return (healthy_cells, poisoned_cells) for a run_batch.

    A cell is one summary.json. Healthy cells may still be low-quality; poisoned
    cells carry an error or zero tokens and must not be scored.
    """
    healthy, poisoned = [], []
    for f in glob.glob("runs/*/summary.json"):
        try:
            s = json.load(open(f))
        except Exception:
            poisoned.append({"file": f, "why": "unparseable summary.json"})
            continue
        if s.get("run_batch") != batch or not s.get("url"):
            continue
        err = s.get("error")
        tok = (s.get("tokens_in") or 0) + (s.get("tokens_out") or 0)
        if err or tok == 0:
            poisoned.append({
                "file": f,
                "url": s.get("url"),
                "framework": s.get("framework"),
                "model": s.get("model"),
                "effort": s.get("effort"),
                "why": f"error={str(err)[:80]}" if err else "zero tokens",
            })
        else:
            healthy.append(s)
    return healthy, poisoned


def validate_batch(batch: str) -> None:
    """Raise ValueError listing any poisoned cell in the batch. Analysis entry
    points should call this before aggregating: silent aggregation of empty
    cells is how understated numbers happen."""
    _, poisoned = scan_batch(batch)
    if poisoned:
        lines = [f"batch {batch}: {len(poisoned)} poisoned cell(s) — refusing to score:"]
        for p in poisoned:
            lines.append(f"  {p['url']} [{p.get('framework')}/{p.get('model')}/{p.get('effort')}] — {p['why']}")
        lines.append("repair with --fill specs: " + ",".join(
            f"{p.get('framework')}/{p.get('model')}/{p.get('effort')}/{(p['url'] or '').rsplit('/', 1)[-1]}"
            for p in poisoned))
        raise ValueError("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description="Validate a run_batch for poisoned cells")
    ap.add_argument("--batch", required=True)
    args = ap.parse_args()
    healthy, poisoned = scan_batch(args.batch)
    print(f"batch {args.batch}: {len(healthy)} healthy, {len(poisoned)} poisoned")
    for p in poisoned:
        print(f"  POISON {p['url']} — {p['why']}")
    if poisoned:
        sys.exit(1)


if __name__ == "__main__":
    main()
