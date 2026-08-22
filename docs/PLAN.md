# harnesseval — Execution Plan

> **For a fresh agent:** read `docs/SPEC.md` first. Execute phases in order. Each phase
> has **concrete commands** and a **done-criteria gate**. Do not start the next phase until
> the gate passes (except Phase B which is iterative). **Never** spend API budget in Phase C
> without an explicit user go-ahead after the Phase C cost pilot.

Pin these facts (verify at start; if upstream moved, re-pin and update `SPEC.md`):
- Martian CRB repo: `withmartian/code-review-benchmark` @ **SHA `2b092b670f`** (2026-08-16).
- metareview checkout: `../metareview` (builds: `go build -o bin/metareview ./cmd/metareview` → v0.6.0).
- Inspect: `pip install inspect-ai` + `inspect-evals[swe_bench]`.

---

## Phase 0 — Scaffold the repo

**Goal:** a runnable, dependency-locked Python project with the directory layout from
`SPEC.md §4`.

**Steps:**
1. Create `pyproject.toml` (Python ≥3.11, `uv`-managed). Deps: `inspect-ai`,
   `inspect-evals`, `openai`, `anthropic`, `google-genai`, `pandas`, `matplotlib`,
   `pyyaml`, `tqdm`. Dev: `pytest`, `ruff`.
2. `uv sync` → commit `uv.lock`.
3. Create the package skeleton (`harnesseval/{dataset,adapters,calibrate,judge,score,
   extract,effort,cost,report,adjudicate,cache}.py`) as empty modules with docstrings +
   the `Finding` dataclass from `SPEC.md §5`.
4. Create `.env.example` (template ONLY — no real keys) documenting the **external** key
   file path per `SPEC.md §7.1`. Add `.gitignore` (`results/`, `.env`,
   `third_party/`, `__pycache__/`, `.cache/`, `~/.config/harnesseval/`). **Never** put real
   `HARNESS_ANTHROPIC_API_KEY`/`HARNESS_OPENAI_API_KEY` (or any key) in the repo or the shell profile.
5. Implement `harnesseval/keys.py` loader: reads `~/.config/harnesseval/keys.env` (or macOS
   Keychain) **only when invoked in API mode**, passes keys to SDK constructors directly,
   never exports to the parent shell. Gate on execution mode so Phase B never loads it.
6. Vendor Martian CRB at the pinned SHA under `third_party/code-review-benchmark/`
   (git submodule or shallow clone + recorded SHA). **Do not modify it.**
7. `git init`, initial commit.

**Done when:** `uv sync` succeeds; `python -c "import harnesseval"` succeeds; Martian
checkout `git rev-parse HEAD` == `2b092b670f...`; `keys.py` loads a test key from the
external file without polluting `os.environ` of the parent shell.

> **Phase A prerequisite (user):** create `~/.config/harnesseval/keys.env` (chmod 600) with at
> least `HARNESS_ANTHROPIC_API_KEY` (Phase A needs only the Anthropic key — Martian's headline
> judge is Opus 4.5 + the Sonnet 4.5 sanity band). Add `HARNESS_OPENAI_API_KEY` later for the
> GPT-5.2 judge cross-check + GPT/Codex arms. Names are HARNESS_-prefixed precisely so they
> cannot collide with the env-var names the CLIs watch for. **Do not** export these in any shell.

---

## Phase A — Calibration (API) ⚠️ spends a small API budget (~$10–50)

**Goal:** prove the lab reproduces published results before any framework comparison.

### A.1 — Reproduce Martian's judge/scorer
1. Load `third_party/code-review-benchmark/offline/golden_comments/*.json` and one
   judge-model's `results/<judge>/candidates.json` + `evaluations.json`.
2. Implement `judge.py` with Martian's `JUDGE_PROMPT` **verbatim** (copy from
   `offline/code_review_benchmark/step3_judge_comments.py` at the pinned SHA).
3. Implement `extract.py` with Martian's `EXTRACT_PROMPT` **verbatim**
   (`step2_extract_comments.py`), and `score.py` with their dedup + profiles + Fβ
   (`step2_5_dedup_candidates.py`, `offline/analysis/score_profiles.py`).
4. Re-run our judge on their stored `candidates × golden` pairs, judge =
   `claude-opus-4-5-20251101` (then `claude-sonnet-4-5-20250929`, then `gpt-5.2`).
5. Compare our match-decisions to their shipped `evaluations.json`; compare our per-tool
   TP/FP/FN to `offline/analysis/benchmark_dashboard.json`.

**Gate A.1:** pairwise judge-decision agreement **≥ 95%**; per-tool TP/FP/FN within **±2
absolute** of their published leaderboard for all 3 judges. Commit a Phase-A evidence log
(Inspect eval log or JSON summary) showing the reproduced numbers vs theirs.

### A.2 — Reproduce an Inspect SWE-bench model number
1. `uv run inspect eval inspect_evals/swe_bench_verified --model <m>` for one model with a
   public swebench.com leaderboard resolve rate (pick a cheap model; a subset is fine).
2. Run `python src/inspect_evals/swe_bench/baseline/compare_baseline.py` (asserts their
   scorer == official SWE-bench scoring).

**Gate A.2:** our resolve rate is within a few points of the public leaderboard number;
`compare_baseline.py` asserts pass. Commit evidence.

### A.3 — Adapter sanity band
1. Implement `adapters/vanilla.py` (`vanilla-engineered` only) per `SPEC.md §2` + §6.
2. Run it (API) on the 50 Martian PRs with `claude-sonnet-4-5-20250929`; judge with Opus 4.5.
3. Compare aggregate TP/FP/FN to Martian's published `claude-code` row (TP 76 / FP 88 / FN
   82, Opus/core).

**Gate A.3:** lands within a sensible neighborhood (not >3× off in any direction). Proves
end-to-end adapter→extract→judge plumbing. Commit evidence.

**Phase A done:** A.1 ∧ A.2 ∧ A.3 pass. **Report to user with reproduced numbers before
proceeding to Phase B.**

---

## Phase B — Build + tune adapters (CLI / OAuth subscriptions; minimal API)

**Goal:** implement all FUT adapters + extractors + scoring + reporting; iterate cheaply.
**No published claims from Phase B.** Use Claude Code (`claude -p --output-format json`)
and Codex (`codex exec --json`) for iteration. **Re-auth Claude Code first** (token was
expired as of scaffold time).

### B.1 — Adapter contract
Define `ReviewerAdapter` protocol in `adapters/base.py`:
```python
class ReviewerAdapter(Protocol):
    name: str
    def review(self, pr: PRSample, model: str, effort: Effort, mode: Mode) -> ReviewRun: ...
```
`ReviewRun` = `{findings: list[Finding], raw_output: str, tokens: Usage, wall_ms: float,
execution_mode: str}`. Every adapter must populate `execution_mode` and token usage.

### B.2 — Implement adapters (in order)
1. `vanilla.py` — naive + engineered (engineered already from A.3).
2. `metareview.py` — invoke real `bin/metareview review task-done` for **deterministic
   gates** (free, exact) + run the 5 LLM lenses **API-direct** (Feasibility, Completeness,
   Scope&Alignment, Architecture, Intent Preservation) per `skills/review-artifact/SKILL.md`
   + `rubrics/artifact-review-rubric.md` + `rubrics/task-done-review-rubric.md`; combine.
   **Assert on the produced artifact path** (the CLI is liberal with args — validate inputs).
3. `superpowers.py` — extract the review methodology from the Superpowers review skills
   (clone `obra/superpowers`, find the spec/plan-review skill + rubric at a pinned SHA);
   render as an API methodology prompt. Document the source file/SHA in the adapter.
4. `compound.py` — extract Compound Engineering's review skill methodology
   (`EveryInc/compound-engineering-plugin`, pinned SHA); render as API prompt.
5. (Run #2) `metaswarm.py` — `../metaswarm` adversarial-review-gate methodology.

### B.3 — Effort + cost + report
- `effort.py`: map {low, high} → adapter params (§6).
- `cost.py`: normalize tokens/time; compute `net_review_tokens`; Pareto frontier.
- `report.py`: per-FUT table (recall/precision/F1/F2/hallucination/tokens/time/$ + 95% CI),
  Pareto plot, per-severity recall, failure-mode breakdown.
- `adjudicate.py`: unmatched-finding reclassification (§9.4); human-spot-check 50 random.
- `cache.py`: memoize API responses for re-iteration without re-paying.

### B.4 — Tune
Run the {low, high} × {vanilla-engineered, metareview} cells on ~5 PRs via CLI; inspect
transcripts; tune prompts/effort mapping. Iterate.

**Phase B done:** all run-#1 adapters run end-to-end on 5 PRs producing scored reports; the
Pareto + failure-mode reports render. **No numbers published.**

---

## Phase C — Final run (API) ⚠️ requires explicit user go-ahead after the cost pilot

**Goal:** the true apples-to-apples matrix; the report.

### C.0 — Cost pilot (must precede full run)
Run the full cell set on **5 PRs only** (API), 5 runs each. Extrapolate total cost.
**Present extrapolated $ + token + time to user; get explicit go-ahead.**

### C.1 — Full matrix
- FUTs: vanilla-naive, vanilla-engineered, superpowers, compound, metareview (§14).
- Models: sonnet-4.5, gpt-5.2, gemini-2.5-pro.
- Efforts: low, high.
- Runs per cell: 5.
- Judges: 3 (Opus 4.5, Sonnet 4.5, GPT-5.2); primary judge = different family from under-test.
- Mode: **API only** (no CLI arms in the final comparison).

### C.2 — Score + report
- Score all runs (`score.py`); adjudicate unmatched findings; bootstrap 95% CIs; paired
  per-PR Δ; multiple-comparison adjustment; per-severity recall; failure-mode analysis.
- Produce: the leaderboard table, the **recall-vs-cost Pareto frontier** (the money plot),
  per-FUT failure-mode writeups, judge-variance report.

### C.3 — Commit + contribute
- Commit Phase C Inspect eval logs (audit trail) + derived tables + plots.
- Open PR to Martian adding agentic-framework rows (per `SPEC.md §14.7`).
- Publish `inspect-evals-code-review` package.

**Phase C done:** report + Pareto + logs committed; user has the decision artifact.

---

## Cross-cutting rules

- **Pin everything** (SHAs, prompt versions, model snapshot IDs, inspect version). Never
  use model aliases (`opus`/`sonnet`) — use full IDs.
- **Record `execution_mode` with every measurement.** Never compare API vs CLI numbers
  head-to-head.
- **Every adapter documents its methodology source** (repo + SHA + file) so faithfulness
  is auditable.
- **Reproducibility over speed.** A run that can't be re-run from `uv.lock` + pinned SHAs is
  a bug.
- **Honesty over winning.** If a framework's unmatched findings look like real bugs the gold
  set missed, report them as *incremental recall*, not as wins — and not as FP.
