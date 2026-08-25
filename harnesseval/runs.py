"""Run registry — the established place for analyzing runs + root evidence over time.

Complements Inspect eval logs (the full evidence: transcripts, per-sample usage, scores)
with a queryable index + per-run manifest so we can compare runs across the
(model × framework × effort × phase) matrix over time.

Design (see docs/SPEC.md):
  runs/registry.jsonl          append-only index, one line per run, queryable with jq/python
  runs/<run-id>/manifest.json  dimensions: phase, model, framework, effort, run#, status, cost, metrics
  runs/<run-id>/summary.json    our aggregate output (calibrate/run_a3 JSON)
  runs/<run-id>/inspect_log.eval  symlink to the Inspect log (full evidence stays there)

Evidence is NOT duplicated: the manifest points to the Inspect log (transcripts, usage,
scores) which is the source of truth. The registry is just the index + dimensions + summary.

Usage:
  from harnesseval.runs import register, query, compare
  rid = register(phase="A.1", model="claude-opus-4-5-20251101", framework="martian-judge",
                 effort="n/a", run_n=1, summary=summary_dict, inspect_log=Path(...))
  runs = query(phase="A.1")                      # all A.1 runs
  runs = query(framework="metareview", model="...")  # all metareview runs on a model
  diff = compare(runs[0], runs[1])              # metrics + cost delta
"""

from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"
REGISTRY = RUNS_DIR / "registry.jsonl"


@dataclass
class RunManifest:
    """The dimensions + summary of one run, queryable over time."""
    run_id: str
    phase: str                 # "A.1" | "A.3" | "B" | "C" | ...
    model: str                # full snapshot id of the model UNDER TEST (or judge for calibration)
    framework: str             # "vanilla-naive" | "metareview" | "martian-judge" | ...
    effort: str                # "n/a" | "low" | "high" | "medium/xhigh" | ...
    run_n: int                 # which repetition within a cell (1..5)
    status: str                # "pass" | "fail" | "error" | "partial"
    cost_usd: float            # estimated $ (0 if unknown)
    tokens_in: int             # total input tokens (0 if unknown)
    tokens_out: int            # total output tokens (0 if unknown)
    wall_s: float              # wall seconds
    metrics: dict              # run-specific (e.g. {"agreement": 0.932, "max_delta": 2})
    inspect_log: str           # path/symlink target to the full-evidence .eval log ("" if none)
    summary_path: str         # path to our aggregate summary.json ("" if none)
    registered_at: str         # ISO timestamp
    run_batch: str = ""        # groups all cells of one matrix run (timestamp slug); query/compare a whole run, rerun its failed cells


def _run_id(phase: str, model: str, framework: str, effort: str, run_n: int) -> str:
    raw = f"{phase}|{model}|{framework}|{effort}|{run_n}|{time.time_ns()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def register(phase: str, model: str, framework: str, effort: str, run_n: int,
             status: str, metrics: dict, *, cost_usd: float = 0.0,
             tokens_in: int = 0, tokens_out: int = 0, wall_s: float = 0.0,
             summary: dict | None = None, inspect_log: Path | None = None,
             run_batch: str = "") -> str:
    """Register a run. Writes manifest + summary (if given) + appends to registry. Returns run_id."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    rid = _run_id(phase, model, framework, effort, run_n)
    run_dir = RUNS_DIR / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    summary_path = ""
    if summary is not None:
        summary_path = str(run_dir / "summary.json")
        Path(summary_path).write_text(json.dumps(summary, indent=2))

    inspect_log_path = ""
    if inspect_log is not None:
        il = Path(inspect_log)
        if il.exists():
            # symlink so evidence lives in one place (the Inspect log dir) but is findable here
            link = run_dir / "inspect_log.eval"
            if not link.exists():
                try:
                    link.symlink_to(il.resolve())
                    inspect_log_path = str(link)
                except (OSError, NotImplementedError):
                    inspect_log_path = str(il.resolve())  # fallback: absolute path

    m = RunManifest(run_id=rid, phase=phase, model=model, framework=framework, effort=effort,
                    run_n=run_n, status=status, cost_usd=cost_usd, tokens_in=tokens_in,
                    tokens_out=tokens_out, wall_s=wall_s, metrics=metrics,
                    inspect_log=inspect_log_path, summary_path=summary_path,
                    registered_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    run_batch=run_batch)
    (run_dir / "manifest.json").write_text(json.dumps(asdict(m), indent=2))
    with REGISTRY.open("a") as f:
        f.write(json.dumps(asdict(m)) + "\n")
    return rid


def query(**filters) -> list[dict]:
    """Return registry entries matching all given dimension filters (exact match)."""
    if not REGISTRY.exists():
        return []
    out = []
    for line in REGISTRY.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if all(e.get(k) == v for k, v in filters.items()):
            out.append(e)
    return out


def compare(run_a: dict, run_b: dict) -> dict:
    """Diff two run manifests (metrics + cost). For over-time comparison."""
    def delta(k): return (run_b.get(k, 0) or 0) - (run_a.get(k, 0) or 0)
    metric_keys = set(run_a.get("metrics", {}).keys()) | set(run_b.get("metrics", {}).keys())
    metric_delta = {k: (run_b.get("metrics", {}).get(k, 0) or 0) - (run_a.get("metrics", {}).get(k, 0) or 0)
                    for k in metric_keys}
    return {"a": run_a["run_id"], "b": run_b["run_id"],
            "cost_usd_delta": delta("cost_usd"), "tokens_in_delta": delta("tokens_in"),
            "tokens_out_delta": delta("tokens_out"), "wall_s_delta": delta("wall_s"),
            "metrics_delta": metric_delta}
