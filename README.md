# harnesseval

A reproducible evaluation lab that compares **AI code-review frameworks** — vanilla,
Superpowers, Compound Engineering, and metareview — across a **(model × framework × effort)**
matrix, reporting **review quality** (recall, precision, incremental recall, hallucination
rate) **and cost** (tokens, wall-time, real and implied $) together.

The central question is not *"which framework is best"* but *"which gives the best review
quality and finds and fixes the most bugs per unit of cost and triage effort"* — the
**quality-vs-cost Pareto frontier**.

> **Status:** the **384/384 pass-cell matrix is complete** (batch_083, 2026-08-26). N is small
> (6 PRs per cell); treat the numbers as a **directional, reproducible read — not a published
> ranking**. Phase C (50 PRs + confidence intervals) remains the bar before any final claim.
> See [`report.md`](report.md) for the results and [`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md)
> for what's next.

## What this is

We did **not** build a new benchmark or harness from scratch. We reuse three established
open-source projects and write only the novel glue (framework adapters + normalized scoring):

| Reuse (no build) | Role |
|---|---|
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | Matrix runner; native per-sample token/time/$ accounting; eval logs as audit trail |
| [Martian Code Review Bench](https://github.com/withmartian/code-review-benchmark) (offline) | Dataset + grader: real PRs across OSS projects, human-verified golden comments, LLM-as-judge with precision/recall/Fβ |
| [OpenEnv Code Review Arena](https://github.com/Rohan5commit/openenv-code-review-arena) | Deterministic-grader complement (no judge variance; security classes; false-positive control) — not yet in the primary matrix |

| Write (the novel part) | Role |
|---|---|
| Framework adapters | Render each framework's *review capability* against a model, tested as a user actually invokes it (`adapters/`) |
| Normalized finding schema + extractors | Turn each framework's prose output into atomic candidate issues the Martian judge can score (`finding.py`, `extract.py`) |
| Cross-family judge + adjudication | Judge that avoids same-model bias; reclassify unmatched findings into real-but-ungold vs hallucination (`judge.py`, `adjudicate.py`) |
| Cost + Pareto reporting | The recall-vs-cost frontier, the actual decision output (`analysis.py`, `report.py`) |

## What we are evaluating

Four **frameworks under test**, each evaluated by its *review capability*:

| Framework | What it is | Adapter |
|---|---|---|
| **vanilla-engineered** | A carefully-built single prompt: rubric (8 categories) + severity guidance; one model call, no subagents | `adapters/vanilla.py` |
| **metareview 0.8.2** | metareview's task-done review: deterministic Go gates (free) + 8 adversarial LLM lenses dispatched as parallel subagents | `adapters/metareview_realistic.py` |
| **Compound Engineering** | The `ce-code-review` skill: risk-driven persona roster dispatched as parallel subagents + a separate synthesis pass | `adapters/compound_realistic.py` |
| **Superpowers** | The `requesting-code-review` skill: coordinator dispatches one code-reviewer subagent with the `code-reviewer.md` template | `adapters/superpowers_realistic.py` |

Across a **(model × effort)** matrix:

- **Models:** `claude-opus-5`, `claude-sonnet-5` (Claude Code); `gpt-5.6-sol`, `gpt-5.6-terra` (Codex). GLM is a sidebar (not in the primary matrix).
- **Efforts:** `low`, `medium`, `high`, `xhigh` (provider-native reasoning knob).
- **Dataset:** 6 PRs from the Martian bench (cal.com, Discourse), 42 human-verified golden comments.

## Where it comes from

This lab was built to empirically validate the design of **[metareview](https://github.com/dsifry/metareview)**
(an internal review harness). metareview 0.8.2 — the "orchestrator discipline" release — was
ported from fixes validated here, and the metareview repo carries an `0.8.2-eval` branch that
pins the metareview state used in this eval. See the **reproducibility pin** below.

## The headline result (see [`report.md`](report.md) for the full numbers)

The factory frameworks (metareview, Compound) trade **precision for coverage** on *every*
model, not just opus:

- **vanilla-engineered** — highest adjudicated precision (**0.71**), cheapest (**~$0.31/cell**),
  competitive recall (0.48). Model-agnostic; works well on Claude, Codex, and GLM.
- **metareview 0.8.2 / Compound** — incremental recall **0.82–0.83**, surface **~3.5× more
  hidden gold** (real bugs the human reviewers missed), at 7–9× the cost and 4–7× more
  hallucinations to triage (adj. precision 0.27–0.33).
- The **one universal factory win is hidden gold** (metareview 16/16, Compound 15/16 across
  model×effort cells — including 8/8 on Codex gpt): the lenses consistently surface real bugs
  beyond the benchmark, regardless of model. You pay for it in tokens + hallucinations.
- **Cost-efficiency (H1) is refuted:** vanilla dominates the recall-per-dollar frontier; the
  harnesses are 10–40× more expensive for the recall they deliver. The harnesses' value is
  *maximum signal*, not *efficiency*.

The recommended move is to **use them in sequence** (an SDLC loop: discover with a harness →
adjudicate with a precision model → fix → repeat), not pick one for the whole workflow. That
loop is the active research direction — see [`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md).

## Reproducibility pin

The exact code that produced the 384/384 matrix is pinned:

```
harnesseval  @ tag v0.8.2-eval  (= commit 1847f7d)
metareview   @ branch 0.8.2-eval  (= the 0.8.2 release; Go binary 0.8.0 gates + 0.8.2 skill)
```

`git checkout v0.8.2-eval` here and `git checkout 0.8.2-eval` in metareview gives the tested
combo. See [`REPRODUCE.md`](REPRODUCE.md).

## Read these first

- [`report.md`](report.md) — the report: methodology, the 384-cell results, per-framework verdicts, SDLC recommendation, caveats.
- [`INSTALL.md`](INSTALL.md) — set up the lab (Python, CLIs, keys, pinned third-party checkouts, metareview binary).
- [`REPRODUCE.md`](REPRODUCE.md) — replicate the matrix + analyses.
- [`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md) — Phase C, the SDLC-loop validation (vanilla `/goal` vs opinionated metareview with deterministic hard gates), GLM, OpenEnv.
- [`docs/SPEC.md`](docs/SPEC.md) — full design spec.
- [`docs/FRAMEWORK_COMPARISON.md`](docs/FRAMEWORK_COMPARISON.md) — the detailed working analysis (the predecessor to `report.md`).

## Quick start

```bash
uv sync
cp .env.example .env          # API keys live OUTSIDE the repo (see INSTALL.md)
uv run python -m harnesseval.calibrate --check    # validate the lab against published anchors
```

## License

MIT.
