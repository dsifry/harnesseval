# Replication kit — verified hidden gold

Every bundle in `bundles/<pr>/` is a self-contained evidence packet: a runnable test that
FAILS on the pinned post-PR revision, a minimal `fix.patch` that makes it PASS, the raw logs of
both runs, and `meta.json` with the exact commits, toolchain and SHA-256 hashes.

## Prerequisites

| repo | toolchain | services |
|---|---|---|
| calcom/cal.com | node 22, yarn 3.4.1 (`corepack prepare yarn@3.4.1 --activate`), ~2 GB deps | only for DB-semantics claims: `docker compose -f docker-compose.verify.yml up -d` |
| discourse-graphite | system ruby 2.6 (the tests stub their collaborators; no bundle install) | redis only for throttle-key claims |

## Steps (any bundle)

```bash
tar xzf bundles/<pr>/<bug-id>-<slug>.tar.gz && cd <bug-id>-<slug>
cat REPRO.md          # claim, pinned SHAs, exact commands, expected output
```

`REPRO.md` in each bundle is written to be machine-independent: it clones the upstream repo at
the pinned SHA, applies `test.diff`, runs the test (expect FAIL), applies `fix.patch`, and runs it
again (expect PASS).

## Fidelity labels you will see

- `repo_suite` — the repository's own test runner at the pinned revision (highest fidelity).
- `repo_suite_harness_config` — same runner, minimal config for `.tsx` tests the repo's workspace glob excludes.
- `standalone_real_code` — the real post-PR file executed with visible stubs for collaborators (Rails 4.2 era).

## Verdicts and what each one means

See `analysis/verified_gold/README.md`. Only `confirmed_regression` and
`behavior_change_not_regression` are promoted as verified hidden gold; `defect_present_before_pr`,
`unresolved_file`, `inconclusive_env`, `not_a_bug` and `static_text_test` are reported as separate
tiers, never discarded.

