# Install

> **⚠️ Historical (August 2026, tag `v0.8.2-eval`).** This page documents the environment for the
> **August 384-cell matrix experiment** (`batch_083`, described in [`report.md`](report.md)).
> The **current report** is [`REPORT_FINAL.md`](REPORT_FINAL.md) (the 2026-09 50-PR campaign, verified
> true golden set, post-publication audit); its reproduction chain, pinned revision
> (`report-2026-09-18`), and mode taxonomy are in **`REPORT_FINAL.md` §11**. The environment basics
> below still apply, but treat every August-specific pointer accordingly.

How to set up the `harnesseval` lab so you can run the matrix and reproduce the results in
[`report.md`](report.md). Reproducibility-pin setup (the exact tested combo) is in
[`REPRODUCE.md`](REPRODUCE.md); this page covers the environment once.

## 1. Prerequisites

| Tool | Why | Version |
|---|---|---|
| **Python** | the lab | 3.11+ |
| **uv** | dependency management (this repo is a uv project) | any recent |
| **Go** | build metareview's deterministic-gate binary | 1.22+ |
| **Claude Code CLI** (`claude`) | the "realistic" mode drives a real `claude -p` agent session for the Claude models | installed + authenticated (OAuth) |
| **Codex CLI** (`codex`) | the "realistic" mode drives a real `codex exec` session for the GPT models | installed + authenticated (OAuth) |

The "realistic" adapters (the primary mode) invoke the real CLIs with tools + subagents, the
way a user actually runs each framework. The API-direct adapters (`adapters/*.py` without
`_realistic`) are a secondary column for exact, reproducible API calls.

## 2. Clone and install

```bash
git clone https://github.com/dsifry/harnesseval.git
cd harnesseval
git checkout v0.8.2-eval        # the reproducibility pin (see REPRODUCE.md)
uv sync
```

`uv sync` installs the Python deps (`inspect-ai`, `openai`, `anthropic`, `pandas`, …) from
`pyproject.toml` / `uv.lock`.

## 3. API keys (kept OUTSIDE the repo)

The harness reads keys from **`~/.config/harnesseval/keys.env`** (chmod 600) — **not** from a
tracked `.env`. Key names are `HARNESS_`-prefixed so an accidentally `source`d file cannot
override your Claude Code / Codex OAuth (those CLIs watch `ANTHROPIC_API_KEY` /
`OPENAI_API_KEY`; the prefixed names never collide):

```bash
mkdir -p ~/.config/harnesseval && chmod 700 ~/.config/harnesseval
cat > ~/.config/harnesseval/keys.env <<'EOF'
HARNESS_ANTHROPIC_API_KEY=sk-ant-...
HARNESS_OPENAI_API_KEY=sk-...
HARNESS_LUNAROUTE_API_KEY=...        # OPTIONAL: only for the open-weight GLM/Kimi lanes, and only if you
                                     # use a Lunaroute gateway. Any OpenAI-compatible endpoint works
                                     # (own router, OpenRouter, vLLM, or the provider directly) - set
                                     # LUNAROUTE_BASE_URL accordingly or call the provider API directly.
LUNAROUTE_BASE_URL=https://gw.lunaroute.com/v1
HARNESS_MARTIAN_API_KEY=...          # optional: Martian-proxy judge cross-check
EOF
chmod 600 ~/.config/harnesseval/keys.env
```

[`keys.py`](harnesseval/keys.py) loads this file **only in API-direct phases**, passes values
directly to SDK constructors, and never sets `os.environ` globally. Phase B (CLI/OAuth)
never loads it, so OAuth stays the default.

> **Do not** `source` this file or export these into your shell profile. The `.env.example`
> in the repo root is a *template only* (truncated placeholders); it documents the format and
> the model/pin constants — it has no real keys.

## 4. Third-party checkouts (pinned SHAs)

The dataset, the grader, and two of the four frameworks come from pinned upstream checkouts.
They are gitignored in this repo (`third_party/`); clone them at the pinned SHAs:

| Checkout | Pin | Used for |
|---|---|---|
| `code-review-benchmark` | `2b092b670f` | dataset + LLM-as-judge grader (Martian) |
| `superpowers` | `b36e0829…` (v6.3.0) | Superpowers review skill |
| `compound-engineering-plugin` | `a32c9474…` | Compound Engineering review skill |

```bash
# example for the dataset:
git clone https://github.com/withmartian/code-review-benchmark.git third_party/code-review-benchmark
cd third_party/code-review-benchmark && git checkout 2b092b670f && cd ../..
```

The Martian bench's offline PR data lives under `third_party/code-review-benchmark/offline/`;
[`harnesseval/dataset/martian.py`](harnesseval/dataset/martian.py) points at it.

## 5. metareview binary (the deterministic gates)

metareview's deterministic Go gates (eval-injection, TODO/missing-test, duplicate-path,
truncated-diff) are model-independent and cost **zero tokens** — they run as a real CLI the
realistic adapter invokes. Two ways to provide the binary:

- **Repro pin (recommended):** check out the metareview repo at its `0.8.2-eval` branch and
  build it: `git clone https://github.com/dsifry/metareview && cd metareview &&
  git checkout 0.8.2-eval && go build -o bin/metareview ./cmd/metareview`. Then point the
  harness at it via `MRV_BIN` (see [`adapters/metareview_realistic.py`](harnesseval/adapters/metareview_realistic.py)).

- `bin/` is **gitignored**, so a fresh clone contains no binary — build it (recommended, matches the pin)
  or copy a prebuilt one into `bin/metareview` and point `HARNESS_MRV_BIN` at it. `calibrate --check`
  reports which one it resolves and whether it is executable.

## 6. CLIs (for the realistic / primary mode)

Authenticate the CLIs you'll use (OAuth is the budget mode used for the primary matrix):

```bash
claude /login     # Claude Code (opus-5, sonnet-5)
codex login       # Codex (gpt-5.6-sol, gpt-5.6-terra)
```

The realistic adapters run `claude -p` / `codex exec` with `--dangerously-skip-permissions`
inside a throwaway materialized-PR repo (git + bash + subagents enabled). They retry on
transient API overload (`cli_backends.is_transient_claude_error`).

## 7. Verify the install

```bash
uv run python -m harnesseval.calibrate --check
```

Offline preflight — **no API calls, no spend**. It reports, item by item, whether the pieces a run needs are
present: the keys file (names only, never values), the judge instrument, the golden comments, the Martian
candidate results (INSTALL §4), writable `results/` + `runs/`, plus the framework-specific items (the
metareview binary for metareview runs, the `claude`/`codex` CLIs for `--mode cli`). Exit 0 means the lab can
run. Example in a clone that has not yet fetched the upstream checkouts:

```
[OK  ] API keys (~/.config/harnesseval/keys.env)      5 names: HARNESS_ANTHROPIC_API_KEY, ...
[OK  ] judge instrument (harnesseval/judge.py)        score_from_matches present
[OK  ] golden comments                                50 PRs from golden_comments
[FAIL] candidate results (benchmark checkout)         FileNotFoundError: missing third_party/code-review-benchmark (INSTALL.md §4)
[warn] metareview binary (metareview harness)         bin/metareview - build per INSTALL.md §5 or set HARNESS_MRV_BIN
```

To reproduce the bench's published anchor numbers (Phase A.1, the paid calibration run) use the same module
without `--check` — that re-judges N shipped pairs (~$1/pair, `--pairs` default 5) and registers the result
in `runs/registry.jsonl`.

## Notes

- **Cost:** running the full matrix spends real money on Claude (Anthropic billing) and burns
Codex/Claude subscription quota. GPT models report $0 via OAuth, so the eval reports an
*implied* $ (pinned 2026-08-22 rates) alongside the real $ — see `report.md` §Cost. Start
small (one PR, one model) before running the 384-cell matrix.
- **Python entry points** are under `bin/` (`analyze_batch_083.py`,
  `analyze_083_interactions.py`, `run_sdlc_loop.py`, …) and `harnesseval/` (`run_model_matrix`,
  `analysis`, `report`, `calibrate`). All invoked via `uv run python …`.

## 7. Smoke test — run ONE cell (recommended before any campaign)

Verify the whole eval path (model call → findings → judging → adjudication → run registration) with a single
cheap cell. `--fill` selects a cell **within** the `--prs × --models × --efforts × --frameworks` matrix, so the
model/effort/framework must also be passed explicitly:

```bash
export HARNESS_KEYS_FILE=~/.config/harnesseval/keys.env          # your own keys (see §3)
.venv/bin/python -u -m harnesseval.run_model_matrix \
  --prs 6 --models glm-5.3-flash-background --efforts low --frameworks vanilla-engineered \
  --fill vanilla-engineered/glm-5.3-flash-background/low/8 \
  --mode api --run-batch smoke-$(date +%s) --out /tmp/smoke.json
```

(Use `--mode cli` for the Claude/Codex OAuth lanes; `api` is the paid, clean-token mode used for
open-weight models like GLM/Kimi. `bin/metareview` is only needed for the metareview harness.)

Expected: one line per cell plus a summary, e.g.

```
[mx] [1/1] vanilla-engineered glm-5.3-flash-background low ...
[mx] [1/1] vanilla-engineered glm-5.3-flash-background low TP=5 FP=6 FN=1 rec=0.83 adj_p=0.83 incr_r=0.90 real=4 hal=1 11,803tok 42s
```

It writes `runs/<id>/{manifest.json,summary.json}` (findings with `issue_text`, per-model usage, the judge id
and the adjudicated real/hallucination split) and appends a row to `runs/registry.jsonl`. Only one run per
(cell, PR) is described above — the campaign's 72 cells × 6 PRs is the full sweep, and costs real money.

**Two things to expect.** (1) Run-to-run variance on a single PR is large — the same cell scored TP 2/2/2 on
PR 8 in the campaign and TP 5 in the smoke test above; that variance is why the report compares cells over
several PRs with cluster-bootstrap CIs. (2) `cost_usd` comes from the provider/gateway response, so a gateway
that does not return cost (some Lunarroute plans) yields `0.0`; the report's GLM costs were retrieved from the
gateway's ledger, not computed locally.
