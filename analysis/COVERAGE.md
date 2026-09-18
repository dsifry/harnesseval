# Coverage & sampling disclosure — final calibrated report (2026-09-16)

**Data freeze:** 2026-09-16 09:35 (all data-generating lanes deliberately stopped; the GLM fill
lanes `logs/mx_glm_fullmatrix_run.log` and `logs/mx_glm_vanilla_full_run.log` last wrote at
09:09/09:31 and were verified dead at 09:45). This table was re-verified after the freeze with the
handoff §5.5 coverage query and with `tools/verify_hitlist.py --verbose` (hitlist: 111 rows —
82 done, 29 remaining, all 29 fable). **Nothing in this document or in `REPORT.md` uses
post-freeze data.**

**Selection basis.** One healthy scored run per (model × framework × effort × PR), selected by
`tools/final_report_extract.py`: health rule (no error, tokens>0, findings or ≤20k tokens) +
scored rule (`tp`/`fn` present) + era rule (handoff §5.2: vanilla reuses healthy runs from any
batch; compound/metareview must be batch `20260910-mrv0120-manifold`), preferring the current
campaign batch, then the fable vanilla batches, then newer legacy batches. Where "+N dup" is
shown, additional healthy scored runs existed for the same cell and PRs; they were not pooled.

**Instruments.** Precision-side verdicts come from rj3 (v3.1 clustered, k=1 — the campaign
judgement lock) where the selected run has `readjudication3.json`, else the in-run v2 three-way
adjudicator (`harnesseval/adjudicate.py`, 2026-09-07), else the v1 binary in-run adjudicator
(pre-2026-09-07 vanilla reuse runs; known to over-count hallucinations — see REPORT.md §2.3.3).
"+"-joined entries mean the cell mixes instruments across its selected runs.

**Judges.** Judge per model row (matcher and adjudicator): Anthropic-model rows and GLM rows are
judged by **gpt-5.2**; OpenAI rows (sol/terra/astra) by **claude-opus-4-5-20251101**. The judge is
constant within each model row, so framework comparisons within a row are judge-consistent.

## The matrix (8 models × 3 frameworks × 3 efforts) and its full-50 backing

top-6 = the six severity-weight-hardest PRs (CAMPAIGN_GLOSSARY.md; `manifold_top6_hitlist.csv`).

| model | framework | effort | top-6 | full-50 | instrument | judge | run dates | notes |
|---|---|---|---|---|---|---|---|---|
| claude-fable-5-1 | vanilla-engineered | low | full 6/6 | full 50/50 | rj3 | gpt-5.2 | 2026-09-06 | |
| claude-fable-5-1 | vanilla-engineered | medium | full 6/6 | partial 17/50 | v1 | gpt-5.2 | 2026-09-06 | v1 = adjP biased low |
| claude-fable-5-1 | vanilla-engineered | high | full 6/6 | partial 14/50 | v1 | gpt-5.2 | 2026-09-06 | v1 = adjP biased low |
| claude-fable-5-1 | compound-realistic | low | **PARTIAL 2/6** | partial 7/50 | v2 | gpt-5.2 | 2026-09-13 | account rate-capped |
| claude-fable-5-1 | compound-realistic | medium | **PARTIAL 1/6** | partial 5/50 | v2 | gpt-5.2 | 2026-09-13 | account rate-capped |
| claude-fable-5-1 | compound-realistic | high | **PARTIAL 1/6** | partial 4/50 | v2 | gpt-5.2 | 2026-09-13 | account rate-capped |
| claude-fable-5-1 | metareview-realistic | low | **PARTIAL 1/6** | partial 4/50 | v2 | gpt-5.2 | 2026-09-13 | account rate-capped |
| claude-fable-5-1 | metareview-realistic | medium | **PARTIAL 1/6** | partial 4/50 | v2 | gpt-5.2 | 2026-09-13 | account rate-capped |
| claude-fable-5-1 | metareview-realistic | high | **PARTIAL 1/6** | partial 4/50 | v2 | gpt-5.2 | 2026-09-13 | account rate-capped |
| gpt-6-astra | vanilla-engineered | low | full 6/6 | ≈full 48/50 | rj3/v2 | claude-opus-4-5 | 2026-09-12 | +6 dup |
| gpt-6-astra | vanilla-engineered | medium | full 6/6 | ≈full 48/50 | rj3 | claude-opus-4-5 | 2026-09-12 | +6 dup |
| gpt-6-astra | vanilla-engineered | high | full 6/6 | ≈full 48/50 | rj3 | claude-opus-4-5 | 2026-09-12 | +6 dup |
| gpt-6-astra | compound-realistic | low | full 6/6 | partial 23/50 | rj3/v2 | claude-opus-4-5 | 09-12/09-14 | |
| gpt-6-astra | compound-realistic | medium | full 6/6 | partial 10/50 | rj3/v2 | claude-opus-4-5 | 09-12/09-14 | |
| gpt-6-astra | compound-realistic | high | full 6/6 | partial 12/50 | rj3/v2 | claude-opus-4-5 | 09-12/09-14 | |
| gpt-6-astra | metareview-realistic | low | full 6/6 | partial 13/50 | rj3 | claude-opus-4-5 | 2026-09-12 | |
| gpt-6-astra | metareview-realistic | medium | full 6/6 | partial 13/50 | rj3/v2 | claude-opus-4-5 | 09-12/09-14 | |
| gpt-6-astra | metareview-realistic | high | full 6/6 | partial 34/50 | rj3/v2 | claude-opus-4-5 | 09-12/09-14 | |
| gpt-5.6-sol | all 6 harness cells | l/m/h | full 6/6 | 48–50/50 | v2 | claude-opus-4-5 | 09-10/09-11 | |
| gpt-5.6-sol | vanilla-engineered | l/m/h | full 6/6 | full 50/50 | v2 | claude-opus-4-5 | 2026-09-12 | +6/+20/+12 dup |
| claude-opus-5 | vanilla-engineered | low | full 6/6 | **top-6 only 6/50** | rj3 | gpt-5.2 | 08-25/08-26 | held by operator decision |
| claude-opus-5 | vanilla-engineered | medium | full 6/6 | **top-6 only 6/50** | v1 | gpt-5.2 | 2026-08-25 | v1 = adjP biased low; +12 dup |
| claude-opus-5 | vanilla-engineered | high | full 6/6 | **top-6 only 6/50** | rj3 | gpt-5.2 | 08-25/08-26 | held by operator decision |
| claude-opus-5 | compound-realistic | l/m/h | full 6/6 | full 50/50 | v2 | gpt-5.2 | 09-11/09-12 | |
| claude-opus-5 | metareview-realistic | l/m/h | full 6/6 | **top-6 only 6/50** | v2 | gpt-5.2 | 2026-09-14 | 36 re-runs (era rule) |
| glm-5.3-vision-background | vanilla-engineered | l/m/h | full 6/6 | partial 30–31/50 | v2 | gpt-5.2 | 2026-09-14 | **6/6 pre-fix** (incident window) |
| glm-5.3-vision-background | compound-realistic | low | full 6/6 | full 50/50 | v2 | gpt-5.2 | 2026-09-11 | 6/6 pre-fix; 6 runs without per-model token split |
| glm-5.3-vision-background | compound-realistic | medium | full 6/6 | partial 18/50 | v2 | gpt-5.2 | 09-11/09-12 | 6/6 pre-fix; 6 no-pmu |
| glm-5.3-vision-background | compound-realistic | high | full 6/6 | partial 23/50 | v2 | gpt-5.2 | 09-12…09-14 | 6/6 pre-fix; 6 no-pmu |
| glm-5.3-vision-background | metareview-realistic | low | full 6/6 | full 50/50 | v2 | gpt-5.2 | 2026-09-10 | **6/6 pre-fix**; 6 no-pmu |
| glm-5.3-vision-background | metareview-realistic | medium | full 6/6 | partial 24/50 | v2 | gpt-5.2 | 09-11…09-15 | 5/6 pre-fix |
| glm-5.3-vision-background | metareview-realistic | high | full 6/6 | partial 14/50 | v2 | gpt-5.2 | 09-15/09-16 | 2/6 pre-fix |
| gpt-5.6-terra | all 9 cells | l/m/h | full 6/6 | 47–50/50 | v2 | claude-opus-4-5 | 2026-09-11 | vanilla +6 dup/effort |
| claude-sonnet-5 | vanilla-engineered | l/m/h | full 6/6 | **top-6 only 6/50** | rj3 | gpt-5.2 | 08-25/08-26 | held by operator decision |
| claude-sonnet-5 | compound-realistic | l/m/h | full 6/6 | full 50/50 | v2 | gpt-5.2 | 2026-09-11 | |
| claude-sonnet-5 | metareview-realistic | l/m/h | full 6/6 | **top-6 only 6/50** | v2 | gpt-5.2 | 2026-09-14 | 36 re-runs (era rule) |
| glm-5.3-flash-background | vanilla-engineered | low | full 6/6 | partial 31/50 | v2 | gpt-5.2 | 2026-09-16 | post-fix; +6 dup |
| glm-5.3-flash-background | vanilla-engineered | medium | full 6/6 | partial 31/50 | v2 | gpt-5.2 | 09-14/09-16 | 1/6 pre-fix; +5 dup |
| glm-5.3-flash-background | vanilla-engineered | high | full 6/6 | partial 31/50 | rj3/v2 | gpt-5.2 | 09-06/09-16 | 1/6 pre-fix; +5 dup |
| glm-5.3-flash-background | compound-realistic | low | full 6/6 | full 50/50 | v2 | gpt-5.2 | 2026-09-12 | 6/6 pre-fix; 6 no-pmu |
| glm-5.3-flash-background | compound-realistic | medium | full 6/6 | partial 20/50 | v2 | gpt-5.2 | 2026-09-12 | 6/6 pre-fix; 6 no-pmu |
| glm-5.3-flash-background | compound-realistic | high | full 6/6 | partial 24/50 | v2 | gpt-5.2 | 09-12…09-14 | 6/6 pre-fix; 6 no-pmu |
| glm-5.3-flash-background | metareview-realistic | low | full 6/6 | full 50/50 | v2 | gpt-5.2 | 2026-09-11 | **6/6 pre-fix** |
| glm-5.3-flash-background | metareview-realistic | medium | full 6/6 | full 50/50 | v2 | gpt-5.2 | 2026-09-11 | 6/6 pre-fix |
| glm-5.3-flash-background | metareview-realistic | high | full 6/6 | partial 24/50 | v2 | gpt-5.2 | 09-13…09-15 | 6/6 pre-fix |

`xhigh` (legacy, out of the matrix by operator decision) exists only as vanilla top-6 rows for
opus, sonnet, glm-flash, glm-5.3-background, terra, sol, gpt-5.2, kimi-k3, glm-5.2-vision-flex and
is not reported except as a capability-floor aside.

## Why each gap exists

- **Fable compound/metareview (the only top-6 gaps).** `claude-fable-5-1`'s account was rate-capped
  for ~3 days (`logs/campaign_fable.log`, last write 2026-09-13 09:35; orchestrator alive, probing
  every 10 min). All 29 outstanding hitlist rows are fable. The few compound/mrv runs that landed
  (1–2 of 6 top-6 PRs per cell) are shown in REPORT.md §3.2 as *coverage gaps, not results*.
- **Opus/sonnet vanilla = top-6 only.** Held deliberately by operator decision (banked 2026-09-13):
  their vanilla cells reuse healthy August-era runs (era rule allows it for vanilla), and no
  full-50 vanilla fill was queued. Their compound cells are full 50/50; their metareview cells are
  the 36 top-6 re-runs required by the era rule (current-campaign binaries).
- **GLM partial cells.** The two fill lanes were ~40% done at the freeze (fullmatrix [44/247],
  vanilla [165/281] at last write) and were stopped for the freeze. `--skip-batch` health-gating
  means re-running resumes without redoing healthy cells.
- **Astra compound/metareview partial.** Fill was never queued to 50; the cells are complete on
  the top-6 but not beyond.

## Provider incident (2026-09-14/15) disclosure

"pre-fix" above = the run's `registered_at` precedes 2026-09-15 16:00 local (2026-09-15 23:00 UTC),
the conservative cutoff for the Lunaroute gateway / streaming / SDK fixes (handoff §6 item 8). All
GLM cells contain pre-fix runs except glm-vis metareview medium (5/6) and high (2/6) and the
glm-flash vanilla cells (which selected the post-fix 2026-09-16 runs). The incident was
operational (wedged calls, silent SDK retries), not a prompt or dataset change; every affected run
passed the health gate, but per-cell exposure is listed above and repeated in REPORT.md §2.3.4.

## What this does to each claim's strength

- **Framework (harness vs vanilla) deltas, per model row:** measured on the same 6 PRs with paired
  CIs — *strong* (complete cells only).
- **GLM cost/benefit recommendation:** measured on the same 6 PRs — *strong on cost ratios*
  (prices are list rates, retrieval 2026-09-16), *moderate on quality* (pre-fix confound on every
  headline GLM cell; direction of any bias unknown but the incident was reliability-side).
- **Model-tier comparisons (flash vs vision):** complete top-6 — *moderate* (same incident
  caveat; vision tier drops ~39–201 real beyond-gold findings per cell at some settings, which is
  outside recall noise).
- **Effort ladder (low/med/high):** complete top-6 — *moderate*; mostly "not resolved by this
  sample", which is itself the finding.
- **Top-6 → full-50 extrapolation:** *directly tested* on 33 cells with ≥40/50 PRs (see REPORT.md
  §4.3): ranking agreement Spearman 0.37–1.00 (median 0.80); recall gaps small (mean ≈ −0.00 to
  +0.01); F1 gaps larger (harness adjP is higher on the top-6, mean +0.08) — so top-6 F1s should
  not be read as full-set F1s without the correction reported there.
- **Fable harness claims:** *unsupported* — no complete fable compound/metareview cell exists.

Reproduce: `.venv/bin/python tools/final_report_extract.py` (rebuilds
`analysis/final_report_dataset.json`), `.venv/bin/python tools/final_report_compute.py`
(`analysis/final_report_metrics.json`), `.venv/bin/python tools/verify_hitlist.py --verbose`.
