"""Credential loader for API-direct phases (A, C).

CRITICAL SAFETY CONTRACT (docs/SPEC.md §7.1):
  - Keys live OUTSIDE the repo at ~/.config/harnesseval/keys.env (chmod 600).
  - Key names are HARNESS_-prefixed so they can NEVER collide with the env-var names
    the CLIs watch for (ANTHROPIC_API_KEY / OPENAI_API_KEY). An accidental `source`d or
    leaked file therefore cannot override your Claude Code / Codex OAuth.
  - This loader reads the file ONLY when invoked in API mode and passes values DIRECTLY
    to SDK constructors (Anthropic(api_key=...), OpenAI(api_key=...)). It must NOT do
    os.environ['ANTHROPIC_API_KEY'] = ... globally. Phase B (CLI/OAuth) never calls this.
  - Returns a dict; callers pass values explicitly to clients. Nothing leaks to the
    parent shell (this process dies with the harness run).
"""

from __future__ import annotations

import os
from pathlib import Path

KEYS_FILE = Path(os.environ.get("HARNESS_KEYS_FILE", Path.home() / ".config/harnesseval/keys.env"))

# Per-request HTTP timeout (seconds) for the SDK clients. Reasoning models (GLM/Kimi via
# Lunaroute, gpt-5.6-sol) can generate up to 16384 tokens on a long review prompt and legitimately
# take 60-120s; but a stalled gateway (Lunaroute holding connections open under concurrent
# load without responding) must fail fast instead of hanging on the SDK's ~600s default read
# timeout. 180s covers legitimate long completions while ensuring a stalled request errors out
# (and is then eligible for the retry-on-empty/transient-retry logic in model_router).
# Without this, a stalled Lunaroute call blocks asyncio.to_thread indefinitely; asyncio.wait_for
# cancels the coroutine but NOT the blocked thread, so the whole cell hangs unrecoverably.
# See HANDOFF: the GLM api-fallback validation cell hung here (concurrency=5 lens calls).
REQUEST_TIMEOUT_S = float(os.environ.get("HARNESS_REQUEST_TIMEOUT_S", "180"))

# File key name -> the SDK constructor argument / Inspect provider it maps to
KEY_NAMES = (
    "HARNESS_ANTHROPIC_API_KEY",
    "HARNESS_OPENAI_API_KEY",
    "HARNESS_LUNAROUTE_API_KEY",
    "HARNESS_MARTIAN_API_KEY",
    "LUNAROUTE_BASE_URL",
)

_cache: dict[str, str] | None = None


def load_keys(path: Path | None = None) -> dict[str, str]:
    """Read ~/.config/harnesseval/keys.env into a dict. Cached. Never sets os.environ globally."""
    global _cache
    if _cache is not None and path is None:
        return _cache
    p = path or KEYS_FILE
    if not p.exists():
        raise FileNotFoundError(
            f"Keys file not found: {p}. Create it (chmod 600) with HARNESS_ANTHROPIC_API_KEY, "
            "HARNESS_OPENAI_API_KEY, HARNESS_LUNAROUTE_API_KEY, LUNAROUTE_BASE_URL. "
            "See .env.example."
        )
    st = p.stat()
    if st.st_mode & 0o077:
        raise PermissionError(
            f"Keys file {p} is group/world readable (mode {oct(st.st_mode & 0o777)}). "
            "Run: chmod 600 {p}".format(p=p)
        )
    keys: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        if k in KEY_NAMES:
            keys[k] = v.strip()
    missing = [k for k in KEY_NAMES if k not in keys]
    if missing:
        raise KeyError(f"Keys file {p} missing entries: {missing}")
    _cache = keys
    return keys


def anthropic_client():
    """Construct an Anthropic client with the HARNESS_-prefixed key (never via env var)."""
    from anthropic import Anthropic
    return Anthropic(api_key=load_keys()["HARNESS_ANTHROPIC_API_KEY"], timeout=REQUEST_TIMEOUT_S)


def openai_client():
    """Construct an OpenAI client (api.openai.com) with the HARNESS_-prefixed key."""
    from openai import OpenAI
    return OpenAI(api_key=load_keys()["HARNESS_OPENAI_API_KEY"], timeout=REQUEST_TIMEOUT_S)


def lunaroute_client():
    """Construct an OpenAI-compatible client pointed at the Lunaroute gateway (GLM/Kimi)."""
    from openai import OpenAI
    k = load_keys()
    return OpenAI(api_key=k["HARNESS_LUNAROUTE_API_KEY"], base_url=k["LUNAROUTE_BASE_URL"],
                  timeout=REQUEST_TIMEOUT_S)


def martian_client():
    """Construct an OpenAI-compatible client pointed at the Martian gateway (judge cross-check).

    Martian judged their benchmark via this proxy (api.withmartian.com) with model ids like
    'anthropic/claude-opus-4-5-20251101' (creator prefix required). Same Opus 4.5 weights as
    native Anthropic, but the exact path they used — eliminates the path-difference variable.
    See docs/SPEC.md §8 (Anchor 1 cross-check).
    """
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=load_keys()["HARNESS_MARTIAN_API_KEY"],
                       base_url="https://api.withmartian.com/v1",
                       timeout=REQUEST_TIMEOUT_S)


def clear_cache() -> None:
    """Drop the in-memory cache (used by tests)."""
    global _cache
    _cache = None
