#!/usr/bin/env python3
"""Package verified-hidden-gold evidence as deterministic tarballs + a human index.

Everything lands under analysis/verified_gold/ so it is findable and attachable:

  <pr>/B<nn>-<slug>/                one directory per bug (unpacked, browsable)
  bundles/<pr>/B<nn>-<slug>.tar.gz  one attachable evidence tarball per bug
  bundles/<pr>/B<nn>-<slug>.tar.gz.sha256
  bundles/<pr>/MANIFEST.json        machine-readable per-PR list (claim, file, verdict, sha256)
  bundles/<pr>/SUMMARY.md           human table for the PR
  bundles/verified_gold_<pr>.tar.gz self-contained per-PR bundle (all bugs + manifest + summary)
  bundles/verified_gold_all.tar.gz  roll-up across PRs
  INDEX.md                          human entry point (per-PR summary + paths + hashes)
  INDEX.json                        machine-readable index

Determinism: entries sorted, mtime pinned, uid/gid 0, normalized modes.
"""
from __future__ import annotations
import gzip, hashlib, io, json, tarfile, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"
BUNDLES = VG / "bundles"
MTIME = 1767225600  # 2026-01-01T00:00:00Z


def _add(tf, path: Path, arc: str):
    ti = tf.gettarinfo(str(path), arcname=arc)
    ti.mtime = MTIME
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = ""
    ti.mode = 0o755 if path.is_dir() else 0o644
    if path.is_file():
        with open(path, "rb") as fh:
            tf.addfile(ti, fh)
    else:
        tf.addfile(ti)


def build_tar(dest: Path, entries: list[tuple[Path, str]]) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for src, arc in entries:
            if src.is_dir():
                for p in sorted(src.rglob("*")):
                    _add(tf, p, f"{arc}/{p.relative_to(src)}")
            else:
                _add(tf, src, arc)
    with open(dest, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, mtime=MTIME) as gz:
            gz.write(buf.getvalue())
    return hashlib.sha256(dest.read_bytes()).hexdigest()


HEAD_SHA = {  # pinned revisions of the PR head each bundle was verified against
    "11059": "9fde0e906897cc0f4f71793f647dd629faba3317",
    "14740": "92f44dcea7ff19e9123a30c63c167a2938df5a55",
    "10967": "de628295646d0848226618108a52f2f1e5d04ac0",
    "4": "4f8aed295a29954023b2849c060ef4fb299d1b5d",
    "10": "d1c69189f3c90ecf56013a8da904da9bff9a8e19",
    "8": "060cda77729cb1c4a827560e09e89a7b22078ba9",
}
BASE_SHA = {
    "11059": "bc89fe00ea84d20bedcec782f0701b9711dc8201",
    "14740": "b004587262e8221083bafbe9a0c515e7becaa7b3",
    "10967": "a308075bc39b77ed7059b0cae9d443d669a7bf98",
    "4": "62db063e1e1abe691313ab42682a68f796d63769",
    "10": "913c3d6f636d02b3dd6c2c022ca1af2bec95d752",
    "8": "4975fc28903a84418f546b2809370f19abf10e08",
}
REPO_URL = {
    "11059": "https://github.com/calcom/cal.com", "14740": "https://github.com/calcom/cal.com",
    "10967": "https://github.com/calcom/cal.com",
    "4": "https://github.com/ai-code-review-evaluation/discourse-graphite",
    "10": "https://github.com/ai-code-review-evaluation/discourse-graphite",
    "8": "https://github.com/ai-code-review-evaluation/discourse-graphite",
}
RUNNER = {"repo_suite": "seq 0", }  # placeholder


def make_test_diff(test_path: str, content: str) -> str:
    """A unified diff that `git apply` accepts for a NEW file (so a researcher never has to guess
    whether test.patch is a patch or raw content)."""
    body = "".join("+" + ln + "\n" for ln in content.splitlines())
    return (f"diff --git a/{test_path} b/{test_path}\nnew file mode 100644\n"
            f"--- /dev/null\n+++ b/{test_path}\n@@ -0,0 +1,{len(content.splitlines())} @@\n{body}")


def repro_md(d: Path, meta: dict) -> str:
    """Machine-independent replication instructions — the whole point of the evidence pack."""
    pr = str(meta.get("pr", "")).split("/")[-1] or (meta.get("bug_id") or "?").split("-")[0]
    slug = d.name
    fidelity = meta.get("fidelity")
    test_path = meta.get("test_path") or "<see meta.json: test_path>"
    head, base = HEAD_SHA.get(pr, "<head SHA in meta.json>"), BASE_SHA.get(pr, "<base SHA>")
    repo = REPO_URL.get(pr, "<repo>")
    lang = "ruby" if fidelity == "standalone_real_code" else "ts"
    if lang == "ruby":
        run = f"ruby -I. {test_path}"
        setup = ("# no dependency install needed: the test stubs its collaborators and runs on system ruby\n"
                 "# (verified with ruby 2.6.10; ActiveRecord 4.1.16 is what the era repo expects)")
    else:
        run = f"yarn vitest run {test_path} --reporter=basic"
        setup = ("yarn install            # yarn 3.4.1 (corepack prepare yarn@3.4.1 --activate); ~2 min, ~2 GB"
                 + ("\n# this claim touches the database: start the verification services first\n"
                    "#   docker compose -f docker-compose.verify.yml up -d\n"
                    "#   export DATABASE_URL=postgresql://verify:verify@127.0.0.1:55432/verify_cal\n"
                    "#   ./node_modules/.bin/prisma db push --schema packages/prisma/schema.prisma --skip-generate --accept-data-loss"
                    if meta.get("services") else ""))
    return f"""# Replication — {slug} ({meta.get('bug_id')})

**Claim.** {(meta.get('candidate') or {}).get('title')}

**Verdict in this bundle:** `{meta.get('verdict')}` ({meta.get('three_way')})
**Fidelity:** `{fidelity}`  ·  **Authoring model:** `{meta.get('authoring_model') or "not recorded (bundle predates model recording; cal.com bundles of this era were authored with gpt-5.2)"}`

Everything needed to check this yourself is in this directory:
`test.diff` (the test, applies cleanly), `fix.patch` (the minimal fix), `logs/` (raw runs),
`meta.json` (SHAs, toolchain, hashes).

## Reproduce it

```bash
git clone {repo} && cd {repo.split('/')[-1]}
git checkout {head}          # the post-PR revision this bundle was verified against

{setup}

git apply test.diff          # adds the test file (must not already exist — a fresh clone is clean)
{run}                        # -> {"RESULT: FAIL" if lang == "ruby" else "1 failed"} : the claimed defect is present

git apply fix.patch          # the minimal fix
{run}                        # -> {"RESULT: PASS" if lang == "ruby" else "1 passed"} : defect gone
```

## What the two runs mean

| run | expected | why it matters |
|---|---|---|
| post-PR, unmodified | **FAIL** | the behaviour the campaign claims is demonstrably wrong here |
| post-PR + `fix.patch` | **PASS** | the claim is fixable, and the fix is real (not just a green test) |

Pre-PR revision `{base}` is only informative: for `behavior_change_not_regression` the code path did
not exist yet, and for `confirmed_regression` the test passes there too.

## Honest limits (please read)

- The test and fix were authored by an LLM and then **executed**; they are artifacts, not a proof of
  severity or business impact. Read the test before trusting the conclusion — one early candidate was
  rejected precisely because its test asserted on source text rather than behaviour.
- `fix.patch` addresses the **demonstrated instance only**; other instances of the same class are
  listed as unverified siblings in `meta.json`.
- Toolchain matters. TS bundles: node 22 + yarn 3.4.1 + the repo's own vitest. If a `.tsx` bundle
  says `repo_suite_harness_config`, the test ran under a minimal harness config (the repo's workspace
  glob excludes `.tsx` and its tsconfig sets `jsx: preserve`); the test file is identical either way.
- Ruby bundles (`standalone_real_code`) stub collaborators (ActiveRecord, I18n, …). The **file under
  test is the real post-PR file**; the stubs are visible at the top of the test.
"""


def main():
    prs = defaultdict(list)
    for pr_dir in sorted(p for p in VG.iterdir() if p.is_dir() and p.name not in {"_work", "bundles"}):
        for b in sorted(p for p in pr_dir.iterdir() if p.is_dir() and (p / "meta.json").exists()):
            prs[pr_dir.name].append(b)

    index = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "prs": {}}
    verdicts = Counter()
    pr_tars = []
    all_rows = []

    for pr, bundles in sorted(prs.items()):
        rows = []
        for b in bundles:
            meta = json.loads((b / "meta.json").read_text())
            slug = b.name
            # researcher-facing artifacts, generated at packaging time
            tc = (b / "test.patch").read_text() if (b / "test.patch").exists() else ""
            tp = meta.get("test_path")
            if tc and tp:
                (b / "test.diff").write_text(make_test_diff(tp, tc))
            (b / "REPRO.md").write_text(repro_md(b, meta))
            tar = BUNDLES / pr / f"{slug}.tar.gz"
            sha = build_tar(tar, [(b, slug)])
            (Path(str(tar) + ".sha256")).write_text(f"{sha}  {slug}.tar.gz\n")
            cand = meta.get("candidate") or {}
            verdicts[meta.get("verdict", "?")] += 1
            row = {"bug_id": meta.get("bug_id") or f"{pr}-{slug}", "class_slug": slug,
                   "verdict": meta.get("verdict"), "three_way": meta.get("three_way"),
                   "title": cand.get("title"), "file": cand.get("file"), "severity": cand.get("severity"),
                   "n_findings": cand.get("n_findings"), "n_cells": cand.get("n_cells"),
                   "claim_restated": meta.get("claim_restated"), "expected_failure": meta.get("expected_failure"),
                   "fidelity": meta.get("fidelity"),
                   "dir": str(b.relative_to(VG)), "tarball": str(tar.relative_to(VG)),
                   "tarball_sha256": sha, "tarball_bytes": tar.stat().st_size}
            rows.append(row); all_rows.append(row)

        manifest = {"pr": pr, "n_candidates": len(rows),
                    "verdicts": dict(Counter(r["verdict"] for r in rows)),
                    "repo": "https://github.com/calcom/cal.com" if pr in {"11059", "14740", "10967"} else None,
                    "candidates": rows,
                    "provenance": {"spec": "analysis/verified_gold/README.md",
                                   "driver": "tools/verified_gold_driver.py",
                                   "builder": "tools/verified_gold_tarballs.py"}}
        (BUNDLES / pr / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))

        sm = [f"# Verified hidden gold — PR {pr}", "",
              f"Candidates: {len(rows)} · verdicts: {manifest['verdicts']}", "",
              "| bug id | bug | verdict | head | base | fix | file | tarball sha256 |",
              "|---|---|---|---|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: (r["verdict"] or "", r["bug_id"])):
            tw = r["three_way"] or {}
            sm.append(f"| {r['bug_id']} | {r['class_slug']} | `{r['verdict']}` | {tw.get('head','—')} | "
                      f"{tw.get('base','—')} | {tw.get('fixed','—')} | `{r['file']}` | `{(r['tarball_sha256'] or '')[:12]}…` |")
        (BUNDLES / pr / "SUMMARY.md").write_text("\n".join(sm) + "\n")

        pr_tar = BUNDLES / f"verified_gold_{pr}.tar.gz"
        pr_sha = build_tar(pr_tar, [(BUNDLES / pr, f"verified_gold_{pr}")])
        pr_tars.append((pr, pr_tar))
        index["prs"][pr] = {"n_candidates": len(rows), "verdicts": manifest["verdicts"],
                            "manifest": str((BUNDLES / pr / "MANIFEST.json").relative_to(VG)),
                            "summary": str((BUNDLES / pr / "SUMMARY.md").relative_to(VG)),
                            "pr_tarball": str(pr_tar.relative_to(VG)), "pr_tarball_sha256": pr_sha,
                            "pr_tarball_bytes": pr_tar.stat().st_size}

    if pr_tars:
        entries = [(BUNDLES / pr, f"verified_gold_{pr}") for pr, _ in pr_tars]
        all_tar = BUNDLES / "verified_gold_all.tar.gz"
        sha = build_tar(all_tar, entries)
        index["all_tarball"] = {"path": str(all_tar.relative_to(VG)), "sha256": sha, "bytes": all_tar.stat().st_size}
    index["verdict_counts"] = dict(verdicts)
    (VG / "INDEX.json").write_text(json.dumps(index, indent=1))

    # replication kit: one document a researcher can start from
    kit = ["# Replication kit — verified hidden gold", "",
           "Every bundle in `bundles/<pr>/` is a self-contained evidence packet: a runnable test that",
           "FAILS on the pinned post-PR revision, a minimal `fix.patch` that makes it PASS, the raw logs of",
           "both runs, and `meta.json` with the exact commits, toolchain and SHA-256 hashes.", "",
           "## Prerequisites", "",
           "| repo | toolchain | services |", "|---|---|---|",
           "| calcom/cal.com | node 22, yarn 3.4.1 (`corepack prepare yarn@3.4.1 --activate`), ~2 GB deps | only for DB-semantics claims: `docker compose -f docker-compose.verify.yml up -d` |",
           "| discourse-graphite | system ruby 2.6 (the tests stub their collaborators; no bundle install) | redis only for throttle-key claims |", "",
           "## Steps (any bundle)", "",
           "```bash",
           "tar xzf bundles/<pr>/<bug-id>-<slug>.tar.gz && cd <bug-id>-<slug>",
           "cat REPRO.md          # claim, pinned SHAs, exact commands, expected output",
           "```",
           "",
           "`REPRO.md` in each bundle is written to be machine-independent: it clones the upstream repo at",
           "the pinned SHA, applies `test.diff`, runs the test (expect FAIL), applies `fix.patch`, and runs it",
           "again (expect PASS).", "",
           "## Fidelity labels you will see", "",
           "- `repo_suite` — the repository's own test runner at the pinned revision (highest fidelity).",
           "- `repo_suite_harness_config` — same runner, minimal config for `.tsx` tests the repo's workspace glob excludes.",
           "- `standalone_real_code` — the real post-PR file executed with visible stubs for collaborators (Rails 4.2 era).",
           "",
           "## Verdicts and what each one means", "",
           "See `analysis/verified_gold/README.md`. Only `confirmed_regression` and",
           "`behavior_change_not_regression` are promoted as verified hidden gold; `defect_present_before_pr`,",
           "`unresolved_file`, `inconclusive_env`, `not_a_bug` and `static_text_test` are reported as separate",
           "tiers, never discarded.", ""]

    # human entry point
    L = ["# Verified hidden gold — evidence bundles", "",
         "Each bug has a browsable directory and an attachable tarball, per PR:",
         "",
         "- unpacked bundle: `analysis/verified_gold/<pr>/<bug-id>-<slug>/` (meta.json, test.patch, fix.patch, logs/, REPRO.md)",
         "- attachable tarball: `analysis/verified_gold/bundles/<pr>/<bug-id>-<slug>.tar.gz` (+ `.sha256`)",
         "- per-PR bundle: `analysis/verified_gold/bundles/verified_gold_<pr>.tar.gz` (all bugs + MANIFEST + SUMMARY)",
         "- roll-up: `analysis/verified_gold/bundles/verified_gold_all.tar.gz`", "",
         "Every attempted candidate produces a bundle whatever the verdict; `not_a_bug` and",
         "`inconclusive_env` are the demotion-review queue (`DEMOTION_REVIEW.md`).", "",
         f"Generated {index['generated_utc']} · verdicts: {dict(verdicts)}", ""]
    for pr, v in sorted(index["prs"].items()):
        L += [f"## PR {pr} — {v['n_candidates']} candidates · {v['verdicts']}",
              f"- per-bug tarballs: `bundles/{pr}/`",
              f"- PR bundle: `{v['pr_tarball']}` · sha256 `{v['pr_tarball_sha256'][:16]}…` · {v['pr_tarball_bytes'] / 1024:.0f} KiB",
              f"- table: `{v['summary']}` · machine index: `{v['manifest']}`", ""]
    if index.get("all_tarball"):
        a = index["all_tarball"]
        L += ["## Roll-up", f"- `{a['path']}` · sha256 `{a['sha256'][:16]}…` · {a['bytes'] / 1024:.0f} KiB", ""]
    (VG / "INDEX.md").write_text("\n".join(L) + "\n")
    (VG / "REPLICATION_KIT.md").write_text("\n".join(kit) + "\n")

    print(f"bundles built: {len(all_rows)} candidates across {len(index['prs'])} PRs")
    print("verdicts:", dict(verdicts))
    for pr, v in index["prs"].items():
        print(f"  PR {pr}: {v['n_candidates']} -> {v['pr_tarball']} ({v['pr_tarball_bytes']/1024:.0f} KiB)")


if __name__ == "__main__":
    main()
