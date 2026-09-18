# Vendored benchmark inputs (required to reproduce the report)

These are the Martian offline benchmark's golden comments — the 42 human-verified golden defects (with their
severity and category) that every recall number in the report is measured against.

They are vendored here because the upstream checkout lives in `third_party/`, which is **gitignored** (it is a
nested git checkout, so its files cannot be committed from this repository). Without them
`tools/final_report_extract.py` and `tools/final_report_compute.py` used to **fail silently**: the golden set
came back empty, per-PR denominators became 0, and a broken dataset/metrics file was written with exit code 0.

- **Source:** `code-review-benchmark` offline dataset, `offline/golden_comments/*.json`
- **Upstream revision at vendoring:** `2b092b670f7d6cae6d429babaaee18948b4bdacb`
- **Files:** cal_dot_com.json, discourse.json, grafana.json, keycloak.json, sentry.json (5 files, ~144 KB)
- **Integrity:** `shasum -a 256 -c SHA256SUMS`

Resolution order used by the tools: this directory first, then
`third_party/code-review-benchmark/offline/golden_comments/` if present.
