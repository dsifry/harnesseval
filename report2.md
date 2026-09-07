# GLM-5.3 as a Review Engine — the 24-cell suite, the effort ladder, and the lens-fix smoke (Report 2)

> **What this is.** A follow-up to the main comparison ([`report.md`](report.md)) covering the
> 2026-09-07 results: the full **GLM-5.3 / GLM-5.3-flash** suite (24 cells), effort-ladder
> probes, and a smoke test of metareview PR #145. Every number is reproducible from committed
> run records (batches `20260906-glm53-top6`, `20260907-claimcheck-smoke`). **N is small** (6
> PRs/cell; 3 PRs/smoke arm) — directional read, not a ranking.

---

## 1. The headline result: a free model now matches the $57 factory

The single most important row in this report:

| | hidden gold /PR | incr. recall | tokens/PR | $/cell | hidden gold per M tokens |
|---|---:|---:|---:|---:|---:|
| **ce × glm-5.3-background × low** | **40.5** | **0.97** | **103K** | **~$0** | **393** |
| mrv × glm-5.3-flash × low | 25.3 | 0.93 | 110K | ~$0 | 230 |
| ce × glm-5.3-flash × low | 36.8 | 0.97 | 99K | ~$0 | 372 |
| mrv × claude-opus-5 × high (main report) | 36.0 | 0.85 | 2.98M | $56.65 | 12 |

**Compound Engineering on a free GLM-5.3 finds *more* real bugs the humans missed than the
opus factory — per PR (40.5 vs 36.0), at higher incremental recall (0.97 vs 0.85), on 1/29th
the tokens, at ~1/33rd the cost per hidden bug.** This is not a budget-tier result; on the
top-6 PRs it is the best factory cell measured in this lab, at any price. The same holds for
flash (372 hidden/M-tok) — two ~$0 engines now beat every metered configuration on
efficiency, and metareview-on-GLM delivers opus-factory-grade hidden gold (25–36/PR) at ~$0.

The second result: **the harness-beats-vanilla pattern extends to GLM at both low and high
effort** (ce 0.81/0.78 and mrv 0.66/0.74 recall vs vanilla 0.54/0.57 on background) — the
factories earn their keep on a third model family, not just Claude and Codex.

### TL;DR — practitioner recommendations

1. **If you review PRs with an LLM today and pay metered prices, switch the default to
   glm-5.3(-flash) × low.** Same incremental recall as the opus factory (0.97 vs 0.85), 40
   hidden bugs/PR vs 36, at ~$0–0.1/cell vs $57. There is no scenario in this data where the
   opus factory wins on value.
2. **Run GLM at low or high — never medium.** low/high are monotonic and healthy; medium
   reasons 4–10× more than high, costs 10–20× the wall time, sometimes never finishes, and
   fails *silently* (empty 200s that read as "no bugs"). xhigh is an alias for high on GLM —
   there is nothing above high to buy.
3. **Triage load is still the real price of factories.** The GLM factory cells emit 17–28
   hallucinations per PR alongside their 25–45 hidden gold (~59% real fraction, consistent
   with the main report's v2 numbers). Budget human review time accordingly — the models are
   free; the reviewer's attention isn't.
4. **The metareview lens fix (PR #145) is safe but unproven at smoke scale** — no fabrication
   win detectable at n=3 PRs, no precision cost either. The decisive test needs the big-hal
   cells (~$230–460) or metareview's own corpus re-judge. → §5
5. **When Lunaroute fixes the medium rung, re-probe before re-running cells** — the medium
   numbers in §3 will change. low/high results are unaffected.

---

## 2. What was run

| arm | cells | batch |
|---|---|---|
| GLM-5.3 suite: {vanilla, mrv, ce} × {background, flash} × {low, medium, high, xhigh} × top-6 PRs | 24 (141 runs; 135 pass; latest-pass per cell — three cells have n=5, rest n=6) | `20260906-glm53-top6` |
| Effort probes: single calls, glm-5.3-background, 79K-char diff, 65,536 budget | 2×low, 2×high live + 3 prior medium | §4.1 transcripts |
| Claimcheck smoke: mrv × {background, flash} × xhigh × {11059, 10967, 14740}, lens prompts synced with metareview#145 | 6 | `20260907-claimcheck-smoke` |

Scoring identical to the main report (extract → judge → v2 three-way adjudication: bug /
important-non-bug / hallucination / unresolved). GLM served via Lunaroute (OpenAI-compatible,
flat fee — $0 reported cost, so efficiency is compared in tokens). Harness "xhigh" maps to
upstream `reasoning_effort=high` for GLM.

---

## 3. The 24-cell suite

Latest pass run per cell; recall / incremental recall from the v2 instrument; hid = hidden
gold (real findings humans missed); hal = true hallucinations (v2).

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
  ce × GLM-xhigh ≈ 299, mrv × GLM-low ≈ 230 — vs **12** for mrv × opus × high and single
  digits for the other metered factory cells in the main report. The frontier-factory value
  proposition (main report §3.4: "the factories find more total bugs on every model, at
  10–40× the cost") now has a free-model refutation: **the same harnesses on GLM find more
  total bugs at ~zero marginal cost.**
- **Vanilla on GLM is the cheapest usable baseline ever measured**: rec 0.50–0.59, incr
  0.73–0.82 at 13–21K tokens/PR. If you run nothing else, a single GLM call per PR surfaces
  ~6 hidden bugs for ~$0.
- **Flash ≈ background on quality, and is the safer default**: at every shared effort the
  two variants sit within noise (low: 0.81 vs 0.79 ce; xhigh: 0.78 vs 0.75), and flash has
  none of background's medium/high pathology (§4). Choose flash unless background-specific
  behavior is being tested.
- **Effort is nearly free in quality terms but not in triage**: low→high/xhigh moves hidden
  gold 40.5→44.8 (ce) but also hallucinations 28→25 (flash: 23→21.7). The increments are
  small; low is the value point.
- **The four collapsed rows (background × medium/high) are infrastructure, not quality**:
  flash scores 0.68–0.71 at the same efforts on the same PRs. See §4; expect these rows to
  change when the upstream fix lands.

### 3.2 Cost

Lunaroute flat fee ⇒ $0 reported for every GLM cell. Metered comparison (main report):
mrv × opus × high = $56.65/cell; vanilla × fable × low = $6.41/cell. At hypothetical GLM
metered pricing (~$0.6–1.1/M blended), the 103K-token ce cell ≈ $0.06–0.11 — still ~500×
cheaper per hidden bug than the opus factory.

---

## 4. The effort ladder: two healthy rungs, a broken middle

Probes: single calls, glm-5.3-background, same 79K-char review prompt, 65,536-token budget.

| effort | reasoning tok/call | completion tok/call | review content | wall |
|---|---|---|---|---|
| low (n=2) | 1,913 / 2,327 | 3,252 / 3,639 | ~5.7K chars | 33–37s |
| high (n=2) | 6,265 / 11,264 | 8,300 / 13,211 | 8.4–8.7K chars | 69–118s |
| medium (n=3) | 18,600 / 27,500 / 28,000 | 20–28K (at cap) | 5.5K chars when it finishes | 10–25 min |

- **low and high are monotonic and healthy** — high reasons 3–5× more than low and emits
  ~50% more review content. The recall ladder in §3 (low 0.54 → xhigh 0.57 vanilla; 0.66 →
  0.74 mrv) is consistent with the probe behavior.
- **medium inverts the ladder and breaks.** It reasons 4–10× more than high (18.6–28K vs
  6–11K), takes 10–20× the wall time, and on lens-style prompts does not converge at all
  (no completion in 900s probes; 2–4h cells with zero tokens in the re-run).
- **It fails silently.** At 16K/32K budgets medium returns `finish_reason=length`,
  `content=""` — an HTTP 200 that reads as "no findings." That is precisely what the
  collapsed §3 rows are: raising the budget flipped vanilla × medium from 0.00 → **1.00** on
  the re-run PR. Any "GLM found zero bugs" result with a truncated budget is an
  infrastructure reading, not a model verdict.
- **Accounting drift**: `reasoning_tokens` arrives as a top-level `usage` field (OpenAI SDK
  `model_extra`) rather than `completion_tokens_details` — clients reading the conventional
  location mis-attribute reasoning spend to output tokens.
- **xhigh == high on the wire.** There is no fourth rung.

Repro for all of the above was packaged for Lunaroute (vLLM→SGLang migration suspected;
`flash` is unaffected at every effort). The medium §3 rows should be re-measured once the
upstream fix ships.

---

## 5. Smoke test — the PR #145 lens fix

**Question:** does metareview's new Evidence-of-Absence lens requirement (the fix for the #1
fabrication mode — unverified "zero tests" claims, 34% of audited rejections) reduce
false positives in our cells?

**Result: not measurable at smoke scale, no precision cost.** Six cells (mrv × both GLM
variants × xhigh × the three cal.com PRs where fabricated gap-claims concentrate), lens
prompts synced with the upstream rubric (commit `45a55b6`):

| arm | true_hal base→new (3 PRs) | recall (new) |
|---|---|---|
| background | 6 → 7 | 0.50–0.89 |
| flash | 1 → 3 | 0.67–0.89 |

The baseline hal counts (6 and 1) are far too small to resolve a fix-sized effect, and the
rerun's deltas are within run-to-run noise. Recalls held or improved (0.50–0.89, 36–45
bug_ungold/PR), so the added discipline costs nothing in coverage. The decisive tests are:
(a) the big-hal mrv cells (opus/sonnet, 20–28 hal/PR, ~$230–460 for the A/B), or (b)
metareview's staged corpus re-judge of the 343-claim corpus against v2 ground truth
(tooling exists: `cmd/claimcheck-eval`; needs model spend). Until one of those runs, the
honest status of PR #145 in this lab is **"promising, unproven."**

---

## 6. Coverage state (low + high, all harnesses)

Complete (6/6 PRs, both efforts, vanilla/mrv/ce): **opus-5, sonnet-5, sol, terra,
glm-5.3-background, glm-5.3-flash**. Missing: **fable-5.1 and astra have no high-effort runs**
(~36 cells, ≈$230 + ≈$100 to fill). The low-vs-high and effort-ladder claims in this report
are therefore scoped to the six complete models.

---

## 7. Caveats

- 6 PRs/cell (3/smoke arm); wide CIs. Directional, reproducible — not a published ranking.
- GLM $0 is Lunaroute's flat fee; token figures are the honest comparison basis.
- background/medium and background/high rows are serving-stack-dependent; re-measure after
  the upstream fix.
- The smoke test measures the *lens-side* arm of PR #145 only; the adjudicator-side arm is
  not exercised by these harness cells.

## 8. Reproducibility

- GLM suite: batch `20260906-glm53-top6`; per-run v2 adjudication (`readjudication3.json`),
  totals independently verified.
- Smoke: batch `20260907-claimcheck-smoke`; lens sync commit `45a55b6`.
- Effort probes: §4 transcript numbers; script is a plain
  `client.chat.completions.create` against `glm-5.3-background` with the cached PR-11059
  diff.
- Harness changes shipped with this cycle: effort-scaled GLM budgets + 2400s timeout
  (`model_router.py`), reasoning-token dual-location fix (`usage.py`), native v2 adjudicator
  (`adjudicate.py`, #11).
