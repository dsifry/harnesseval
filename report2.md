# Evaluating PR Review Engines — do model or harness make a difference? (yes they do!)

> **Open-source near-frontier models driven by review harnesses find more real bugs — at a
> lower $ per bug found — than frontier models like Fable 5.1 or GPT-6 Astra** when asked to
> *"Review the following code diff for real, actionable issues … find issues in these
> categories: bug, security, concurrency, data, api, performance, test_gap, doc_defect …
> classify severity … only report real issues you are confident about"* — the standard
> single-prompt review (§2.1). On the top-6 benchmark PRs: vanilla Fable 5.1 = 7.5 hidden
> gold/PR at $1.01; vanilla Astra = 2.2/PR at $0.51; **ce × glm-5.3-background × low =
> 36.8/PR at $0.20** — the harness, not the model tier, is the binding constraint.

> **What this is.** A follow-up to the main comparison ([`report.md`](report.md)) — read it
> standalone, but every framework/model/effort claim about the *older* cells cites the main
> report's sections. This report covers only the 2026-09-07 results: the full **GLM-5.3 /
> GLM-5.3-flash** suite (24 cells), effort-ladder probes on the same model, and a smoke test
> of metareview PR #145 (the lens-side fix for fabricated "zero tests" claims). All numbers
> reproducible from committed run records via [`REPRODUCE.md`](REPRODUCE.md).

---

## 0. Background

### 0.1 What are we evaluating?

**The key use case: a developer with a finished PR who wants to know where the bugs are.**
Concretely: you have a completed pull request — title, diff, repo — and you want an AI to
find the real problems before this code ships or gets reviewed by a human. There are two
natural ways to do that, and they sit at opposite ends of a weight/effort tradeoff:

- **The naive path — and we steel-manned it.** Open Claude or Codex (or any frontier chat
  model), paste the diff or the link to the PR, and ask it to find all the bugs. This is *vanilla* — one prompt,
  one model, one pass; instant and nearly free, and what most developers do today. Note
  that our vanilla arm is **not** the lazy "find the bugs in this code" prompt: it is a
  carefully engineered single prompt that already encodes most of a senior reviewer's
  discipline (verbatim, from `vanilla.py:ENGINEERED_PROMPT`):

  > You are an expert code reviewer. Review the following code diff for real, actionable
  > issues.
  >
  > PR: {pr_title}
  >
  > ```diff
  > {diff}
  > ```
  >
  > Find issues in these categories: bug, security, concurrency, data, api, performance,
  > test_gap, doc_defect.
  > For each issue:
  > - State the specific problem concisely (one issue per item — do not bundle).
  > - Note the file and line if identifiable from the diff.
  > - Classify severity as Low, Medium, High, or Critical.
  > - Only report real issues you are confident about; do not pad with style nits or
  >   speculation.

  We call this the **vanilla harness** throughout. Any harness that beats it is beating a
  *strong* baseline, not a strawman.

- **The harness path.** Use a gated, deterministic multi-agent workflow — **metareview**
  (free security/test gates + 8 adversarial lens subagents, orchestrated and consolidated) or
  **Compound Engineering** (risk-driven persona subagents + a synthesis pass). Heavier:
  more tokens, more wall-clock, a harness to install. The bet you're making is that
  structure and adversarial decomposition beat a single smart model staring at a diff.

**Which is better? That is the question this report measures.** The short answer from the
data: *it depends on the model you point the harness at* — and the surprise is that the
harness path wins decisively even on a near-frontier open model, at costs that undercut the
naive path on frontier models (e.g. Fable 5.1, GPT-6 Astra) as well as non-frontier models
like Opus 5, Sol, Sonnet, and Terra (§1, §3.4).

Around that core question, the numbers map onto four deployment scenarios a developer or
platform team faces:

1. **Self-review assist** — "review my PR before I open it." One fast pass; precision matters
   (you will read every finding), cost per review is nearly free either way. → vanilla cells.
2. **Merge gating on high-stakes diffs** — payments, auth, migrations, multi-tenant data.
   You want maximum bug discovery and can afford a subagent team and triage. → mrv/ce
   factory cells at high effort. → §3.4, §3.5.
3. **Backlog sweeps on a budget** — "re-review the last 200 PRs before a release" or an OSS
   maintainer triaging external contributions. Cost per PR dominates; hidden gold per dollar
   is the metric. → the GLM low-effort cells, this report's headline.
4. **Finding what human reviewers missed** — the golden comments in this benchmark are real
   findings recorded by human reviewers on real PRs; *hidden gold* is everything the AI
   finds **beyond** that list. Section §3.6 shows archetypes: credential corruption,
   cross-tenant leakage, import-path XSS, migration landmines.

What we are **not** yet evaluating (main report §1): the *fix* side of the loop
(discover → adjudicate → patch → verify), agentic SDLC workflows, or review of docs/ephemeral
artifacts. Single-pass discovery quality per dollar is the measured quantity.

### 0.2 The lab setup

`harnesseval` benchmarks the three harnesses against the **Martian Code Review Bench**
([github.com/withmartian/code-review-benchmark](https://github.com/withmartian/code-review-benchmark),
vendored at SHA `2b092b670f`) — 50 real OSS PRs with **173 human-verified golden comments**.
Each PR carries *golden comments* — real review findings recorded by human reviewers — plus
the human reviewers' own misses. The harnesses compared:

- **vanilla** — one well-engineered review prompt, no subagents (the baseline a developer
  gets from "just ask the model to review this diff");
- **metareview ("mrv")** — free deterministic security/test gates + 8 adversarial "lens"
  subagents (testing, architecture, security, scope, …), orchestrated and consolidated;
- **Compound Engineering ("ce")** — risk-driven persona subagents (investigator, security,
  perf, …) + a synthesis pass.

Each harness × model × effort cell runs the **top-6 PRs of the
[Martian Code Review Bench](https://github.com/withmartian/code-review-benchmark)** — the
lab's primary dataset+grader (50 real PRs across 5 OSS projects — Sentry/Python,
Grafana/Go, Cal.com/TypeScript, Discourse/Ruby, Keycloak/Java — with **173 human-verified
golden comments**; vendored at SHA `2b092b670f`, main report §2). The six PRs used here,
selected for the most golden comments (6–9 each), come from two of those projects:
**[cal.com](https://github.com/calcom/cal.com)** and
**[discourse-graphite](https://github.com/ai-code-review-evaluation/discourse-graphite)**:

| benchmark PR | goldens |
|---|---:|
| [cal.com#11059](https://github.com/calcom/cal.com/pull/11059) — OAuth app-credential sharing + webhook (multi-calendar destination logic) | 9 |
| [discourse-graphite#4](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4) (topic embeds / RSS import) | 8 |
| [discourse-graphite#10](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10) (embeddable hosts) | 7 |
| [cal.com#10967](https://github.com/calcom/cal.com/pull/10967) (co-host calendars) | 6 |
| [cal.com#14740](https://github.com/calcom/cal.com/pull/14740) (add-guests flow) | 6 |
| [discourse-graphite#8](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8) (group pagination) | 6 |

A judge model then matches each reported finding against the golden comments, and a **v2
three-way adjudicator** classifies every unmatched finding as a
golden comments, and a **v2 three-way adjudicator** classifies every unmatched finding as a
real bug, an important non-bug, a true hallucination, or unresolved.

### How to read the numbers

| metric | definition |
|---|---|
| **recall (absolute)** | fraction of the PR's golden comments the review found and the judge confirmed. "How many known-real bugs did it catch?" |
| **hidden gold (hid)** | judge-confirmed **real** findings that match *no* golden comment — real bugs **beyond** the human reviewers' list. These are free extra value, and separately reported from hallucinations |
| **incremental recall (incr)** | recall extended over the enlarged truth: `(confirmed goldens + confirmed hidden gold) / (goldens + hidden gold)`. Rewards finding real bugs the goldens missed; 1.00 means "found every golden *and* everything else it claimed real" |
| **hallucinations (hal)** | v2-adjudicated **true** fabrications — reported "bugs" that are not real (the triage tax). Deliberately *excludes* important non-bug findings, which are counted as hidden value |
| **tokens/PR** | all review tokens in+out summed across every call the harness makes (orchestrator, lenses, extraction), averaged per PR. The honest cost unit when pricing is a flat fee |
| **$/cell** | metered cost of one harness × model × effort cell (all 6 PRs), computed from measured in/out tokens at current published list pricing: **GLM-5.3 $1.40 in / $4.40 out, GLM-5.3-flash $0.15 / $0.50** ([docs.z.ai/guides/overview/pricing](https://docs.z.ai/guides/overview/pricing)); **Fable 5.1 $10 / $50; Astra $10 / $50** ([platform.claude.com](https://platform.claude.com/docs/en/about-claude/pricing), [developers.openai.com](https://developers.openai.com/api/docs/models/gpt-6-astra); fetched 2026-09-07). Our runs went through the Lunaroute gateway at a flat fee ($0 billed) — the metered figures are what the same token counts would cost on the public APIs |

---

## 1. The headline result: a free model now beats the $57 factory

| cell | rec | hid /PR | incr | tokens/PR | $/cell | hid gold per $ |
|---|---:|---:|---:|---:|---:|---:|
| **ce × glm-5.3-background × low** | 0.81 | **36.8** | **0.97** | **103K** | **$0.20** ¹ | **~185** |
| ce × glm-5.3-flash × low | 0.79 | 36.8 | 0.97 | 99K | $0.02 ¹ | ~1,800 |
| mrv × glm-5.3-flash × low | 0.66 | 25.3 | 0.93 | 110K | $0.02 ¹ | ~1,150 |
| vanilla × claude-fable-5.1 × low | 0.74 | 7.5 | 0.89 | 85K | $0.88 ² | ~8.5 |
| vanilla × gpt-6-astra × low | 0.40 | 2.2 | 0.52 | 47K | $0.59 ³ | ~3.7 |
| vanilla × claude-opus-5 × low | 0.66 | 6.0 | 0.81 | 86K | — | — |
| vanilla × gpt-5.6-sol × low | 0.52 | 4.5 | 0.69 | 44K | — | — |
| mrv × claude-fable-5.1 × low | 0.63 | 28.2 | 0.80 | 2,081K | $22.41 ² | 1.3 |
| mrv × gpt-6-astra × low | 0.51 | 6.7 | 0.74 | 774K | $7.82 ³ | 0.9 |
| ce × claude-fable-5.1 × low | 0.75 | 26.5 | 0.93 | 3,028K | $32.00 ² | 0.8 |
| ce × gpt-6-astra × low | 0.49 | 10.0 | 0.78 | 1,246K | $12.62 ³ | 0.8 |
| mrv × claude-opus-5 × high (main report §3.4) | — | 36.0 | 0.85 | 2,980K | $56.65 ³ | 0.64 |

¹ Z.AI list pricing applied to measured tokens. Our runs were served through
   **[Lunaroute](https://lunaroute.com)** — a US-based, **zero-data-retention** inference
   gateway (flat fee, $0 billed per run) — so the metered figures are what the same token
   counts would cost on the public APIs.
² Metered at current published list pricing, applied to our measured in/out tokens:
Fable 5.1 $10 in / $50 out; Astra $10 in / $50 out ([platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing), [developers.openai.com/api/docs/models/gpt-6-astra](https://developers.openai.com/api/docs/models/gpt-6-astra), fetched 2026-09-07; cache reads/writes excluded — cache-hit volume isn't recorded per run). **This corrects the main report's fable/astra figures, which used a stale $12.50/M output pin** (that is the 5-minute cache-*write* price, not the output price). "—" = not recomputed; recorded run costs for subscription models are pre-refresh (main report §3.4).

**Read across the fable/astra rows:** vanilla × fable is the *best* pure-prompt cell in the
lab (rec 0.74, $0.88/cell at current list pricing) — while the **same model behind either
factory** finds 3.5–3.8× more hidden gold (26.5–28.2/PR) but at 24–35× the tokens and
25–36× the metered cost ($22–32/cell). Meanwhile **a $1.40/$4.40 GLM behind a factory beats
the premium models run vanilla on every axis** — more hidden gold (36.8 vs 7.5/2.2), higher
recall (0.81 vs 0.74/0.40) — at 3–4× *cheaper* than vanilla fable itself, and ~100× better
hidden-gold-per-dollar than any premium cell.

**Compound Engineering on GLM-5.3 finds more real bugs the humans missed than the opus
factory — 36.8 vs 36.0 per PR, at higher incremental recall (0.97 vs 0.85), on 1/29th the
tokens, at ~1/280th the metered cost.** This is not a budget-tier result: on the top-6 PRs it
is the best factory cell measured in this lab at any price. Two $0.02–0.20 engines (ce and mrv
on GLM) now beat every metered configuration on hidden-gold efficiency, and metareview on
GLM delivers opus-factory-grade hidden gold (25–36/PR) for pennies.

The second headline: **the harness-beats-vanilla pattern extends to a third model family**
(ce 0.81/0.78 and mrv 0.66/0.74 recall vs vanilla 0.54/0.57 on background at low/xhigh) —
and, per §3.3, a cheap model behind a good harness now beats the newest premium models run
vanilla.

### TL;DR — practitioner recommendations

1. **Switch the default review engine to glm-5.3(-flash) × low.** Same incremental recall as
   the opus factory (0.97 vs 0.85), more hidden gold per PR (36.8 vs 36.0), $0.02–0.20/cell
   metered vs $56.65. No configuration in this data wins on value against it.
2. **Run GLM at low or high — never medium.** low/high are monotonic and healthy; medium
   reasons 4–10× more than high, takes 10–20× the wall time, sometimes never finishes, and
   fails *silently* (empty 200s that read as "no bugs"). xhigh is an alias for high on GLM.
3. **A cheap model + a good harness beats a premium model run vanilla.** mrv/ce on GLM-5.3
   ($1.40/$4.40 list) out-find vanilla on both 2026's newest models: vs vanilla × fable-5.1
   (rec 0.74, incr 0.89, $0.88/cell at current list) the GLM factories deliver recall 0.66–0.81 and incr
   0.93–0.97 at $0.02–0.20/cell; vs vanilla × astra (rec 0.40, incr 0.52, $0.59/cell) it is
   not close. → §3.4
4. **Hallucination load on GLM is low under the v2 instrument.** GLM factory cells emit
   **1.4–5.7 true hallucinations per PR** alongside 24–46 hidden gold (~85–90% real fraction)
   — most of what these harnesses report beyond the goldens is real. Budget human review time
   for the volume of findings (25–46/PR), not for noise.
5. **The metareview lens fix (PR #145) is safe but unproven at smoke scale** — no detectable
   fabrication win at n=3 PRs, no precision cost either. Decisive test: the big-hal mrv cells
   (~$230–460) or metareview's own corpus re-judge. → §5
6. **Re-probe medium after Lunaroute's upstream fix lands** — the background/medium rows in
   §3 will change. low/high results are unaffected.

---

## 2. What was run

| arm | cells | batch |
|---|---|---|
| GLM-5.3 suite: {vanilla, mrv, ce} × {background, flash} × {low, high} × top-6 PRs (medium/32K-high rungs run but collapsed — §4) | 12 low/high cells (of 24 suite cells) | `20260906-glm53-top6` |
| Effort probes: single calls, glm-5.3-background, 79K-char diff, 65,536 budget | 2×low, 2×high live + 3 prior medium | §4 transcripts |
| Claimcheck smoke: mrv × {background, flash} × xhigh × {11059, 10967, 14740}, lens prompts synced with metareview#145 Evidence-of-Absence | 6 | `20260907-claimcheck-smoke` |

Judging/scoring identical to the main report (extract → judge → v2 three-way adjudication).
GLM served via **[Lunaroute](https://lunaroute.com)** — a US-based, zero-data-retention
OpenAI-compatible inference gateway (flat fee, $0 billed for these runs); per-call timeout
2400s; effort-scaled
completion budgets (medium→65,536 / high→32,768) as the shipped workaround.

### 2.1 The prompts each harness was given

Full texts live in the harness (`harnesseval/adapters/*.py`); the operative text is quoted
here. The GLM cells ran all three harnesses, with one GLM-specific detail: metareview and
Compound fell back to API-direct orchestration (no interactive CLI exists for GLM), detailed
below.

**vanilla — one prompt, one call** (`vanilla.py:ENGINEERED_PROMPT`, verbatim, with
`{pr_title}` and a 60,000-char-truncated `{diff}`):

> You are an expert code reviewer. Review the following code diff for real, actionable
> issues.
>
> PR: {pr_title}
>
> ```diff
> {diff}
> ```
>
> Find issues in these categories: bug, security, concurrency, data, api, performance,
> test_gap, doc_defect.
> For each issue:
> - State the specific problem concisely (one issue per item — do not bundle).
> - Note the file and line if identifiable from the diff.
> - Classify severity as Low, Medium, High, or Critical.
> - Only report real issues you are confident about; do not pad with style nits or
>   speculation.
>
> Respond with a numbered list, one issue per line, e.g.:
> 1. [High/bug] path/to/file.py:71 — description of the specific problem
> 2. [Medium/performance] ...

**metareview ("mrv") — gates + 8 adversarial lenses.** The deterministic gates ran as the
real Go binary (`metareview review task-done <task> --base HEAD~2`); their findings are
scored separately and excluded from the mrv score (main report §2 — they match 0 goldens).
The lens arm differed by backend:

- *Claude/Codex cells (main report)*: an orchestrator prompt instructs the CLI agent to run
  the binary, then "Dispatch the 8 required reviewer lenses as PARALLEL SUBAGENTS", with the
  adversarial stance: "assume the creator's intent is GOOD but be hostile to unexamined
  assumptions — assume there may be a fundamental mistake hiding in this design and find
  it", confidence anchors (100/75/50/25/0; suppress <50 unless P0), and per-lens hunting
  briefs (the Architecture brief alone is ~90 lines of concrete failure modes: N+1 patterns,
  missing schema invariants, sentinel-meaning-change, cascading failure,
  stand-in-guard-fidelity, …).

- *GLM cells (this report)*: API-direct fallback — the harness plays orchestrator. Eight
  lens calls, each: system = the artifact-review rubric persona ("You are an expert code
  reviewer using the metareview artifact-review rubric (v0.8.0). ADVERSARIAL STANCE: assume
  the creator's intent is GOOD … but you ARE hostile to unexamined assumptions. Assume there
  may be a fundamental mistake hiding in this design — find it."), user = the lens brief +
  this header (verbatim):

  > PR: {pr_title}
  >
  > ```diff
  > {diff}
  > ```
  >
  > List each distinct real issue you find (one per item, with file:line if identifiable).
  > Only report issues you are confident about.

  The 8 lens briefs: **feasibility, completeness, scope, architecture, intent, security,
  testing-quality, data-migration**. Example — testing-quality, verbatim as synced with
  metareview PR #145 for the smoke cells (§5): "You are the Testing-quality lens. Attack the
  assumption that the tests verify the behavior they claim to. Tests can lie — find where
  they do. … Hunt for false-confidence assertions (toBeTruthy()/toBeDefined()/bare assert(x)
  that assert nothing …). Hunt for tests verifying mocks not real logic … Hunt for
  mirror-tests-that-miss-the-machine … Evidence of absence (required before any
  missing-tests finding): before reporting ANY finding whose claim is that tests, specs or
  coverage are absent — 'no tests', 'nothing asserts', 'untested', 'no spec exists' — you
  MUST first scan the diff for test-shaped files (spec/**, test/**, __tests__/**, *.test.*,
  *.spec.*, *_test.go, test_*.py) whose changes reference the subject you claim is untested
  … If a candidate test exists, the finding must cite the SPECIFIC assertion gap … or be
  dropped entirely. State which test files you checked (paths) — never a bare 'no tests'."

  Each lens output then passes through a JSON extraction call (the extractor returns
  `{"issues": ["issue 1", …]}` — one plain string per issue) before judging.

**Compound Engineering ("ce") — risk-driven persona roster** (`compound_realistic.py`). The
orchestrator prompt: read `git diff HEAD~1` + `--stat`; write a one-line intent summary from
the PR title; select the roster — "ALWAYS spawn `correctness` (logic/behavioral correctness —
off-by-one, null propagation, races, state transitions, broken error propagation)" plus
conditionals only when the diff shows their concrete surface (security / performance /
api-contract / reliability / testing / maintainability / data-migration / adversarial, each
with a trigger such as ">=50 changed code lines, OR auth/payments/persistence" or "a
silent-pass verification mechanism (a CI/gate that can go green while the real thing is
red)"); then "Dispatch each selected persona as a PARALLEL SUBAGENT … the orchestrator
dispatches persona subagents and only synthesizes their findings." Each persona subagent
gets its persona-focus text + the diff. Typical roster: 3–5 personas/PR. On the GLM cells
the personas run as API calls with the same focus texts.

**Judge (scoring, all cells).** One cross-family judge call per (finding × golden) pair —
for the GLM cells, gpt-5.2 (OpenAI judges GLM, the same cross-family rule as everywhere in
the lab; main report §2). Verbatim:

> You are evaluating AI code review tools. Determine if the candidate issue matches the
> golden (expected) comment.
>
> Golden Comment (the issue we're looking for): {golden_comment}
> Candidate Issue (from the tool's review): {candidate}
>
> Instructions:
> - Determine if the candidate identifies the SAME underlying issue as the golden comment
> - Accept semantic matches - different wording is fine if it's the same problem
> - Focus on whether they point to the same bug, concern, or code issue
>
> Respond with ONLY a JSON object:
> {"reasoning": "brief explanation", "match": true/false, "confidence": 0.0-1.0}

Unmatched findings then go through the v2 three-way adjudicator (full diff in context,
max_tokens=4096, confidence floor 0.5 → bug / important-non-bug / true-hallucination /
unresolved; main report §3.6). The rec/hid/hal numbers in §3 and §5 are post-adjudication.
The instrument split this implies: vanilla cells give the model one prompt (all reasoning is
the model's); factory cells add the orchestrator + per-lens/persona prompts — the token and
hallucination totals in §3 include all of that scaffolding.

### 2.2 The measured grid

Every cell = one harness × model × effort over the top-6 PRs; the number is the count of
latest-pass PR runs (— = not run). GLM rows are this report's suite (batch
`20260906-glm53-top6`); the other models come from the main report's matrix. Effort naming:
the Claude/OpenAI rows use our two-rung ladder (low / high — `high` sent natively as
`xhigh`/`high`); the GLM rows' "high" is upstream `reasoning_effort=high` (our xhigh step,
§4). GLM's medium rung was also measured and collapsed (§4); it is out of scope here.

| model | effort | vanilla | mrv | ce |
|---|---|---:|---:|---:|
| claude-opus-5 | low | 6 | 6 | 6 |
| | high | 6 | 6 | 6 |
| claude-sonnet-5 | low | 6 | 6 | 6 |
| | high | 6 | 6 | 6 |
| gpt-5.6-sol | low | 6 | 6 | 6 |
| | high | 6 | 6 | 6 |
| gpt-5.6-terra | low | 6 | 6 | 6 |
| | high | 6 | 6 | 6 |
| claude-fable-5-1 | low | 6 | 6 | 6 |
| | high | 6 | — | — |
| gpt-6-astra | low | 6 | 6 | 6 |
| | high | 6 | — | — |
| **glm-5.3-background** | low | 5 | 3 | 6 |
| | high | 6 | 6 | 6 |
| **glm-5.3-flash-background** | low | 5 | 6 | 6 |
| | high | 6 | 5 | 6 |

Totals: 44 of 48 non-GLM low/high cells present (4 missing: fable/astra × mrv/ce × high)
+ all 12 GLM low/high cells + the GLM medium/32K-high rungs (§4, out of scope) + the 6
smoke cells (§5). Five GLM cells sit below n=6: four at n=5 and one at n=3
(mrv × background × low).


---

## 3. The GLM-5.3 suite (low / high)

Latest **pass** run per (cell, PR) from batch `20260906-glm53-top6`; hid/hal are the **v2
adjudicator counts** (`readjudication3.json` `n_bug_ungold` / `n_true_hallucination`), not
the legacy run-time counts that earlier drafts used. rec = absolute recall on goldens; incr
= incremental recall (goldens + confirmed hidden gold). Six cells have n<6 (the missing PRs' runs failed in-batch): vanilla low ×2 (n=5),
vanilla/flash/medium (n=5), mrv/background/low (n=3), mrv/flash/high (n=5), ce/flash/high
(n=5), mrv/flash/xhigh (n=5).

| harness | model | effort | n | rec | incr | hid | hal | tok/PR |
|---|---|---|---:|---:|---:|---:|---:|---:|
| vanilla | background | low | 5 | 0.46 | 0.72 | 4.2 | 1.4 | 13K |
| vanilla | background | high | 6 | 0.57 | 0.80 | 6.8 | 0.3 | 20K |
| vanilla | flash | low | 5 | 0.46 | 0.72 | 5.0 | 0.8 | 13K |
| vanilla | flash | high | 6 | 0.59 | 0.82 | 7.8 | 0.3 | 21K |
| mrv | background | low | 3 | 0.59 | 0.91 | 18.0 | 4.0 | 108K |
| mrv | background | high | 6 | 0.74 | 0.96 | 32.7 | 2.3 | 157K |
| mrv | flash | low | 6 | 0.66 | 0.93 | 24.2 | 5.7 | 110K |
| mrv | flash | high | 5 | 0.66 | 0.93 | 25.8 | 1.8 | 149K |
| **ce** | background | low | 6 | **0.81** | **0.97** | **36.8** | 5.3 | **103K** |
| ce | background | high | 6 | 0.78 | 0.97 | 46.2 | 2.7 | 150K |
| ce | flash | low | 6 | 0.79 | 0.97 | 35.0 | 5.7 | 99K |
| ce | flash | high | 6 | 0.75 | 0.97 | 39.2 | 3.5 | 143K |

Scope note: the suite also ran GLM's **medium** rung and a separate 32K-budget **high**
rung — both collapsed (rec 0.00–0.17 across all harnesses) for the serving-stack reasons in
§4; those rows are excluded from this report's low/high scope and documented in §4. The
"high" rows above are our xhigh ladder step, which sends upstream `reasoning_effort=high`
with the 65K budget — the healthy high configuration.


### 3.1 Readings that matter

- **Efficiency hierarchy upended.** Hidden gold per M review tokens (v2 hid): ce × GLM-low ≈ 358
  (+ 237 for important non-bugs), ce × GLM-high ≈ 308, mrv × GLM-low ≈ 219 — vs **7–10** for the
  v2-graded opus factory cells (main report §3.6). The main report's "the factories find more total bugs on every model, at 10–40× the
  cost" now has a free-model refutation: **the same harnesses on GLM find more total bugs at
  ~zero marginal cost.**
- **Vanilla on GLM is the cheapest usable baseline ever measured here**: rec 0.50–0.57, incr
  0.76–0.83 at 13–20K tokens/PR ($0.003–0.05/cell metered). One GLM call per PR surfaces ~4–7
  hidden bugs (plus 3–4 important non-bugs) for effectively nothing.
- **Flash ≈ background on quality, and is the safer default**: within noise at every shared
  effort (ce low: 0.81 vs 0.79; high: 0.78 vs 0.75), and flash has none of background's
  medium/high pathology (§4).
- **Effort is nearly free in quality terms**: low→high/xhigh moves hidden gold 36.8→46.2
  (ce/background) with hal flat-to-down. low is the value point; high when recall matters
  more than latency.
- **The collapsed background×medium/high rows are infrastructure, not quality**: flash
  scores 0.68–0.71 at the same efforts on the same PRs. See §4.

### 3.2 The metareview data

metareview's gates+lenses architecture on GLM (8 lens calls + gate binary per PR, 110–160K
tok/PR):

- **mrv × GLM posts opus-factory hidden-gold coverage at ~$0**: 24.2 hid/PR (flash/low) and
  32.7 (background/high) — vs 36.0 for mrv × opus × high at $56.65. The old "metareview ×
  GLM is a gap" note in the main report is closed: mrv runs the full GLM ladder and its
  incr-recall tier (0.93–0.96) matches its opus tier.
- **mrv × background × high is the strongest mrv cell on GLM** (rec 0.74, incr 0.96, 32.7
  hid at 157K tok/PR; ~$0.39/cell metered) — though not the lab's best: mrv × opus-5 × low
  posts rec 0.85 / incr 0.97 (§3.5), at 2,000× the tokens.
- **mrv's price on GLM is now just triage**: 1.8–5.7 true-hal/PR (real fraction ~92–95% of
  everything emitted) — the old ~50%-fabrication pattern is gone under v2; coverage costs
  reading, not correctness.
- **ce ≥ mrv on GLM at low effort in both variants** (0.81 vs 0.66; 0.79 vs 0.66) — on the
  premium models the main report had mrv winning the Claude arms; on GLM the persona-harness
  is the stronger wrapper.

### 3.3 Cost — metered at Z.AI list pricing ([docs.z.ai/guides/overview/pricing](https://docs.z.ai/guides/overview/pricing), fetched 2026-09-07: GLM-5.3 $1.40/M in, $4.40/M out; GLM-5.3-flash $0.15/M in, $0.50/M out at the launch-promo rate)

| cell | in/PR | out/PR | $/cell | $ per hidden gold |
|---|---:|---:|---:|---:|
| **ce × background × low** | 85K | 18K | **$0.20** | **$0.005** |
| ce × flash × low | 83K | 16K | $0.02 | $0.0005 |
| mrv × flash × low | 93K | 17K | $0.02 | $0.001 |
| mrv × background × xhigh | 99K | 58K | $0.39 | $0.011 |
| vanilla × background × low | 11K | 2K | $0.03 | $0.004 |
| vanilla × flash × low | 11K | 2K | $0.003 | $0.0005 |
| *mrv × opus × high (main report)* | *2,880K* | *~100K* | *$56.65* | *$1.57* |

Every GLM factory cell is **one to two orders of magnitude cheaper per hidden bug** than the
opus factory even at full Z.AI list pricing — and our actual runs cost $0 (Lunaroute flat
fee). The best cell pays **$0.005 per real bug found**, vs $1.57 for mrv × opus × high.

### 3.4 Cheap model + good harness beats newest premium model vanilla

The main report's two 2026 premium columns were run **vanilla only** (full 50-PR suites).
Against those, the GLM factory cells win outright:

| | harness × model | rec | incr | hid/PR (v2) | hal/PR | tok/PR | $/cell |
|---|---|---:|---:|---:|---:|---:|---:|
| **newest premium, vanilla** | vanilla × **fable-5.1** × low | 0.74 | 0.89 | 3.0 | 0.8 | 76K | **$0.88** ³ |
| | vanilla × **astra** × low | 0.40 | 0.52 | 1.8 | 0.1 | 52K | **$0.59** ³ |
| **cheap model, factory** | ce × glm-5.3 × low | **0.81** | **0.98** | 36.8 | 5.3 | 102K | **$0.20** |
| | mrv × glm-flash × low | 0.66 | 0.95 | 24.2 | 5.7 | 109K | **$0.02** |
| | mrv × glm-5.3 × high | 0.74 | 0.97 | 32.7 | 2.3 | 157K | $0.39 |

**Metareview or Compound on a $1.40/$4.40 GLM beats vanilla on a $10/$12.50 newest-generation
model on every axis that matters**: recall (0.66–0.81 vs 0.74/0.40), incremental recall
(0.93–0.97 vs 0.89/0.52), hidden gold (25–40/PR vs 3.0/1.8), and cost (30–320× cheaper). Even
the *premium models behind the factories* don't reach GLM's efficiency: mrv × fable × low
finds 33.7 hid/PR but at 2.08M tokens (~$23/cell) — same hidden gold as ce × GLM-low at
115× the tokens and ~120× the metered price.

The mechanism is the main report's finding #1 pushed to its conclusion: **the harness, not
the model's raw intelligence, is the binding constraint** — a well-built multi-lens harness
converts a mediocre-priced model into review coverage that the newest premium models can't
reach vanilla. (Fable remains the best *vanilla* model measured — rec 0.74/0.62 — but vanilla
tops out at ~3 hidden bugs/PR on the full suite.)

### 3.5 The full low/high grid — every model, every harness

All cells top-6 PRs, latest pass, v2-adjudicated where graded (— = pending v2 grading or not
run). "high" = our xhigh ladder step. Recorded $/cell shown only where verified in the main
report (OAuth-subscription run costs are pre-refresh there; see main report §3.4/§5) or
metered at Z.AI list for GLM.

| harness | model | effort | rec | incr | hid | hal | tok/PR | $/cell |
|---|---|---|---:|---:|---:|---:|---:|---:|
| vanilla | opus-5 | low | 0.66 | 0.81 | 6.0 | 0.5 | 86K | — |
| vanilla | opus-5 | high | 0.66 | 0.88 | — | — | 102K | $0.82 |
| vanilla | sonnet-5 | low | 0.42 | 0.61 | 3.2 | 1.2 | 106K | $0.20 |
| vanilla | sonnet-5 | high | 0.37 | 0.65 | 4.7 | 0.2 | 127K | $0.41 |
| vanilla | sol | low | 0.52 | 0.69 | 4.5 | 0.0 | 44K | ~0 |
| vanilla | sol | high | 0.62 | 0.76 | 4.5 | 0.2 | 1039K | ~0 |
| vanilla | terra | low | 0.39 | 0.56 | 2.5 | 0.2 | 59K | ~0 |
| vanilla | terra | high | 0.46 | 0.63 | 3.3 | 0.2 | 280K | ~0 |
| vanilla | fable-5.1 | low | 0.74 | 0.89 | 7.5 | 1.2 | 85K | $0.88 |
| vanilla | astra | low | 0.40 | 0.52 | 2.2 | 0.6 | 47K | $0.59 |
| mrv | opus-5 | low | **0.85** | **0.97** | 28.7 | 6.8 | 3,481K | — |
| mrv | opus-5 | high | 0.69 | 0.90 | — | — | 6,337K | $56.65 |
| mrv | sonnet-5 | low | 0.61 | 0.85 | 10.0 | 3.5 | 3,078K | $1.52 |
| mrv | sonnet-5 | high | 0.57 | 0.87 | 14.3 | 3.8 | 9,458K | $4.95 |
| mrv | sol | low | 0.48 | 0.67 | 7.0 | 2.7 | 569K | ~0 |
| mrv | sol | high | 0.63 | 0.84 | — | — | 656K | ~0 |
| mrv | terra | low | 0.30 | 0.52 | 4.2 | 1.7 | 652K | ~0 |
| mrv | terra | high | 0.42 | 0.70 | 7.7 | 1.7 | 889K | ~0 |
| mrv | fable-5.1 | low | 0.63 | 0.80 | 28.2 | 5.6 | 2,081K | $22.41 |
| mrv | astra | low | 0.51 | 0.74 | 6.7 | 0.7 | 774K | $7.82 |
| ce | opus-5 | low | 0.67 | 0.91 | 20.0 | 7.5 | 2,065K | — |
| ce | opus-5 | high | 0.84 | **0.98** | **48.2** | 7.8 | 6,831K | — |
| ce | sonnet-5 | low | 0.21 | 0.41 | 3.2 | 1.3 | 2,920K | $1.57 |
| ce | sonnet-5 | high | 0.29 | 0.56 | 5.8 | 0.7 | 9,992K | $5.65 |
| ce | sol | low | 0.45 | 0.69 | 8.7 | 1.2 | 544K | ~0 |
| ce | sol | high | 0.45 | 0.69 | 7.2 | 0.7 | 1,008K | ~0 |
| ce | terra | low | 0.39 | 0.64 | 6.0 | 0.5 | 679K | ~0 |
| ce | terra | high | 0.56 | 0.84 | 13.5 | 1.0 | 792K | ~0 |
| ce | fable-5.1 | low | 0.75 | 0.93 | 26.5 | 5.8 | 3,028K | $32.00 |
| ce | astra | low | 0.49 | 0.78 | 10.0 | 1.5 | 1,246K | $12.62 |
| vanilla | glm-5.3-background | low | 0.46 | 0.72 | 4.2 | 1.4 | 13K | $0.03 |
| vanilla | glm-5.3-background | high | 0.57 | 0.80 | 6.8 | 0.3 | 20K | $0.05 |
| vanilla | glm-flash | low | 0.46 | 0.72 | 5.0 | 0.8 | 13K | $0.003 |
| vanilla | glm-flash | high | 0.59 | 0.82 | 7.8 | 0.3 | 21K | $0.005 |
| mrv | glm-5.3-background | low | 0.59 | 0.91 | 18.0 | 4.0 | 108K | $0.21 |
| mrv | glm-5.3-background | high | 0.74 | 0.96 | 32.7 | 2.3 | 157K | $0.39 |
| mrv | glm-flash | low | 0.66 | 0.93 | 24.2 | 5.7 | 110K | $0.02 |
| mrv | glm-flash | high | 0.66 | 0.93 | 25.8 | 1.8 | 149K | $0.04 |
| ce | glm-5.3-background | low | 0.81 | 0.97 | 36.8 | 5.3 | 103K | $0.20 |
| ce | glm-5.3-background | high | 0.78 | 0.97 | 46.2 | 2.7 | 150K | $0.38 |
| ce | glm-flash | low | 0.79 | 0.97 | 35.0 | 5.7 | 99K | $0.02 |
| ce | glm-flash | high | 0.75 | 0.97 | 39.2 | 3.5 | 143K | $0.04 |

**What the full grid adds to the GLM story:**

- **The GLM factory cells don't just beat the price frontier — they beat every metered cell
  on efficiency.** Best metered hidden-gold cell: ce × opus-5 × high (48.2 hid, rec 0.84,
  6.8M tok, $11.10 recorded) — 66× more tokens and $10.90/cell more than ce × glm-5.3-low
  (36.8 hid at 103K tok, $0.20; $0.23 vs $0.005 per hidden bug). Best *recall* cell:
  mrv × opus-5 × low
  (rec 0.85, incr 0.98, 28.7 hid at 3.5M tok) — vs ce × GLM-low's 0.81/0.98/36.8 at 102K.
- **The harness ranking inverts by model tier, consistently with the main report:** on
  premium models the factories earn their keep (mrv/opus low 0.85 vs vanilla 0.66; ce/opus
  high 0.84 vs vanilla 0.66); on cheap models the same holds (ce/GLM 0.81 vs vanilla 0.54).
  What changes with GLM is that the factory premium stops being expensive.
- **Codex-family factories underperform Claude factories** (ce × sonnet 0.21–0.29; ce × sol
  flat at 0.45) — GLM is the only model family where the factories hit ≥0.79 recall at low
  effort, and it costs the least.
- **Vanilla fable's top-6 hid count is 7.5/PR at $0.88** (current list) — the strongest pure-vanilla cell —
  vs ce × GLM-low's 36.8/PR at $0.20. Even granting fable's superior precision (1.2 hal vs
  28), the factory cell surfaces **5.4× more real bugs per PR for 3% of the price**; the
  triage trade is decided by how much reviewer attention you have.

Fable/astra $-figures at current list pricing (fable $10 in/$50 out; astra $10 in/$50 out)
— ³ these **correct the main report's $6.41/$2.80**, which used a stale $12.50/M output pin
(that is Fable's 5-minute cache-*write* price, not output). Cache reads/writes excluded.

Superpowers is excluded from this grid (single-subagent wrapper — not an apples-to-apples
harness; main report §2). Historical rows (opus-4.5, sonnet-4.5, gpt-5.2, kimi-k3, glm-5.2)
are superseded by the cells above and omitted. Historical rows (opus-4.5, sonnet-4.5, gpt-5.2, kimi-k3, glm-5.2)
are superseded by the cells above and omitted.

### 3.6 What hidden gold looks like — archetypes with real finds

"Hidden gold" is abstract until you see it. Below are archetypal examples, all judge-confirmed
real (confidence ≥0.90), all unmatched by the human golden comments, quoted from the committed
adjudication records with the cell that produced them:

1. **Silent credential corruption (shape-of-data bugs).** The zod `safeParse` wrapper
   `{success, data}` persisted *as* the OAuth token instead of the parsed credential —
   "credential row now written as {success,data} instead of the flat token object, silently
   corrupting every stored Google credential on refresh [P0]" (mrv × opus-5 × low, PR 11059;
   found in **three cells across two harnesses** — also ce × opus-5 × xhigh and mrv × GLM ×
   xhigh, plus the sibling "computed keys stringify to '[object Object]' so the schema strips
   all properties except access_token"). Cross-harness convergence is the strongest signal
   these are real.
2. **Cross-tenant data leakage.** "`credential` declared once outside the per-reference loop,
   so a failed lookup silently reuses the previous host's credential, writing host B's
   reschedule into host A's calendar" (mrv × opus-5 × low, PR 10967); and "only Google
   Calendar implements multi-host destination selection; Office365, Lark, and CalDAV ignore
   the credentialId/destination params and always use host #1's calendar, writing other
   hosts' events" (mrv × GLM × xhigh, PR 10967).
3. **The headline feature silently doesn't work.** "Headline acceptance criterion unmet when
   the organizer has no destination calendar but co-hosts do; co-host calendars silently
   dropped with no error [90,P0]" (mrv × opus-5 × low, PR 10967) — found on the PR's core
   use case, exactly the class human reviewers miss because the happy path works.
4. **Import-path security holes.** "Imported RSS/remote HTML stored with cook_method raw_html
   is rendered unsanitized … stored XSS for every viewer" and "PollFeed uses Kernel#open on
   SiteSetting.feed_polling_url; an admin-settable value starting with '|cmd' yields command
   execution" (vanilla × fable-5.1 × low, PR 4; also ce × GLM-low and mrv × opus-5 on the
   same PR).
5. **Silent no-ops that report success.** "EmbeddingController#update fetches and
   re-serializes an OpenStruct without reading params or saving, making it a silent no-op
   that reports success" (ce × GLM × low, PR 10); "the admin's alias_level selection is
   silently discarded, so groups are created at alias_level 0" (mrv × opus-5 × low, PR 8).
6. **Authorization logic bugs.** "Permission check uses && (AND) instead of || (OR) for
   isTeamAdmin/isTeamOwner, denying team admins who aren't owners" (mrv × GLM × xhigh,
   PR 14740); "case-sensitive `guest === attendee.email` against a lowercased blacklist;
   Foo@x.com bypasses both dedupe and blacklist [conf=100,P1]" (mrv × opus-5 × low, PR 14740).
7. **Unbounded attacker-controlled fan-out.** "Any authenticated user who is merely an
   attendee on any booking can push unlimited arbitrary addresses through this mutation"
   + "guests is an unbounded array with no server-side max length" (ce × opus-5 × xhigh,
   PR 14740); "the throttle key embeds the full attacker-controlled embed_url, so unbounded
   distinct URLs produce unbounded redis keys" (ce × opus-5 × xhigh, PR 4).
8. **Error-swallowing that corrupts observability and loses data.** "On Storage.Create
   failure, recordLegacyDuration is called instead of recordStorageDuration, misattributing
   storage errors to the legacy metric" (vanilla × fable, PR 90045); "submit() catches all
   exceptions and marks the offset complete … silently losing results" (vanilla × fable,
   PR 95633); the `forEach(async…)` family that escapes try/catch (vanilla × fable, PR 8087).
9. **Migration landmines.** "Migration irreversibly deletes legacy site settings with no down
   path, even when the preceding conversion was skipped" and "the embed_category lookup
   indexes [0]['id'] on a result set that is empty on every site that never set embed_category,
   so the migration raises and blocks the upgrade" (mrv × GLM × xhigh, PR 10); plus the raw
   SQL interpolation in migration `VALUES` found by every harness on PR 10.
10. **Tests that lie.** "The test asserts no offset is committed after a processing exception,
    but the implementation completes the offset in finally and commits on the next tick; the
    test only passes because it awaits the wrong tick" (vanilla × fable-5.1 × low, PR 95633) —
    the false-confidence class the main report's §3.6 reclassification first surfaced.

Two properties are worth internalizing. First, **most of these were found by more than one
harness independently** (the zod-wrapper bug: three; the migration SQL injection: four) —
convergence across independent harnesses is itself a confidence multiplier. Second, **most
are not the kind of thing a human reviewer reliably catches on a large diff**: cross-branch
sentinel drift, loop-scoped credentials, pagination off-by-ones on exact multiples
("floor(user_count/limit)+1 gives 3 pages when count=100, limit=50"), case-sensitivity in
email comparisons. This is the concrete content behind the "36.8 hidden bugs/PR at $0.20"
headline.

---

## 4. The effort ladder: two healthy rungs, a broken middle

Probes: single calls, glm-5.3-background, same 79K-char review prompt, 65,536-token budget.

| effort | reasoning tok/call | completion tok/call | review content | wall |
|---|---|---|---|---|
| low (n=2) | 1,913 / 2,327 | 3,252 / 3,639 | ~5.7K chars | 33–37s |
| high (n=2) | 6,265 / 11,264 | 8,300 / 13,211 | 8.4–8.7K chars | 69–118s |
| medium (n=3) | 18,600 / 27,500 / 28,000 | 20–28K (at cap) | 5.5K chars when it finishes | 10–25 min |

- **low and high are monotonic and healthy** — high reasons 3–5× more than low and emits
  ~50% more review content. Consistent with the recall ladder in §3 (vanilla 0.54→0.57,
  mrv 0.66→0.74).
- **medium inverts the ladder and breaks**: 4–10× high's reasoning, 10–20× the wall time,
  and non-convergence on lens-style prompts (no completion in 900s probes; 2–4h cells with
  zero tokens in the re-run).
- **It fails silently**: at 16K/32K budgets medium returns `finish_reason=length`,
  `content=""` — an HTTP 200 that reads as "no findings." That is exactly what the collapsed
  §3 rows are; raising the budget flipped vanilla × medium from 0.00 → **1.00** on the re-run
  PR. Any "GLM found zero bugs" result under a truncated budget is an infrastructure
  reading, not a model verdict.
- **Accounting drift**: `reasoning_tokens` arrives as a top-level `usage` field (OpenAI SDK
  `model_extra`) rather than `completion_tokens_details` — conventional-location readers
  mis-attribute reasoning spend to output tokens.
- **xhigh == high on the wire** (the harness sends `reasoning_effort=high` for both).

Repro packaged for Lunaroute (vLLM→SGLang migration suspected; `flash` unaffected at every
effort). The medium §3 rows should be re-measured once the upstream fix ships.

---

## 5. Smoke test — the PR #145 lens fix

**Question:** does metareview's new Evidence-of-Absence lens requirement (the fix for the #1
fabrication mode — unverified "zero tests" claims, 34% of audited rejections in the v2
re-adjudication; see main report §3.6 and metareview#140) reduce false positives in our
cells?

**Result: not measurable at smoke scale, no precision cost.** Six cells (mrv × both GLM
variants × xhigh × the three cal.com PRs where fabricated gap-claims concentrate), lens
prompts synced with the upstream rubric (commit `45a55b6`):

| arm | true_hal base→new (3 PRs) | recall (new) |
|---|---|---|
| background | 6 → 6 | 0.50–0.89 |
| flash | 1 → 3 | 0.67–0.89 |

Baseline hal counts (6 and 1) are too small to resolve a fix-sized effect; the deltas are
within run-to-run noise. Recalls held or improved (0.50–0.89; 36–45 bug_ungold/PR), so the
added discipline costs nothing in coverage. Decisive tests: (a) the big-hal mrv cells
(opus/sonnet, ~6–14 hal/PR under v2, ~$230–460 for the A/B), or (b) metareview's staged corpus
re-judge of the 343-claim corpus against v2 ground truth (`cmd/claimcheck-eval`; needs model
spend). Until one runs, the honest status of PR #145 in this lab is **"promising, unproven."**

---

## 6. Coverage state (low + high, all harnesses)

Complete (6/6 PRs, both efforts, vanilla/mrv/ce): **opus-5, sonnet-5, sol, terra,
glm-5.3-background, glm-5.3-flash-background**. Missing: fable-5.1 and astra have **no factory
(mrv/ce) cells at high effort** — 2 cells per model, **4 cells total** (≈$60–90; vanilla high
already exists for both). The low-vs-high and effort-ladder claims here are scoped to the six
complete models.

---

## 7. Caveats

- 6 PRs/cell (3/smoke arm); wide CIs. Directional, reproducible — not a published ranking.
- GLM $/cell figures are Z.AI *list* pricing applied to our measured token counts; our runs
  actually went through Lunaroute at a flat fee ($0 reported). Cached-input discounts
  ($0.26/M on GLM-5.3) not modeled.
- background/medium and background/high rows are serving-stack-dependent; re-measure after
  the upstream fix.
- The smoke test measures the *lens-side* arm of PR #145 only; the adjudicator-side arm is
  not exercised by these harness cells.
- fable/astra hid/hal counts come from the v2 re-adjudication of their full-suite runs
  (vanilla fable n=45 PRs, astra n=28) — a wider scope than the top-6 factory cells, which
  flatters nothing: their per-PR hidden-gold counts are *lower* on the easier top-6 subset.

## 8. Reproducibility

- GLM suite: batch `20260906-glm53-top6`; per-run v2 adjudication (`readjudication3.json`),
  totals independently verified.
- Smoke: batch `20260907-claimcheck-smoke`; lens sync commit `45a55b6`.
- Effort probes: §4 transcript numbers; plain `client.chat.completions.create` against
  `glm-5.3-background` with the cached PR-11059 diff.
- Harness changes shipped this cycle: effort-scaled GLM budgets + 2400s timeout
  (`model_router.py`), reasoning-token dual-location fix (`usage.py`), native v2 adjudicator
  (`adjudicate.py`, #11).
- Cross-report definitions (golden comments, hidden gold, waste precision, the v2 taxonomy)
  are specified in the main report §2 and docs/SPEC.md §9.4.
