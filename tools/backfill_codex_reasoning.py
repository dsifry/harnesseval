"""Backfill harnesseval#19 into stored run summaries.

Before the fix, from_codex_cli kept Codex's output_tokens (which already include
reasoning) and total_tokens added reasoning_output_tokens on top. This rewrites
each Codex per-model entry in runs/*/summary.json to the fixed shape:
output_tokens -= reasoning (clamped at 0), total_tokens recomputed.

Codex entries are identified as gpt-* models with cost_usd == 0 (OAuth via
`codex exec`); paid OpenAI API entries came through from_openai_api and are
already correct. A summary-level marker makes the rewrite idempotent.

Dry run by default; pass --write to modify files.
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

MARKER = "codex_reasoning_normalized"  # harnesseval#19


def _is_codex(model: str, u: dict) -> bool:
    return model.startswith("gpt") and not u.get("cost_usd")


def normalize(summary: dict) -> int:
    """Rewrite Codex entries in place. Returns reasoning tokens removed from totals."""
    if summary.get(MARKER):
        return 0
    removed = 0
    for model, u in (summary.get("per_model_usage") or {}).items():
        if not isinstance(u, dict) or not _is_codex(model, u):
            continue
        rt = int(u.get("reasoning_output_tokens", 0) or 0)
        u["output_tokens"] = max(0, int(u.get("output_tokens", 0)) - rt)
        new_total = (u["input_tokens"] + u["cache_read_input_tokens"] +
                     u["cache_creation_input_tokens"] + u["output_tokens"] + rt)
        removed += u.get("total_tokens", 0) - new_total
        u["total_tokens"] = new_total
    summary[MARKER] = True
    return removed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    files = changed = removed = 0
    for p in sorted(glob.glob(f"{args.runs}/*/summary.json")):
        path = Path(p)
        try:
            d = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict) or d.get(MARKER):
            continue
        if not any(isinstance(u, dict) and _is_codex(m, u)
                   for m, u in (d.get("per_model_usage") or {}).items()):
            continue
        files += 1
        r = normalize(d)
        if r:
            changed += 1
            removed += r
        if args.write:
            path.write_text(json.dumps(d, indent=2))
    verb = "rewrote" if args.write else "would rewrite"
    print(f"{verb} {files} Codex summaries ({changed} with reasoning); "
          f"{removed:,} double-counted tokens removed from total_tokens")


if __name__ == "__main__":
    main()
