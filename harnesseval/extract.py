"""Extract atomic findings from a framework's prose review (Martian's EXTRACT_PROMPT, verbatim).

Every adapter's raw_output goes through this so findings are comparable across frameworks.
See docs/SPEC.md §5, docs/PLAN.md B.3.
"""

from __future__ import annotations

import json
import asyncio

from harnesseval import keys
from harnesseval.finding import Finding

# Verbatim from offline/code_review_benchmark/step2_extract_comments.py @ SHA 2b092b670f
EXTRACT_PROMPT = """You are analyzing an AI code review comment to extract individual issues mentioned.

The comment may discuss multiple distinct problems. Extract each separate issue as a standalone item.

Code Review Comment:
{comment}

Instructions:
- Extract each distinct code issue, bug, or concern mentioned
- Each issue should be a single, specific problem (not a general observation)
- Ignore meta-commentary like "I found 2 issues" - extract the actual issues
- Ignore sign-offs, greetings, or formatting instructions
- If the comment contains no actionable code review issues, return an empty list

Example input:
"Found several problems: 1) The getUserById function doesn't handle null input, which will cause a crash.
2) The cache key uses user.name but should use user.id for uniqueness.
Also, consider adding retry logic for the API call."

Example output:
{{"issues": [
  "getUserById function doesn't handle null input, causing potential crash",
  "Cache key uses user.name instead of user.id, breaking uniqueness",
  "Missing retry logic for the API call"
]}}

Respond with ONLY a JSON object:
{{"issues": ["issue 1", "issue 2", ...]}}"""

EXTRACT_SYSTEM = "You are a code review analyzer. Always respond with valid JSON."


async def _extract_via_anthropic(client, model: str, review_text: str) -> list[str]:
    prompt = EXTRACT_PROMPT.format(comment=review_text)
    resp = await asyncio.to_thread(
        client.messages.create, model=model, max_tokens=1024, system=EXTRACT_SYSTEM,
        messages=[{"role": "user", "content": prompt}], extra_body={"temperature": 0.0},
    )
    content = resp.content[0].text.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    parsed = json.loads(content)
    return list(parsed.get("issues", []))


async def extract_findings_async(client, model: str, review_text: str, source: str = "") -> list[Finding]:
    """Async variant — safe to call from inside a running event loop (used by adapters that
    extract per-lens inside asyncio.gather)."""
    issues = await _extract_via_anthropic(client, model, review_text)
    return [Finding(issue_text=i, source=source, raw=review_text[:500]) for i in issues if i]


def extract_findings(review_text: str, model: str = "claude-opus-4-5-20251101",
                     source: str = "") -> list[Finding]:
    """Extract atomic Findings from a prose review (sync wrapper, top-level use only)."""
    client = keys.anthropic_client()
    issues = asyncio.run(_extract_via_anthropic(client, model, review_text))
    return [Finding(issue_text=i, source=source, raw=review_text[:500]) for i in issues if i]
