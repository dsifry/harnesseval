# HANDOFF — harnesseval, 2026-08-23

> **For a fresh agent:** read `docs/SPEC.md` (the design) and `docs/PLAN.md` (the phases)
> first, then this doc. This doc is the **operational state + hard-won gotchas + next steps**;
> SPEC/PLAN are the source of truth for design. If anything conflicts, SPEC wins — update it.

## 1. Mission (one paragraph)

A reproducible eval lab comparing **AI code-review frameworks** (vanilla, metareview,
Superpowers, Compound Engineering, metaswarm) across a **(model × effort)** matrix, reporting
**review quality** (recall/precision/Fβ, with adjudication of false positives) **and cost**
(per-model tokens + time + $) on a **calibrated** foundation. Built on Inspect AI + the
Martian Code Review Bench dataset + a run registry for longitudinal analysis. Repo:
`/Users/dsifry/Developer/harnesseval`.

## 2. Current state (as of this handoff)

**Phase 0 (scaffold) ✅** — `pyproject.toml`, `uv.lock`, keys loader, Martian vendored at SHA
`2b092b670f`, metareview built (`bin/metareview` v0.6.0 @ `7a29617c`).

**Phase A (calibration) ✅ COMPLETE:**
- A.1: judge/scorer reproduces Martian's published TP/FP/FN within ±2 (50-pair pilot: 41/46
  exact, max Δ=2). Native Anthropic. Martian-proxy code path retained but parked (gateway
  rate-limits).
- A.3: same pipeline through Inspect's `eval` runner — validates Inspect's native per-sample
  token/time accounting + eval logs. (A.2 skipped; subsumed by A.3.)

**Phase B (build + tune) — IN PROGRESS:**
- ✅ PR-diff fetcher (`dataset/pr_diff.py`, cached via `gh`)
- ✅ Adapter base + Finding schema + extractor (Martian `EXTRACT_PROMPT`)
- ✅ vanilla adapter (api + cli/realistic)
- ✅ metareview adapter: api-direct (5 lenses → API) **AND** realistic (real `bin/metareview`
  gates + 5 lenses as real `Agent` subagents via `claude -p`)
- ✅ effort axis wired (Anthropic `thinking`, OpenAI/Kimi `reasoning_effort`)
- ✅ per-model usage accounting (orchestrator vs subagent split, cached/uncached, costUSD)
- ✅ parallel OAuth matrix runner (concurrency 3-4)
- ✅ adjudication (real-but-ungold vs hallucination) + score decomposition
- ✅ run registry (longitudinal analysis) — every run auto-registers
- ✅ report module (leaderboard + Pareto plot + per-model breakdown)
- **A 48-cell realistic matrix is RUNNING in the background** (PID in `/tmp/mm_pid.txt`,
  output `/tmp/mm_out.txt`, results → `results/phase_b_realistic_48.json`). Check with
  `ps -p $(cat /tmp/mm_pid.txt)` and `tail /tmp/mm_out.txt`.

**NOT built yet:** superpowers adapter, compound adapter (the work to do next — see §6).

## 3. The key learnings/gotchas (discovered the hard way — READ THESE)

1. **Claude Code subagent routing (SPEC §6.3.1):** when a user runs metareview with
   `--model opus` and the skill dispatches the 5 lenses via the `Agent` tool, Claude Code
   **routes subagents to Haiku by default**, regardless of `--model`. So "metareview-realistic
   @ opus" = opus orchestrator + Haiku 5-lens subagents (NOT 5 opus lens reviews). The
   orchestrator is ~99.96% of the cost; the lenses are cheap. This is REALISTIC — don't force
   anything; report per-model usage so it's visible. Actionable for future metareview tuning
   (pin lenses to orchestrator model) but the eval reports the realistic default.

2. **Per-model accounting is load-bearing (usage.py):** `claude -p` usage has 5 token fields
   (`input_tokens` is just the user's literal prompt, often ~2; the ~15k+ scaffolding is in
   `cache_creation_input_tokens` + `cache_read_input_tokens`) AND per-model `modelUsage` with
   `costUSD` per model. Recording only input+output undercounts by ~385×. ALWAYS use
   `usage.from_claude_cli`/`from_codex_cli`/`from_anthropic_api`/`from_openai_api` and record
   `per_model_usage` on `ReviewRun`.

3. **`claude -p` subagent tool is named `Agent`** (input: `{description, prompt,
   subagent_type, run_in_background}`), NOT `Task`. The realistic metareview prompt MUST
   say "Agent tool" or it falls back to in-session (non-adversarial — the weak fallback the
   skill warns against).

4. **`--append-system-prompt` is required** on `claude -p` or it can silently use a different
   model for the work turn in some cases; always pass it.

5. **Effort mapping is provider-specific (effort.py):** Anthropic `thinking{disabled|enabled}`
   (medium→disabled, xhigh→enabled with budget≥1024 < max_tokens; **temperature must be 1 when
   thinking enabled**). OpenAI `reasoning_effort` {low,medium,high}. **Kimi has no "medium"
   level** — `medium→high`, `xhigh→max` (sending "medium" 500s). GLM accepts the ladder.

6. **Codex CLI:** valid slugs are `gpt-5.6-sol`, `gpt-5.6-terra`, etc. — `gpt-5.2` is API-only.
   `codex exec` prints "Reading additional input from stdin..." to **stdout** before the JSONL
   (skip non-`{` lines). Use `stdin=subprocess.DEVNULL`. Route `gpt-5.2`→`gpt-5.6-sol` for CLI.

7. **metareview `bin/metareview review task-done` reads git from a real repo** — the realistic
   adapter materializes the PR into a throwaway git repo (`dataset/materialize.py`: base→pr→task
   commits; `--base HEAD~2` reviews the pr commit). metareview filters generated paths, so get
   the base ref right or it reviews an empty diff.

8. **Adjudication (SPEC §9.4):** a chunk of "false positives" are real bugs the gold set missed
   (Martian's superhuman-find problem). `adjudicate.py` re-judges each FP against the diff:
   high-confidence reals → `real_but_ungold` (incremental recall, not FP); rest → hallucination.
   `adjudicated_precision` + `incremental_recall` are the fairer metrics.

9. **Two columns, never compared head-to-head (SPEC §7):** `mode=api` (pinned snapshot IDs,
   clean, concurrent, the "methodology isolated" academic column + Phase C reproducibility
   anchor) vs `mode=cli` (OAuth, realistic, ~15k scaffolding tax, serial-ish, the "what users
   get" column). Record `execution_mode` with every measurement. Judge layer ALWAYS api.

10. **Cross-family judging (SPEC §9):** primary judge is a DIFFERENT family from the model
    under test (claude→gpt-5.2 judge; gpt→opus judge; glm/kimi→gpt-5.2 judge). Judge trio stays
    on the calibrated old models (opus-4-5, sonnet-4-5, gpt-5.2) for calibration compatibility.

## 4. Keys & budget (CRITICAL)

- Keys live at `~/.config/harnesseval/keys.env` (chmod 600), names are `HARNESS_`-prefixed
  (`HARNESS_ANTHROPIC_API_KEY`, `HARNESS_OPENAI_API_KEY`, `HARNESS_LUNAROUTE_API_KEY`,
  `HARNESS_MARTIAN_API_KEY`, `LUNAROUTE_BASE_URL`). These names are collision-proof so an
  accidental shell export CANNOT override Claude Code/Codex OAuth. `keys.py` reads them and
  passes to SDK constructors directly — NEVER `os.environ[...] = ...` globally. Phase B (cli)
  never loads them; Phase A/C (api) do.
- OAuth (free): Claude Code (`claude -p`, re-auth via `claude auth login` if token expires),
  Codex (`codex exec`, logged in). GLM/Kimi via Lunaroute (flat-fee subscription, free marginal).
- API (paid): Anthropic + OpenAI keys present + validated. Martian $10 credit (mostly unused).
- **Budget phasing (SPEC §7.2):** Phase A/C = API (calibration + final apples-to-apples);
  Phase B = OAuth subscriptions (free iteration). The in-flight matrix is OAuth (free).

## 5. Key files (what each does)

```
harnesseval/
  keys.py                 # HARNESS_-prefixed key loader; no env pollution
  effort.py               # provider-specific effort mapping (thinking/reasoning_effort)
  usage.py                # per-model usage accounting (THE apples-to-apples fix)
  anthropic_util.py       # text_content() skips ThinkingBlock
  model_router.py         # provider-agnostic call_model(call_model_json); execution_mode {api,cli}
  cli_backends.py         # claude -p / codex exec OAuth backends (per-model usage)
  judge.py                # Martian JUDGE_PROMPT + greedy scorer + judge_pairs_router (cross-family)
  extract.py              # Martian EXTRACT_PROMPT (prose -> atomic Findings)
  adjudicate.py           # reclassify FPs as real-but-ungold vs hallucination (sync + async)
  finding.py              # Finding dataclass (the integration schema, SPEC §5)
  runs.py                 # run registry: register/query/compare (longitudinal analysis)
  report.py              # leaderboard + Pareto plot + per-model breakdown
  calibrate.py            # Phase A.1 (Martian judge reproduction)
  inspect_a3.py / run_a3.py # Phase A.3 (Inspect runner validation)
  crosscheck.py           # Martian-proxy judge cross-check (parked)
  run_one.py              # one-PR end-to-end driver
  run_matrix.py           # multi-PR x framework runner (api)
  run_model_matrix.py     # (model x effort) matrix runner (parallel, api+cli)
  backfill_runs.py        # one-time: register completed Phase-A runs
  adapters/
    base.py               # ReviewerAdapter protocol + PRSample + ReviewRun (+ per_model_usage)
    vanilla.py            # naive + engineered, api + cli/realistic
    metareview.py         # api-direct metareview (deterministic gates + 5 API lenses)
    metareview_realistic.py # REALISTIC: real bin/metareview + 5 Agent subagents via claude -p/codex
  dataset/
    martian.py            # load golden_comments + shipped results at pinned SHA
    pr_diff.py            # fetch + cache PR diffs via gh
    materialize.py        # materialize PR into throwaway git repo for metareview
third_party/             # gitignored: Martian CRB @ 2b092b670f, metareview_sha.txt
bin/metareview            # built metareview binary (gitignored)
runs/                    # run registry (COMMITTED — the longitudinal analysis place)
logs/                    # Inspect eval logs (gitignored except force-added evidence)
.cache/                  # pr_diffs + mrv_repos (gitignored)
```

## 6. What to do next (priority order)

### 6.1 Build superpowers + compound adapters (realistic) — THE NEXT STEP

These are the missing frameworks. The pattern is established by `metareview_realistic.py`:
drive a real host-agent session (`claude -p`/`codex exec`) that installs/uses the real plugin
and invokes its review skill, capturing per-model usage. The hard part is these are
**external plugins** (not local like metareview) — you need to install the real plugin in a
throwaway host config and drive it headlessly.

- **Superpowers** (`obra/superpowers`): clone at a pinned SHA, find the spec/plan-review skill
  + rubric. Realistic = a user invokes the review skill in-session. Build
  `adapters/superpowers_realistic.py` mirroring `metareview_realistic.py` structure (drive a
  real session that uses the review skill). Document the methodology source (repo+SHA+file).
- **Compound Engineering** (`EveryInc/compound-engineering-plugin`): same pattern, their
  review skill. `adapters/compound_realistic.py`.
- Also keep api-direct versions (`adapters/superpowers.py`, `adapters/compound.py`) as the
  secondary column (extract the methodology to a bare API prompt), per SPEC §7.

Reference their eval approach (Drill for Superpowers; `skill-eval-cell` for Compound) for how
they drive real sessions — but our adapter just needs to invoke their review skill on a PR diff
and capture findings + per-model cost.

### 6.2 The 48-cell matrix was STOPPED (2026-08-23) — rerun clean

It was stopped after ~15/48 cells because it launched BEFORE the per-model-usage propagation
edit (§3 gotcha #2), so its runs lack `per_model_usage` and the cost axis is unusable. Those
15 cells are registered in runs/registry.jsonl but should be TREATED AS DEBUGGING SIGNAL
ONLY — they show vanilla-engineered is reliable (opus medium ~0.75 recall) and
metareview-realistic has bugs to fix FIRST (gpt-5.2 scored 0.00 recall on 3 cells; opus xhigh
0.11 recall @ 6.5M tok; codex xhigh times out at 300s — bump to 900s).

BEFORE rerunning the matrix, debug metareview-realistic (gpt-5.2 = 0.00 is the loudest signal —
the codex subagent path isn't producing matchable findings). Then rerun a clean matrix with
the current code (which propagates per_model_usage + total_cost_usd). A 4-8 cell subset first
to confirm per-model cost populates, then the full matrix.

### 6.3 Full matrix (after superpowers/compound built)

6 hard PRs × {vanilla, metareview, superpowers, compound} × {opus, sonnet, fable, gpt-5.2,
glm, kimi} × {medium, xhigh} via OAuth (concurrency 3-4), judge on API (cross-family).
~144+ cells, hours. Then Phase C (API, pinned IDs, the final apples-to-apples) per PLAN.

### 6.4 Report improvements

- failure-mode analysis (which goldens each framework misses)
- deterministic_gate_recall vs llm_lens_recall decomposition visualization (SPEC §6.3)
- bootstrap 95% CIs (SPEC §11) — 6 PRs is anecdotal; need full 50 + CIs for Phase C claims

## 7. How to run things (cheat sheet)

```bash
export PATH="$HOME/.local/bin:$PATH"   # uv lives here
cd /Users/dsifry/Developer/harnesseval

# one PR end-to-end (api or cli)
uv run python -m harnesseval.run_one --url <golden-url> --framework metareview-realistic --mode cli --effort medium

# (model x effort) matrix — the main runner
uv run python -m harnesseval.run_model_matrix --prs 6 --models <...> --efforts medium,xhigh \
    --frameworks vanilla-engineered,metareview-realistic --mode cli --concurrency 3

# report (leaderboard + Pareto + per-model breakdown)
uv run python -m harnesseval.report --phase B --pareto results/pareto.png

# query the run registry
uv run python -c "from harnesseval.runs import query; print(query(phase='B', framework='metareview-realistic'))"
```

## 8. Things to NOT do

- Don't export `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` to the shell (overrides OAuth).
- Don't compare api vs cli numbers head-to-head (different scaffolding).
- Don't report only `input_tokens+output_tokens` for CLI runs (undercounts ~385×).
- Don't force subagent models — record what the host actually does (per-model).
- Don't trust model aliases without recording the resolved id (`opus`→`claude-opus-5` today).
- Don't skip `--append-system-prompt` on `claude -p`.
- Don't sink budget on the full 50-PR matrix without the 5-PR cost pilot (PLAN §C.0).
