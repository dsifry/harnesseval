# Further Research

The 384/384 matrix (see [`report.md`](report.md)) answered the single-pass question — *which
framework gives the best review quality and finds the most bugs per unit of cost* — but it
raised more questions than it closed. This page lists the open directions, in priority order,
with the empirical motivation for each.

The **centerpiece** is the SDLC-loop validation: the central question asks which framework
*finds and fixes* the most bugs, but the matrix measured only the *finding* (single-pass
review). The eval's single-pass data pointed to a *loop* (discover → adjudicate → fix →
repeat), but never measured a loop. The active experiment tests whether that loop — opinionated
metareview with deterministic hard gates — actually beats the unstructured vanilla `/goal`
control (and isolates the gate from the loop *structure* via a structured-vanilla ablation).

---

## 1. SDLC-loop validation — vanilla `/goal` vs opinionated metareview with deterministic hard gates

**Status:** prototype built, not yet run at scale. The prototype lives on branch
`sdlc-loop-experiment` — check it out to see the code: `git checkout sdlc-loop-experiment`, then
see `bin/run_sdlc_loop.py` and `harnesseval/sdlc_loop.py` there.

### Why this is the priority

`report.md` §7 recommends using the frameworks **in sequence** — discover with a harness,
adjudicate with a precision model, fix, repeat — because the single-pass data shows the
harnesses win at *discovery* (hidden gold 16/16) while vanilla/precision-models win at
*precision* and *cost*. But that recommendation is an **extrapolation**: the eval measures
single-pass review quality, not the iterative discover→adjudicate→fix cycle. The most important
open question is whether the loop **actually converges** — does iterating it find/fix more real
bugs than a single pass, and does it beat simply letting a strong model loop itself
autonomously (`/goal`)?

### The experiment

`bin/run_sdlc_loop.py` runs **2 models × 3 conditions** on a PR, all in parallel, against a
**UNION bug universe** (unbiased: a bug vanilla found that metareview missed is in the
universe and vanilla gets credit for finding it):

| condition | what runs | what it isolates |
|---|---|---|
| **structured-mrv** | metareview discover → adjudicate → fix → iterate | the **opinionated loop with deterministic hard gates** (Go gates + 8 lenses as the discovery layer) |
| **structured-vanilla** | vanilla discover → adjudicate → fix → iterate | the structured loop **without** metareview's gates/lenses — isolates the loop *structure* from the metareview discovery layer |
| **naive-vanilla** (`/goal`) | one long autonomous `claude -p --max-turns N` / `codex` session: "review, fix, add tests, keep going until confident" | the **unstructured control** — the agent loops itself with its own judgment for when to stop |

Both structured conditions use the **same model** (claude-opus-5, gpt-5.6-sol) so the only
variable is the *process*; the naive control uses higher effort to give the autonomous agent a
fair shot at self-directed depth.

Four phases:
1. **Discovery + adjudicate** on the original code, all 3 conditions in parallel (the structured
   conditions discover-and-adjudicate; the naive `/goal` control runs its full discover+fix
   session autonomously).
2. **Build the UNION bug universe** — dedup all conditions' confirmed bugs via a file:line-grouped
   LLM judge (`dedup_bugs_llm`).
3. **Fix + iterate** — the structured conditions fix their confirmed bugs and iterate
   discover→adjudicate→fix until the confirmed-bug count stops growing; the naive control
   already fixed.
4. **Score fixation** — for each condition, which UNION bugs are still present in its final
   code (`_bug_still_present`, judged against the golden + the union).

**Per-condition metrics:** bugs found (in union), bugs fixed, hallucinations, tokens (incl.
cache), wall time, and (for structured) per-iteration convergence.

### What it tests (the hypotheses)

- **Does the opinionated loop (structured-mrv, with deterministic hard gates) find and fix more
  union bugs than the unstructured `/goal` control?** This is the §7 recommendation made
  measurable. metareview's deterministic gates (eval/TODO/missing-test/duplicate-path) act as a
  free, model-independent **hard gate** inside the loop — they block "done" claims that the
  LLM lenses might rubber-stamp. The loop tests whether that gate earns its place.
- **Is the win the *structure* (the discover→adjudicate→fix staging + confirmed-bug list) or the
  *discovery layer* (metareview's 8 lenses + gates)?** structured-vanilla vs structured-mrv
  answers this. If structured-vanilla ≈ structured-mrv, the *loop structure* is the active
  ingredient and the harness's single-pass coverage advantage doesn't transfer to a fix loop. If
  structured-mrv > structured-vanilla, metareview's discovery layer (hidden gold 16/16) earns its
  keep *even after* the adjudication filter — i.e. it surfaces bugs vanilla's single pass never
  sees, so the loop has more to fix.
- **Does the loop converge?** The §7 stop conditions (recall stops improving; tests pass;
  candidate list collapses to hallucinations) are asserted, not shown. Measuring
  per-iteration confirmed-bug counts shows whether 1–2 iterations capture the value (as §7
  predicts) or whether the loop keeps finding real bugs for many rounds (or stalls).

### How to run it

> The prototype is on branch `sdlc-loop-experiment` — `git checkout sdlc-loop-experiment`
> first (these files are not on `main` / the `v0.8.2-eval` repro pin).

```bash
uv run python bin/run_sdlc_loop.py [PR_URL]    # default PR = cal.com #11059
```

It reuses the eval's discovery path verbatim (`harnesseval.adapters.metareview_realistic` —
same `REALISTIC_PROMPT`, same `_run_claude_session`, same `_extract_findings_from_session`) and
the eval's scoring (`harnesseval.judge` + `harnesseval.adjudicate`). **The only new code is the
fix step + the loop orchestration** — so the loop's discovery quality is the eval's measured
discovery quality, not a new variable.

### Why the UNION universe matters

A naive loop comparison would score each condition only on the bugs *it* found. That biases
toward whichever condition discovered first. The UNION universe dedups all conditions' confirmed
bugs and scores every condition against the *same* bug set — so a bug vanilla found that
metareview missed is in the universe and metareview is penalized for missing it (and vice versa).
This is the unbiased version of the single-pass "hidden gold" accounting.

### Open sub-questions (for after the prototype)

- Does the deterministic-gate layer (`metareview-deterministic/*`) earn its place in the loop
  even though it contributed **0 recall** in single-pass? In a loop, the gates may matter
  differently: they block "done" on missing-test/eval/TODO, forcing the fix step to add tests
  before the loop can converge — a *process* role, not a *discovery* role. The single-pass eval
  couldn't see this; the loop can.
- Should the adjudication step (c) use a *panel* rather than one cross-family judge? The stored
  findings carry a diff-context hash, so re-adjudication with a frontier panel is possible
  without re-running discovery (see §5).
- Does the structured loop's cost (iterations × discovery + adjudicate + fix tokens) actually
  beat the naive control's cost (one long autonomous session) *per bug fixed*? The §3.4
  cost-efficiency refutation (H1) was about single-pass review; a loop changes the economics.

---

## 2. Phase C — 50 PRs + confidence intervals (the bar before any final ranking)

Every number in `report.md` carries the same caveat: **N is tiny** (6 PRs per cell; bootstrap
95% CIs wide or undefined). No "X beats Y" claim survives the bootstrap at this N — the
interaction analyses report raw win-rates, not significance. The patterns (hidden-gold 16/16,
opus-5 concentration) are directional, not proven.

Phase C is:
- **Expand the dataset** from 6 to ~50 PRs (the Martian bench has 50 PRs / 173 golden comments;
  the primary matrix used 6). Sample across all 5 OSS projects (the 6-PR subset skews
  cal.com/Discourse).
- **Report bootstrap CIs** on every headline metric and every win-rate. Promote a finding to a
  "claim" only when the CI excludes the null.
- **Re-run under identical conditions** (batch, judge panel, model snapshots). batch_083 is
  ~0.14 lower recall than the earlier 0824-1019 batch on matched cells — a batch effect; Phase C
  must be one consistent batch.

This is the gating step before the practitioner table in `report.md` §1 can be called a
ranking rather than a directional read.

---

## 3. metareview 0.8.2 × GLM (close the GLM sidebar gap)

The GLM sidebar (`report.md` §4) excludes metareview because only metareview 0.8.2 results
count and the 0.8.2 adapter was never run on GLM. Run `metareview_realistic` on
`glm-5.2-vision-flex` × {medium, xhigh} on the same 6 PRs to complete the apples-to-apples
factory comparison on GLM. Expect: the 0.7.0 metareview GLM row (excluded) hit recall 0.76–0.77,
incr. 0.94 — but that was the 0.7.0 batch (higher-recall batch effect), so a fresh 0.8.2 GLM run
is needed, not a port of the old numbers.

---

## 4. OpenEnv Code Review Arena — deterministic-grader cross-check

The eval uses an LLM-as-judge (cross-family, to avoid same-model bias). OpenEnv Code Review
Arena provides a **deterministic grader** — no judge variance — with explicit security classes
(SQLi, path traversal, …) and an explicit false-positive control task. Folding it in would:
- **Cross-check the LLM-judge numbers** against a zero-variance grader on the security subset,
  catching any judge bias the cross-family design misses.
- **Add an explicit false-positive control** — a task designed to catch frameworks that
  hallucinate security bugs. This directly stress-tests the hallucination tax (`report.md` §6.3:
  superpowers 60% hallucination, metareview 54%).

Not yet in the primary matrix; the integration point is a second grader path in
`harnesseval/judge.py` + `harnesseval/adjudicate.py`.

---

## 5. Per-lens / orchestrator tuning (the cost levers the data points at)

These are cheap knobs the single-pass data identified but did not test:

- **Pin the lenses to Sonnet instead of Haiku (H3 tuning).** metareview's cost is 99.96%
  orchestrator (opus) and 0.04% lenses (Haiku) — the lens fanout is nearly free. Upgrading the
  lenses to Sonnet is a *cheap* cost increase that might raise lens recall (the lenses do the
  actual bug-finding; Haiku may be the bottleneck on hard PRs). Untested. Measure: does
  Sonnet-lens recall rise enough to justify the small cost delta?
- **Downgrade the orchestrator to Sonnet.** The orchestrator (opus) is 99.96% of cost. The
  orchestrator's job is dispatch + synthesis, not bug-finding (per the 0.8.2 "orchestrator
  discipline" release). A Sonnet orchestrator might cut cost substantially with little recall
  loss. Measure: recall delta vs cost delta.
- **Conditional lens coverage.** metareview runs all 8 lenses on every diff, even when (e.g.)
  there's no security surface. Compound's risk-driven roster (skip personas whose surface is
  absent) is an empirically supported efficiency idea (`report.md` §6.4 / §7 tactical #5).
  Making metareview's lenses conditional on diff signals could trim fanout without losing
  coverage where it matters. Measure: per-lens real_rate by diff-surface vs unconditional.
- **Re-adjudicate with a frontier judge panel.** Each stored finding carries its source-lens,
  matched-golden, judge verdict, and a **diff-context hash** (`_build_finding_records`). This
  means the committed run records can be **re-adjudicated later with a stronger judge panel
  without re-running any framework**. As frontier judges ship, re-score the whole matrix and
  see whether the precision/hallucination split (§6.3) shifts — a cheap way to harden every
  number in `report.md` over time.

---

## 6. The hallucination tax, measured as a process cost

`report.md` treats hallucinations as a count to triage. In a real team they are a *process
cost*: every factory finding that gets auto-filed as an issue costs a human a read. The next
step is to model the **triage cost** explicitly:

- **Threshold the factories' output by adjudicated confidence + multi-lens agreement.** The
  data says ~40–54% of unmatched factory findings are hallucinations (`report.md` §6.3). A
  threshold (only file findings with confidence ≥ 75 *and* ≥ 2 lenses agreeing) may drop the
  hallucination rate sharply at a modest recall cost. Measure: the recall/hallucination
  tradeoff curve per threshold.
- **Measure the adjudicator's own error rate.** The cross-family judge reclassifies unmatched
  findings; its own false-positive rate (calling a real bug a hallucination, or vice versa) is
  unmeasured. A labeled subset of adjudication decisions would quantify this and bound the
  error in every "real-but-ungold" number.

---

## How these connect

Phase C (§2) and the OpenEnv cross-check (§4) **harden the existing single-pass numbers**. The
SDLC-loop validation (§1) **extends the eval from single-pass review to the iterative workflow**
the data actually recommends — and is the experiment that justifies (or refutes) building
metareview's deterministic hard gates into a loop rather than treating review as a one-shot
gate. The tuning levers (§5) and the triage-cost model (§6) are the cheap follow-ons that turn
the directional read into actionable product decisions for metareview.

The repo is set up to support all of this from the committed run records: every finding is
atomic and source-tagged, every adjudication is re-runnable via the diff-context hash, and the
SDLC-loop prototype reuses the eval's discovery path verbatim so loop results are directly
comparable to the single-pass matrix.
