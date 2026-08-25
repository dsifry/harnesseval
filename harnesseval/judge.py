"""Martian judge reproduction (Phase A.1).

Reuses Martian's JUDGE_PROMPT verbatim and their greedy best-confidence scoring, but with
OUR key loader (HARNESS_-prefixed) so we can reproduce their published decisions with the
same judge model (claude-opus-4-5-20251101 etc.) and verify agreement vs their shipped
evaluations.json.

See docs/SPEC.md §8 (Anchor 1), docs/PLAN.md Phase A.1.
"""

from __future__ import annotations

import json
import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

from harnesseval import keys

# Verbatim from offline/code_review_benchmark/step3_judge_comments.py @ SHA 2b092b670f
JUDGE_PROMPT = """You are evaluating AI code review tools.
Determine if the candidate issue matches the golden (expected) comment.

Golden Comment (the issue we're looking for):
{golden_comment}

Candidate Issue (from the tool's review):
{candidate}

Instructions:
- Determine if the candidate identifies the SAME underlying issue as the golden comment
- Accept semantic matches - different wording is fine if it's the same problem
- Focus on whether they point to the same bug, concern, or code issue

Respond with ONLY a JSON object:
{{"reasoning": "brief explanation", "match": true/false, "confidence": 0.0-1.0}}"""

JUDGE_SYSTEM = "You are a precise code review evaluator. Always respond with valid JSON."


def _strip_fences(content: str) -> str:
    """Verbatim fence-stripping from step3."""
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


@dataclass
class JudgeResult:
    match: bool
    confidence: float
    reasoning: str
    raw: str
    error: str | None = None


async def _call_anthropic(client, model: str, prompt: str, max_retries: int = 5) -> JudgeResult:
    """Call the Anthropic judge at temperature 0 (matches Martian's temp=0.0).

    anthropic SDK v1.0.0 dropped `temperature` as a top-level kwarg (reasoning models);
    pass it via extra_body. No `thinking` config => no extended-thinking tokens billed.
    """
    for attempt in range(max_retries):
        try:
            resp = await asyncio.to_thread(
                client.messages.create,
                model=model,
                max_tokens=256,
                system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"temperature": 0.0},
            )
            content = resp.content[0].text.strip()
            content = _strip_fences(content)
            parsed = json.loads(content)
            return JudgeResult(
                match=bool(parsed.get("match", False)),
                confidence=float(parsed.get("confidence", 0.0)),
                reasoning=str(parsed.get("reasoning", "")),
                raw=content,
            )
        except Exception as e:  # noqa: BLE001
            es = str(e).lower()
            is_rate = "429" in es or "rate" in es or "overloaded" in es
            if attempt == max_retries - 1:
                return JudgeResult(False, 0.0, "", "", error=str(e))
            await asyncio.sleep(min(10 * (3 ** attempt), 120) if is_rate else 2 ** attempt)
    return JudgeResult(False, 0.0, "", "", error="max retries exceeded")


async def judge_match(client, model: str, golden_comment: str, candidate: str) -> JudgeResult:
    prompt = JUDGE_PROMPT.format(golden_comment=golden_comment, candidate=candidate)
    return await _call_anthropic(client, model, prompt)


async def judge_match_router(model: str, golden_comment: str, candidate: str, effort: str = "medium") -> JudgeResult:
    """Provider-agnostic judge (Anthropic + OpenAI + Lunaroute via model_router). For the
    calibrated judge trio (claude-opus-4-5 / sonnet-4-5 / gpt-5.2). Judge has NO effort axis
    (effort is a property of the model under test, not the grader) — effort here only sets
    the call mechanics, default medium = no extended thinking."""
    from harnesseval.model_router import call_model_json
    prompt = JUDGE_PROMPT.format(golden_comment=golden_comment, candidate=candidate)
    parsed, tin, tout, _ = await call_model_json(model, JUDGE_SYSTEM, prompt, effort=effort, max_tokens=256)
    if not parsed:
        return JudgeResult(False, 0.0, "", "", error="json parse failed")
    return JudgeResult(match=bool(parsed.get("match", False)),
                      confidence=float(parsed.get("confidence", 0.0)),
                      reasoning=str(parsed.get("reasoning", "")), raw=json.dumps(parsed))


async def judge_pairs_router(model: str, pairs: list[tuple[str, str]],
                             concurrency: int = 15, effort: str = "medium") -> list[JudgeResult]:
    """Provider-agnostic batch judge (Anthropic + OpenAI + Lunaroute)."""
    sem = asyncio.Semaphore(concurrency)
    async def bounded(g, c):
        async with sem:
            return await judge_match_router(model, g, c, effort=effort)
    return await asyncio.gather(*(bounded(g, c) for g, c in pairs))


async def judge_pairs(client, model: str, pairs: list[tuple[str, str]],
                      concurrency: int = 20) -> list[JudgeResult]:
    """Judge many (golden, candidate) pairs with bounded concurrency."""
    sem = asyncio.Semaphore(concurrency)

    async def bounded(g, c):
        async with sem:
            return await judge_match(client, model, g, c)

    return await asyncio.gather(*(bounded(g, c) for g, c in pairs))


# ---- Martian-proxy judge path (cross-check; OpenAI-compat via api.withmartian.com) ----

async def _call_martian(client, model: str, prompt: str, max_retries: int = 3) -> JudgeResult:
    """Call the Martian gateway judge (same model Martian used, their exact API path).

    client is an AsyncOpenAI instance -> await .create() directly (do NOT use asyncio.to_thread,
    which is for sync SDKs like anthropic's and would leave the coroutine un-awaited).

    NOTE: the Martian gateway rate-limits concurrent calls heavily (5 conc calls took ~260s
    with 2 errors). Keep concurrency LOW (2-3) and retries short to avoid huge wall times.
    """
    for attempt in range(max_retries):
        try:
            resp = await client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=[{"role": "system", "content": JUDGE_SYSTEM},
                          {"role": "user", "content": prompt}],
            )
            content = resp.choices[0].message.content.strip()
            content = _strip_fences(content)
            parsed = json.loads(content)
            return JudgeResult(match=bool(parsed.get("match", False)),
                              confidence=float(parsed.get("confidence", 0.0)),
                              reasoning=str(parsed.get("reasoning", "")), raw=content)
        except Exception as e:  # noqa: BLE001
            es = str(e).lower()
            is_rate = "429" in es or "rate" in es or "too many" in es or "timeout" in es
            if attempt == max_retries - 1:
                return JudgeResult(False, 0.0, "", "", error=str(e))
            await asyncio.sleep(min(5 * (attempt + 1), 15) if is_rate else 2 ** attempt)
    return JudgeResult(False, 0.0, "", "", error="max retries exceeded")


async def martian_judge_match(client, model: str, golden_comment: str, candidate: str) -> JudgeResult:
    return await _call_martian(client, model, JUDGE_PROMPT.format(golden_comment=golden_comment, candidate=candidate))


async def martian_judge_pairs(client, model: str, pairs: list[tuple[str, str]],
                             concurrency: int = 20) -> list[JudgeResult]:
    sem = asyncio.Semaphore(concurrency)

    async def bounded(g, c):
        async with sem:
            return await martian_judge_match(client, model, g, c)

    return await asyncio.gather(*(bounded(g, c) for g, c in pairs))


def score_from_matches(golden_comments: list[dict], candidates: list[str],
                       results: list[JudgeResult],
                       dedup_groups: list[list[int]] | None = None) -> dict:
    """Reproduce Martian's greedy best-confidence TP/FP/FN scoring (verbatim logic)."""
    sibling_map: dict[str, set[str]] = {}
    if dedup_groups:
        for group in dedup_groups:
            group_texts = {candidates[i] for i in group if i < len(candidates)}
            for i in group:
                if i < len(candidates):
                    sibling_map[candidates[i]] = group_texts - {candidates[i]}

    golden_matched = {
        gc["comment"]: {"severity": gc.get("severity"), "category": gc.get("category"),
                        "matched": False, "best_confidence": 0.0, "matched_candidate": None,
                        "reasoning": None}
        for gc in golden_comments
    }
    candidate_matched = dict.fromkeys(candidates, False)
    errors = []

    idx = 0
    for gc in golden_comments:
        for candidate in candidates:
            r = results[idx]; idx += 1
            golden = gc["comment"]
            if r.error:
                errors.append({"golden": golden, "candidate": candidate, "error": r.error})
                continue
            if r.match and r.confidence > golden_matched[golden]["best_confidence"]:
                golden_matched[golden].update(matched=True, best_confidence=r.confidence,
                                              matched_candidate=candidate, reasoning=r.reasoning)
                candidate_matched[candidate] = True
                for sibling in sibling_map.get(candidate, set()):
                    candidate_matched[sibling] = True

    tp = [{"golden_comment": g, "severity": v["severity"], "category": v["category"],
           "matched_candidate": v["matched_candidate"], "confidence": v["best_confidence"],
           "reasoning": v["reasoning"]} for g, v in golden_matched.items() if v["matched"]]
    fn = [{"golden_comment": g, "severity": v["severity"], "category": v["category"]}
          for g, v in golden_matched.items() if not v["matched"]]
    fp = [{"candidate": c} for c, m in candidate_matched.items() if not m]
    tp_n, fp_n, fn_n = len(tp), len(fp), len(fn)
    prec = tp_n / (tp_n + fp_n) if (tp_n + fp_n) else 0.0
    rec = tp_n / (tp_n + fn_n) if (tp_n + fn_n) else 0.0
    return {"skipped": False, "true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "errors": errors, "total_candidates": len(candidates), "total_golden": len(golden_comments),
            "tp": tp_n, "fp": fp_n, "fn": fn_n, "errors_count": len(errors),
            "precision": prec, "recall": rec}
