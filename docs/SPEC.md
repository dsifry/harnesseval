# harnesseval — Specification

> **Audience:** a coding agent with a *fresh* context executing `docs/PLAN.md`. This
> document is self-contained: it carries the facts a new agent needs without re-deriving
> them. If anything here conflicts with the live upstream repos, **upstream wins** —
> update this doc and pin the new SHA.

## 1. Purpose

Compare AI code-review **frameworks** (not models, not tools) on a **model × framework ×
effort** matrix, reporting **review quality** and **cost** together, on a validated lab.

The central question is not *"which framework is best"* but *"which framework gives the
best review quality per unit of token/time cost"* — i.e. the **recall-vs-cost Pareto
frontier**.

## 2. What we are evaluating (scope)

**Frameworks under test (FUTs)**, each evaluated by its *review capability specifically*:

| FUT | Review capability under test | Adapter mechanism |
|---|---|---|
| `vanilla-naive` | A bare "review this diff for bugs" prompt | API: single prompt |
| `vanilla-engineered` | A carefully-built single prompt containing the rubric + severity guidance | API: single prompt |
| `superpowers` | Superpowers plan/spec-review methodology (extracted from the review skills) | API: methodology prompt; (optional CLI-faithful via the plugin) |
| `compound` | Compound Engineering review skill methodology | API: methodology prompt; (optional CLI-faithful) |
| `metaswarm` | metaswarm adversarial-review-gate | API: methodology prompt; (optional CLI-faithful) |
| `metareview` | metareview task-done review: **deterministic gates (real `bin/metareview`, free) + LLM lenses (API)** | CLI (deterministic) + API (lenses) |

**In scope:** each framework's review of a static PR diff, producing structured findings.

**Out of scope (future axes):** agentic repo-browsing vs diff-only; multi-turn fix loops;
the full Superpowers/Compound lifecycle (brainstorm→spec→plan→TDD); metaswarm
orchestration. We isolate the *review* skill of each.

**metareview mode:** **standalone**, not `metaswarm-extension` (cleaner; no Beads/lifecycle).
metareview's deterministic Go gates (eval/TODO/missing-test/duplicate-path) *do* fire on
Martian PR diffs and are part of what metareview catches — the adapter combines free
deterministic findings with API lens findings.

## 3. Reuse decisions (why not build our own)

- **Inspect AI** (`pip install inspect-ai`) — harness backbone. Model-agnostic; native
  per-sample **token + wall-time + cost**; eval logs are a full audit trail; ships SWE-bench,
  cybench, cyberseceval. The matrix is an Inspect `Task` per (framework, effort) with the
  model passed at eval time.
- **Martian Code Review Bench (offline)** — primary dataset + grader. 50 PRs × 5 real OSS
  projects (Sentry/Py, Grafana/Go, Cal.com/TS, Discourse/Ruby, Keycloak/Java), **173
  human-verified golden comments** with severity (Low/Med/High/Critical) + category (bug,
  security, concurrency, data, api, perf, test_gap, doc_defect, style, speculative). Ships
  the judge prompt, the candidate-extraction prompt, scoring profiles (strict=139 /
  core=158 / all=173 golden issues), and Fβ weighting. Pin **SHA `2b092b670f`** (2026-08-16).
- **OpenEnv Code Review Arena** — deterministic-grader complement. SQLi, path traversal,
  SSRF, broken access control, JWT, race conditions, XSS, plus a clean-refactor task that
  explicitly measures false positives. Use to cross-check Martian's LLM judge.

## 4. Architecture

```
harnesseval/
  pyproject.toml              # inspect-ai, openai, anthropic, google-genai, uv.lock
  .env.example               # API keys (never committed)
  docs/
    SPEC.md  PLAN.md
  harnesseval/
    calibrate.py              # Phase A: reproduce Martian + Inspect SWE-bench anchors
    dataset/
      martian.py              # load golden_comments + benchmark_data at pinned SHA
      openenv.py              # load OpenEnv tasks
    adapters/
      base.py                 # ReviewerAdapter protocol + NormalizedFinding schema
      vanilla.py              # naive + engineered single-prompt
      superpowers.py  compound.py  metaswarm.py  metareview.py
    extract.py                # per-framework prose -> atomic candidate issues (Martian's EXTRACT_PROMPT)
    judge.py                  # Martian's JUDGE_PROMPT, multi-judge, stored-decision agreement check
    score.py                  # TP/FP/FN, profiles, Fβ, severity-weighted, dedup, hallucination rate
    adjudicate.py             # Phase-B+: reclassify high-confidence unmatched findings (real-but-ungold vs hallucination)
    effort.py                 # effort profiles -> adapter params
    cost.py                   # token/time/$ normalization, Pareto frontier
    report.py                 # tables, plots, failure-mode analysis
    cache.py                  # local API-response cache for Phase B budget protection
    runs.py                   # run registry: append-only index + per-run manifest, query/compare over time
    backfill_runs.py          # one-time: register completed Phase-A runs into the registry
  results/                    # our JSON summaries (gitignored except force-added evidence)
  logs/                       # Inspect eval logs (gitignored except force-added evidence; full transcripts/usage/scores)
  runs/                       # run registry (COMMITTED — the established place for longitudinal analysis)
    registry.jsonl            #   append-only index, one line per run, queryable with jq/python
    <run-id>/manifest.json    #   dimensions: phase, model, framework, effort, run#, status, cost, metrics
    <run-id>/summary.json     #   our aggregate output for the run
    <run-id>/inspect_log.eval  #   symlink to the full-evidence Inspect log (not duplicated)
```

### 4.1 Run registry (longitudinal analysis)

The registry **complements** Inspect logs (which hold the full evidence — transcripts,
per-sample token usage, scores) with a queryable index keyed by dimensions
(phase × model × framework × effort × run#), so we can compare runs over time and across
the matrix. Evidence is NOT duplicated: each run dir symlinks to the Inspect log.
`harnesseval/runs.py` provides `register()`, `query()`, `compare()`; `calibrate.py` and
`run_a3.py` auto-register on completion. Phase B/C runs will auto-register too. Query with
`query(framework="metareview", model="...")`; diff two runs with `compare(a, b)`.
  third_party/                # git submodules or vendored: martian CRB @ pinned SHA, metareview checkout
```

## 5. The normalized finding schema (the integration layer)

Martian judges **atomic issue strings**. Frameworks emit prose. The bridge:

```python
@dataclass
class Finding:
    issue_text: str          # atomic, standalone problem description (the unit Martian judges)
    file: str | None         # path if extractable
    line: int | None
    severity: str | None      # low|medium|high|critical if the framework states it
    category: str | None      # bug|security|concurrency|... if stated
    source: str              # which framework+lens produced it (for provenance)
    raw: str                 # original snippet for audit
```

**Extraction** uses Martian's `EXTRACT_PROMPT` verbatim (`offline/code_review_benchmark/
step2_extract_comments.py`) so a framework's prose report becomes a `list[Finding]` whose
`issue_text` values are directly comparable to golden comment strings under Martian's
`JUDGE_PROMPT`.

**Dedup** uses Martian's `step2_5_dedup_candidates.py` logic so a framework that states the
same issue in a summary + inline isn't double-counted.

This schema is the one piece that is genuinely novel; everything downstream reuses Martian.

## 6. Effort abstraction (redefined for static-PR review)

metareview's retry FSM is about *revising an artifact until it passes* — irrelevant to
reviewing a fixed PR. Effort has two layers: a **model reasoning-effort knob** (verified
real and near-uniform across hosts — see §6.1) and our **review-method effort knobs**
(below). The (model × framework × effort) matrix uses the model effort knob as the
`effort` axis and the review-method knobs as adapter parameters.

### 6.1 Model reasoning-effort knob (verified 2026-08-22)

| Model family | Access (Phase B iterate / Phase C final) | Effort mechanism | "Medium"→ | "Extra High"→ |
|---|---|---|---|---|
| Claude (Opus 4.8, Opus 5, Fable) | Claude Code `claude -p` (OAuth, **free**) / Anthropic API (paid) | `--effort` / API `reasoning_effort` | `medium` | `xhigh` |
| Codex (5.6 Sol) | Codex `codex exec` (ChatGPT OAuth, **free**) / OpenAI API (paid) | `model_reasoning_effort` / API `reasoning_effort` | `medium` | `xhigh` |
| GLM (`glm-5.2-vision-flex`) | **Lunaroute** (subscription, flat-fee, free marginal) - API-direct, all phases | OpenAI-compat `reasoning_effort` | `medium` | `xhigh` |
| Kimi (`kimi-k3`) | **Lunaroute** (subscription, flat-fee, free marginal) - API-direct, all phases | OpenAI-compat `reasoning_effort` | Kimi `high` | Kimi `max` |

Effort levels: Claude Code `--effort {low,medium,high,xhigh,max}`; Codex
`model_reasoning_effort {low,medium,high,xhigh,max,ultra}`. Codex `gpt-5.6-sol` confirmed in
`~/.codex/models_cache.json` (default low, levels `[low,medium,high,xhigh,max,ultra]`). "Extra High" = `xhigh` (NOT `max`/`ultra`) so the
high-but-not-maximum comparison is uniform across families; `max`/`ultra` reserved as an
optional extra axis.

**GLM/Kimi access (verified 2026-08-22):** configured in `~/.pi/agent/models.json` via the
**Lunaroute gateway** (`gw.lunaroute.com/v1`, OpenAI-compatible, `LUNAROUTE_API_KEY` is set).
Both `reasoning: true` + `supportsReasoningEffort: true`. pi's `thinkingLevelMap`:
GLM `medium->medium, xhigh->xhigh` (clean 1:1); **Kimi `medium->high, xhigh->max`** (two distinct
levels — valid for our {medium,xhigh} pair). Lunaroute is a **flat-fee subscription** (per user, 2026-08-22), so GLM/Kimi marginal cost is
~0 in **every** phase — they join Phase B free iteration. pi is the *config/credential source*;
our Inspect harness calls Lunaroute **directly** (OpenAI-compatible) — no pi/CLI scaffolding, so
GLM/Kimi are consistent with Claude/Codex API-direct in Phase C.

**Budget reality (updated 2026-08-22):** Phase B free iteration now covers **all four** families —
Claude Code (OAuth), Codex (ChatGPT OAuth), GLM + Kimi (Lunaroute subscription). Only the
**Anthropic API + OpenAI API** spend (per-token, for the Claude/Codex arms in API-direct mode)
is deferred to Phase C. Gemini 2.5 Pro: **dropped** (no access). Codex 5.6 Terra: **dropped**
(per user, 2026-08-22). *Caveat:* a flat-fee Lunaroute plan may have rate limits / token caps
that could distort a large 50-PRx5-run matrix - watch in the Phase C cost pilot (PLAN S C.0).

### 6.2 Review-method effort knobs

| Knob | low | medium | high |
|---|---|---|---|
| `independent_passes` (aggregated, majority/dedup) | 1 | 1 | 3 |
| `lenses` (reviewer perspectives, metareview=5) | 1 | 1 | framework-native (≤5) |
| `thinking_budget` | none | low | high |
| `context_depth` | diff only | +changed files | +changed files |

Run-#1 effort cells (proposed; confirm in §14): model effort `{medium, xhigh}` × review-
method `{low, high}`. `vanilla` ignores `lenses` (it has none) so its effort varies only by
`independent_passes` + `thinking_budget`.

## 6.3 metareview's deterministic floor (decompose in scoring)

metareview's Go gates (eval injection, TODO/FIXME, missing-tests, duplicate-path,
truncated-diff) are **model-independent** — they fire identically across the entire
(model × effort) matrix and cost **zero tokens**. So metareview has a free recall floor
that pure-LLM frameworks lack. The scorer MUST decompose metareview's findings into:
`deterministic_gate_recall` (free, constant across models) and `llm_lens_recall`
(model/effort-dependent). Report both, plus the combined recall. This is a real structural
finding the eval surfaces — and a fairness point: those catches cost nothing.

### 6.3.1 Realistic subagent routing: opus orchestrator + Haiku lenses (discovered 2026-08-22)

**Key learning from the realistic runs:** when a user runs metareview via the real harness
in Claude Code (`claude -p --model opus` + the review-artifact skill dispatching the 5 lenses
via the `Agent` tool), Claude Code routes **subagent dispatches to Haiku by default**,
regardless of `--model`. So "metareview-realistic @ opus" is in practice **opus orchestrator
(planning + context reading + cache-heavy) + Haiku 5-lens subagents (cheap)** — NOT 5 opus
lens reviews. Verified via per-model `modelUsage`: opus ~$3.2 / ~1.8M tok (orchestrator,
~99.96% of cost), haiku ~$0.0015 / ~1.4k tok (the 5 lenses).

Implications for analysis (do NOT force anything — this IS what users get):
- The (model × effort) axis for realistic metareview varies the **orchestrator**; lenses stay
  Haiku unless metareview is later tuned to pin them. Record which model the lenses actually
  used (per-model usage captures this).
- Cost is dominated by the orchestrator, not the lens fanout. The 5-lens fanout is cheap.
- Recall reflects **Haiku-quality lenses**, not the orchestrator's quality. The fair reading
  of "metareview-realistic @ opus vs vanilla @ opus" is: *does opus planning + Haiku 5-lens
  fanout beat a bare opus review?* — not *does opus 5-lens beat opus 1-lens*.
- This is actionable for future metareview tuning: pinning lenses to the orchestrator model
  (or to a mid-tier like Sonnet) is a knob that could change the quality/cost tradeoff — but
  that's a metareview design change, not an eval change. The eval reports the realistic default.

The per-model `usage` accounting (§10) is therefore load-bearing: a single total would hide
that ~99.96% of metareview's cost is orchestrator overhead, and would make "metareview is
expensive because of 5 lenses" a false conclusion (the lenses are cheap; the orchestrator is).

## 7. Execution modes and the budget phasing

### 7.1 Credential handling (no OAuth override)

**Hard rule:** `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` must NEVER be exported in the lab
host's login shell (`~/.zshrc`, `~/.bash_profile`, etc.) — both CLIs prefer the env var over
OAuth (Claude Code: "Anthropic auth is strictly `ANTHROPIC_API_KEY` or apiKeyHelper"; Codex
reads `OPENAI_API_KEY` over ChatGPT OAuth). Exporting them would silently switch your regular
`claude`/`codex` to paid-per-token API billing.

**Where keys live:**
- **Primary:** a plaintext file **outside every git repo** and outside the shell profile:
  `~/.config/harnesseval/keys.env` (chmod 600), one `KEY=value` per line. Never committed.
  **Key names in the file (explicit, as of 2026-08-22):** `HARNESS_`-prefixed names so they
  can NEVER collide with the env-var names the CLIs watch for — an accidental `source`d or
  leaked file therefore cannot override your Claude Code / Codex OAuth:
  | File key | Harness passes to |
  |---|---|
  | `HARNESS_ANTHROPIC_API_KEY` | `Anthropic(api_key=...)` / Inspect `anthropic` provider |
  | `HARNESS_OPENAI_API_KEY` | `OpenAI(api_key=...)` / Inspect `openai` provider |
  | `HARNESS_LUNAROUTE_API_KEY` | `OpenAI(base_url=LUNAROUTE_BASE_URL, api_key=...)` for GLM/Kimi |
  | `LUNAROUTE_BASE_URL` | `base_url` for the Lunaroute OpenAI-compatible client (NOT prefixed — not a collision risk) |
- **Gold standard (optional):** macOS Keychain — `security add-generic-password -s
  harnesseval-anthropic -a $USER -w`, read via `security find-generic-password -s … -w`.
  Zero plaintext on disk.
- `LUNAROUTE_API_KEY` is already in the env (pi config) and may stay there (it does not
  affect Claude Code / Codex auth).

**How the harness loads them:** `harnesseval/keys.py` reads the keys file **only during
API-direct phases (A, C)** and passes them **directly to SDK constructors**
(`Anthropic(api_key=keys['HARNESS_ANTHROPIC_API_KEY'])`, `OpenAI(api_key=keys['HARNESS_OPENAI_API_KEY'])`, `OpenAI(base_url=keys['LUNAROUTE_BASE_URL'], api_key=keys['HARNESS_LUNAROUTE_API_KEY'])` for GLM/Kimi)
and Inspect provider config — NOT by
exporting into a broad `os.environ`. If Inspect requires an env var, the harness sets it
**only within the harness subprocess**. **Phase B (CLI/OAuth) never loads this file**, so
OAuth stays the default for `claude`/`codex`. The in-repo `.env.example` is a **template
only** (placeholders, no real keys) that documents the external file path.

### 7.2 Modes

| Mode | Token cost | Faithfulness | Use in |
|---|---|---|---|
| `api` | exact; no host scaffolding (~15k token CLI tax absent) | methodology-only | Phase A, Phase C |
| `cli` | as-reported by the CLI (includes ~15k host scaffolding) | real plugin behavior | Phase B |

**Honesty rule:** every measurement stores its `execution_mode`. The **final apples-to-apples
comparison (Phase C) is API-only**. Phase B (CLI) numbers are never compared head-to-head with
API numbers. Additionally report `net_review_tokens` (prompt+output, excluding host scaffolding)
where extractable.

**Phasing:**
- **Phase A — calibration (API).** Validate the lab against published anchors. Gate.
- **Phase B — build + tune (CLI/OAuth + Lunaroute subscription).** Implement adapters; iterate
  cheaply across all four families (Claude Code, Codex, GLM, Kimi); no published claims.
- **Phase C — final run (API).** The real matrix; the report; the Pareto plot. API keys
  loaded per §7.1.

## 8. Calibration protocol (Phase A — the validation gate)

No framework number is trusted until Phase A passes.

### Anchor 1 — judge/scorer reproduction (Martian)
- **Input:** Martian's shipped `offline/results/<judge>/candidates.json` (stored tool
  reviews) + `offline/golden_comments/*.json` (ground truth).
- **Run:** our `judge.py` with Martian's `JUDGE_PROMPT` verbatim, judge =
  `claude-opus-4-5-20251101` (their default), then Sonnet 4.5, then GPT-5.2.
- **Pass:** our per-(tool,PR,golden) match decisions agree with their shipped
  `evaluations.json` on **≥ 95%** of pairs; aggregate TP/FP/FN per tool reproduces their
  `benchmark_dashboard.json` leaderboard within **±2 absolute** on each count.
- **Proves:** our judge + scorer + dedup + profile/Fβ wiring is correct.

### Anchor 2 — model/effort reproduction (Inspect SWE-bench Verified)
- **Run:** `inspect eval inspect_evals/swe_bench_verified --model <m>` for ≥1 model with a
  public swebench.com leaderboard number; run their `compare_baseline.py` (asserts their
  scorer == official SWE-bench scoring).
- **Pass:** our resolve rate ≈ public leaderboard number for `<m>`; baseline assert passes.
- **Proves:** our model routing + API config + solver harness is correct (no silent
  degradation: wrong context window, dropped tools, wrong temperature).

### Anchor 3 — adapter sanity band (Martian `claude-code` row)
- **Run:** our `vanilla-engineered` adapter on Claude against the 50 PRs.
- **Pass:** lands in a sensible neighborhood of Martian's published `claude-code` row
  (Opus 4.5 judge, core profile: TP 76 / FP 88 / FN 82). Not exact (different prompt), but
  not an order of magnitude off — proves end-to-end adapter→extract→judge plumbing.

**Phase A done-criteria:** all three anchors pass. Budget: ~$10–50 of API (judge calls
are cheap-but-numerous; ~candidate×golden pairs across 50 PRs × 26 tools, but we only need
to reproduce a subset for the agreement check — sample if budget-bound).

## 9. Scoring

Reuse Martian's pipeline:
1. **Extract** framework output → atomic `Finding.issue_text` (Martian `EXTRACT_PROMPT`).
2. **Dedup** sibling duplicates (Martian `step2_5`).
3. **Judge** each candidate × each golden comment (Martian `JUDGE_PROMPT`, semantic match).
   → TP = matched candidate; FN = unmatched golden; unmatched candidate = FP-pending.
4. **Adjudicate** unmatched candidates (the "superhuman find" fix): re-run judge on
   `{candidate, diff context}` asking "is this a real issue in this diff?" High-confidence
   reals → reclassified **real-but-ungold** (excluded from FP; reported separately as
   *incremental recall*). Low-confidence → **hallucination** (true FP).
5. **Score:** precision = TP/(TP+FP_hallucination); recall = TP/(TP+FN);
   severity-weighted variants; **Fβ** (report F1 and F2 — F2 weights recall 4×, matching
   Martian's default `beta=2.0`); per-profile (strict/core/all).
6. **Per-severity recall** (catching Critical bugs matters more than Low).

**Judges:** 3 (Opus 4.5, Sonnet 4.5, GPT-5.2) — report judge variance; for a given
under-test model the *primary* judge is a different family (anti self-preference).

## 10. Cost & time measurement

- **tokens:** from API usage (exact) or CLI JSON `usage` (Phase B). Record
  `total_tokens` and `net_review_tokens`.
- **time:** wall-clock per sample. Record `execution_mode` (startup/sandbox overhead
  differs by mode).
- **$**: derived = tokens × price table pinned to a date (e.g. 2026-08-22); labeled
  *estimated*. Subscription CLI runs report `$ ≈ 0` (amortized) — fine; relative token/time
  deltas are the real metric.
- **caching:** enable Anthropic prompt caching consistently for repeated system prompts
  (judge calls are highly repetitive); report cache hit rate.
- **output:** the **recall-vs-cost Pareto frontier** per (model, effort) — the decision plot.

## 11. Statistical rigor

- 50 PRs / 173 golden → wide CIs. Report **bootstrap 95% CIs** on every precision/recall/Fβ.
- **Paired per-PR analysis:** every FUT sees the same 50 PRs → per-PR Δrecall, more powerful
  than unpaired.
- **Multiple runs per cell:** ≥3 (aim 5) in Phase C, to measure run-to-run LLM variance.
- **Significance:** report whether FUT-A vs FUT-B Δ is outside the bootstrap CI / paired
  noise. No "wins" claims within noise.
- **Multiple comparisons:** 6 FUTs × several metrics → report Bonferroni/FDR-adjusted
  significance.
- **Failure-mode analysis:** for each missed golden issue, categorize the miss
  (wrong-category / insufficient-depth / context-limited / hallucinated-override). This is
  where the insight lives, not the headline score.

## 12. Reproducibility & pinning

- Martian: pin **SHA `2b092b670f`** (2026-08-16); pin the exact `JUDGE_PROMPT` +
  `EXTRACT_PROMPT` from `step2/step3` at that SHA.
- Inspect: pin via `uv.lock`; pin `inspect_evals` version.
- **Models:** use **full snapshot IDs**, never aliases: `claude-opus-4-5-20251101`,
  `claude-sonnet-4-5-20250929`, `openai/gpt-5.2`, `google/gemini-2.5-pro`. Aliases drift.
- metareview: pin checkout SHA; build `bin/metareview` from source (verified builds:
  `go build -o bin/metareview ./cmd/metareview` → v0.6.0).
- Env: Python via `uv`; `uv.lock` committed. API keys in `.env` (gitignored).
- **Phase B budget protection:** `cache.py` memoizes API responses keyed by
  (model, prompt-hash) so iteration doesn't re-pay.
- **Audit trail:** Inspect eval logs (full transcript + usage + scores) committed for the
  Phase C final run; a representative Phase A log committed as evidence.

## 13. Known limitations (state in the report)

1. Martian's 50 PRs are from famous repos → possible training contamination of the
   model-under-test (less severe for *framework* comparison since all FUTs share the model,
   but the model may have seen the PR). OpenEnv/online is the future mitigation.
2. LLM judge introduces model-dependent variance → mitigated by 3 judges + reported variance.
3. Golden set is human-curated and incomplete → the adjudication step (§9.4) mitigates the
   "superhuman find punished as FP" problem but is itself judge-limited.
4. API-direct mode tests the *methodology*, not the real plugin plumbing (tool dispatch,
   worktree isolation). CLI-faithful spot-checks in Phase B cover this; Phase C is API.
5. Context is fixed to diff + changed files; agentic repo-browsing is a future axis.

## 14. Open decisions (confirm with user before Phase C)

These have **proposed defaults** so a fresh agent is never guessing; confirm to lock.

**Sequencing (confirmed 2026-08-22):** calibration-first. Phase A is a **single
calibration pass only**; the expanded model matrix runs after Phase A passes. Judges stay on
the **old trio** (Opus 4.5, Sonnet 4.5, GPT-5.2) for calibration compatibility — only the
*models-under-test* expand. Framework sequencing: validated FUTs (vanilla ×2, Superpowers,
Compound) on the model matrix first; **metaswarm + metareview after** (isolates new-framework
risk from new-model risk).

1. **Models-under-test (run #2, after calibration):** the **newer** set — Opus 4.8
   (Medium, xHigh), Opus 5 (Medium, xHigh), Fable (Medium, xHigh), Codex 5.6 Sol (Medium,
   xHigh), Codex 5.6 Terra (Medium, xHigh), GLM-5.2-vision-flex (Medium, xHigh), Kimi-k3
   (Medium, xHigh) — plus the **older** set Sonnet 4.5 + GPT-5.2 as anchors. **Gemini 2.5
   Pro: dropped** (no access). Model effort = `--effort`/`model_reasoning_effort`/OpenAI-compat
   `reasoning_effort` `{medium, xhigh}` (§6.1). Full snapshot IDs required (not aliases) —
   resolve in Phase 0. Access: Claude/Codex via OAuth (Phase B free) + API (Phase C); GLM/Kimi
   via Lunaroute API (paid, every phase).
2. **FUTs (run #1):** vanilla-naive, vanilla-engineered, superpowers, compound, metareview.
   Add metaswarm in run #2. (Confirmed.)
3. **Effort cells:** model effort `{medium, xhigh}` × review-method `{low, high}`.
   (Proposed.)
4. **Phase A agreement threshold:** ≥95% pairwise judge agreement; ±2 absolute on
   leaderboard counts. (Proposed.)
5. **Phase C runs per cell:** 5 (drop to 3 if budget-bound). 5-PR cost pilot (PLAN §C.0) is a
   **hard gate** before the full 50-PR run. (Confirmed: pilot required.)
6. **Adjudication of unmatched findings:** LLM judge first; human spot-check of 50 random
   adjudications to validate the adjudicator. (Proposed.)
7. **Contribute upstream:** plan to PR our framework rows to Martian and publish an
   `inspect-evals-code-review` package so we don't maintain a fork forever. (Proposed: yes.)
8. **GLM & Kimi access (resolved 2026-08-22):** via pi's config → **Lunaroute gateway**
   (OpenAI-compatible, `LUNAROUTE_API_KEY` set), paid API. Effort settable (§6.1): GLM
   {medium,xhigh}->{medium,xhigh}; Kimi {medium,xhigh}->{high,max}. Inspect calls Lunaroute
   directly in Phase C (no pi scaffolding).
9. **Gemini 2.5 Pro (resolved 2026-08-22):** **dropped** — no paid Gemini subscription.
10. **metareview scoring decomposition:** report `deterministic_gate_recall` +
    `llm_lens_recall` + combined (§6.3). (Confirmed.)

## 15. Risks

- **Budget overrun in Phase C:** 5 FUTs × 3 models × 2 efforts × 50 PRs × 5 runs ×
  multi-lens = large. Mitigate: run a 5-PR pilot first; extrapolate cost; get explicit
  go-ahead before the full Phase C.
- **Adapter faithfulness disputes:** "that's not how Superpowers really reviews." Mitigate:
  document each adapter's methodology source (file/SHA) and offer CLI-faithful spot-checks.
- **Judge drift if Martian updates their prompt:** we pin the SHA; re-calibrate if we re-pin.
- **metareview CLI arg liberality:** `review task-done` treats unexpected args as a target
  and writes a scaffold. The adapter must pass explicit, validated args and assert on the
  produced artifact path.
