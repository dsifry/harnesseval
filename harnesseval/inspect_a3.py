"""Phase A.3 — vanilla-adapter sanity band via Inspect's eval runner.

CALIBRATION-COMPLETING STEP (docs/SPEC.md §8 Anchor 3, docs/PLAN.md A.3):
This validates TWO things at once, on our actual task (Martian judge), which A.1 (custom
driver) and a heavy SWE-bench run each only partially cover:

  1. Our adapter -> extract -> judge -> score pipeline end-to-end (the load-bearing half
     A.1's custom driver didn't exercise through Inspect).
  2. Inspect's native per-sample TOKEN + TIME accounting + eval-log audit trail (the
     infrastructure A.1 skipped and A.2 would have covered on a tangential task).

Design: an Inspect Task where each Sample is a (golden_comment, candidate) pair, the solver
calls the Martian JUDGE_PROMPT via the model-under-judgment, and the scorer compares the
judge's match decision to Martian's shipped decision (the calibration target). We run a
subset of pairs and report:
  - pairwise agreement vs Martian (sanity band)
  - Inspect's reported per-sample tokens + time (proving cost accounting works)
  - the eval-log path (audit trail)

We use the Martian proxy OR native Anthropic; default native Anthropic (Opus 4.5, Martian's
headline judge) since A.1 confirmed it reproduces aggregate. This re-judges a SUBSET (cheap)
to prove the Inspect harness is wired correctly.

Usage:
  uv run inspect eval harnesseval/inspect_a3.py --model anthropic/claude-opus-4-5-20251101 \
      --limit 30 -T judge_key=opus
"""

from __future__ import annotations

import json
import os

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import Score, scorer, mean
from inspect_ai.solver import Generate, TaskState, solver, generate
from inspect_ai.model._chat_message import ChatMessageUser


def _build_pairs(judge_key: str, limit: int) -> list[tuple[str, str, str, str, bool]]:
    """Return [(url, tool, golden, candidate, their_match_decision), ...] for Inspect samples.

    Uses Martian's shipped Opus decisions as the calibration target (their_match_decision =
    whether their judge matched this (golden, candidate)). A subset (limit pairs), spread
    across tools, balanced match/no-match so agreement is meaningful.
    """
    from harnesseval.dataset import martian
    cands = martian.candidates_by_url(judge_key)
    shipped = martian.shipped_evaluations(judge_key)
    goldens = martian.golden_comments_by_url()

    # reconstruct their per-pair decisions: (golden, candidate) -> match iff candidate is
    # that golden's matched_candidate (greedy; see calibrate.their_pair_decisions)
    pairs: list[tuple[str, str, str, str, bool]] = []
    matched_t, matched_f = 0, 0
    for url, tools in cands.items():
        for tool, cl in tools.items():
            ev = shipped.get(url, {}).get(tool)
            if not ev:
                continue
            tp_pairs = {(tp.get("golden_comment"), tp.get("matched_candidate"))
                        for tp in ev.get("true_positives", [])}
            g = goldens.get(url, [])
            for gi in g:
                for c in cl:
                    t = c.get("text")
                    if not t:
                        continue
                    is_match = (gi["comment"], t) in tp_pairs
                    pairs.append((url, tool, gi["comment"], t, is_match))
                    if is_match: matched_t += 1
                    else: matched_f += 1
    # balance: roughly equal match/no-match, spread tools
    pos = [p for p in pairs if p[4]]
    neg = [p for p in pairs if not p[4]]
    # interleave for a representative subset
    chosen: list[tuple[str, str, str, str, bool]] = []
    i = j = 0
    while len(chosen) < limit and (i < len(pos) or j < len(neg)):
        if i < len(pos):
            chosen.append(pos[i]); i += 1
        if j < len(neg) and len(chosen) < limit:
            chosen.append(neg[j]); j += 1
    return chosen


@solver
def martian_judge_solver(judge_model_for_prompt: str = "anthropic/claude-opus-4-5-20251101"):
    """Solver: ask the model the Martian JUDGE_PROMPT and parse the JSON decision.

    The model arg here is only for clarity (Inspect passes --model to the solver via state).
    We render JUDGE_PROMPT from the sample metadata and call generate().
    """
    from harnesseval.judge import JUDGE_PROMPT

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata or {}
        prompt = JUDGE_PROMPT.format(golden_comment=meta["golden"], candidate=meta["candidate"])
        state.messages = [ChatMessageUser(content=prompt)]
        state = await generate(state)
        return state
    return solve


@scorer(metrics=[mean()])
def martian_agreement_scorer():
    """Scorer: parse the model's JSON {match, confidence} and compare to their_match_decision.

    Returns 1.0 if our match == theirs (agreement), 0.0 if disagree. mean() -> agreement rate.
    Also records per-sample token/time via Inspect's native accounting (in the eval log).
    """
    async def score(state: TaskState, target):
        meta = state.metadata or {}
        theirs = meta["their_match"]
        content = state.output.completion.strip()
        # strip fences (martian step3 style)
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        try:
            parsed = json.loads(content)
            ours = bool(parsed.get("match", False))
            conf = float(parsed.get("confidence", 0.0))
        except Exception:
            ours = False; conf = 0.0
        agree = 1.0 if ours == theirs else 0.0
        return Score(value=agree, explanation=f"ours={ours} theirs={theirs} conf={conf} agree={bool(agree)}",
                     metadata={"ours": ours, "theirs": theirs, "confidence": conf})
    return score


@task
def a3_judge_agreement(judge_key: str = "opus", limit: int = 30):
    """Inspect Task: re-judge a subset of (golden, candidate) pairs and measure agreement
    vs Martian's shipped decisions. Exercises Inspect's runner + cost accounting on our task.
    """
    pairs = _build_pairs(judge_key, limit)
    samples = [Sample(
        id=f"{i}",
        input=p[3][:80],  # candidate snippet (for log readability)
        target=str(p[4]),
        metadata={"url": p[0], "tool": p[1], "golden": p[2], "candidate": p[3], "their_match": p[4]},
    ) for i, p in enumerate(pairs)]
    return Task(
        dataset=MemoryDataset(samples),
        solver=[martian_judge_solver()],
        scorer=[martian_agreement_scorer()],
    )
