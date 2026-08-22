# harnesseval

A reproducible evaluation lab that compares **AI code-review frameworks** — vanilla,
Superpowers, Compound Engineering, metaswarm, and metareview — across a
**(model × framework × effort)** matrix, reporting **review quality** (recall,
precision, Fβ, hallucination rate) **and cost** (tokens, wall-time, estimated $).

The lab is calibrated against **published, reproducible anchor results** before any
framework comparison is trusted.

## What this is

We are *not* building a new benchmark or a new eval harness from scratch. We reuse
three established open-source projects and write only the novel glue:

| Reuse (no build) | Role |
|---|---|
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | Matrix runner: model × framework × effort → samples; native per-sample token/time/$ accounting; eval logs as audit trail |
| [Martian Code Review Bench](https://github.com/withmartian/code-review-benchmark) (offline) | Dataset + grader: 50 real PRs across 5 OSS projects, 173 human-verified golden comments, LLM-as-judge with precision/recall/Fβ |
| [OpenEnv Code Review Arena](https://github.com/Rohan5commit/openenv-code-review-arena) | Deterministic-grading complement (no judge variance; security classes; explicit false-positive control task) |

| Write (the novel part) | Role |
|---|---|
| Framework adapters | Render each framework's *review methodology* against a model: vanilla (×2), Superpowers, Compound Engineering, metaswarm, metareview (real CLI deterministic gates + API lenses) |
| Normalized finding schema + extractors | Turn each framework's prose output into atomic candidate issues the Martian judge can score |
| Calibration harness | Reproduce Martian's published Aug-2026 leaderboard numbers before trusting our own |
| Cost + Pareto reporting | The recall-vs-cost frontier, the actual decision output |

## Budget phasing (decided)

| Phase | Access | Why |
|---|---|---|
| **A — calibration** | API | Exact, reproducible; validates the lab |
| **B — build + tune** | OAuth subscriptions (Claude Code, Codex) | Budget-burning iteration; free |
| **C — final run** | API | True apples-to-apples, comparable numbers |

Tokens and wall-time are measured in *both* modes. Only `$` is an estimate.

## Read these first

- [`docs/SPEC.md`](docs/SPEC.md) — full specification: design, decisions, the gaps addressed, open decisions.
- [`docs/PLAN.md`](docs/PLAN.md) — phased execution plan with concrete commands and done-criteria for a fresh agent.

## Quick start (after Phase A scaffolding)

```bash
uv sync
cp .env.example .env   # fill in API keys
uv run python -m harnesseval.calibrate --check   # Phase A: validate the lab
```

## Status

Scaffold + spec/plan only. No code yet. See `docs/PLAN.md`.
