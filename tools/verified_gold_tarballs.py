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

    print(f"bundles built: {len(all_rows)} candidates across {len(index['prs'])} PRs")
    print("verdicts:", dict(verdicts))
    for pr, v in index["prs"].items():
        print(f"  PR {pr}: {v['n_candidates']} -> {v['pr_tarball']} ({v['pr_tarball_bytes']/1024:.0f} KiB)")


if __name__ == "__main__":
    main()
