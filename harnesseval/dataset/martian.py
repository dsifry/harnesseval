"""Load Martian CRB golden comments + shipped results at the pinned SHA.

Reads from third_party/code-review-benchmark/ (vendored at SHA 2b092b670f).
See docs/SPEC.md §4 (dataset/martian.py).
"""

from __future__ import annotations

import json
import glob
from pathlib import Path

# Vendored Martian CRB root (gitignored; provenance in third_party/martian_crb_sha.txt)
CRB_ROOT = Path(__file__).resolve().parents[2] / "third_party" / "code-review-benchmark"
OFFLINE = CRB_ROOT / "offline"
GOLDEN_DIR = OFFLINE / "golden_comments"
RESULTS_DIR = OFFLINE / "results"

# Martian's three judge models with stored results
JUDGE_MODELS = {
    "opus": "anthropic_claude-opus-4-5-20251101",
    "sonnet": "anthropic_claude-sonnet-4-5-20250929",
    "gpt": "openai_gpt-5.2",
}
# Map our HARNESS_ judge-name -> the Anthropic model id (Phase A.1 uses Anthropic judges)
ANTHROPIC_JUDGE_IDS = {
    "opus": "claude-opus-4-5-20251101",
    "sonnet": "claude-sonnet-4-5-20250929",
}


def golden_comments_by_url() -> dict[str, list[dict]]:
    """url -> list of golden comment dicts {comment, severity, category}."""
    out: dict[str, list[dict]] = {}
    for f in sorted(GOLDEN_DIR.glob("*.json")):
        for pr in json.load(open(f)):
            out[pr["url"]] = pr.get("comments", [])
    return out


def candidates_by_url(judge_key: str = "opus") -> dict[str, dict[str, list[dict]]]:
    """url -> tool -> list of candidate dicts {text, path, line, source} (extracted issues)."""
    model_dir = RESULTS_DIR / JUDGE_MODELS[judge_key]
    d = json.load(open(model_dir / "candidates.json"))
    return d


def dedup_groups_by_url(judge_key: str = "opus") -> dict[str, dict[str, list[list[int]]]]:
    """url -> tool -> list of dup-group index lists (may be empty)."""
    model_dir = RESULTS_DIR / JUDGE_MODELS[judge_key]
    p = model_dir / "dedup_groups.json"
    if not p.exists():
        return {}
    return json.load(open(p))


def shipped_evaluations(judge_key: str = "opus") -> dict[str, dict[str, dict]]:
    """url -> tool -> evaluation dict (the published decisions we reproduce)."""
    model_dir = RESULTS_DIR / JUDGE_MODELS[judge_key]
    return json.load(open(model_dir / "evaluations.json"))
