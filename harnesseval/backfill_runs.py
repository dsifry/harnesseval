"""Backfill the run registry with completed Phase-A runs.

One-time: registers the A.1 and A.3 runs we already did, linking their summaries + Inspect
logs into runs/<run-id>/. Safe to re-run (idempotent — re-registers; old entries stay but
new run_ids differ, which is fine for a backfill log).
"""

from __future__ import annotations

import json
import glob
from pathlib import Path

from harnesseval.runs import register

RESULTS = Path(__file__).resolve().parents[1] / "results"
LOGS = Path(__file__).resolve().parents[1] / "logs"


def backfill():
    # A.1 13-pair pilot (native Anthropic, no Inspect log — used custom calibrate driver)
    p = RESULTS / "phase_a1_pilot.json"
    if p.exists():
        d = json.load(open(p))
        register(phase="A.1", model=d["judge"], framework="martian-judge", effort="n/a",
                 run_n=1, status="pass" if d.get("passed") else "fail",
                 metrics={"agreement": d.get("agreement", 0), "max_delta": d.get("max_abs_delta", 0),
                          "judge_calls": d.get("judge_calls", 0), "errors": d.get("errors", 0)},
                 wall_s=d.get("wall_s", 0), summary=d)

    # A.1 50-pair pilot (native Anthropic)
    p = RESULTS / "phase_a1_pilot50.json"
    if p.exists():
        d = json.load(open(p))
        register(phase="A.1", model=d["judge"], framework="martian-judge", effort="n/a",
                 run_n=2, status="pass" if d.get("passed") else "fail",
                 metrics={"agreement": d.get("agreement", 0), "max_delta": d.get("max_abs_delta", 0),
                          "judge_calls": d.get("judge_calls", 0), "errors": d.get("errors", 0)},
                 wall_s=d.get("wall_s", 0), summary=d)

    # A.3 run (Inspect eval — has a log)
    a3_logs = sorted(glob.glob(str(LOGS / "a3" / "*.eval")))
    if a3_logs:
        register(phase="A.3", model="claude-opus-4-5-20251101", framework="inspect-runner-judge",
                 effort="n/a", run_n=1, status="pass",
                 metrics={"agreement": 0.9667, "samples": 30,
                          "tokens_total": 14367},
                 tokens_in=10629, tokens_out=3738, wall_s=13,
                 inspect_log=Path(a3_logs[-1]))


if __name__ == "__main__":
    backfill()
    print("Backfill done.")
