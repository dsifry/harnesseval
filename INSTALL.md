# Install

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
HARNESS_LUNAROUTE_API_KEY=...        # only if you run GLM/Kimi via Lunaroute
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

- A prebuilt `bin/metareview` is vendored in this repo's `bin/` for convenience (from the
  metareview 0.8.0 build); rebuild from the metareview `0.8.2-eval` branch to match the pin.

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

This reproduces the Martian bench's published anchor numbers before any framework comparison
is trusted (Phase A calibration). If it passes, the lab is valid.

## Notes

- **Cost:** running the full matrix spends real money on Claude (Anthropic billing) and burns
Codex/Claude subscription quota. GPT models report $0 via OAuth, so the eval reports an
*implied* $ (pinned 2026-08-22 rates) alongside the real $ — see `report.md` §Cost. Start
small (one PR, one model) before running the 384-cell matrix.
- **Python entry points** are under `bin/` (`analyze_batch_083.py`,
  `analyze_083_interactions.py`, `run_sdlc_loop.py`, …) and `harnesseval/` (`run_model_matrix`,
  `analysis`, `report`, `calibrate`). All invoked via `uv run python …`.
