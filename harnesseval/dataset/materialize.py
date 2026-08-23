"""Materialize a PR diff into a throwaway git repo so metareview's real bin/metareview
can run its deterministic gates on it (the gates read git context from a real repo).

Robust approach (works for any PR, no patch-application fragility):
  1. fetch each changed file's content at the PR BASE sha -> commit as 'base'
  2. fetch each changed file's content at the PR HEAD sha -> commit as 'pr'
  metareview then sees the diff as HEAD~1..HEAD and its sourceFiles()/hasTestChange() gates fire.

Cached per-URL under .cache/mrv_repos/ so re-runs are free.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from harnesseval.dataset.pr_diff import _parse, _cache_path as diff_cache_path, CACHE_DIR as DIFF_CACHE_DIR

REPO_CACHE = Path(__file__).resolve().parents[2] / ".cache" / "mrv_repos"


def _gh_json(args: list[str]) -> dict:
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}


def _fetch_file_content(org: str, repo: str, path: str, ref: str) -> bytes:
    r = subprocess.run(
        ["gh", "api", f"repos/{org}/{repo}/contents/{path}?ref={ref}", "--jq", ".content"],
        capture_output=True, text=True, check=False,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return b""
    import base64
    return base64.b64decode(r.stdout.strip())


def materialize(url: str, *, force: bool = False) -> Path:
    """Materialize a PR into a throwaway git repo with base + pr commits. Returns repo path. Cached."""
    REPO_CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    repo_dir = REPO_CACHE / h
    if repo_dir.exists() and not force:
        return repo_dir

    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.mkdir(parents=True)

    # need the diff's file list + base/head shas
    diff_path = DIFF_CACHE_DIR / f"{h}.json"  # matches pr_diff._cache_path hash
    # pr_diff uses its own sha1 of url; reuse by loading its cache
    from harnesseval.dataset.pr_diff import fetch_diff
    d = fetch_diff(url)
    org, repo, pr = d["org"], d["repo"], d["pr"]
    pr_meta = _gh_json([f"repos/{org}/{repo}/pulls/{pr}"])
    base_sha = pr_meta.get("base", {}).get("sha")
    head_sha = pr_meta.get("head", {}).get("sha")

    # init repo
    env = {**os.environ, "GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x",
           "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x"}
    def git(*a):
        subprocess.run(["git", "-C", str(repo_dir), *a], check=True, env=env,
                       capture_output=True, text=True)
    git("init", "--quiet"); git("config", "user.email", "x@x"); git("config", "user.name", "x")

    files = [f["filename"] for f in d["files"]]
    # base versions
    for f in files:
        c = _fetch_file_content(org, repo, f, base_sha)
        fp = repo_dir / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_bytes(c)
    # remove files that were added in the PR (don't exist at base) -> empty file is fine; git rm if head deletes
    git("add", "-A"); git("commit", "--allow-empty", "-m", "base")
    # head versions
    for f in files:
        c = _fetch_file_content(org, repo, f, head_sha)
        fp = repo_dir / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        if c:
            fp.write_bytes(c)
        else:
            # file deleted in head
            if fp.exists(): fp.unlink()
    git("add", "-A"); git("commit", "--quiet", "--allow-empty", "-m", "pr")
    return repo_dir
