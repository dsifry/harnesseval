"""Report the read-time harnesseval#19 correction over stored run summaries.

Pre-fix, from_codex_cli kept Codex's output_tokens (which already include reasoning) and
total_tokens added reasoning_output_tokens on top. Stored runs/*/summary.json files are
never rewritten (frozen readjudication passes pin their sha256); readers apply
harnesseval.usage.corrected_per_model_usage instead. This tool only measures that
correction: how many legacy Codex summaries it touches and how many tokens it removes.
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from harnesseval.usage import _is_codex, corrected_per_model_usage, needs_codex_correction


def _registered_at(run_dir: Path) -> str | None:
    try:
        manifest = json.loads((run_dir / "manifest.json").read_text())
    except (OSError, json.JSONDecodeError):
        return None
    ts = manifest.get("registered_at") if isinstance(manifest, dict) else None
    return ts if isinstance(ts, str) else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="runs")
    args = ap.parse_args()
    files = with_reasoning = removed = 0
    for p in sorted(glob.glob(f"{args.runs}/*/summary.json")):
        path = Path(p)
        try:
            d = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict):
            continue
        pm = d.get("per_model_usage") or {}
        if not any(isinstance(u, dict) and _is_codex(m, u) for m, u in pm.items()):
            continue
        ts = _registered_at(path.parent)
        if not needs_codex_correction(d, ts):
            continue
        files += 1
        fixed = corrected_per_model_usage(d, ts)
        # tokens moved out of output_tokens == the double count removed from total_tokens
        r = sum(int(u.get("output_tokens") or 0) - fixed[m]["output_tokens"]
                for m, u in pm.items() if isinstance(u, dict) and _is_codex(m, u))
        if r:
            with_reasoning += 1
            removed += r
    print(f"{files} legacy Codex summaries corrected at read time ({with_reasoning} with reasoning); "
          f"{removed:,} double-counted tokens removed from total_tokens")


if __name__ == "__main__":
    main()
