# Handoff: produce the final calibrated report + executive summary from the manifold campaign

> **DATA FREEZE (2026-09-16 09:35):** all data-generating lanes were deliberately stopped
> (both GLM fill lanes and the fable orchestrator) so the report is computed on a stable
> dataset. **Compute every number from `runs/*/summary.json` as it stands at this freeze**
> (or from the snapshot artifact `analysis/DATA_FREEZE_2026-09-16.md`). If you re-query
> coverage and find MORE data than the freeze snapshot, do not use it — new runs are
> post-freeze and would make the report irreproducible. Note the freeze timestamp in the report.
> To resume data generation later, relaunch `tools/campaign_glm_fullmatrix.sh`,
> `tools/campaign_glm_vanilla_full.sh` (both `--skip-batch` health-gated, so they resume without
> redoing healthy cells) and `tools/campaign_fable_limited.sh`.

**Date:** 2026-09-16
**Author of this handoff:** the agent that ran the manifold campaign to completion
**Audience:** a fresh agent with no prior context, producing the *new* report
**Status of prior reports:** `report.md`, `report2.md`, `docs/FRAMEWORK_COMPARISON.md` are
**SUPERSEDED / DEPRECATED** — do not edit their content. Add a one-line deprecation banner at
the top of each pointing to the new report. All new work goes into new files.

---

## 1. What this document is

Everything a fresh agent needs to turn the campaign's run data into a **reliable, calibrated,
methodologically explicit** report + executive summary. It contains:

1. The **official benchmark** we are measuring against (Martian's offline code-review benchmark)
2. The **calibrated pipeline we already use** to score it (frozen instruments — do not change)
3. The **improved methodologies beyond the benchmark** (bug-vs-nitpick re-adjudication, clustering,
   beyond-gold, advisory analysis)
4. The **data inventory** (where runs live, what is complete, what is sampled)
5. **Known caveats** the report must be explicit about
6. **Open questions / further research**
7. **Deliverables, format, and hard rules**

---

## 2. The official benchmark (external ground truth)

Source: <https://github.com/withmartian/code-review-benchmark/blob/main/offline/README.md>
(and linked docs in that repo). Read it before writing; this is a summary of the parts that
constrain our methodology.

- **Dataset:** 50 PRs across 5 major open-source codebases (in our harness:
  `calcom/cal.com`, `ai-code-review-evaluation/discourse-graphite`, `keycloak/*`, `getsentry/*`,
  `grafana/*` and greptile-eval repos). Each PR carries **golden comments**: real issues a human
  reviewer identified, each with a **severity** (Low/Medium/High/Critical) and a **category tag**
  (bug, security, concurrency, data, api, perf, test_gap, doc_defect, style, speculative).
- **Pipeline (4 steps):**
  1. **Extract** distinct issues from the tool's review output
  2. **Deduplicate** semantically (same underlying concern ⇒ one candidate)
  3. **Judge** each candidate against each golden comment with an LLM: "do these describe the
     same underlying issue?" — semantic matches accepted, wording may differ
  4. **Score** with category-based profiles and F-beta
- **Scoring profiles** (which golden categories count):

  | Profile | Categories | Golden count |
  |---|---|---|
  | Strict | bug, security, concurrency, data, api | 139 |
  | **Core (default)** | Strict + perf, test_gap, doc_defect | 158 |
  | All | Core + style, speculative | 173 |

  A match to a golden comment **excluded** by the active profile is **matched-excluded**: neither
  rewarded nor penalised (this prevents long-winded tools being punished for real-but-minor finds).
- **F-beta:** the dashboard supports β = 0.5–3.0. `F1` weights precision/recall equally; **`F2`
  weights recall 4×**, reflecting the real-world asymmetry (a missed bug costs more than a false
  alarm). **Report at least F1 and F2.** Our `tools/scoreboard.py` currently emits F1; add F-beta.
- **Judge models:** results are stored per judge model (`anthropic_claude-opus-4-5-...` etc.).
  Report which judge produced the numbers.

**What we replicate:** the dataset, the golden comments, semantic judging, and profile-based
scoring. Our harness implements the pipeline in `harnesseval/judge.py` (the frozen matcher) and
`readjudicate3.py` (our hardened adjudicator). See §3.

---

## 3. Our calibrated pipeline (frozen instruments — do not modify)

These are established, validated, and must be used as-is so results are comparable across runs.

### 3.1 The frozen golden matcher (recall side)
- `harnesseval/judge.py` — golden-comment matching via a paid API judge
  (**`claude-opus-4-5`**, frozen prompt). Treat as immutable.
- Produces per-run `tp`, `fn`, `fp` in `runs/<run_id>/summary.json`.
- **recall = TP / (TP + FN)** — the benchmark's recall, computed against golden comments.

### 3.2 Honest re-adjudication v3 (`readjudicate3.py`) — the precision side
This is our **key methodological improvement over the raw benchmark**. History (see the tool's
docstring for the full derivation):
- v0 labelled every unmatched finding as "hallucination" → conflated *waste* with *breadth*.
- v2 introduced a **three-way** classification of every unmatched finding:
  - `bug` — verifiable defect in the diff
  - `important_non_bug` — real, specific, diff-grounded review concern that is not a defect
    (missing tests for new behaviour, completeness gaps, scope/architecture risk). Must cite
    specific diff code; generic advice does not qualify.
  - `hallucination` — false, misreads the diff, fabricated behaviour, pure style nit, vague.
- **v3 (current) hardens v2 with measured fixes:**
  1. **Cluster-level adjudication** — unmatched findings are grouped across ALL runs of the batch
     by (PR, near-verbatim normalised text); ONE representative per cluster is adjudicated and
     members inherit the verdict. Kills phrasing-driven verdict flips by construction.
  2. **Grounded hallucination** — the judge must cite the diff line/detail that *contradicts* the
     finding before it may return `hallucination`; "cannot verify" routes to `bug` with
     confidence < 0.5. Hedged wording is not evidence of falsity.
  3. **Majority vote (k)** — k adjudications per cluster at temperature 0; ≥2 votes wins; a 3-way
     tie triggers one tie-break call that sees all three.
  4. **Provenance stripping** — `[confidence:100][severity:P1]`-style prefixes and lens tags are
     removed before judging (they leaked into judged text and distorted verdicts).
- Output: `runs/<run_id>/readjudication3.json` with per-finding `new_verdict`.

**Campaign judgement lock (banked decision):** the manifold campaign's rj3 was run at
**k=1 with v3.1 clustering**. If you re-run adjudication, note the change explicitly and keep the
old numbers as a sensitivity check — do NOT silently swap.

### 3.3 The scoreboard (`tools/scoreboard.py`)
Per cell `(framework, model, effort)`:
```
recall = TP / (TP + FN)                     # frozen matcher
adjP   = TP / (TP + hallucinations)         # rj3-corrected precision
F1     = 2·recall·adjP / (recall + adjP)
beyond-gold = rj3 verdicts of bug + important_non_bug   # real findings outside gold
```
Usage: `tools/scoreboard.py --batch <batch> [--model M] [--rj-since "YYYY-MM-DD HH:MM"]`
**To add for the report:** F-beta (esp. F2), and the profile split (Strict/Core/All) using the
golden category tags.

---

## 4. Improved methodologies beyond the benchmark (our differentiators)

These are what make our report more useful than a leaderboard number. Each has a tool; use them
and describe them explicitly in the report's methodology section.

| Tool | What it does | Why it matters |
|---|---|---|
| `readjudicate3.py` | three-way bug / important_non_bug / hallucination, clustered, grounded, k-vote | separates *waste* from *breadth* — the benchmark's precision is otherwise distorted by defensible non-bug findings |
| `tools/scoreboard.py` | recall / adjP / F1 / beyond-gold per cell | the honest headline metric pair |
| `tools/eval_adjudicator.py`, `tools/eval_adjudicator_oauth.py` | measures adjudicator stability/agreement | quantifies how much of the precision number is judge noise |
| `tools/eval_clustering.py` | measures cluster/dedup quality | validity of the dedup step the benchmark mandates |
| `tools/enum_advisory_ceiling.py` | ceiling analysis of advisory-worthy findings | how much real value is *outside* the golden set (recall ceiling) |
| `tools/extract_flip_pairs.py`, `tools/score_flips.py` | finds findings whose verdict flips across runs/phrasings | evidence for the v3 hardening; also a *reliability* metric per tool |
| `tools/anchor_matcher.py` | anchor/line-level matching helper | line-anchored correctness beyond comment-level matching |
| `tools/campaign_dashboard.py` | campaign-wide rollups + cost | cost/benefit framing |
| `tools/key_usage_report.py` | per-key token/cost accounting | real $ per cell/codebase |
| `tools/verify_hitlist.py` | authoritative done/remaining against the severity top-6 | scope control / sampling disclosure |
| `tools/spy_tail.py`, `tools/lunaroute_spy.py` | wire-level gateway capture | provenance for provider-side anomalies (see §6) |

Related analysis docs to absorb (do not rewrite them, cite them):
`analysis/ADJUDICATOR_INTERRATER.md`, `analysis/ADVISORY_RECALIBRATION.md`,
`analysis/CE_VS_MRV_GAPS.md`, `analysis/EXTERNAL_REVIEWER_GAPS.md`,
`analysis/ACCEPTANCE_0111_FINAL.md`, `analysis/CE_RESIDUE_AFTER_UPGRADE.md`,
`FURTHER-RESEARCH.md`, `docs/FRAMEWORK_COMPARISON.md` (prior analysis; deprecated as a *report*
but a source of framing).

---

## 5. Data inventory (what exists, and what "full" means)

### 5.1 Structure
- **Dataset:** 50 PRs, 5 codebases, golden comments
  (`harnesseval/dataset/martian.py` → `GOLDEN_DIR`; `harnesseval/dataset/pr_diff.py` caches diffs
  in `.cache/pr_diffs/`).
- **Cell** = one `(PR × framework × model × effort)` run. A "cell" in run logs (`[N/247]`) is
  therefore **one PR**, not a whole framework.
- **Frameworks:** `vanilla-engineered` (naive single-call review; the control),
  `compound-realistic` (Claude-Code-style host session), `metareview-realistic` (our tool's
  lens pipeline).
- **Models:** `claude-opus-5`, `claude-sonnet-5`, `claude-fable-5-1`, `gpt-5.6-sol`,
  `gpt-5.6-terra`, `gpt-6-astra`, `glm-5.3-flash-background`, `glm-5.3-vision-background`
  (+ legacy rows that are out of scope).
- **Efforts:** `low`, `medium`, `high` (legacy `xhigh` exists only in the old glm top-6 batches).
- **Run records:** `runs/<run_id>/summary.json` (metrics, findings, tokens, error) and
  `runs/<run_id>/readjudication3.json`; `runs/registry.jsonl` (append-only index).

### 5.2 Batch ids (the era rule matters — see `CAMPAIGN_GLOSSARY.md`)
- Primary: **`20260910-mrv0120-manifold`**
- Vanilla reuse batches: `20260906-fable51-vanilla-low`, `20260906-fable51-vanilla-medhigh`
- Legacy glm vanilla: `20260906-glm53-top6`, `20260906-glm53-smoke`

**ERA RULE (banked, non-negotiable):**
- `vanilla-engineered` pairs may reuse healthy runs from **any** batch/era (no metareview binary
  involved, so no instrument confound)
- `metareview-realistic` / `compound-realistic` pairs must come from the **current campaign batch**
  — pre-0.12 binaries are instrument-confounded.

### 5.3 Scope discipline: "top-N"
**"top-N" means the HARNESS severity ordering** — sum of golden-comment severity weights
(Critical=4, High=3, Medium=2, Low=1) descending, then comment count descending. It does **not**
mean lexicographic URL order or dataset file order. The severity top-6 of this dataset is listed
in `CAMPAIGN_GLOSSARY.md`; authoritative artifact `manifold_top6_hitlist.csv`; verifier
`tools/verify_hitlist.py --verbose`. See `CAMPAIGN_GLOSSARY.md` before writing anything about
"top-6" — a lexicographic misreading already produced one wrong subset in this campaign.

### 5.4 Coverage as of this handoff (state it honestly in the report)
Full 50-PR matrix coverage, per model row, at the time of writing:

| Model | vanilla | compound | metareview |
|---|---|---|---|
| gpt-5.6-sol | 50/50 | 50/50 | 50/50 |
| gpt-5.6-terra | 50/50 | 50/50 | 50/50 |
| gpt-6-astra | 50/50 | partial | partial |
| claude-opus-5 | **6/50** | 50/50 | **~6/50** |
| claude-sonnet-5 | **6/50** | 50/50 | **~6/50** |
| claude-fable-5-1 | 50/50 | **0/50** | **0/50** |
| glm-5.3-flash-background | **6/50** (+fill running) | partial | partial |
| glm-5.3-vision-background | **6/50** (+fill running) | partial | partial |

**Two fill lanes were running when this handoff was written — re-check before reporting:**
- `logs/mx_glm_fullmatrix_run.log` — glm flash+vision, compound+metareview, low/medium/high,
  **247 cells** (~2/3 done at handoff; ETA ~2–3 days)
- `logs/mx_glm_vanilla_full_run.log` — glm flash+vision vanilla, low/medium/high,
  **281 cells** (mostly done at handoff)
Both are `--skip-batch` health-gated, so re-running resumes without redoing healthy cells.
**Do not report coverage numbers without re-running the coverage query in §5.5.**

### 5.5 Coverage query (use this, do not eyeball)
```bash
cd ~/Developer/harnesseval
.venv/bin/python - <<'PY'
import json, glob
from collections import defaultdict
Bs = ('20260910-mrv0120-manifold','20260906-fable51-vanilla-low','20260906-fable51-vanilla-medhigh')
d = defaultdict(set)
for f in glob.glob('runs/*/summary.json'):
    try: s=json.load(open(f))
    except Exception: continue
    if s.get('framework')!='vanilla-engineered' and s.get('run_batch') not in Bs: continue
    tok=(s.get('tokens_in') or 0)+(s.get('tokens_out') or 0)
    if s.get('error') or tok==0: continue
    if not (len(s.get('findings',[])) or tok<=20000): continue   # health rule
    d[(s.get('model'),s.get('framework'),s.get('effort'))].add(s.get('url'))
for k in sorted(d, key=lambda x: str(x)):
    print(f'{k[0]:30s} {k[1]:20s} {str(k[2]):7s} {len(d[k])}/50')
PY
```

---

## 6. Known caveats the report MUST disclose

1. **Fable is a gap.** `claude-fable-5-1` has 0/29 top-6 pairs and no compound/metareview matrix
   runs — its account was rate-capped for ~3 days (`logs/campaign_fable.log`, last write
   2026-09-13 09:35; orchestrator alive, probing every 10 min). All 29 outstanding top-6 rows are
   fable. State this as a coverage gap, not a result.
2. **Opus/sonnet vanilla is top-6-only (6/50).** Held deliberately by operator decision. Their
   compound cells are full 50/50; their metareview coverage must be re-measured per §5.5.
3. **glm vanilla was top-6-only until 2026-09-16**, now being filled to 50/50 by the vanilla lane.
4. **n = 1 run per cell** in general. Retries exist only where earlier attempts failed. Do not
   report variance you did not measure; `tools/eval_adjudicator.py` and `score_flips.py` are the
   tools for the reliability statements you *can* make.
5. **Single judge model** for both the frozen matcher and rj3 (claude-opus-4-5 family). Say so.
6. **Campaign rj3 is k=1 (v3.1 clustering).** Higher-k re-adjudication changes precision; if you
   re-run it, report both.
7. **Category profiles change the denominator.** Always state which profile (Strict/Core/All) a
   precision/recall/F number uses; Core is the benchmark default.
8. **Provider incident (2026-09-14/15), resolved.** GLM runs wedged for ~24h on a Lunaroute
   gateway bug (aggregate concurrent output > ~400k tokens ⇒ every call in the batch hung;
   plus the OpenAI SDK's `max_retries=2` silently tripling timeouts). Fixes banked:
   `max_retries=0` (`keys.py`), first-attempt transient retry + streaming (`model_router.py`),
   lens semaphore 4 (`metareview.py`), FD headroom + healthy-evidence `--skip-batch`.
   **Runs completed before ~2026-09-15 16:00 in the GLM rows may carry this confound — check
   timestamps and disclose if any GLM cell predates the fix.** (Opus/sonnet/astra/sol/terra calls
   are native-API and were unaffected.)
9. **Legacy/out-of-scope rows** exist in `runs/` (older models, other batches). Filter by the
   batch ids in §5.2 and the model list in §5.1.
10. **Cost** comes from token accounting (`tools/key_usage_report.py`), and includes retries.

---

## 7. Open questions / further research (carry into the report's "further work")

- **Vanilla matrix for opus/sonnet** — not run; needed for a like-for-like control on those rows.
- **Fable** — blocked on account capacity; the only path to a complete matrix.
- **Heavy non-bug findings** — `important_non_bug` volume is large for the lens frameworks; is it
  *useful* to a developer? `enum_advisory_ceiling.py` bounds it; a human-preference study is not
  done.
- **Judge sensitivity** — everything rests on one judge model family; cross-judge agreement is
  only partially measured (`eval_adjudicator*.py`).
- **Recall ceiling** — the golden set cannot contain every real issue; beyond-gold counts suggest
  the ceiling is materially above 100% of golden. Quantify, do not guess.
- **Effort ladder** — is `high` worth its cost vs `medium`? The data now exists to answer per
  framework/model with F-beta and $/finding.
- **Line-anchored correctness** — `anchor_matcher.py` exists; a proper analysis (does the tool
  point at the right line?) has not been reported.

---

## 8. The apples-to-apples comparison design (operator directive, 2026-09-16)

**This is the analytical spine of the report. Build the main tables around it.**

### 8.1 The comparison
```
      MODELS (8)                    FRAMEWORKS (3)          EFFORTS (3)        PRs (6)
  claude-fable-5-1             vanilla-engineered         low            top-6 by severity
  gpt-6-astra                  compound-realistic         medium         (see CAMPAIGN_GLOSSARY.md)
  gpt-5.6-sol                  metareview-realistic       high
  claude-opus-5
  glm-5.3-vision-background
  gpt-5.6-terra
  claude-sonnet-5
  glm-5.3-flash-background
```
= 8 × 3 × 3 = 72 cells, each across the **same 6 PRs** — that is the apples-to-apples surface.

**`xhigh` is OUT of the matrix by operator decision.** Do not present it as a gap; if legacy
`xhigh` runs exist (opus/sonnet/glm vanilla), mention them at most as an aside. **Do not** add
`xhigh` runs.

### 8.2 Why the top-6, and why we claim they are representative

The report **must argue this explicitly** — it is a deliberate design choice, not a convenience:

1. **Definition.** top-6 = the six PRs with the highest summed golden-comment severity weight
   (Critical=4/High=3/Medium=2/Low=1), ties broken by comment count. I.e. **the six *hardest*
   PRs in the 50-PR set** by ground-truth finding density. (`CAMPAIGN_GLOSSARY.md` is binding.)
2. **Why hard PRs first.** Cost/benefit for an engineering team is decided at the hard end: a
   reviewer that only catches easy issues is not worth buying. Difficulty-weighted evaluation is
   therefore the *more decision-relevant* measurement, not merely a cheaper one.
3. **Representativeness claim (must be tested, not asserted).** The claim is: top-6 is a
   *deliberately biased toward hard* but *internally valid* sample — differences between tools
   measured on it are expected to *persist* (and likely be *conservative*) on the full set. This
   claim is testable against the models where we have full 50-PR runs (§8.3). Report the result
   either way.
4. **Monotonicity assumption to check.** Check the per-PR trend of recall/precision against PR
   severity weight within the top-6 and (where full runs exist) within the 50. If hard PRs are
   systematically harder for every tool, the top-6 ranking is a lower bound on full-set recall.

### 8.3 Full-run backing and the sampling / error-bar analysis (REQUIRED)

We hold **full 50-PR runs for some rows** — use them to quantify what the top-6 sample misses.
As of this handoff (re-verify before reporting, §5.5):

| Row | vanilla | compound | metareview |
|---|---|---|---|
| gpt-5.6-sol | 50/50 | 50/50 | 50/50 |
| gpt-5.6-terra | 50/50 | 50/50 | 50/50 |
| gpt-6-astra | 50/50 | partial (fill not queued) | partial (fill not queued) |
| claude-fable-5-1 | 50/50 | 0/50 | 0/50 |
| claude-opus-5 / sonnet-5 | 6/50 | 50/50 | 50/50 |
| glm-flash / glm-vision | 6/50 → filling to 50/50 | filling to 50/50 | filling to 50/50 |

Required analyses:

1. **Selection effect (top-6 vs full-50).** For every row/cell with ≥~40 of 50 PRs healthy,
   compute recall / adjP / F1 on (a) the six top-6 PRs and (b) the full 50 — the *gap* is the
   top-6 selection bias. Report it per cell and summarised. If the top-6 ranking agrees with the
   full-set ranking on those rows, that is direct evidence for §8.2's representativeness claim.
2. **Variance / confidence intervals.** The top-6 is a 12% sample of the 50 PRs. For each cell
   reported on top-6, compute a **cluster (PR-level) bootstrap** CI: resample the 6 PRs with
   replacement (B ≥ 10,000), recompute the cell metric from per-PR TP/FN/hallucination counts, and
   report the 2.5–97.5 percentile interval. Do **not** treat findings within a PR as independent;
   the PR is the sampling unit. Where a cell has only one run per PR, that is the only honest
   variance available (and say so).
3. **Error bars in every headline figure.** Any bar chart / table of recall, adjP or F-beta must
   carry these CIs; differences smaller than the overlap of the CIs must be described as
   *not resolved by this sample*.
4. **Effort-ladder and cost analysis.** With CIs in place, answer: does `high` beat `medium`
   beyond noise, per framework/model — and at what $/finding delta? (`tools/key_usage_report.py`,
   `tools/campaign_dashboard.py`.)
5. **Where we sampled.** A short table stating exactly which combinations are full-50 vs top-6 vs
   empty, and what that does to each claim's strength (`analysis/COVERAGE_FINAL.md`).

**Do not skip this section, and do not present a single point estimate without its interval.**
The benchmark's leaderboard style (bare numbers, no error bars) is exactly what makes it
unreliable for a purchase decision — our report's value-add is that it states its uncertainty.

---

## 9. Cost, tokens, wall-clock, and the capability/cost frontier (operator directive, 2026-09-16)

**This is the report's headline economic analysis.** The audience is choosing what to run and pay
for; quality without cost is not a recommendation.

### 9.1 Data to extract (per run, then aggregate per §8 cell)

| Quantity | Where |
|---|---|
| `tokens_in`, `tokens_out` | `runs/<id>/summary.json` |
| cached input tokens | `logs/key_usage.jsonl` (`in`/`out`/`cached` per call), `tools/key_usage_report.py` |
| wall time | `summary.json` `wall_ms` (and per-call `s` in the ledger) |
| cost | price table × token split — **build a single explicit price table in the report**; cached reads are a different (usually much cheaper) rate than fresh input |
| findings / TP / hallucinations | summary + `readjudication3.json` |

Derived: **$ per run, $ per finding, $ per true-positive (golden) finding, $ per
beyond-gold real finding, tokens per finding, wall-seconds per finding** — each with the §8
cluster-bootstrap CI.

### 9.2 The required cost tables and figures

1. **Cost per cell** (8 models × 3 frameworks × 3 efforts × top-6) — table + bar chart.
2. **$/finding vs F1 (or F2) scatter** — the efficiency frontier. Mark each model/framework/effort
   as a point; the Pareto frontier is the headline picture.
3. **Token composition** — stacked bars of fresh-input / cached-input / output per cell (shows
   *why* one harness is cheaper: cache reuse vs raw output volume).
4. **Wall-clock table** — median and CI per cell; note where the cheaper option is *also*
   competitive on latency.
5. **Effort-ladder cost curve** — quality vs cost as effort rises within a model.

### 9.3 The findings the report must test and (if supported) state

State each only if the data supports it, with the computed number and its CI:

1. **Harnesses spend more tokens but find more bugs.** Lens/compound frameworks consume far more
   tokens than vanilla and catch more golden defects. Quantify the token multiple and the recall
   gain together — never one without the other.
2. **Per-token cost is orders of magnitude lower for the small-model harness.** Open-weight/
   "frontier-minus-N" models cost a small fraction per token (the operator's working figure is
   ~**1/200th** the frontier per-token price, giving roughly **~1/10th** total cost per task after
   the harness's extra token spend). **Recompute these two ratios from our own data — do not
   repeat them unverified.** Present as: per-token ratio, tokens-per-task ratio, net cost-per-task
   ratio.
3. **Higher thinking budgets do not reliably buy more bugs.** Test `high` vs `medium` per
   model/framework: if the recall/F1 difference is inside the CI overlap, say **not resolved by
   this sample**, and note the cost increase. A null result here is a *finding*, not a failure —
   it is exactly what a buyer needs to know.
4. **Too little model capability collapses recall.** Compare a materially weaker model (e.g. flash
   vs vision tier, or the legacy rows) and show the recall/finding-count drop — the other side of
   the trade-off, and the reason a floor exists.
5. **The recommendation, if the data supports it:** a **frontier-minus-two** open/gateway model
   (e.g. `glm-5.3-vision-background` or `glm-5.3-flash-background`) at **low reasoning** delivers
   **near-frontier recall, precision and F1 at a small fraction of the cost**, with wall-clock in
   the same range — i.e. the best cost/benefit point on the frontier. The report must state the
   measured ratios, the CIs, and the conditions under which it stops holding (hardest PRs, long
   diffs, capacity-limited providers).

### 9.4 Guards

- **Do not confuse token price with task cost** — the harness's token overhead can partly offset a
  cheap per-token rate; show both ratios.
- **Do not compare quality at a single point estimate** — §8's CIs apply to every cost-quality
  claim; overlapping intervals mean the ranking is unresolved.
- **Include the provider-capacity caveat** (§6 item 8): the cheap lane's throughput was
  gateway-limited during the incident window; note it as an operational, not a quality, issue.
- **Publish the price table with its retrieval date**; token prices change.

---

## 10. Deliverables and hard rules

**Deliverables**
1. `REPORT_FINAL.md` — the new report (rigorous; methodology explicit; every number traceable to
   a command or tool). Must include: the §8 apples-to-apples surfaces (8 models × 3 frameworks ×
   3 efforts × top-6), the **top-6 rationale + representativeness argument**, the **selection-effect
   (top-6 vs full-50) analysis**, **cluster-bootstrap confidence intervals** on every headline
   metric, and the **§9 cost/token/wall-clock economics** (cost-per-cell tables, $/finding vs F1
   frontier, token composition, effort-ladder cost curve, and the capability-vs-cost recommendation
   with computed ratios and CIs).
2. `EXECUTIVE_SUMMARY_FINAL.md` — 1–2 pages for a software-engineering leader deciding on
   cost/benefit of automated review.
3. `analysis/COVERAGE_FINAL.md` — the matrix coverage table + sampling disclosure (full-50 vs
   top-6 vs empty per cell, and why).
4. Add a **deprecation banner** to `report.md`, `report2.md`, `docs/FRAMEWORK_COMPARISON.md`
   pointing at the new report. **Do not edit their content otherwise.**

**Hard rules**
- **Never fabricate a number.** Every metric must be reproducible by re-running the stated
  command. If a tool must be modified to produce a metric (e.g. adding F-beta to `scoreboard.py`),
  say so and show the change.
- **Do not modify frozen instruments:** `harnesseval/judge.py`, the rj3 prompt/version semantics,
  or the golden dataset. Adjudicator/judge changes invalidate comparability.
- **State profile, β, judge model, batch ids, era rule, n, and k** for every reported metric.
- **Sampling disclosure is mandatory:** a "coverage & sampling" section listing exactly which
  cells are 50/50, which are top-6-only, which are empty (fable), and why.
- **Cost discipline:** report $ (from token accounting) alongside quality for any
  recommendation; the audience is choosing what to run and what to pay for.
- Prefer **tables + F1/F2 + $/finding** over prose. Explicitly separate *measured* from
  *inferred*, and *benchmark-defined* from *our extension*.
