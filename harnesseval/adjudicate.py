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

ADJUDICATE_PROMPT = """You are verifying whether a code review finding identifies a REAL problem in the diff.

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

ADJUDICATE_SYSTEM = "You are a strict code review verifier. Always respond with valid JSON."


async def _adjudicate_one(client, model: str, candidate: str, diff: str, max_chars: int = 30000) -> JudgeResult:
    prompt = ADJUDICATE_PROMPT.format(diff=diff[:max_chars], candidate=candidate)
    resp = await asyncio.to_thread(
        client.messages.create, model=model, max_tokens=512, system=ADJUDICATE_SYSTEM,
        messages=[{"role": "user", "content": prompt}], extra_body={"temperature": 0.0},
    )
    content = _strip_fences(resp.content[0].text.strip())
    parsed = json.loads(content)
    return JudgeResult(match=bool(parsed.get("is_real", False)),
                      confidence=float(parsed.get("confidence", 0.0)),
                      reasoning=str(parsed.get("reasoning", "")), raw=content)


async def adjudicate_findings(client, model: str, candidates: list[str], diff: str,
                              concurrency: int = 15) -> list[JudgeResult]:
    """For each unmatched candidate, judge if it's a REAL issue in the diff."""
    sem = asyncio.Semaphore(concurrency)
    async def bounded(c):
        async with sem:
            return await _adjudicate_one(client, model, c, diff)
    return await asyncio.gather(*[bounded(c) for c in candidates])


def reclassify(scored: dict, candidates: list[str], diff: str, model: str = "claude-opus-4-5-20251101",
               real_threshold: float = 0.7) -> dict:
    """Reclassify a scored result's false_positives into real-but-ungold vs hallucination (sync top-level)."""
    client = keys.anthropic_client()
    fps = [fp["candidate"] for fp in scored.get("false_positives", [])]
    if not fps:
        return {**scored, "real_but_ungold": [], "hallucination": [], "adjudicated_precision": scored["precision"],
                "incremental_recall": scored["recall"]}
    results = asyncio.run(adjudicate_findings(client, model, fps, diff))
    return _split_adjudication(scored, fps, results, real_threshold)


async def reclassify_async(scored: dict, candidates: list[str], diff: str, model: str = "claude-opus-4-5-20251101",
                           real_threshold: float = 0.7) -> dict:
    """Async variant — safe inside a running event loop (used by run_model_matrix)."""
    from harnesseval.model_router import call_model_json
    from harnesseval.judge import _strip_fences
    fps = [fp["candidate"] for fp in scored.get("false_positives", [])]
    if not fps:
        return {**scored, "real_but_ungold": [], "hallucination": [], "adjudicated_precision": scored["precision"],
                "incremental_recall": scored["recall"]}
    # adjudicate via the router (cross-family judge)
    sem = asyncio.Semaphore(15)
    async def adj(c):
        async with sem:
            from harnesseval.adjudicate import ADJUDICATE_PROMPT, ADJUDICATE_SYSTEM
            parsed, _, _ = await call_model_json(model, ADJUDICATE_SYSTEM,
                ADJUDICATE_PROMPT.format(diff=diff[:30000], candidate=c), effort="medium", max_tokens=256)
            from harnesseval.judge import JudgeResult
            if not parsed:
                return JudgeResult(False, 0.0, "", "", error="parse")
            return JudgeResult(match=bool(parsed.get("is_real", False)),
                              confidence=float(parsed.get("confidence", 0.0)),
                              reasoning=str(parsed.get("reasoning", "")), raw="")
    results = await asyncio.gather(*[adj(c) for c in fps])
    return _split_adjudication(scored, fps, results, real_threshold)


def _split_adjudication(scored, fps, results, real_threshold) -> dict:
    real_but_ungold, hallucination = [], []
    for cand, r in zip(fps, results):
        if r.error:
            hallucination.append({"candidate": cand, "reason": f"adjudicate-error: {r.error}"})
        elif r.match and r.confidence >= real_threshold:
            real_but_ungold.append({"candidate": cand, "confidence": r.confidence, "reasoning": r.reasoning})
        else:
            hallucination.append({"candidate": cand, "is_real": r.match, "confidence": r.confidence, "reasoning": r.reasoning})
    tp = scored["tp"]; fn = scored["fn"]
    adjudicated_precision = tp / (tp + len(hallucination)) if (tp + len(hallucination)) else 0.0
    incremental_recall = (tp + len(real_but_ungold)) / (tp + fn + len(real_but_ungold)) if (tp + fn + len(real_but_ungold)) else 0.0
    return {**scored, "real_but_ungold": real_but_ungold, "hallucination": hallucination,
            "adjudicated_precision": adjudicated_precision, "incremental_recall": incremental_recall}
