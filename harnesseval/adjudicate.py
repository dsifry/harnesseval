"""Adjudicate unmatched findings — separate real-but-ungold from hallucination.

Martian's gold set is human-curated and incomplete (Martian's own methodology doc flags this):
a framework that finds a REAL bug not in the gold set is scored as a false positive, so more-
thorough frameworks get PUNISHED. This module re-runs the judge on each unmatched candidate
against the diff context: "is this a real issue in this diff?" High-confidence reals are
reclassified as real-but-ungold (excluded from FP; reported as incremental recall). Low-
confidence stay as hallucination (true FP).

See docs/SPEC.md §9.4, docs/PLAN.md B.3.
"""

from __future__ import annotations

import asyncio
import json

from harnesseval import keys
from harnesseval.judge import JudgeResult, _strip_fences

# --- v2 adjudication constants (2026-09-07; supersedes the v1 binary instrument) -------------
# Fixes three measured defects (harnesseval#8, report §3.6):
#   1. diff[:30000] truncation blinded the judge on 15-41% of the largest PRs
#   2. max_tokens=1024 let reasoning models eat the budget -> parse failures counted as
#      hallucinations with no verdict
#   3. binary taxonomy conflated waste (fabricated findings) with real-but-non-bug review
#      content (testing gaps, completeness, scope, architecture)
DIFF_LIMIT = 1_000_000   # adjudicate against the FULL diff
MAX_TOKENS = 4096        # room for reasoning + JSON (v1 used 1024 -> parse failures)
CONF_FLOOR = 0.5         # a bug/important verdict below this is UNRESOLVED, not hidden gold
REAL_THRESHOLD = 0.7     # kept from v1: (bug) findings need confidence >= 0.7 to count as TP-grade

ADJUDICATE_PROMPT = """You are verifying a code review finding against a PR diff. Classify it into exactly one category:

DIFF (unified):
```diff
{diff}
```

FINDING:
{candidate}

Categories:
- "bug": a real, verifiable defect introduced or exposed by this diff (correctness, security,\n  data loss, broken behavior). A reasonable reviewer would agree the diff has this problem.
- "important_non_bug": a real, specific, diff-grounded review issue that is not a defect — e.g.\n  a missing test for newly added nontrivial logic, an incomplete edge-case, a scope/architecture\n  concern created by the change. Must cite specific code in the diff; generic advice\n  ("add more tests") is NOT important.
- "hallucination": the finding is false, misreads the diff, references behavior that does not\n  exist, is a pure style/format nit, or is too vague to act on.

Rules: judge ONLY what the diff shows. If the finding is plausible but you cannot verify it from\nthe diff, assign low confidence (< 0.5) rather than guessing. Respond with ONLY a JSON object:
{{"category": "bug|important_non_bug|hallucination", "reasoning": "brief, grounded in the diff", "confidence": 0.0-1.0}}"""

ADJUDICATE_PROMPT_V1 = """You are verifying whether a code review finding identifies a REAL problem in the diff.

Diff (unified):
```diff
{diff}
```

Proposed finding:
{candidate}

Instructions:
- Determine if this finding describes a real, verifiable problem present in the diff
  (a bug, security issue, correctness problem, or a clear defect the code introduces).
- It is NOT real if it is: a style nit, speculation about code not in the diff, a
  misreading of the diff, a duplicate of something already fine, or vague/general.
- Be strict: "real" means a reasonable reviewer would agree the diff has this problem.

Respond with ONLY a JSON object:
{{"reasoning": "brief explanation grounded in the diff", "is_real": true/false, "confidence": 0.0-1.0}}"""
# ADJUDICATE_PROMPT_V1 is retained ONLY for reproducing pre-2026-09-07 runs (report §3.6).
# It is deprecated: it truncated the diff, and its parse-failure path mis-ruled findings as
# hallucinations. Do not use for new measurements.

ADJUDICATE_SYSTEM = "You are a strict code review verifier. Always respond with valid JSON."


def _parse_adjudication(parsed: dict) -> JudgeResult:
    """Parse a v2 category response (with v1 is_real fallback for old stored formats)."""
    cat = str(parsed.get("category") or "").strip().lower()
    conf = float(parsed.get("confidence", 0.0) or 0.0)
    reasoning = str(parsed.get("reasoning", ""))
    if cat == "hallucination":
        return JudgeResult(match=False, confidence=conf, reasoning=reasoning, raw="", category="hallucination")
    if cat in ("bug", "important_non_bug"):
        if conf < CONF_FLOOR:
            # prompt tells the judge: unverifiable -> low confidence. A low-confidence positive
            # is NOT evidence; count it unresolved rather than hidden gold (readjudicate3 rule).
            return JudgeResult(match=False, confidence=conf, reasoning=reasoning, raw="",
                               category="unresolved")
        # match=True ONLY for bugs; important_non_bug is real-but-not-a-defect
        return JudgeResult(match=(cat == "bug"), confidence=conf, reasoning=reasoning, raw="", category=cat)
    # v1 fallback: is_real boolean
    if "is_real" in parsed:
        real = bool(parsed.get("is_real"))
        if real and conf < CONF_FLOOR:
            # a v1 positive below CONF_FLOOR is uncertain, not fake -> unresolved
            return JudgeResult(match=False, confidence=conf, reasoning=reasoning, raw="",
                               category="unresolved")
        return JudgeResult(match=real, confidence=conf, reasoning=reasoning, raw="",
                           category=("bug" if real else "hallucination"))
    return JudgeResult(match=False, confidence=conf, reasoning=reasoning, raw="", category="unresolved")


async def _adjudicate_one(client, model: str, candidate: str, diff: str, max_chars: int = DIFF_LIMIT) -> JudgeResult:
    prompt = ADJUDICATE_PROMPT.format(diff=diff[:max_chars], candidate=candidate)
    try:
        resp = await asyncio.to_thread(
            client.messages.create, model=model, max_tokens=MAX_TOKENS, system=ADJUDICATE_SYSTEM,
            messages=[{"role": "user", "content": prompt}], extra_body={"temperature": 0.0},
        )
        content = _strip_fences(resp.content[0].text.strip())
        parsed = json.loads(content)
        return _parse_adjudication(parsed)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        # provider/parse errors are UNKNOWN, not fake: unresolved (harnesseval#8).
        # The sync path (run_matrix.py) depends on this never raising.
        return JudgeResult(False, 0.0, f"adjudicate-error: {type(e).__name__}: {str(e)[:120]}", "",
                           error="adjudicate-error", category="unresolved")


async def adjudicate_findings(client, model: str, candidates: list[str], diff: str,
                              concurrency: int = 15) -> list[JudgeResult]:
    """For each unmatched candidate, judge if it's a REAL issue in the diff."""
    sem = asyncio.Semaphore(concurrency)
    async def bounded(c):
        async with sem:
            return await _adjudicate_one(client, model, c, diff)
    return await asyncio.gather(*[bounded(c) for c in candidates])


def reclassify(scored: dict, candidates: list[str], diff: str, model: str = "claude-opus-4-5-20251101",
               real_threshold: float = CONF_FLOOR) -> dict:
    """Reclassify a scored result's false_positives into real-but-ungold vs hallucination (sync top-level)."""
    client = keys.anthropic_client()
    fps = [fp["candidate"] for fp in scored.get("false_positives", [])]
    if not fps:
        return {**scored, "bug_ungold": [], "important_non_bug": [], "true_hallucination": [],
                "unresolved": [], "real_but_ungold": [], "hallucination": [],
                "adjudicated_precision": scored["precision"], "incremental_recall": scored["recall"]}
    results = asyncio.run(adjudicate_findings(client, model, fps, diff))
    return _split_adjudication(scored, fps, results, real_threshold)


async def reclassify_async(scored: dict, candidates: list[str], diff: str, model: str = "claude-opus-4-5-20251101",
                           real_threshold: float = CONF_FLOOR) -> dict:
    """Async variant — safe inside a running event loop (used by run_model_matrix).

    v2 instrument: FULL diff, max_tokens=4096, three-way taxonomy, parse failures -> unresolved.
    """
    from harnesseval.model_router import call_model_json
    from harnesseval.judge import _strip_fences
    fps = [fp["candidate"] for fp in scored.get("false_positives", [])]
    if not fps:
        return {**scored, "bug_ungold": [], "important_non_bug": [], "true_hallucination": [],
                "unresolved": [], "real_but_ungold": [], "hallucination": [],
                "adjudicated_precision": scored["precision"], "incremental_recall": scored["recall"]}
    # adjudicate via the router (cross-family judge). max_tokens MUST be large enough that
    # reasoning models (gpt-5.2 with reasoning_effort) can emit reasoning tokens AND still have
    # room for the JSON content — at 256-1024 the reasoning eats the whole budget -> empty content
    # -> parse error -> everything mis-ruled hallucination (the H4 "all-hallucination" red flag).
    # v2: parse failures become UNRESOLVED, never hallucination.
    sem = asyncio.Semaphore(15)
    async def adj(c):
        async with sem:
            from harnesseval.adjudicate import ADJUDICATE_PROMPT, ADJUDICATE_SYSTEM
            try:
                parsed, _, _, _ = await call_model_json(model, ADJUDICATE_SYSTEM,
                    ADJUDICATE_PROMPT.format(diff=diff[:DIFF_LIMIT], candidate=c), effort="medium", max_tokens=MAX_TOKENS)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # provider/parse errors are UNKNOWN, not fake: unresolved (harnesseval#8)
                return JudgeResult(False, 0.0, f"adjudicate-error: {type(e).__name__}: {str(e)[:120]}", "",
                                   error="adjudicate-error", category="unresolved")
            if not parsed:
                return JudgeResult(False, 0.0, "", "", error="parse", category="unresolved")
            return _parse_adjudication(parsed)
    results = await asyncio.gather(*[adj(c) for c in fps])
    return _split_adjudication(scored, fps, results, real_threshold)


def _split_adjudication(scored, fps, results, real_threshold) -> dict:
    """v2 three-way split: bug_ungold / important_non_bug / true_hallucination / unresolved.

    Legacy keys kept for downstream compat (analysis.py, _build_finding_records):
      real_but_ungold  = bug_ungold
      hallucination    = true_hallucination
    adjudicated_precision is the WASTE precision: TP / (TP + true_hallucinations).
    Unresolved (adjudicator failures / low-confidence positives) are EXCLUDED from the
    precision denominator — they are unknown, not fake (harnesseval#8).

    real_threshold gates the bug bucket: a bug verdict with confidence < real_threshold is
    demoted to unresolved (unconfirmed at TP grade). Default = CONF_FLOOR, matching the
    validated readjudicate3 campaign exactly (report §3.6).
    """
    bug_ungold, important_non_bug, true_hallucination, unresolved = [], [], [], []
    for cand, r in zip(fps, results):
        cat = getattr(r, "category", None) or ("hallucination" if not getattr(r, "match", False) else "bug")
        base = {"candidate": cand, "confidence": getattr(r, "confidence", None),
                "reasoning": getattr(r, "reasoning", "")}
        if r.error:
            unresolved.append({**base, "reason": f"adjudicate-error: {r.error}"})
        elif cat == "bug":
            if (getattr(r, "confidence", None) or 0.0) < real_threshold:
                unresolved.append({**base, "reason": f"bug below real_threshold ({real_threshold})"})
            else:
                bug_ungold.append(base)
        elif cat == "important_non_bug":
            important_non_bug.append(base)
        elif cat == "unresolved":
            unresolved.append(base)
        else:
            true_hallucination.append(base)
    tp = scored["tp"]; fn = scored["fn"]
    adjudicated_precision = tp / (tp + len(true_hallucination)) if (tp + len(true_hallucination)) else 0.0
    incremental_recall = (tp + len(bug_ungold)) / (tp + fn + len(bug_ungold)) if (tp + fn) else 0.0
    return {**scored,
            "bug_ungold": bug_ungold, "important_non_bug": important_non_bug,
            "true_hallucination": true_hallucination, "unresolved": unresolved,
            # legacy compat keys:
            "real_but_ungold": bug_ungold, "hallucination": true_hallucination,
            "adjudicated_precision": adjudicated_precision, "incremental_recall": incremental_recall}
