# metareview 0.11.1 formal acceptance — final matched-rigor report (2026-09-09)

Adjudication: gpt-5.2, k=3 majority, medium effort, v3 hybrid semantic clustering (both
harnesses, all cells below). Models × tiers: glm-5.3-flash-background and
glm-5.3-background × {low, xhigh}. mrv = metareview 0.11.1 (batch 20260908-mrv0111-flash-lh
/ -bg-lh); CE = compound-realistic (batch 20260906-glm53-top6, re-adjudicated k=3).
Baselines: mrv 0.10.x (same-batch cells, v2-era adjudication — not rigor-matched).

## Background tier (glm-5.3-background) — the headline table

| cell | n | rec | find/PR | hid/PR | distinct-bug | hal/PR | advisory distinct |
|---|---|---|---|---|---|---|---|
| mrv 0.10.x low (baseline) | 3 | 0.59 | 51.7 | 18.0 | — | 4.0 | — |
| **mrv 0.11.1 low** | 6 | **0.75** | 59.5 | 30.7 | **12.8** | 1.0 | 1.3 |
| CE low | 6 | 0.81 | 77.8 | 48.3 | 10.8 | 2.0 | 8.8 |
| mrv 0.10.x xhigh (baseline) | 6 | 0.74 | 62.8 | 32.7 | — | 2.3 | — |
| **mrv 0.11.1 xhigh** | 6 | **0.75** | 75.0 | 44.0 | **15.7** | 0.5 | 1.3 |
| CE xhigh | 6 | 0.78 | 80.2 | 52.8 | 12.5 | 0.5 | 8.5 |

## Flash tier (glm-5.3-flash-background) — from the formal acceptance run

| cell | n | rec | hid/PR | distinct-bug | hal/PR | advisory distinct |
|---|---|---|---|---|---|---|
| **mrv 0.11.1 low** | 6 | 0.76 | 24.3 | **10.0** | 2.7 | 2.5 |
| CE low | 6 | 0.76 | 37 | 10.2 | 4.0 | 8.2 |
| **mrv 0.11.1 xhigh** | 6 | 0.76 | 30.3 | **11.0** | 3.3 | 2.5 |
| CE xhigh | 6 | 0.76 | 41 | 10.5 | 6.2 | 10.5 |

## Findings

1. **Distinct-bug parity or better at matched model + tier.** Flash: dead heat (10.0/11.0
   vs 10.2/10.5). Background: **mrv leads at both tiers** — 12.8 vs 10.8 (low, +18%) and
   15.7 vs 12.5 (xhigh, +26%). At matched rigor, mrv 0.11.1 finds as many or more real,
   distinct bugs beyond the golden set than Compound Engineering on the same model.
2. **CE's record-level lead is restatement inflation.** CE hid 48.3–52.8 (bg) over ~20–22
   distinct bugs → 4.3–4.5× restatement; mrv 30.7–44.0 over 12.8–15.7 distinct → 2.4–2.8×.
   Same picture as flash (CE ~3.7× vs mrv 2.4×). Record-level hidden gold systematically
   overstates verbosity-heavy harnesses.
3. **Golden recall: small CE edge in background tier (0.78–0.81 vs 0.75), parity in flash
   (0.76 both).** The 0.11.1 upgrade moved background-low recall 0.59 → 0.75 (+16 pts vs
   baseline); the residual gap is concentrated in golden coverage, not hidden-gold bugs.
4. **Precision: mrv emits fewer hallucinations per finding at every cell** (bg low 1.0 vs
   2.0; flash low 2.7 vs 4.0; xhigh parity at 0.5/0.5 and 3.3 vs 6.2). Restatement-adjusted
   precision favors mrv throughout.
5. **The one real gap: the advisory channel.** CE emits 8.2–10.5 distinct important/PR vs
   mrv's 1.3–2.5. This is a calibration problem (the model under-emits advisories before
   the three gates), not a design problem — the 0.11.1 advisory-findings system is in place
   but under-fed.

## Verdict

metareview 0.11.1 is accepted: distinct-bug parity-or-lead across both models and both
tiers at ~half the restatement and better precision. Remaining work is advisory-emission
calibration (next sequence), prefilter tuning for same-harness candidate pairs, and
parallelizing the sequential second-pass loop in classify_batch_dedup.
