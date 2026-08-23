"""Fetch + cache PR diffs for the Martian golden-comment dataset.

The Martian offline benchmark ships golden comments + tool reviews but NOT the PR diffs.
Our adapters need the actual diff to produce reviews. This fetches the unified diff for a
golden-comment URL via `gh api` (free, uses the user's gh auth) and caches it locally so
re-runs are free + offline.

See docs/SPEC.md §13.5 (context = diff + changed files).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "pr_diffs"  # repo-root .cache/pr_diffs"

_URL_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def _parse(url: str) -> tuple[str, str, int]:
    m = _URL_RE.search(url)
    if not m:
        raise ValueError(f"not a GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def _cache_path(url: str) -> Path:
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


def fetch_diff(url: str, *, force: bool = False) -> dict:
    """Return {url, org, repo, pr, diff, files} for a golden-comment PR URL. Cached.

    `files` = list of {filename, additions, deletions, patch} from the /files endpoint
    (per-file patches; the unified `diff` is the same content in hunk form). Cached to
    .cache/pr_diffs/<hash>.json so re-runs are free + offline.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cp = _cache_path(url)
    if cp.exists() and not force:
        return json.loads(cp.read_text())

    org, repo, pr = _parse(url)

    # unified diff
    diff = subprocess.run(
        ["gh", "api", f"repos/{org}/{repo}/pulls/{pr}", "-H", "Accept: application/vnd.github.diff"],
        capture_output=True, text=True, check=False,
    )
    if diff.returncode != 0:
        raise RuntimeError(f"gh api diff failed for {url}: {diff.stderr.strip()}")

    # per-file metadata + patches (one call)
    files = subprocess.run(
        ["gh", "api", f"repos/{org}/{repo}/pulls/{pr}/files", "--jq",
         "[.[] | {filename, additions, deletions, patch}]"],
        capture_output=True, text=True, check=False,
    )
    files_json = json.loads(files.stdout) if files.returncode == 0 and files.stdout.strip() else []

    out = {"url": url, "org": org, "repo": repo, "pr": pr,
           "diff": diff.stdout, "diff_bytes": len(diff.stdout), "files": files_json,
           "n_files": len(files_json)}
    cp.write_text(json.dumps(out))
    return out


def fetch_all(urls: list[str], *, force: bool = False, limit: int | None = None) -> dict[str, dict]:
    """Fetch diffs for many URLs (cached). Returns url -> diff dict. Skips failures with a warning."""
    out = {}
    urls = urls[:limit] if limit else urls
    for u in urls:
        try:
            out[u] = fetch_diff(u, force=force)
        except Exception as e:  # noqa: BLE001
            print(f"  WARN: skip {u}: {e}")
    return out
