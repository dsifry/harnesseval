# HANDOFF — harnesseval + metareview, 2026-08-24 (end of context)

> For the fresh agent: read docs/SPEC.md + docs/PLAN.md first, then docs/PARTIAL_RUN_REPORT.md
> (the operational log of every fix), then this. This doc = current state + the analysis from a
> second agent (VERIFIED, with corrections) + exact next steps.

## 1. Where we are

**Phase B (build + tune) — nearly done.** metareview 0.7.0 eval run COMPLETE (run_batch
`20260824-101905-cli-144cells`): 143 pass cells in the registry (131 original + 11 fill-ins; 2
stubborn errors remain, both compound-realistic claude-opus-5 xhigh). metareview 0.8.0 is BUILT
on branch `feat/adversarial-lenses-0.8.0` (PR #11, threads resolved, ready to merge) — adds
adversarial stance to all lenses + 2 new lenses (Testing-quality, Data-migration) + security/
architecture content grafts + anchored confidence + suppression lists. 8 lenses total.

**Two codebases:**
- `/Users/dsifry/Developer/harnesseval` — the eval lab. Run registry is the source of truth
  (append-only, run_batch-tagged). Results JSON writes on matrix completion but the registry is
  durable even if the matrix hangs on the final write (it did — data is safe).
- `/Users/dsifry/Developer/metareview` — the tool under test. Branch
  `feat/adversarial-lenses-0.8.0` has the 0.8.0 work (committed) PLUS two UNCOMMITTED C1/C2
  changes from a second agent (see §3 — verify before committing).

## 2. The 0.7.0 baseline (the dataset 0.8.0 compares against)

run_batch=`20260824-101905-cli-144cells`, 144 cells: 6 PRs × {opus-5, gpt-5.6-sol, glm} ×
{medium, xhigh} × {vanilla-engineered, metareview-realistic, superpowers-realistic,
compound-realistic}. 143 pass (11 fill-ins merged into the same run_batch). 2 stubborn errors
(both compound-realistic opus-5 xhigh — the big-diff 400 overload). Per-finding adjudication
records + per-golden matches + per-finding source-lens all persisted to summary.json (the H1/H4
data unlock). Analysis artifacts in results/ (ANALYSIS.md, per_lens_attribution.json,
adjudication_split.json, per_golden_miss.json).

## 3. Second-agent analysis — VERIFIED, with corrections

A second agent analyzed the 0.7.0 data + built two metareview-side fixes. I verified the key
claims; one is WRONG.

### VERIFIED TRUE
- **C1/C2 are built** (uncommitted on feat/adversarial-lenses-0.8.0): C1 tags deterministic
  gates as `Classification: "gate"` + routes them to a `## Gate Findings` section; C2 routes
  orchestrator prose to `## Orchestrator Notes`. Build passes (`metareview --version` → 0.8.0).
  Evidence in `metareview/docs/0.8.0-candidates.md`. UNCOMMITTED — needs review + commit.
- **superpowers-realistic × gpt-5.6-sol recall is low** (verified n=12, mean 0.15; agent said
  0.11 — close enough). Same class as the old metareview/codex 0.00 bug: likely superpowers'
  realistic path isn't dispatching its code-reviewer subagent on codex CLI. DEBUG NEEDED.
- **H4 (real-but-ungold vs hallucination)**: vanilla 67% real, compound 54%, metareview 46%,
  superpowers 40% (more hallucination than real — so superpowers' low precision is partly
  genuine noise). Plausible + actionable.
- **Per-golden miss**: compound + metareview miss fewest goldens (~20-27%); superpowers most
  (57%). Missed bugs disproportionately High/Critical. The jsforce stale-token +
  refreshOAuthTokens credentialId-vs-userId bugs missed by every framework.
- **GLM findings bug fixed** (the `_call_cli` tuple-unpacking fix — see PARTIAL_RUN_REPORT).
- **gpt-5.6-sol + GLM per-model cost = $0** (CLI/Lunaroute JSON lacks costUSD). Fix: a
  pricing.py with pinned-date price tables; derive cost from tokens. Token counts are ground
  truth.

### WRONG (corrected)
- **"H1: the no-security-lens gap was in our api-direct adapter's hard-coded LENS_PROMPTS, not
  metareview-the-tool. The api adapter is the straggler — add security to it."** FALSE. I
  verified: `from harnesseval.adapters.metareview import LENS_PROMPTS` → `['feasibility',
  'completeness', 'scope', 'architecture', 'intent', 'security']` — the security lens IS in the
  api-direct adapter (built in 0.7.0). The second agent was looking at stale state. Do NOT
  re-add security to the api adapter. (The realistic path's security lens also works — 71%
  real_rate, 27 matched + 136 real-but-ungold.)

## 4. Exact next steps (priority order)

### 4.1 Commit the kept C2 changes in metareview (C1 was reverted — already done)
The second agent built two metareview-side changes. I verified them:
- **C1 (reclassify gates blocking->gate) was UNSAFE — I already REVERTED it.** It would flip
  metareview's task-done verdict (`internal/taskdone/review.go:446` `blocking := counts.Blocking > 0`)
  from NEEDS_REVISION to PASS on an unsafe `eval()` diff. The 3 C1 files
  (internal/findings/findings.go, internal/reviewers/taskdone.go, internal/taskdone/review.go)
  are back to their committed state. Do NOT re-introduce C1.
- **C2 (## Orchestrator Notes section) was SAFE — KEPT, uncommitted.** It's pure markdown
  scaffolding/doc (internal/artifactreview/review.go + rubrics/artifact-review-rubric.md +
  skills/review-artifact/SKILL.md) — separates orchestrator prose from findings for readability +
  future extractors. No verdict logic touched. I fixed its doc lines that referenced the reverted
  `## Gate Findings` (they now say gates stay `blocking` and point extractors to filter by source).
  Build passes (`metareview --version` -> 0.8.0).

ACTION for the fresh agent: commit the 3 kept C2 files on `feat/adversarial-lenses-0.8.0` and
push to PR #11. (The C2 docs/0.8.0-candidates.md note from the second agent is untracked —
optional to keep; it documents the original C1/C2 intent.)

The eval benefit (stop gate/orchestrator-prose hallucinations from penalizing metareview's
precision) is achieved EVAL-SIDE (§4.2), NOT by C1. The deterministic gates stay `blocking`
for metareview's own verdict; the eval extractor skips them by `source` field.

### 4.2 The eval-side extractor skip (REQUIRED for the gate/session hallucination fix)
`harnesseval/adapters/metareview_realistic.py` `_extract_findings_from_session` must SKIP
findings whose `source`/`source_lens` is `metareview-deterministic/*` (the gates — 100%
hallucination under adjudication, boilerplate text) or `metareview-session` (orchestrator
prose — 92% hallucination). This is the load-bearing fix for metareview's unfair precision
penalty; it is metareview-specific (compound/superpowers have no gate/session layer). This
replaces the unsafe C1 metareview-side change.

### 4.3 Merge PR #11 + rebuild bin/metareview to 0.8.0
After PR #11 merges: `cd ../metareview && git checkout main && git pull && go build -o
bin/metareview ./cmd/metareview` → verify `bin/metareview --version` = 0.8.0. Update
`third_party/metareview_sha.txt` to the merged SHA.

### 4.4 Update harnesseval adapters to 0.8.0 (6→8 lenses + adversarial stance)
`metareview.py` LENS_PROMPTS + `metareview_realistic.py` REALISTIC_PROMPT: add Testing-quality +
Data-migration lenses, re-stance all 8 adversarially, add the security/architecture grafts +
the anchored-confidence + suppression. Mirror the metareview rubric. (The api adapter's
security lens already exists — don't re-add.)

### 4.5 Launch the 48-cell 0.8.0 comparison run
`--frameworks vanilla-engineered,metareview-realistic --models claude-opus-5,gpt-5.6-sol,glm-5.2-vision-flex --efforts medium,xhigh --prs 6 --mode cli --concurrency 3` (skipping compound/superpowers — their 0.7.0 baseline carries forward; their code is unchanged). Compare metareview-realistic 0.8.0 vs 0.7.0 (run_batch `20260824-101905-cli-144cells`).

### 4.6 Debug superpowers-realistic on codex (the 0.15 recall bug)
Same class as the old metareview/codex 0.00 (PARTIAL_RUN_REPORT FIX 1). The codex CLI subagent
dispatch for superpowers isn't producing matchable findings. Capture a `codex exec --json` stream
for one superpowers-realistic gpt-5.6-sol cell and check whether the code-reviewer subagent
dispatched via `collaboration.spawn_agent`.

### 4.7 Pricing.py (derived $ for gpt/glm) + registry durability
- `harnesseval/pricing.py`: pinned-date OpenAI + Z.ai price tables; `usage.from_codex_cli` +
  the Lunaroute path derive `cost_usd` from tokens. Label Pareto x-axis "priced token cost
  (derived)".
- Roll `per_model_usage` + aggregate adjudication counts (`n_real_ungold`, `n_hallucination`)
  into the registry line; re-add `raw_review` to summary.json (the finding→adjudication chain
  is missing it in the new batch).
- Exclude `model=="kimi-k3"` going forward (removed from eval; early runs are test artifacts).

### 4.8 The 2 stubborn errors (compound-realistic opus-5 xhigh)
Both are the big-diff 400 "Could not finish the message" (Anthropic context/overload limit),
not 529. The transient-529 retry doesn't catch 400. Options: cap diff size for compound xhigh,
or accept as a known hard-cell limitation. `/tmp/debug_note_holdout.md` has the full debug.
Also: capture proc.stdout on nonzero exit (the empty-stderr fails are undiagnosable) —
`compound_realistic.py:156`, `metareview_realistic.py`, `cli_backends.py:97`.

## 5. Key files / state
- harnesseval/docs/PARTIAL_RUN_REPORT.md — every fix (GLM `_call_cli`, transient-529 retry,
  run_batch, per-finding persistence, etc.)
- harnesseval/docs/METAREVIEW_IMPROVEMENTS.md — hypothesis register H1–H5 + H1b/H1c done +
  H5b (codex flips the metareview-vs-compound conclusion).
- harnesseval/docs/research/metaswarm_vs_compound_comparison.md — the comparison that drove
  the 0.8.0 adversarial stance + grafts.
- metareview/docs/0.8.0-candidates.md — the second agent's C1/C2 evidence + verification steps
  (C1 was UNSAFE and is reverted; C2 is kept — see §4.1).
- /tmp/debug_note_holdout.md — the compound opus-5 xhigh holdout debug.
- results/ANALYSIS.md + per_lens_attribution.json + adjudication_split.json +
  per_golden_miss.json — the 0.7.0 analysis.
- Active branch: metareview `feat/adversarial-lenses-0.8.0` (PR #11, threads resolved, ready
  to merge). C1 REVERTED (safe); C2 KEPT but UNCOMMITTED — commit the 3 C2 files + push (§4.1).
  harnesseval on `main` has UNCOMMITTED `run_model_matrix.py` changes (--run-batch + --fill
  flags) — commit before the 0.8.0 run.

## 6. What NOT to do
- Don't re-add security to the api-direct metareview adapter (it's already there — the second
  agent was wrong).
- Don't compare api vs cli numbers head-to-head (SPEC §7).
- Don't trust any "X beats Y" claim yet — bootstrap CIs wide at N=6; Phase C (50 PRs) is the bar.
- Don't rerun compound/superpowers for 0.8.0 (unchanged code; carry the 0.7.0 baseline forward).
- Don't retry the 3s compound-opus-xhigh fail as a 529 (it's an empty-stderr nonzero exit, not
  overload — capture stdout to diagnose).
