"""Adapter base: the ReviewerAdapter protocol + PRSample + ReviewRun.

Every framework under test (vanilla, superpowers, compound, metaswarm, metareview) implements
this protocol. A review produces prose; the harness extracts atomic Findings (via
extract.py / Martian's EXTRACT_PROMPT) and judges them (via judge.py) against golden comments.

See docs/SPEC.md §5 (Finding), §6 (effort), §7 (execution modes), docs/PLAN.md B.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from harnesseval.finding import Finding


@dataclass
class PRSample:
    """A PR to review, with its golden comments for scoring."""
    url: str
    pr_title: str
    source_repo: str
    diff: str                       # unified diff
    files: list[dict] = field(default_factory=list)  # per-file {filename, additions, deletions, patch}
    golden_comments: list[dict] = field(default_factory=list)  # {comment, severity, category}


@dataclass
class ReviewRun:
    """The output of one adapter reviewing one PR."""
    framework: str
    model: str
    effort: str
    execution_mode: str             # "api" | "cli"
    raw_output: str                 # the prose review
    findings: list[Finding] = field(default_factory=list)  # extracted atomic issues
    tokens_in: int = 0
    tokens_out: int = 0
    wall_ms: float = 0.0
    error: str | None = None
    per_model_usage: dict = field(default_factory=dict)  # {model: {input,cache_read,cache_creation,output,reasoning,cost_usd,total_tokens}}
    total_cost_usd: float = 0.0


@runtime_checkable
class ReviewerAdapter(Protocol):
    """A framework's review capability. review() -> ReviewRun (prose + extracted findings)."""
    name: str

    def review(self, pr: PRSample, model: str, effort: str, mode: str) -> ReviewRun: ...
