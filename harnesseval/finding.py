"""Normalized finding schema — the integration layer between framework output and the Martian judge.

Martian judges atomic issue strings. Frameworks emit prose. This dataclass is the bridge:
each framework's output is extracted into a list[Finding], and Finding.issue_text is the unit
the Martian JUDGE_PROMPT compares against golden comment strings.

See docs/SPEC.md §5.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Match a file path with a known source/config extension, optionally followed by :line.
# Appears at start-of-string or after whitespace/punctuation (backticks, parens, brackets).
# Examples matched:
#   packages/app-store/_utils/oauth/parseRefreshTokenResponse.ts:25 — bug
#   app-credential.ts falls back ...
#   .env.example comment says ...
#   `src/foo.py:42` — the issue
_FILE_LINE_RE = re.compile(
    r'(?:^|[\s`(*\[{])'  # boundary (not captured)
    r'('  # capture whole file path
    r'(?:[\w./-]+\.(?:ts|tsx|js|jsx|mjs|cjs|py|rb|go|rs|java|kt|scala|c|cpp|cc|h|hpp|cs|php|swift|m|sh|sql|yml|yaml|json|toml))'  # normal path.ext
    r'|(?:\.env(?:\.(?:example|local|development|production))?|\.gitignore|\.eslintrc|\.prettierrc|\.babelrc)'  # dotfiles
    r')'
    r'(?::(\d+))?'  # optional :line
)


def parse_file_line(issue_text: str) -> tuple[str | None, int | None]:
    """Extract (file, line) from a finding's issue_text, if present.

    Prefers the first match that carries a line number; falls back to the first file
    match with no line. Returns (None, None) if no file path is mentioned. This lets
    the SDLC-loop union dedup pre-cluster by file (O(Σ kᵢ²) per file, not O(N²) global).
    """
    if not issue_text:
        return None, None
    first_file, first_line = None, None
    for m in _FILE_LINE_RE.finditer(issue_text):
        f, ln = m.group(1), m.group(2)
        ln = int(ln) if ln else None
        if first_file is None:
            first_file, first_line = f, ln
        # prefer a match with a line number
        if ln is not None:
            return f, ln
    return first_file, first_line


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

    def __post_init__(self) -> None:
        # auto-populate file/line from issue_text if not explicitly provided
        if self.file is None:
            self.file, self.line = parse_file_line(self.issue_text)


    def to_candidate_dict(self) -> dict:
        """The dict shape the Martian judge expects for a candidate issue."""
        return {"issue_text": self.issue_text, "file": self.file, "line": self.line,
                "severity": self.severity, "category": self.category, "source": self.source}
