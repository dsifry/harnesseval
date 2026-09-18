# Replication test — following §11 as an outside researcher (2026-09-18)

Method: clone the committed state into a clean tmp directory, create a venv, `pip install -r requirements.txt`,
and run the §11 chain **after deleting every chain output**, so a byte-identical result cannot be a false pass
(a stale committed file trivially "matches itself").

## What broke on the first attempt (all now fixed)

| # | symptom | root cause | fix |
|---|---|---|---|
| 1 | `final_report_extract.py` **exited 0** but wrote a dataset with `pr_golden: []`; `top6 0/6` for every cell | it requires `third_party/code-review-benchmark/offline/golden_comments/*.json`, which is **gitignored** (and a nested git checkout, so it cannot be committed from here). The failure was silent | vendored the 5 files (144 KB) at `analysis/inputs/golden_comments/` with provenance + `SHA256SUMS`; the 8 tools that read them prefer the vendored copy; both entry points now abort with a FATAL message |
| 2 | `final_report_compute.py` then died with `KeyError` on `pr_golden` | consequence of #1 | loud guard |
| 3 | …and in the metrics path `_goldens_list()` returned `[]`, producing **zero denominators**: 1,705 numbers in `final_report_metrics.json` silently changed (§10c pair summaries and sign counts among them), exit 0 | same root cause, different code path | loud guard |
| 4 | no way to set up the environment | **no `requirements.txt`**; the chain needs exactly numpy + matplotlib | added `requirements.txt`; §11.1 documents setup |
| 5 | §11 documented only the pre-§10d chain | docs lagged the analysis | §11.2 rewritten with the true order and an inputs-vs-outputs list |
| 6 | `final_report_compute.py` appended the §10d block via a subprocess and **swallowed failures** (exit 0), so downstream tools failed later with `KeyError: 'true_gold_defects'` | missing fatal check | the append now raises with the underlying error |
| 7 | rebuilding from scratch **deadlocked**: `compute` needs `DEFECT_METRICS.json`, while `defect_metrics` read the generated `final_report_metrics.json` | circular dependency | `verified_gold_defect_metrics.py` now takes the six-PR list and golden counts from the **dataset** (identical values, verified); `final_report_metrics.json` is optional to it |
| 8 | a mechanical patch to the golden glob matched inside a `_glob.glob(...)` alias and produced `_(...)` → `TypeError: 'list' object is not callable` — **not caught by `py_compile`**, only by running the chain | patch bug | repaired; all 8 tools compile and run |

## Result after the fixes

Fresh clone, **all chain outputs deleted**, chain run in the documented order:

| artifact | result |
|---|---|
| `analysis/final_report_dataset.json` | **byte-identical** |
| `analysis/final_report_metrics.json` (frozen §1–§9 + §10b/§10c + `true_gold_defects`) | **byte-identical** |
| `analysis/verified_gold/DEFECT_METRICS.json` | **byte-identical** |
| `analysis/verified_gold/GOLD_DEFECT_CATALOG.json` / `.md` | **byte-identical** |
| `analysis/verified_gold/DEFECT_REGISTRY.md` | **byte-identical** |
| `analysis/figures/interactive_dashboard.html` | **byte-identical** |
| `analysis/figures/*.png` | same data, different bytes — matplotlib 3.11.1 vs 3.11.2 rendering |
| LLM steps (§10b clustering, §10c overlap, §10d verification) | not reproducible by re-running, by design; the stored artifacts are the record |

## Safety behaviour verified

With the vendored golden comments hidden: `final_report_extract.py` and `final_report_compute.py` both abort
with exit 1 and a FATAL message naming the expected paths — instead of writing a degenerate dataset/metrics.

## End-to-end test with API keys (final)

Run in a fresh temp directory, following **only** §11 (the report's bash blocks were extracted verbatim and
executed), with the campaign's keys copied to a file outside the repo (`/tmp/e2e/keys.env`, chmod 600) and
`HARNESS_KEYS_FILE` pointing at it:

```
fable keys file contained (names only, values never printed or committed):
  HARNESS_OPENAI_API_KEY, HARNESS_ANTHROPIC_API_KEY, HARNESS_LUNAROUTE_API_KEY, LUNAROUTE_BASE_URL,
  HARNESS_MARTIAN_API_KEY, TEST_HARNESS_ANTHROPIC_API_KEY
```

| step | result |
|---|---|
| `final_report_extract.py` | OK |
| `verified_gold_defect_metrics.py` | OK |
| `verified_gold_registry_sync.py` | OK |
| `final_report_compute.py` | OK |
| `gold_defect_catalog.py` | OK |
| `final_report_figures.py` | OK |
| `final_report_figures_true_gold.py` | OK |
| `final_report_tables.py` | OK |
| `final_report_html.py` | OK |
| `key_usage_report.py` | OK (ledger: 5,628 ok / 5,005 failed calls) |
| `verify_hitlist.py` | exit 1 — informational: 29/111 hitlist rows unrun (the disclosed fable coverage gap) |

**Then every chain output was deleted and the chain re-run from scratch**: all steps OK, and
`final_report_dataset.json`, `final_report_metrics.json` (incl. the §10d block), `DEFECT_METRICS.json`,
`GOLD_DEFECT_CATALOG.{json,md}`, `DEFECT_REGISTRY.md` and `interactive_dashboard.html` all regenerated
**byte-identical** to the committed state.

**Keys are not needed for the published numbers** — proven, not asserted: with an *empty* keys file
`final_report_compute.py` still exits 0 and reproduces the metrics exactly, and
`verified_gold_defect_metrics.py` exits 0 with all key environment variables unset. Keys are only used by the
model-running steps (`INSTALL.md` §3), where you should supply **your own** OpenAI/Anthropic credentials.
**Lunarroute is optional**: it is just the OpenAI-compatible gateway this campaign used for the open-weight
GLM/Kimi lanes — any router or direct provider works.
