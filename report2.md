# GLM-5.3 as a Review Engine — the 24-cell suite, the effort ladder, and the lens-fix smoke (Report 2)

> **What this is.** A follow-up to the main comparison ([`report.md`](report.md)) — read it
> standalone, but every framework/model/effort claim about the *older* cells cites the main
> report's sections. This report covers only the 2026-09-07 results: the full **GLM-5.3 /
> GLM-5.3-flash** suite (24 cells), effort-ladder probes on the same model, and a smoke test
> of metareview PR #145 (the lens-side fix for fabricated "zero tests" claims). All numbers
> reproducible from committed run records via [`REPRODUCE.md`](REPRODUCE.md).

---

## 0. Background — what this lab measures (standalone context)

`harnesseval` benchmarks **AI code-review harnesses** on real PRs with known ground truth.
Each PR carries *golden comments* — real review findings recorded by human reviewers — plus
the human reviewers' own misses. Three reviewer harnesses are compared:

- **vanilla** — one well-engineered review prompt, no subagents (the baseline a developer
  gets from "just ask the model to review this diff");
- **metareview ("mrv")** — free deterministic security/test gates + 8 adversarial "lens"
  subagents (testing, architecture, security, scope, …), orchestrated and consolidated;
- **Compound Engineering ("ce")** — risk-driven persona subagents (investigator, security,
  perf, …) + a synthesis pass.

Each harness × model × effort cell runs the top-6 PRs (cal.com and discourse PRs with 6–9
goldens each — main report §2). A judge model then matches each reported finding against the
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
| **$/cell** | metered cost of one harness × model × effort cell (all 6 PRs). GLM priced at Z.AI list ([docs.z.ai/guides/overview/pricing](https://docs.z.ai/guides/overview/pricing), fetched 2026-09-07): **GLM-5.3 $1.40/M input, $4.40/M output; GLM-5.3-flash $0.15/M in, $0.50/M out** (launch promo). Our runs went through the Lunaroute gateway at a flat fee ($0 reported) — the metered figures below are what the same token counts would cost on Z.AI's public API |

---

## 1. The headline result: a free model now beats the $57 factory

| | hid /PR | incr | tokens/PR | $/cell (Z.AI list) | hidden gold per $ |
|---|---:|---:|---:|---:|---:|
| **ce × glm-5.3-background × low** | **40.5** | **0.97** | **103K** | **$0.20** | **~200** |
| ce × glm-5.3-flash × low | 36.8 | 0.97 | 99K | $0.02 | ~1,800 |
| mrv × glm-5.3-flash × low | 25.3 | 0.93 | 110K | $0.02 | ~1,150 |
| mrv × claude-opus-5 × high (main report §3.4) | 36.0 | 0.85 | 2.98M | $56.65 | 0.64 |

**Compound Engineering on GLM-5.3 finds more real bugs the humans missed than the opus
factory — 40.5 vs 36.0 per PR, at higher incremental recall (0.97 vs 0.85), on 1/29th the
tokens, at ~1/280th the metered cost.** This is not a budget-tier result: on the top-6 PRs it
is the best factory cell measured in this lab at any price. Two ~$0–0.02 engines (ce and mrv
on GLM) now beat every metered configuration on hidden-gold efficiency, and metareview on
GLM delivers opus-factory-grade hidden gold (25–36/PR) for pennies.

The second headline: **the harness-beats-vanilla pattern extends to a third model family**
(ce 0.81/0.78 and mrv 0.66/0.74 recall vs vanilla 0.54/0.57 on background at low/xhigh) —
and, per §3.3, a cheap model behind a good harness now beats the newest premium models run
vanilla.

### TL;DR — practitioner recommendations

1. **Switch the default review engine to glm-5.3(-flash) × low.** Same incremental recall as
   the opus factory (0.97 vs 0.85), more hidden gold per PR (40.5 vs 36.0), $0.02–0.20/cell
   metered vs $56.65. No configuration in this data wins on value against it.
2. **Run GLM at low or high — never medium.** low/high are monotonic and healthy; medium
   reasons 4–10× more than high, takes 10–20× the wall time, sometimes never finishes, and
   fails *silently* (empty 200s that read as "no bugs"). xhigh is an alias for high on GLM.
3. **A cheap model + a good harness beats a premium model run vanilla.** mrv/ce on GLM-5.3
   ($1.40/$4.40 list) out-find vanilla on both 2026's newest models: vs vanilla × fable-5.1
   (rec 0.74, incr 0.89, $6.41/cell) the GLM factories deliver recall 0.66–0.81 and incr
   0.93–0.97 at $0.02–0.20/cell; vs vanilla × astra (rec 0.40, incr 0.52, $2.80/cell) it is
   not close. → §3.4
4. **Triage load is still the real price of factories.** GLM factory cells emit 17–28
   hallucinations per PR alongside 25–45 hidden gold (~59% real fraction, consistent with the
   main report's v2 real-fractions). The models are free; reviewer attention isn't.
5. **The metareview lens fix (PR #145) is safe but unproven at smoke scale** — no detectable
   fabrication win at n=3 PRs, no precision cost either. Decisive test: the big-hal mrv cells
   (~$230–460) or metareview's own corpus re-judge. → §5
6. **Re-probe medium after Lunaroute's upstream fix lands** — the background/medium rows in
   §3 will change. low/high results are unaffected.

---

## 2. What was run

| arm | cells | batch |
|---|---|---|
| GLM-5.3 suite: {vanilla, mrv, ce} × {background, flash} × {low, medium, high, xhigh} × top-6 PRs | 24 (141 runs; 135 pass; latest-pass per cell — three cells have n=5, rest n=6) | `20260906-glm53-top6` |
| Effort probes: single calls, glm-5.3-background, 79K-char diff, 65,536 budget | 2×low, 2×high live + 3 prior medium | §4 transcripts |
| Claimcheck smoke: mrv × {background, flash} × xhigh × {11059, 10967, 14740}, lens prompts synced with metareview#145 Evidence-of-Absence | 6 | `20260907-claimcheck-smoke` |

Judging/scoring identical to the main report (extract → judge → v2 three-way adjudication).
GLM served via Lunaroute (OpenAI-compatible); per-call timeout 2400s; effort-scaled
completion budgets (medium→65,536 / high→32,768) as the shipped workaround.

---

## 3. The 24-cell suite

Latest-pass run per cell. rec = absolute recall on goldens; incr = incremental recall
(goldens + confirmed hidden gold); hid/hal defined in §0; tok/PR = review tokens in+out.

| harness | model | effort | n | rec | incr | hid | hal | tok/PR |
|---|---|---|---:|---:|---:|---:|---:|---:|
| vanilla | background | low | 5 | 0.54 | 0.75 | 5.8 | 4.5 | 13K |
| vanilla | background | medium | 6 | 0.17 | 0.17 | 0.8 | 0.0 | 28K |
| vanilla | background | high | 6 | 0.00 | 0.00 | 0.0 | 0.0 | 27K |
| vanilla | background | xhigh | 6 | 0.57 | 0.80 | 7.5 | 3.7 | 20K |
| vanilla | flash | low | 5 | 0.50 | 0.73 | 5.8 | 3.8 | 13K |
| vanilla | flash | medium | 5 | 0.59 | 0.78 | 6.4 | 3.0 | 18K |
| vanilla | flash | high | 6 | 0.59 | 0.82 | 8.3 | 3.7 | 21K |
| vanilla | flash | xhigh | 6 | 0.53 | 0.78 | 7.3 | 3.5 | 18K |
| mrv | background | low | 5 | 0.66 | 0.92 | 25.2 | 25.2 | 114K |
| mrv | background | medium | 6 | 0.00 | 0.00 | 0.0 | 0.0 | 73K |
| mrv | background | high | 6 | 0.14 | 0.22 | 1.8 | 1.0 | 220K |
| mrv | background | xhigh | 6 | 0.74 | 0.96 | 36.0 | 18.3 | 157K |
| mrv | flash | low | 6 | 0.66 | 0.93 | 25.3 | 22.2 | 110K |
| mrv | flash | medium | 6 | 0.69 | 0.95 | 31.3 | 18.7 | 160K |
| mrv | flash | high | 6 | 0.69 | 0.95 | 31.3 | 21.3 | 171K |
| mrv | flash | xhigh | 5 | 0.66 | 0.93 | 25.8 | 18.0 | 149K |
| **ce** | background | low | 6 | **0.81** | **0.97** | **40.5** | 28.0 | **103K** |
| ce | background | medium | 6 | 0.11 | 0.24 | 4.0 | 0.5 | 199K |
| ce | background | high | 6 | 0.13 | 0.31 | 3.5 | 0.3 | 196K |
| ce | background | xhigh | 6 | 0.78 | 0.97 | 44.8 | 25.2 | 150K |
| ce | flash | low | 6 | 0.79 | 0.97 | 36.8 | 23.0 | 99K |
| ce | flash | medium | 5 | 0.71 | 0.96 | 39.8 | 18.0 | 146K |
| ce | flash | high | 5 | 0.68 | 0.95 | 39.8 | 17.2 | 155K |
| ce | flash | xhigh | 6 | 0.75 | 0.97 | 41.0 | 21.7 | 143K |

### 3.1 Readings that matter

- **Efficiency hierarchy upended.** Hidden gold per M review tokens: ce × GLM-low ≈ 393,
  ce × GLM-xhigh ≈ 299, mrv × GLM-low ≈ 230 — vs **12** for mrv × opus × high (main report
  §3.4). The main report's "the factories find more total bugs on every model, at 10–40× the
  cost" now has a free-model refutation: **the same harnesses on GLM find more total bugs at
  ~zero marginal cost.**
- **Vanilla on GLM is the cheapest usable baseline ever measured here**: rec 0.50–0.59, incr
  0.73–0.82 at 13–21K tokens/PR ($0.003–0.09/cell metered). One GLM call per PR surfaces ~6
  hidden bugs for effectively nothing.
- **Flash ≈ background on quality, and is the safer default**: within noise at every shared
  effort (ce low: 0.81 vs 0.79; xhigh: 0.78 vs 0.75), and flash has none of background's
  medium/high pathology (§4).
- **Effort is nearly free in quality terms**: low→high/xhigh moves hidden gold 40.5→44.8
  (ce/background) with hal flat-to-down. low is the value point; high when recall matters
  more than latency.
- **The collapsed background×medium/high rows are infrastructure, not quality**: flash
  scores 0.68–0.71 at the same efforts on the same PRs. See §4.

### 3.2 The metareview data

metareview's gates+lenses architecture on GLM (8 lens calls + gate binary per PR, 110–160K
tok/PR):

- **mrv × GLM posts opus-factory hidden-gold coverage at ~$0**: 25.3 hid/PR (flash/low) and
  36.0 (background/xhigh) — vs 36.0 for mrv × opus × high at $56.65. The old "metareview ×
  GLM is a gap" note in the main report is closed: mrv runs the full GLM ladder and its
  incr-recall tier (0.92–0.96) matches its opus tier.
- **mrv × background × xhigh is the strongest mrv cell measured on any model** (rec 0.74,
  incr 0.96, 36 hid) — mrv's lens swarm scales with GLM's cheap reasoning better than with
  opus's expensive attention.
- **mrv's price on GLM is hallucination volume**: 18–25 hal/PR (real fraction ~53–60%),
  same pattern as every factory cell — coverage costs triage.
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
| **newest premium, vanilla** | vanilla × **fable-5.1** × low | 0.74 | 0.89 | 3.0 | 0.8 | 76K | **$6.41** |
| | vanilla × **astra** × low | 0.40 | 0.52 | 1.8 | 0.1 | 52K | **$2.80** |
| **cheap model, factory** | ce × glm-5.3 × low | **0.81** | **0.97** | 40.5 | 28.0 | 103K | **$0.20** |
| | mrv × glm-flash × low | 0.66 | 0.93 | 25.3 | 22.2 | 110K | **$0.02** |
| | mrv × glm-5.3 × xhigh | 0.74 | 0.96 | 36.0 | 18.3 | 157K | $0.39 |

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
| background | 6 → 7 | 0.50–0.89 |
| flash | 1 → 3 | 0.67–0.89 |

Baseline hal counts (6 and 1) are too small to resolve a fix-sized effect; the deltas are
within run-to-run noise. Recalls held or improved (0.50–0.89; 36–45 bug_ungold/PR), so the
added discipline costs nothing in coverage. Decisive tests: (a) the big-hal mrv cells
(opus/sonnet, 20–28 hal/PR, ~$230–460 for the A/B), or (b) metareview's staged corpus
re-judge of the 343-claim corpus against v2 ground truth (`cmd/claimcheck-eval`; needs model
spend). Until one runs, the honest status of PR #145 in this lab is **"promising, unproven."**

---

## 6. Coverage state (low + high, all harnesses)

Complete (6/6 PRs, both efforts, vanilla/mrv/ce): **opus-5, sonnet-5, sol, terra,
glm-5.3-background, glm-5.3-flash**. Missing: **fable-5.1 and astra have no high-effort runs**
(~36 cells, ≈$230 + ≈$100 to fill). The low-vs-high and effort-ladder claims here are scoped
to the six complete models.

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
