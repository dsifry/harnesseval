# Reproduce

How to replicate the 384-cell matrix and every number in [`report.md`](report.md). The eval
is **reproducible**: the exact code is pinned, the dataset + grader are an established public
benchmark, and the analysis is one command per snapshot.

## The reproducibility pin

The exact code that produced the 384/384 pass-cell matrix (batch_083, 2026-08-26T05:30Z) is:

| Repo | Pin | What it is |
|---|---|---|
| **harnesseval** | tag **`v0.8.2-eval`** = commit `1847f7d` | the eval lab; the adapter that produced the matrix (incl. the load-bearing output-cap pattern + extractor markdown-strip) |
| **metareview** | branch **`0.8.2-eval`** = commit `61ffdf7` (the 0.8.2 release) | the Go binary (0.8.0 gates) + the 0.8.2 "orchestrator discipline" skill the realistic adapter drives |

```bash
# 1. harnesseval at the pin
git clone https://github.com/dsifry/harnesseval.git
cd harnesseval
git checkout v0.8.2-eval
uv sync                         # Python deps (see INSTALL.md for the full environment)

# 2. metareview at its eval pin (the binary the realistic adapter invokes)
git clone https://github.com/dsifry/metareview.git ../metareview
cd ../metareview && git checkout 0.8.2-eval
go build -o bin/metareview ./cmd/metareview      # builds the deterministic-gate binary
./bin/metareview --version                      # -> 0.8.2
cd ../harnesseval
```

> **Why the pin matters:** commit `1847f7d` is the *tested* state — it contains the output-cap
> pattern (per-lens file writes + `cat` concatenation) and the extractor markdown-wrapper strip
> that the 384/384 matrix actually ran on. The earlier `8567d40` "0.8.2 prompt" commit has
> *neither*; checking it out hits `400 max_tokens` failures on hard PRs and 0.00-recall cells on
> markdown-wrapped findings. Use the pin.

Set up the rest of the environment per [`INSTALL.md`](INSTALL.md): API keys at
`~/.config/harnesseval/keys.env`, the pinned third-party checkouts under `third_party/`, and
authenticated `claude` / `codex` CLIs.

## The dataset (6 PRs, 42 goldens)

The primary matrix uses 6 PRs from the [Martian Code Review Bench](https://github.com/withmartian/code-review-benchmark)
(offline), 42 human-verified golden comments total. Source: `harnesseval/dataset/martian.py`,
`bin/analyze_batch_083.py` (`PRS`).

| PR | label | goldens |
|---|---|---:|
| 11059 | calcom/cal.com#11059 | 9 |
| 4 | discourse-graphite#4 | 8 |
| 10 | discourse-graphite#10 | 7 |
| 14740 | calcom/cal.com#14740 | 6 |
| 8 | discourse-graphite#8 | 6 |
| 10967 | calcom/cal.com#10967 | 6 |

Goldens carry severity (Low/Med/High/Critical) + category (bug, security, concurrency, data,
api, perf, test_gap, doc_defect, style, speculative).

## Running the matrix

The matrix is a `(framework × model × effort × PR)` grid driven by
[`harnesseval/run_model_matrix.py`](harnesseval/run_model_matrix.py). It materializes each PR
into a throwaway git repo, runs the framework's review via the realistic adapter, extracts
atomic findings, judges them cross-family against the goldens, adjudicates the unmatched
findings, and writes a run record to `runs/`.

```bash
# A single cell (one framework × one model × one effort × one PR) — start here:
uv run python -m harnesseval.run_model_matrix \
    --prs 1 \
    --models claude-opus-5 \
    --efforts low \
    --frameworks vanilla-engineered,metareview
```

The full 384-cell matrix (4 frameworks × 4 models × 4 efforts × 6 PRs) is large and costs
real money — see the cost warning below. The orchestrator scripts under `bin/` drove the
batch with quota-window reruns; for a clean reproduction, run cells in batches and let
`runs/registry.jsonl` accumulate. Each completed cell appends a record to
`runs/registry.jsonl` and writes `runs/<id>/summary.json` (metrics + `per_model_usage` +
per-finding adjudication + per-golden matches).

### Judges (cross-family, anti self-preference)

To avoid a model judging its own output, the primary judge is from a *different* family than
the model under test ([`run_model_matrix.primary_judge`](harnesseval/run_model_matrix.py)):

- Claude-family findings → judged by `gpt-5.2`
- GPT-family findings → judged by `claude-opus-4-5-20251101`
- Adjudication (real-but-ungold vs hallucination) uses the same cross-family judge.

This is what produced every number in `report.md`. Re-adjudication can be re-run later with a
frontier panel without re-running the framework: each stored finding carries its source-lens,
matched-golden, judge verdict, and a diff-context hash (`_build_finding_records`).

## Refreshing the analysis (no re-run needed)

You do **not** need to re-run the matrix to reproduce the *numbers* — the committed
`runs/registry.jsonl` + `runs/<id>/summary.json` are the source of truth. Refresh the
analysis from them:

```bash
# The rolling batch_083 analysis (writes results/batch_083_ANALYSIS.md + appends history):
uv run python bin/analyze_batch_083.py

# The interaction analyses (report.md §4.6–4.7: H1/H2a/H2b tests, cost-efficiency, SDLC inputs):
uv run python bin/analyze_083_interactions.py      # -> stdout: 6 analyses on the 384-cell matrix

# The full Phase-B analysis (leaderboards, per-lens, adjudication split, failure-mode):
uv run python -m harnesseval.analysis               # -> results/ANALYSIS.md + results/*.json
uv run python -m harnesseval.report                 # -> results/leaderboard_*.json + pareto_*.png
```

## Key artifacts

| Path | What |
|---|---|
| `runs/registry.jsonl` | append-only run registry (the source of truth; 979 runs) |
| `runs/<id>/summary.json` | per-run metrics + `per_model_usage` + per-finding adjudication + per-golden matches |
| `results/batch_083_ANALYSIS.md` | the rolling analysis `report.md` cites (refresh with `bin/analyze_batch_083.py`) |
| `results/ANALYSIS.md` | the 0.7.0 deep-dive (per-lens, adjudication split, failure-mode) |
| `results/*.json` | machine-readable snapshots (`per_lens_attribution.json`, `adjudication_split.json`, `bootstrap_ci.json`, …) |
| `logs/*.eval` | Inspect eval logs (audit trail) — only selected evidence is force-tracked |

## Pinned versions (full list)

| Pin | SHA / version |
|---|---|
| Martian Code Review Bench (dataset + grader) | `third_party/code-review-benchmark` @ `2b092b670f` |
| Superpowers plugin | `third_party/superpowers` @ `b36e0829…` (v6.3.0) |
| Compound Engineering plugin | `third_party/compound-engineering-plugin` @ `a32c9474…` |
| metareview Go binary | 0.8.0 gates; metareview 0.8.2 slim-orchestration skill (branch `0.8.2-eval`) |
| Inspect AI | see `pyproject.toml` / `uv.lock` |

## Cost warning ⚠

Running the full 384-cell matrix is **not free**:

- **Reported $** = real Anthropic billing (cache-discounted); the completed 255/384 cells cost
  **~$229 reported / ~$255 implied**. Linear extrapolation to 384: **~$384 implied**.
- **GPT models report $0** via Codex OAuth/subscription, so reported $ understates true cost;
  the eval adds an **implied $** (pinned 2026-08-22 rates: gpt-5.6-sol $1.25 in / $10 out per
  1M; gpt-5.6-terra $2.5 in / $20 out per 1M — **unverified**) for a fairer cross-model view.
- The matrix took multiple Claude quota-window reruns to finish (Claude Code hit weekly +
  session limits mid-run); a looping auto-rerun watcher drained the remaining ~126 failed
  cells across quota windows.

Start with a few cells. Expect the realistic adapters to spend the bulk of cost on the
orchestrator (Claude opus), not the subagent lenses — see `report.md` §6.

## Caveats (apply to every number)

- **N is tiny.** 6 PRs per cell; bootstrap 95% CIs are wide or undefined. No "X beats Y" claim
  survives the bootstrap at this N — the interaction analyses report raw win-rates, not
  significance. The patterns (hidden-gold 16/16, opus-5 concentration) are directional, not
  proven. **Phase C (50 PRs + CIs) is the bar before any final ranking.**
- **Batch effect.** batch_083 is ~0.14 lower recall than the earlier 0824-1019 batch on matched
  cells — a batch/judge effect, not a framework regression. Cross-batch pooling is avoided;
  GLM is a separate sidebar.
- **Model provenance.** API `opus` = `claude-opus-4-5` (pinned); CLI realistic `opus` resolves
  to `claude-opus-5`. API and CLI are never compared head-to-head.
