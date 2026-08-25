# metareview — empirically-suggested improvements (hypotheses)

> **Living document.** Hypotheses for metareview design improvements surfaced by the harnesseval
> lab. Each entry: the **hypothesis**, the **current-defect evidence** (what the eval measured that
> suggests a gap), the **mechanism** (why the gap exists, traced to metareview's design/rubric),
> the **proposed improvement** (concrete change to test), and the **confirming experiment**
> (what the eval would need to show to support the improvement — the bar to clear before claiming
> it as a finding).
>
> **Status key:** 🔬 hypothesis (not yet tested) · 🧪 improvement-build proposed · ✅ confirmed by
> Phase C · ❌ refuted by Phase C.
>
> **Hard caveat on all current evidence:** N ≤ 6 PRs, many cells N=1, bootstrap CIs wide/undefined
> (see `results/bootstrap_ci.json`). Every "defect" here is a *signal worth testing*, not a proven
> result. Phase C (50 PRs + CIs) is the bar. Do not ship a metareview change on this evidence alone
> — but these are the right things to test next.
>
> **Scope discipline:** this doc records *empirically-suggested* metareview improvements only — not
> general roadmap items. Each must trace to a measured eval signal.

---

## H1 — Add a dedicated security lens (the 6th lens)

**Status:** 🔬 hypothesis · 🧪 improvement-build proposed

### Hypothesis
metareview's review-artifact skill has no dedicated security lens. Its 5 lenses (Feasibility,
Completeness, Scope/alignment, Architecture, Intent preservation) are all *artifact-shape*
checks, none prompt a reviewer to look for vulnerabilities. Adding a 6th, dedicated security lens
would raise metareview's security-bug recall toward (or above) vanilla's, at ~zero marginal cost
(the orchestrator, not the lenses, dominates cost — see H3).

### Current-defect evidence (what the eval measured)
- **Failure-mode signal (api, opus, medium, 5–6 PR subset):** on PRs containing a `security`
  golden, vanilla-engineered mean recall = **0.56** vs metareview = **0.44** (vanilla edges
  metareview on security). Source: `results/failure_mode.json` →
  `metareview|api(inferred).category_profile.security` vs
  `vanilla-engineered|api(inferred).category_profile.security`.
- **This is the *only* category where vanilla beats metareview** in that subset — on `api`
  (0.72 vs 0.31) and `data` (0.70 vs 0.44) metareview's lens fanout wins. So the security gap is
  category-specific, not a general "metareview is worse" effect — consistent with a *missing
  lens* rather than a weak model.
- **Concrete goldens at stake (from the Martian set):** discourse/pull/4 has a Critical
  SQL-string-interpolation golden + a Critical unescaped-header XSS; discourse/pull/10 has a
  Critical SQL injection; sentry-greptile/pull/1 has access-control/IDOR goldens
  (API-key/org-auth-token `user_id=None`, org-scoping bypass); cal/11059 has a hardcoded
  refresh-token bug. metareview's lenses are never asked about any of these classes.
- **Caveat on the evidence:** security N=3 PRs in this subset; the 0.56-vs-0.44 gap is within
  bootstrap noise. Treated as a signal to test, not a result.

### Mechanism (why the gap exists — traced to metareview's design)
- **`/Users/dsifry/Developer/metareview/skills/review-artifact/SKILL.md` line 15:** the 5
  required lenses are explicitly "Feasibility, Completeness, Scope and alignment, Architecture,
  Intent preservation." No security lens is named.
- **`harnesseval/adapters/metareview.py` `LENS_PROMPTS` (lines ~30–37):** our api-direct adapter
  mirrors this exactly — 5 lenses, each an artifact-shape prompt ("verify paths/commands",
  "map the change to its stated intent", "boundaries, ownership, duplication risk", etc.).
  None mentions injection, authn/authz, CSRF, SSRF, XSS, path traversal, crypto, secret
  handling, access control, escaping, or deserialization.
- **Confirmed absent across all metareview review skills:** checked `review-pr-ready`,
  `review-task-done`, `review-epic-ready` — none define a security lens or security rubric. The
  only "security" string matches in the metareview repo are in Go *test* files, not rubrics. So
  this is a structural absence, not a skill-specific omission.
- **The realistic path inherits the gap:** our realistic adapter uses `review task-done` for the
  deterministic gates but dispatches the 5 LLM lenses from the review-artifact skill
  (`metareview_realistic.py`), so realistic metareview has the same no-security-lens coverage.

### Contrast (metaswarm, the reference point — not yet in our clean data)
metaswm has security coverage in **two** places:
1. **`/Users/dsifry/Developer/metaswarm/rubrics/security-review-rubric.md`** — a standalone 376-line
   rubric enumerating OWASP A01–A10 with code patterns to flag (SQL/NoSQL/command/LDAP/XPath
   injection, IDOR/org-scoping, hardcoded secrets, weak hashing, SSRF, deserialization, missing
   security headers, etc.).
2. **`/Users/dsifry/Developer/metaswarm/rubrics/code-review-rubric.md` §2 "Security (CRITICAL)"**
   (lines 60–77) — even the *general* code-review rubric has an OWASP injection/XSS/auth/input-
   validation/secrets section. So metaswarm's general reviewer already out-shoots metareview's
   specialized lenses on security.
- **Note:** metaswarm is not yet measured in our clean data (Phase B add per SPEC §14.2). "metaswarm
  would beat both on security" is a *prediction* from rubric analysis, not a measured result. The
  eval will test it.

### Proposed improvement (concrete, testable)
- **Add a 6th lens: `security`** to metareview's review-artifact skill (and to our adapter's
  `LENS_PROMPTS`), with a prompt mined from metaswarm's OWASP A01–A10 rubric (injection,
  access-control/IDOR, crypto/secrets, SSRF, XSS/escaping, deserialization, security headers).
- **Cost expectation (from §6.3.1):** ~free. Lenses run as Haiku subagents (~0.04% of cost in our
  3-run sample; the orchestrator is 99.96%). One more Haiku lens is essentially zero marginal $.
  This is the cheap-test sweet spot.
- **Prompt design (proposed, to be finalized):** the lens should (a) enumerate the OWASP classes
  to look for (so the reviewer doesn't have to recall them unprompted), (b) ask for file:line
  evidence, (c) be told the PR's stated intent (so it can separate "intended behavior" from
  "vulnerability"), and (d) avoid double-counting the deterministic gates' catches (eval-injection
  gate already covers `eval(`). A first draft lives at the bottom of this doc.

### Confirming experiment (the bar to clear)
Run, in Phase C (50 PRs, CIs), a **paired comparison** on the security-bearing PRs:
- metareview (5 lenses, current) vs **metareview (6 lenses, +security)** — same orchestrator,
  same PRs, same judge, same effort. (api mode for the apples-to-apples column.)
- **Supports the improvement if:** the +security variant's security-category recall
  *significantly* exceeds the 5-lens variant's (CIs separate), AND total recall doesn't regress
  (the new lens doesn't crowd out others), AND precision doesn't crater (the new lens isn't a
  hallucination firehose — track `n_hallucination`).
- **Even stronger:** if the +security variant's security recall meets/exceeds metaswarm's
  security-auditor agent on the same PRs, that's evidence the *lens* approach can match a
  *dedicated agent* at lower orchestration cost.
- **Refutes the improvement if:** the gap closes in raw recall but `n_hallucination` on the
  security lens is high (adjudicated_precision collapses) — i.e. the lens invents
  vulnerabilities. That would mean the prompt needs tightening, not that the idea is wrong.

### Data needed before this experiment can run
- **Phase C completion** (50 PRs, ≥3 runs/cell) to shrink CIs so a security-recall delta is
  detectable. At N=3 PRs the current 0.56-vs-0.44 gap is noise.
- **Persist per-golden match decisions** in `summary.json` (currently absent) — so we can say
  "the security lens caught golden SQL-injection #X that the 5-lens variant missed on PR Y,"
  not just "security-category mean recall went up." This is the single biggest unlock for
  turning this from a category-level correlation into a per-bug mechanistic claim.
- **Optionally:** a metaswarm run on the same PRs (Phase B/C) as the reference upper bound.

---

## H2 — Deterministic gates contribute 0 recall on this PR subset (revisit the "free floor" claim)

**Status:** 🔬 hypothesis (preliminary finding, pending wider N)

### Hypothesis
SPEC §6.3 predicted metareview's deterministic Go gates (eval-injection, TODO/FIXME,
missing-tests, duplicate-path, truncated-diff) give a "free recall floor" — catches that cost
zero tokens and fire regardless of model. On our 6-PR subset, that floor is **0.0**. The
hypothesis for improvement: the gates' current rule-set is tuned to *artifact/task* defects, not
to the *vulnerability* classes the golden set rewards, so they contribute nothing on
vulnerability-heavy PRs. Tuning/adding a gate (or accepting that the floor is PR-class-dependent)
is a candidate improvement.

### Current-defect evidence
- **`results/decomposition.json`:** on every CLEAN metareview cell (api + cli),
  `deterministic_gate_recall = 0.00`. The gates fired 0–1 findings (`n_det_findings` 0–3 across
  cells) but **none matched a golden issue**. 100% of metareview's recall comes from the LLM
  lenses (`llm_lens_recall`).
- **The gates did run (not a bug):** `n_det_findings` > 0 on several cells, so the gates
  executed and produced output — they just didn't hit gold. This is a *coverage* finding, not a
  plumbing failure.
- **Caveat:** N=6, and these PRs are vulnerability-heavy (security/bug goldens dominate — see
  `golden_profile`). The gates are designed for eval-injection/TODO/missing-test, which may
  simply not appear here. The "0 floor" may not generalize to a PR set with more
  test-gap/eval-injection goldens.

### Mechanism
- The deterministic gates are *static pattern matches* (regex/AST on the diff): `eval(`,
  `TODO`/`FIXME`, missing test files, duplicate-path, truncated-diff. None of these patterns
  correspond to the golden categories present (bug/security/data/api), so the gates' catches
  can't match gold. The floor is real in *principle* but its *height* is a function of how many
  goldens are of the gate-detectable type.

### Proposed improvement (lower priority than H1 — investigate before changing)
- **First: characterize** — run the gates on a PR set *with* test-gap/eval-injection goldens and
  measure `deterministic_gate_recall`. If it's still 0, the gates are mismatched to the golden
  distribution. If it's >0, the floor exists but is PR-class-dependent (a finding to report, not
  a defect to fix).
- **If mismatched:** candidate new gates (each free, deterministic): string-interpolation-into-
  SQL (regex for `'...${...}...` in query strings), missing-org-scope (AST for DB queries
  without an org/tenant filter), hardcoded-secret (regex for `api_key|token|password = "..."`).
  These map directly to goldens we have. *But* these overlap with H1's security lens — the
  design question is whether to catch these deterministically (free, brittle) or via the lens
  (cheap, flexible). Probably the lens (H1) for most; a gate only for high-precision patterns.

### Confirming experiment
- **Supports "floor is PR-class-dependent":** deterministic_gate_recall > 0 on a
  test-gap/eval-injection-heavy PR subset. Report as a finding (the floor is real but narrow).
- **Supports "add a deterministic security gate":** a new gate catches a golden that both the
  5-lens and +security-lens variants miss, at zero token cost. (Would need per-golden match
  persistence to prove.)
- **Refutes:** gates stay at 0 even on gate-relevant PRs → the gate rules are too narrow; fix
  the rules, don't add new ones.

---

## H3 — The orchestrator-vs-lens cost split (a *confirmed* structural finding, with a tuning implication)

**Status:** ✅ confirmed in data (structural) · 🔬 tuning implication is hypothesis

### Finding (confirmed, not a defect)
metareview-realistic cost is ~99.96% orchestrator (opus), ~0.04% lenses (Haiku). The 5-lens
fanout is essentially free; the orchestrator dominates. This is *exactly* SPEC §6.3.1. It means:
- "metareview is expensive because of 5 lenses" is **false** — the lenses are cheap.
- The (model × effort) axis for realistic metareview varies the **orchestrator**, not the lenses
  (Haiku lenses stay Haiku unless pinned).

### Evidence
- `results/per_model_cost.json`: across 3 CLEAN cli runs with `per_model_usage`,
  `claude-opus-5` = $12.18 (99.96%), `claude-haiku-4-5-20251001` = $0.005 (0.04%).
- `results/ANALYSIS.md` §4.

### Improvement implication (hypothesis, the actionable part)
Since lenses are ~free, **pinning lenses to a stronger model (e.g. Sonnet, or the orchestrator
model itself) is a cheap knob** that could change the quality/cost tradeoff — at potentially
large quality gain for small cost. The eval currently reports the *realistic default* (Haiku
lenses); this would be a *metareview design change* to test.
- **Cheap to test:** because lenses are 0.04% of cost, pinning them to Sonnet might raise lens
  cost to (say) 1–2% — still negligible — while possibly raising lens recall. The
  orchestrator stays opus.
- **This is a metareview tuning change, not an eval change** (SPEC §6.3.1 is explicit: the eval
  reports the realistic default; tuning is metareview's call). But the eval can *measure* it.

### Confirming experiment
- Run metareview-realistic with lenses pinned to (a) Haiku [current], (b) Sonnet, (c) opus
  [same as orchestrator], same orchestrator/PRs/effort.
- **Supports pinning:** lens recall rises with lens model strength AND the cost delta is small
  (lenses stay <5% of cost) AND orchestrator cost doesn't rise (lens pinning shouldn't
  re-trigger orchestrator context).
- **Refutes:** cost rises sharply (e.g. opus lenses re-inflate the orchestrator cache) or
  recall doesn't move (the bottleneck is the orchestrator's planning, not lens quality).
- **Caveat:** our current realistic path *can't* pin lenses (Haiku routing is a Claude Code
  default). Testing this needs a metareview/adapter change to pass the lens model explicitly.

---

## H4 — metareview's high FP / high incremental_recall: thoroughness or noise? (adjudication-quality question)

**Status:** 🔬 hypothesis → likely-pending-data (prior weakly supported; needs the data unlock + a stronger adjudicator panel to confirm)

### Hypothesis / prior
metareview's raw precision is very low (api 0.06–0.18; realistic 0.16–0.35) because it emits
28–133 FPs per cell. But its `incremental_recall` is high (0.71–0.97 api; 0.73–0.74 realistic) —
many "FPs" are reclassified by adjudication as real-but-ungold bugs. **Working prior: most of
those unmatched findings are real issues the human gold-set reviewers missed (the Martian
"superhuman find" problem, SPEC §9.4), not hallucinations.** The open question: are those
real-but-ungold findings *concentrated in the categories metareview's lenses target*
(strengthening the lens story) or scattered (weakening it — metareview is just verbose)? This
isn't a defect per se, but resolving it determines whether metareview's thoroughness is a
*feature* (it finds bugs the gold set missed) or a *bug* (it hallucinates).

### Current evidence (weakly supports the prior)
- **On the one cell where the counts are stored, the prior holds:** metareview api, gpt-5.2,
  low — 40 unmatched findings split **23 real-but-ungold vs 17 hallucination** (adjudicator
  ruled more than half are real bugs the gold set missed). vanilla cli, gpt-5.2, medium is even
  more lopsided: **9 real-but-ungold vs 1 hallucination**. Source: `results/leaderboard_cli.json`
  + the gpt-5.2 low api cell in `runs/registry.jsonl`.
- **But the counts aren't stored on most cells.** The early api opus batch stores the
  *rate* (`incremental_recall`) but NOT the counts (`n_hallucination`/`n_real_ungold`) — so
  across the opus api cells we can't currently compute the real-vs-hallucination split, only
  the blended rate (flagged `†mean-rate` in `results/ANALYSIS.md` §2).
- **One realistic run is a red flag / data bug:** 133 FPs on a cal/11059 run with
  `n_real_ungold = 0` — adjudication called *all 133* hallucinations. Given the 23-vs-17 pattern
  on comparable cells, this is more likely an adjudication under-count / data-quality bug than a
  genuine all-hallucination result. Must be diagnosed before H4 can resolve.

### Mechanism (candidate)
- The 5 lenses each emit "distinct issues, one per item" with no dedup *across lenses* until our
  score step — so the same issue seen by 2 lenses becomes 2 findings, both "FP" if not matched.
  Cross-lens dedup may be undertuned. (Plausible, unverified.)

### Proposed improvement (investigate before changing metareview)
- **First: fix the data.** Persist per-golden match decisions + per-finding source-lens +
  **per-finding adjudication records** (verdict, adjudicating judge, confidence, rationale,
  diff-context hash) in `summary.json` — see "Methodology: adjudicator panel expansion" below.
  Then we can ask: of metareview's FPs, how many are (a) cross-lens duplicates, (b)
  real-but-ungold (adjudication says real), (c) hallucination? And cross (b) against category.
- **Second: validate the adjudicator** with a human spot-check of ~50 random adjudications
  (SPEC §13.3 mitigation). If a human agrees with the adjudicator on ~40/50, the real-but-ungold
  count is trustworthy; if ~25/50, the adjudicator is the bottleneck and H4 can't resolve until
  the adjudicator panel improves (see the methodology section).
- **If (a) dominates:** improve cross-lens dedup (an adapter/scorer fix, cheap).
- **If (b) dominates and concentrates in api/data/security:** metareview is genuinely
  thorough — report as a strength, and H1's +security lens should *raise* (b)-type finds, not
  (c)-type. **This is the outcome the working prior predicts.**
- **If (c) dominates:** the lens prompts are too permissive; tighten them (prompt engineering,
  not architecture).

### Confirming experiment
Needs the per-golden-match + per-finding-adjudication persistence unlock AND the expanded
adjudicator panel (below). Then: on 50 PRs, report the (a)/(b)/(c) split per lens and the
category distribution of (b), with the adjudication validated by both the expanded AI panel and
a human spot-check. The "improvement" is whichever of the three fixes the dominant cause turns
out to be.

### Strategic framing if H4 resolves toward the prior
If real-but-ungold dominates, it **reframes metareview's worst-looking number** (raw precision
0.06–0.18) as evidence of a *gold-set limitation*, not a metareview defect — and
`adjudicated_precision` / `incremental_recall` become the metrics to defend it with. The eval
was designed (SPEC §9.4) precisely so a thorough reviewer isn't punished for the gold set's
gaps; H4 is the test of whether metareview is such a reviewer.

---

## Methodology: expand the adjudicator panel to frontier models (enables H4; doesn't break calibration)

> **For the build/run agent.** This is an *eval-methodology* change, not a metareview change —
> but it directly gates H4 and H1's confirming experiment, so it's recorded here.

### The distinction that makes this safe
SPEC §9 deliberately keeps the **primary judge** (candidate-vs-golden *match*) on the old trio
(opus-4.5, sonnet-4.5, gpt-5.2) so Phase A's calibration anchor (§8 Anchor 1) holds — those
are the models Martian's shipped `evaluations.json` was produced with, and our calibration
reproduces their decisions. **Adjudication is a different decision layer** — "is this *unmatched*
finding a real issue in this diff?" — and it is *not* the calibrated anchor. Expanding the
*adjudicator* panel therefore does NOT touch Phase A calibration; it strengthens the
real-but-ungold signal that H4 depends on.

### Proposed adjudicator panel
Keep opus-4.5 (calibration-compat baseline + continuity with existing runs) AND add newer
frontier models:
- **opus-5** (frontier Anthropic)
- **gpt-5.6-sol** (frontier OpenAI)
- **Fable** — only as a *tiebreaker / contested-case* judge, not on every finding (cost:
  very expensive per the user; reserve for disagreements where opus-5 and gpt-5.6-sol split,
  or for a human-spot-check sample).

### Anti-self-preference rule (carry SPEC §9 to the adjudicator)
The adjudicator for a given run must be a **different family** from the model under test (a
model shouldn't adjudicate its own output). Concretely:
- model-under-test = opus family → adjudicate with gpt-5.6-sol (+ Fable tiebreak)
- model-under-test = gpt family → adjudicate with opus-5 (+ Fable tiebreak)
- model-under-test = glm/kimi → adjudicate with opus-5 + gpt-5.6-sol (both)
Report adjudicator-model variance (as we do for the primary judge).

### What this buys
- A stronger real-but-ungold verdict: if opus-4.5, opus-5, AND gpt-5.6-sol all call a finding
  real-but-ungold, that's far more trustworthy than opus-4.5 alone — and opus-4.5 is, as the
  user notes, quite old by today's frontier standard. H4's prior (most FPs are real-missed)
  becomes much more credible under a multi-frontier adjudicator panel.
- A path to validate/replace the existing 23-vs-17 / 9-vs-1 splits with frontier-judge splits.
- A cheap way to re-adjudicate stored api findings retroactively (see restart recommendation).

### Cost guardrail
Adjudication is a per-finding judge call (NOT per-PR-pair like the primary judge). For a
metareview cell with ~40 findings, a 3-model adjudicator panel = ~120 judge calls/cell — still
cheap vs the orchestrator's $5–12/run, but Fable on every finding would be prohibitive. Keep
Fable to the contested subset only.

---

## Cross-cutting data needs (unlocks for H1, H2, H4)

These are eval-pipeline gaps, not metareview changes, but they gate the confirming experiments:
1. **Persist per-finding adjudication records** in `summary.json` — for each finding:
   `{issue_text, source_lens, matched_golden_ids: []|null, primary_judge_verdict,
   adjudication: {verdict: real_but_ungold|hallucination|matched, adjudicating_judge,
   confidence, rationale, diff_context_hash}}`. This is the single biggest unlock — without it,
   H4 can't be tested per-bug and re-adjudication with newer models is impossible without
   re-running the framework. **Highest priority.**
2. **Persist per-golden match decisions** (which candidate matched which golden).
3. **Persist per-finding source-lens** (which lens emitted each finding) — needed for H4's
   cross-lens-dedup question and to attribute recall to specific lenses.
4. **Persist adjudication counts on ALL runs** (the early api batch stored the rate but not
   `n_hallucination`/`n_real_ungold` — see `results/ANALYSIS.md` §2 †mean-rate note). Needed so
   adjP/incR can be recomputed from sums across cells.
5. **metaswarm in the clean data** (Phase B/C) as the reference upper bound for H1.
6. **Phase C (50 PRs, ≥3 runs/cell)** to shrink CIs so deltas are detectable.

---

## Appendix: proposed security-lens prompt (for H1) — first draft, to be refined

```
You are a Security reviewer. Given the PR diff below, hunt for security vulnerabilities. For
each class, check whether the diff introduces or fails to prevent it; report each distinct
issue, one per item, with file:line and the vulnerable code.

Check for, at minimum:
- Injection (SQL/NoSQL/command/LDAP/XPath): user input concatenated or interpolated into a
  query, shell command, or expression. Flag string-template SQL (`...${...}...` in a query),
  exec/spawn with user input, unvalidated JSON.parse into a query.
- Broken access control / IDOR: DB queries or lookups using a user-supplied id without an
  ownership/org/tenant scope check; routes without auth middleware; role checks missing or
  bypassable; CORS overly permissive.
- Cryptographic failures / secrets: hardcoded keys/tokens/passwords; secrets or PII written to
  logs; weak hashing (MD5/SHA1) for credentials; insecure random for security tokens.
- SSRF: user-supplied URLs fetched server-side without validation; internal-network/localhost
  access; protocol bypass (file://, gopher://).
- XSS / escaping: unescaped user input rendered to HTML/JS; missing output encoding; unescaped
  header values reflected; missing CSP / X-Frame-Options where a frame-protection golden exists.
- Deserialization / integrity: unvalidated parse of untrusted input; unsigned updates.
- Security misconfiguration: debug mode in prod, default credentials, exposed error details.

Do not double-report issues the deterministic gates already catch (eval(...) injection is
gate-covered). Only report issues you are confident are real vulnerabilities in THIS diff, not
generic hardening advice. If the PR's stated intent is to change auth behavior, judge whether
the change preserves or weakens security. List each distinct real issue, one per item.
```

Miner's note: this is condensed from metaswarm's `security-review-rubric.md` (OWASP A01–A10) +
the security section of `code-review-rubric.md`, scoped to what a diff-review can see (no
runtime/audit-log checks). The "do not double-report gate catches" clause prevents overlap with
metareview's `eval(` gate. To be A/B tested against the current 5-lens set per H1's confirming
experiment.

---

## H1b — Enrich the Architecture lens with data-model + efficiency + scalability (DONE, 2026-08-24)

Per user direction (don't add a 7th lens — enrich the existing architecture lens). Signal:
metareview-realistic under-recalled on `data` (0.778) and `api` (0.778) vs vanilla (0.856) in
`results/failure_mode.json` — the architecture lens's "boundaries, ownership, duplication,
integration shape" wasn't catching data-modeling / efficiency issues vanilla's general prompt
picked up.

### Research (subagent brief, gitignored artifact)
`.pi/subagents/artifacts/outputs/8fa72b4a/research.md` — data-modeling & data-structure best
practices for a diff-review lens (SQL Antipatterns / Use The Index Luke / High Performance MySQL /
PoEAA / Refactoring Databases). Five buckets: schema design, structure efficiency, scalability/
expandability, redundancy, query/write efficiency.

### Changes (metareview repo + harnesseval adapters)
- `metareview/rubrics/artifact-review-rubric.md` Architecture lens: added data-model +
  data-structure design/efficiency, schema invariants, scalability/expandability, redundancy,
  query/write efficiency guidance + blocking criteria (O(n^2) over growing collection, unbounded
  materialization on hot path, N+1, derivable data w/o invalidation).
- `harnesseval/adapters/metareview.py` LENS_PROMPTS["architecture"]: enriched with the same
  data-model/efficiency/scalability/redundancy/query-shape checks (api-direct).
- `harnesseval/adapters/metareview_realistic.py` REALISTIC_PROMPT architecture lens: same
  enrichment (realistic).
- Lens count stays 6 (Feasibility, Completeness, Scope, Architecture, Intent, Security).

### Validated
cal.com/pull/7232 (2 data goldens): the enriched architecture lens produced 10 findings catching
real data-model issues — unbounded findMany w/o pagination, individual deletes instead of batch,
missing composite index -> full scan, nullable boolean w/o default -> three-state flag, new
column w/o @@index on a hot path. Full pipeline: TP=2 rec=0.67, 1/2 data goldens matched,
incr_r=0.95 (17 real-but-ungold). The architecture lens now contributes data-modeling findings
the judge matches against data goldens.

### Confirming experiment (Phase C)
Paired: metareview (enriched arch) vs metareview (old arch) on the data/perf-bearing PRs at 50 PRs
+ CIs. Supports the enrichment if `data`/`perf`-category recall rises w/o regressing total recall
or cratering precision (watch `n_hallucination` — the enriched lens is more verbose, may emit more
FPs; track adj_p). Even stronger: matches vanilla's data recall (0.856) at lower cost.

---

## H1c — Architecture lens: principal-engineer pass (DONE, 2026-08-24)

Research (`claude -p --model opus`, brief at
`.pi/subagents/artifacts/outputs/data_model_review_brief.md`): the architecture lens checked
whether the model is *tidy* (schema mechanics, Big-O, redundancy) but not whether it is *right*.
Senior/principal engineers catch semantic, lifecycle, concurrency, coupling, and LLM-specific
defects that junior reviewers and LLMs miss — especially in LLM-generated code (fluent but
subtly wrong). Five missing dimensions folded into the existing Architecture lens (still 6 lenses):

1. **Semantic correctness** — under-scoped uniqueness (`UNIQUE(email)` vs `UNIQUE(org_id,email)`),
   conflated orthogonal statuses, illegal states the schema permits (no CHECK forbidding
   `shipped_at AND cancelled_at`), soft-delete defeating uniqueness.
2. **Data lifecycle & state transitions** — state machine enforced only in one app method a
   second caller bypasses, terminal states reachable again, temporal overlap/gaps, soft-delete
   not filtered in every read path, audit tables written out-of-transaction.
3. **Concurrency at the data layer** — missing optimistic-concurrency (version/etag),
   read-modify-write without FOR UPDATE, TOCTOU check-then-insert without a unique index,
   money/quantity as float not Decimal, non-idempotent handlers.
4. **Coupling & evolvability** — business rule baked into schema shape (roles as boolean columns),
   internal repr leaked to API contract, destructive migration in one step.
5. **LLM-specific failure modes** — phantom-maintained derived columns (no trigger/increment),
   indexes that don't match the queries in the diff, typed data hidden in JSONB, invented
   relationships, docstrings describing unimplemented behavior.

### Changes
- `metareview/rubrics/artifact-review-rubric.md` Architecture lens: +5 dimensions + blocking
  criteria (illegal state permitted, unguarded transition, lost-update, money as float,
  phantom-maintained column).
- `harnesseval/adapters/metareview.py` LENS_PROMPTS["architecture"] + `metareview_realistic.py`
  REALISTIC_PROMPT: same enrichment (api + realistic).

### Validated
cal.com/pull/7232: architecture lens produced 11 findings hitting the new dimensions — nullable
tri-state boolean (semantic/lifecycle), migration with no DEFAULT/backfill (lifecycle/coupling),
three orthogonal flags with no CHECK (semantic), non-transactional cancel+delete with no
idempotency key (concurrency), singular deletes in a loop (concurrency/efficiency). The lens now
asks "is the model right" not just "is it tidy."

### Confirming experiment (Phase C)
Paired: enriched-arch vs prior-arch on data/perf/concurrency-bearing PRs at 50 PRs + CIs. Watch
total recall (the new pass is more verbose — may emit more FPs; track adj_p/n_hallucination) and
whether concurrency/data-category recall rises. The brief's scoring guidance: weight semantic
correctness + concurrency highest (silent data corruption), lifecycle + LLM-specific high-frequency
in generated diffs, evolvability recoverable (major-not-blocking unless in a public API/migration).

---

## H5 — metareview vs Compound Engineering: cost efficiency + lessons (2026-08-24, partial data)

Question: compound costs ~13× vanilla and metareview ~11× vanilla for similar incremental
recall (compound 0.94, metareview 0.91). Is compound's extra cost a primary factor (it genuinely
finds more bugs) or waste? And what can metareview learn to be more efficient?

### Data (run_batch=20260824-101905, opus-5 medium, apples-to-apples)
- metareview-realistic opus-5 medium: $5.75/cell, 3.88M tok, rec=0.80, inc_r=0.94, ~51 findings
- compound-realistic opus-5 medium:    $5.77/cell, 2.94M tok, rec=0.54, inc_r=0.70, ~40 findings
  (n=4 each; compound has 1 outlier $0 cell + 1 $9.69 cell; metareview is tighter $4.93-$6.51)
- At medium, they are ~the same cost ($5.75 vs $5.77). compound is NOT uniformly more expensive.

### Where compound's "13×" reputation comes from: opus-5 xhigh
- compound opus-5 xhigh: $12.32/cell avg, 9.84M tok — driven by TWO expensive opus-5 orchestrator
  passes (8.3M + 4.3M / 10.3M + 6.6M sonnet-5) per cell. metareview xhigh: $8.88/cell, 6.16M tok.
- compound's xhigh cost is inflated by the orchestrator dispatching personas AND a synthesis pass,
  both on opus-5, plus persona subagents routing to sonnet-5 (23% of compound's tokens are
  sonnet-5, not haiku). metareview's lenses stay haiku (0% of cost).
- So the "compound is more expensive" finding is **xhigh-specific + persona-tier-specific**, not
  a uniform property. At medium the two are cost-equivalent.

### Primary factor vs lessons for metareview
The cost difference is NOT "compound finds more bugs" (at medium, metareview actually finds MORE:
51 vs 40 findings, rec 0.80 vs 0.54). It's:
1. **Persona model tier**: compound routes ~23% of tokens to sonnet-5 (a mid-tier persona model),
   not haiku. metareview's lenses are haiku (free). This is the single biggest cost lever — and
   it's a place metareview could *learn the opposite lesson*: compound pays for stronger persona
   models and gets slightly higher adj_precision on some cells, but metareview's haiku lenses
   already match its recall at lower cost.
2. **xhigh amplification**: compound's two-pass (dispatch + synthesis) on the orchestrator
   doubles the xhigh reasoning cost. metareview is single-pass (orchestrator + lens fanout in one
   turn). Lesson: metareview's single-pass design is more xhigh-efficient.
3. **Roster size variance**: compound's risk-driven roster is variable (up to 21 distinct
   persona sources in one cell vs metareview's fixed 6 lenses, max 13 sources). More personas =
   more fanout = more orchestrator context. metareview's fixed 6 is cheaper and more predictable.

### Lessons metareview can take from compound (to be MORE efficient, not less)
- **Keep lenses on haiku** (the data confirms haiku lenses = free; compound's sonnet-5 personas
  are 23% of its cost for no recall win at medium). metareview already does this — keep it.
- **Single-pass synthesis** (metareview's one-turn dispatch+aggregate beats compound's two-pass
  on xhigh cost). Don't adopt compound's separate synthesis pass.
- **Conditional roster COULD trim cost**: compound's risk-driven selection (skip personas whose
  surface is absent) is a real efficiency idea metareview could borrow — metareview's 6 lenses
  always all run even when (e.g.) a diff has no security surface. Making the security/architecture
  lenses conditional on diff signals could cut lens fanout cost. But since lenses are already
  ~free (haiku), the savings are marginal — the lever is the orchestrator, not the lenses.
- **The real cost lever for BOTH**: the orchestrator is 65-84% of cost. metareview's orchestrator
  reads the full diff + plans on opus-5. Caching orchestrator context across the 6 lens dispatches
  (Anthropic prompt caching) or downgrading the orchestrator to sonnet for low-risk diffs are the
  real efficiency knobs — not the lenses.

### Confirming experiment (Phase C)
At 50 PRs + CIs, compare metareview vs compound at matched (model, effort): is compound's
higher xhigh cost justified by higher adj_precision or real-but-ungold count? If metareview
matches compound's recall at lower xhigh cost, metareview's design (fixed haiku lenses +
single-pass) is the more efficient architecture — report as a structural finding. If
compound's sonnet-5 personas give it a precision edge metareview can't match, that's a lesson
to optionally upgrade metareview's lenses to sonnet (still cheap) — test as H3.

---

## H5b — metareview vs Compound Engineering on CODEX (gpt-5.6-sol) — the conclusion flips (2026-08-24)

Re-ran the H5 cost/quality analysis on the codex (gpt-5.6-sol) cells only. The codex picture
INVERTS the opus-5 conclusion from H5.

### Data (run_batch=20260824-101905, codex gpt-5.6-sol, n=3-4 per cell)
- vanilla: 86K-1.03M tok, rec 0.57-0.59, adj_p 0.85-0.97, inc_r 0.71-0.78
- metareview-realistic: 1.09M (med) / 2.13M (xhigh) tok, rec 0.55-0.57, inc_r 0.82, 17-21 findings
- compound-realistic: 860K (med) / 990K (xhigh) tok, rec 0.70-0.75, inc_r 0.92-0.94, 35-38 findings

### The flip
On opus-5 (H5): metareview and compound were cost-equivalent at medium; metareview found more.
On codex: **compound dominates metareview on BOTH cost (1.6× vs 2.8× vanilla tokens) AND quality**
(rec 0.70-0.75 vs 0.55-0.57, inc_r 0.92-0.94 vs 0.82, 35-38 vs 17-21 findings). compound gets ~2×
the findings per token on codex.

### Why (the codex-specific lessons)
1. **metareview's xhigh is wasted spend on codex**: 2.13M tok (2× medium) for the same recall
   (0.55 vs 0.57). The xhigh reasoning improves the orchestrator's planning but not the lens
   *dispatch* quality on codex. compound's xhigh is productive (rec 0.70->0.75, flat tokens).
2. **compound's severity-banded persona roster (P0/P1/P2) is more token-efficient than
   metareview's 5+1 artifact-shape lenses on codex.** compound's P0/P1/P2 findings = 86% of its
   output; metareview's lenses spread thinner (architecture 28%, feasibility 21%, completeness
   15%). compound gets ~2× findings/token.
3. **Orchestrator is 100% of cost on codex** (codex subagents bill to gpt-5.6-sol; no haiku
   split visible). The "lenses are free (haiku)" lesson from opus does NOT apply on codex — the
   lens fanout IS the cost, so fanout efficiency matters here.

### Lessons metareview can take from compound (codex-specific)
- **Severity-band the lens output** (P0/P1/P2 + targeted focus per lens) to raise
  findings-per-token, borrowing compound's structure. metareview's artifact-shape lenses
  (feasibility/completeness/scope/...) don't map to severity the way compound's personas do.
- **Investigate why metareview xhigh doesn't convert to findings on codex** (the orchestrator's
  xhigh thinking may not improve dispatch quality on codex, unlike opus). Possibly cap metareview
  at medium on codex, or fix the xhigh dispatch.
- **Conditional lens selection matters MORE on codex** (lenses aren't free here — they're the
  cost). Borrow compound's risk-driven roster: skip lenses whose surface is absent. This is the
  real efficiency lever on codex, unlike opus where lenses are free.

### Open bug (not a cost story): superpowers-realistic on codex is broken
rec 0.11-0.12, adj_p 0.12 — the codex subagent dispatch for superpowers isn't producing
matchable findings (same class as the pre-materialize-fix codex bug). Investigate separately.

### Caveat
n=3-4 per cell; codex cost is $0 (OAuth) so tokens are the cost proxy. Phase C (50 PRs + CIs)
needed to claim compound > metareview on codex. But the direction is clear and opposite to opus.
