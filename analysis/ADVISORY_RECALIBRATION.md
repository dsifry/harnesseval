# Advisory-channel recalibration (2026-09-09)

## The measurement bug that started this

Formal acceptance reported "advisory distinct 1.3–2.5/PR vs CE's 8–10.5" — the one remaining
gap. A full-channel audit found this was an **accounting artifact**: every advisory number
counted only the rj3-re-adjudicated slice (findings the in-harness judge had called
real_but_ungold/hallucination that rj3 upgraded to important_non_bug). The primary advisory
channel — findings the in-harness judge passes as important_non_bug directly — was never
counted. Both harnesses were measured the same way, so comparisons were internally
consistent, but both undercounted the true advisory output by ~10x.

## Corrected full-channel state (15 ceiling PRs, judge-matched vs opus ceiling)

| channel | emitted/PR | coverage of 163 ceiling concerns | ceiling-worthy of emitted |
|---|---:|---:|---:|
| CE (compound-realistic) | 13.6 | 69/163 = 42% | 55% |
| mrv 0.11.1 | 18.7 | 83/163 = 51% | 61% |
| **mrv 0.11.2-rc3** (families + tags) | 20.4 | **95/163 = 58%** | **70%** |

**mrv 0.11.1 already led CE on the advisory channel** (51% vs 42% coverage, 61% vs 55%
worthiness) once measured correctly. The "advisory gap" never existed.

## The 0.11.2 changes (validated by A/B on the same 17 PRs)

1. **Five advisory hunt families** (from a 29-concern manual audit of the ceiling):
   coverage gaps, hot-path regressions, ships-inert features, silent public-surface
   changes, rolling-deploy skew. Plus explicit suppression of the audit's nit classes
   (stale comments/doc-drift, hypothetical misuse with no present trigger).
2. **Mandatory [BUG]/[ADVISORY] output tags** with an embedded decision rule ("does the item
   claim the code does the wrong thing?"). Tag adoption ~98%. The extractor preserves tags
   verbatim (framework-neutral change). Tags give advisory content a lane that does not
   require masquerading as a bug claim, and flow into both judge prompts.
3. Rejected by A/B: imperative framing alone (rc2) — no measurable effect. The constraint
   was channel structure, not motivation.

Net effect (rc3 vs 0.11.1, full channel): coverage +7 pts (51%→58%), ceiling-worthiness
+9 pts (61%→70%), volume similar (18.7→20.4/PR).

## Remaining work (quality, not volume)

- Coverage is 58%; the ratifiable ceiling is ~7/PR (69% of opus's 10.7 enumeration, per
  manual audit) while we emit ~20/PR — the open problem is curation: ~30% of emissions are
  off-ceiling (below-bar or judge-overruled content). Per the ratified principle this is a
  quality-bar question for the gates, not a numeric cap.
- The formal acceptance report's advisory column should be recomputed on the full channel
  before any future comparison (analysis/ACCEPTANCE_0111_FINAL.md §5 is now known to
  undercount both sides).

## Artifacts

- Ceiling: analysis/advisory_ceiling/ (15 PRs, 163 concerns, opus OAuth enumeration)
- A/B batches: 20260909-mrv0112-ab2 (rc1), -ab3 (rc2), -ab4 (rc3)
- Adapter changes: harnesseval/adapters/metareview.py (LENS_SYSTEM v0.11.2-rc3),
  harnesseval/extract.py (tag preservation)
