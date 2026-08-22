"""Normalized finding schema — the integration layer between framework output and the Martian judge.

Martian judges atomic issue strings. Frameworks emit prose. This dataclass is the bridge:
each framework's output is extracted into a list[Finding], and Finding.issue_text is the unit
the Martian JUDGE_PROMPT compares against golden comment strings.

See docs/SPEC.md §5.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finding:
    """A single atomic code-review issue, normalized for the Martian judge."""

    issue_text: str  # atomic, standalone problem description (the unit Martian judges)
    file: str | None = None  # path if extractable
    line: int | None = None
    severity: str | None = None  # low|medium|high|critical if the framework states it
    category: str | None = None  # bug|security|concurrency|... if stated
    source: str = ""  # which framework+lens produced it (for provenance)
    raw: str = ""  # original snippet for audit

    def to_candidate_dict(self) -> dict:
        """The dict shape the Martian judge expects for a candidate issue."""
        return {"issue_text": self.issue_text, "file": self.file, "line": self.line,
                "severity": self.severity, "category": self.category, "source": self.source}
