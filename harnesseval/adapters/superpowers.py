"""Superpowers adapter — API-direct methodology (the secondary column, SPEC §7).

Superpowers (`obra/superpowers`, pinned SHA in third_party/superpowers_sha.txt) is an external
plugin whose review methodology is the `requesting-code-review` skill: a user dispatches a
`general-purpose` code-reviewer SUBAGENT (skills/requesting-code-review/code-reviewer.md) that
reviews a git range against its plan/requirements + code quality + architecture + testing +
production readiness, and returns Strengths + Issues (Critical/Important/Minor) + Assessment.

This adapter extracts that methodology to a bare API prompt (the "methodology isolated"
academic column per SPEC §7). It does NOT invoke the real plugin plumbing (tool dispatch,
subagent spawn) — that's the realistic adapter (`superpowers_realistic.py`). Both columns are
recorded; api vs cli are never compared head-to-head.

The methodology source (auditable):
  - skills/requesting-code-review/SKILL.md (the skill)
  - skills/requesting-code-review/code-reviewer.md (the reviewer prompt template)
  - skills/subagent-driven-development/task-reviewer-prompt.md (spec-compliance + quality gate)
  at repo SHA b36e0829c6d0140e93cfef2ca599b1b07d4a7797.

Output is prose; the harness extracts atomic Findings via extract.py (Martian EXTRACT_PROMPT)
so findings are comparable across all frameworks.
"""

from __future__ import annotations

import asyncio
import time

from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.finding import Finding

# The Superpowers code-reviewer methodology, extracted from
# skills/requesting-code-review/code-reviewer.md @ SHA b36e0829. This IS the prompt a
# `general-purpose` subagent receives in a real Superpowers session — we render it API-direct
# (no subagent spawn, no git range, just the diff inlined) so the methodology is isolated from
# the plugin plumbing. The reviewer is told it does NOT dispatch subagents (the skill's rule:
# "a reviewer you spawn duplicates one of them at full cost, and its verdict counts for nothing").
METHODOLOGY_PROMPT = """You are a Senior Code Reviewer with expertise in software architecture, \
design patterns, and best practices. Your job is to review completed work against its plan or \
requirements and identify issues before they cascade.

## What Was Implemented

A pull request: {pr_title}

## Requirements / Plan

The PR title above states the intent. Review the change against that intent and against general \
production-readiness standards.

## Diff Under Review

```diff
{diff}
```

## Read-Only Review

Your review is read-only. Do not mutate anything. Inspect the diff above.

## You Do Not Dispatch Subagents

Do all of this review yourself. Never spawn a subagent to review part of the diff, and never \
spawn another reviewer for a second opinion. This process already provides every review seat the \
work gets; a reviewer you spawn duplicates one of them at full cost, and its verdict counts for \
nothing. If the diff feels too large for one pass, review it in passes yourself and say so in your \
report.

## What to Check

**Plan alignment:**
- Does the implementation match the stated intent / requirements?
- Are deviations justified improvements, or problematic departures?
- Is all intended functionality present?

**Code quality:**
- Clean separation of concerns?
- Proper error handling?
- Type safety where applicable?
- DRY without premature abstraction?
- Edge cases handled?

**Architecture:**
- Sound design decisions?
- Reasonable scalability and performance?
- Security concerns?
- Integrates cleanly with surrounding code?

**Testing:**
- Tests verify real behavior, not mocks?
- Edge cases covered?
- Integration tests where they matter?
- All tests passing?

**Production readiness:**
- Migration strategy if schema changed?
- Backward compatibility considered?
- Documentation complete?
- No obvious bugs?

## Calibration

Categorize issues by actual severity. Not everything is Critical. Acknowledge what was done \
well before listing issues — accurate praise helps the implementer trust the rest of the feedback.

If you find significant deviations from the intent, flag them specifically. If you find issues \
with the intent itself rather than the implementation, say so.

## Output Format

### Strengths
[What's well done? Be specific.]

### Issues

#### Critical (Must Fix)
[Bugs, security issues, data loss risks, broken functionality]

#### Important (Should Fix)
[Architecture problems, missing features, poor error handling, test gaps]

#### Minor (Nice to Have)
[Code style, optimization opportunities, documentation polish]

For each issue:
- File:line reference (from the diff)
- What's wrong
- Why it matters
- How to fix (if not obvious)

### Assessment

**Ready to merge?** [Yes | No | With fixes]
**Reasoning:** [1-2 sentence technical assessment]

## Critical Rules

DO: categorize by actual severity; be specific (file:line, not vague); explain WHY each issue \
matters; acknowledge strengths; give a clear verdict.
DON'T: say "looks good" without checking; mark nitpicks as Critical; give feedback on code you \
didn't actually read; be vague; avoid giving a clear verdict."""


def _truncate(diff: str, max_chars: int = 60000) -> str:
    """Keep the diff within prompt limits (Phase B context is diff-only per SPEC §6.2)."""
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n[... diff truncated: {len(diff) - max_chars} more chars ...]"


async def _review_api(pr: PRSample, model: str, effort: str, execution_mode: str) -> tuple[str, int, int, dict]:
    """Run the Superpowers code-reviewer methodology via model_router (api or cli OAuth)."""
    from harnesseval.model_router import call_model
    prompt = METHODOLOGY_PROMPT.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    return await call_model(model, system="You are an expert code reviewer using the Superpowers "
                                "requesting-code-review methodology.",
                            user=prompt, effort=effort, max_tokens=2048, execution_mode=execution_mode)


async def review_async(pr: PRSample, model: str, effort: str = "medium",
                       mode: str = "api") -> ReviewRun:
    """Async core — safe inside a running event loop.

    mode: 'api' (paid, clean, methodology-only) | 'cli' (OAuth, free, realistic host-scaffolding
    tax). Records execution_mode. For the real-plugin realistic column use
    superpowers_realistic.review_realistic_async (drives a real host session with the plugin).
    """
    name = "superpowers"
    t0 = time.time()
    try:
        out, tin, tout, pmu = await _review_api(pr, model, effort, execution_mode=mode)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=str(e))
    from harnesseval.model_router import call_model_json
    from harnesseval.extract import EXTRACT_PROMPT, EXTRACT_SYSTEM
    from harnesseval.usage import merge, grand_total
    parsed, pi, po, pmu_ext = await call_model_json(model, EXTRACT_SYSTEM, EXTRACT_PROMPT.format(comment=out),
                                           effort=effort, max_tokens=1024, execution_mode=mode)
    findings = [Finding(issue_text=i, source=name, raw=out[:500]) for i in parsed.get("issues", []) if i]
    per_model = merge(dict(pmu), pmu_ext)
    gt = grand_total(per_model)
    return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                     raw_output=out, findings=findings, tokens_in=tin + pi, tokens_out=tout + po,
                     wall_ms=(time.time() - t0) * 1000, per_model_usage=per_model,
                     total_cost_usd=gt["total_cost_usd"])


def review(pr: PRSample, model: str, effort: str = "medium", mode: str = "api") -> ReviewRun:
    """Sync wrapper (top-level use). mode: 'api' | 'cli'."""
    return asyncio.run(review_async(pr, model, effort, mode))
