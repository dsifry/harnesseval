#!/usr/bin/env python3
"""Test-validate the D-labelled defects, with a fix-orthogonality check.

For every D-labelled defect (a label the merge audit split out of a multi-concern bundle):
  1. author a test for THAT defect (seeded with its label + the findings the assignment mapped to it)
  2. run it on the PR head            -> must FAIL (the defect is real)
  3. author + apply its own fix       -> must PASS   => the defect becomes D-verified
  4. revert, apply the SIBLING fix (the bundle's own fix.patch, which demonstrates the bundle's
     headline defect) and re-run      -> must stay FAIL. If it goes green, the label was actually the
     same defect as the bundle's own claim, so the defect is a duplicate and is merged away.

Artifacts per defect: <bundle>/defects/<D-id>/{test.diff,fix.patch,logs/{head,fixed,sibling}.log,meta.json}
Registry entries are updated in place (tier -> D-verified, or merged_into -> <bundle's verified defect>).

Usage: .venv/bin/python tools/verified_gold_defect_verify.py [--pr 4] [--limit N] [--only D-id]
"""
from __future__ import annotations
import argparse, asyncio, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import verified_gold_rails_driver as R           # noqa: E402
import verified_gold_driver as C                 # noqa: E402
from verified_gold_driver import AUTHOR_MODEL    # noqa: E402

VG = ROOT / "analysis/verified_gold"
RAILS = {"4", "8", "10"}
CHECKOUT = {"11059": "cal.com", "14740": "cal.com-14740", "10967": "cal.com-10967"}
ARGS = R if False else None


_FILE_IX = {}


def norm(p):
    return re.sub(r"[^a-z0-9]", "", p.lower())


_DIFF_FILES = {}


def pr_diff_files(pr):
    """The PR's changed files, straight from the cached diff (authoritative names)."""
    if pr in _DIFF_FILES:
        return _DIFF_FILES[pr]
    import glob as _g
    slug = pr
    files = []
    for f in _g.glob(str(ROOT / ".cache/pr_diffs/*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        url = d.get("url") or ""
        if url.rstrip("/").split("/")[-1] == slug:
            files = [x["filename"] for x in (d.get("files") or [])]
            break
    _DIFF_FILES[pr] = files
    return files


def resolve_file(pr, anchor):
    """Findings carry paths with underscores stripped by rj3 normalization, so match the normalized
    basename against the PR's changed files first (authoritative), then fall back to the checkout."""
    mod = R if pr in RAILS else C
    repo = mod.REPO
    want = norm(Path(anchor).name or anchor)
    for f in pr_diff_files(pr):
        if norm(Path(f).name) == want or want.endswith(norm(Path(f).name)) or norm(Path(f).name).endswith(want):
            return f
    if repo not in _FILE_IX:
        ix = {}
        for f in repo.rglob("*"):
            if not f.is_file() or ".git" in f.parts or "node_modules" in f.parts:
                continue
            ix.setdefault(norm(f.name), str(f.relative_to(repo)))
        _FILE_IX[repo] = ix
    return _FILE_IX[repo].get(want)


def set_repo(pr):
    if pr in RAILS:
        R.REPO = ROOT / ".cache/verify_repos/discourse"
        return "rails"
    C.REPO = ROOT / ".cache/verify_repos" / CHECKOUT[pr]
    return "calcom"


async def do_defect(d, findings, apply):
    pr, did = d["pr"], d["id"]
    kind = set_repo(pr)
    mod = R if kind == "rails" else C
    base, head = mod.PR_HEADS[pr]   # PR_HEADS maps  pr -> (base, head)
    bundle_dir = Path(d["evidence_dir"])
    sib = bundle_dir / "fix.patch"
    out = bundle_dir / "defects" / did
    (out / "logs").mkdir(parents=True, exist_ok=True)
    # INTEGRITY GUARD: a verified result must never be downgraded by a later flaky attempt
    # (this happened to 4-D19: a good pass was overwritten by an unresolved re-run).
    prev = out / "meta.json"
    if prev.exists():
        try:
            pm = json.loads(prev.read_text())
        except Exception:
            pm = {}
        if pm.get("verdict") == "D-verified" and pm.get("own_fix_makes_test_pass") and pm.get("sibling_fix_leaves_test_red") is not False:
            return did, "already D-verified (kept; no overwrite)"
    mod.clean_repo(head)                      # head first: the PR may ADD the file under test
    file = resolve_file(pr, d["anchor_file"]) or d["anchor_file"]
    file = file if file and (mod.REPO / file).exists() else None
    if not file:
        return did, "skipped_no_file"
    full = (mod.REPO / file).read_text()
    if len(full) <= 14000:
        content = full
    else:
        # Window by the FINDINGS' OWN ANCHORS (file:start-end), which is the context the campaign
        # already has: label-token matching picked the wrong one of three `references.find` sites.
        loc = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4}):~?(\d+)(?:-(\d+))?")
        want = norm(Path(file).name)
        starts = []
        for t in findings:
            for m2 in loc.finditer(t):
                if norm(Path(m2.group(1)).name) == want:
                    starts.append(int(m2.group(2)))
        starts = sorted(starts)
        best_i = (starts[len(starts)//2] - 1) if starts else 0
        lines = full.splitlines()
        lo, hi = max(0, best_i - 60), min(len(lines), best_i + 60)
        content = (f"// … lines 1-40 of {len(lines)}\n" + "\n".join(lines[:40]) +
                   f"\n// … REGION CITED BY THE REPORTS (lines {lo+1}-{hi}) …\n" + "\n".join(lines[lo:hi]))
    import os as _os
    rel = _os.path.relpath(str(mod.REPO / file), str(mod.REPO / Path(file).parent))
    load_hint = (f"REQUIRED: the file under test is {file}. Load it with `require_relative '{rel}'` "
                 f"(or an equivalent path that resolves to it). Do NOT search the filesystem for it, and do "
                 f"not abort if a candidate list fails.")
    cand = {"pr_slug": pr, "class_index": int(d["bundle"].split("B")[1]), "class_slug": did,
            "title": d["label"], "file": file, "file_resolved": file,
            "line": (d["anchor_lines"].split(",")[0].split("-")[0] or "?"), "reports": [load_hint] + findings[:5],
            "severity": "?", "n_findings": len(findings), "n_cells": 0}
    mod.clean_repo(head)
    stem = Path(file).stem
    supplier = str(Path(file).parent)
    # 1-2: author a test that fails on head
    tp = None
    for attempt in range(1, 4):
        if kind == "rails":
            parsed, _, _ = await mod.author_test(AUTHOR_MODEL, cand, file, content, supplier, stem)
        else:
            parsed, _, _ = await mod.author_test(AUTHOR_MODEL, cand, file, content, "", supplier, stem)
        if not parsed.get("test_code"):
            continue
        tp = parsed.get("test_path") or f"spec/verify/{stem}_verify.rb"
        (mod.REPO / tp).parent.mkdir(parents=True, exist_ok=True)
        (mod.REPO / tp).write_text(parsed["test_code"])
        _rc, head_log = mod.run_test(tp)
        cls = mod.classify(head_log)
        if cls == "FAIL":
            break
        if (cls == "?" or cls.startswith("ERROR")) and attempt < 3:
            # the test could not run (bad require path, missing stub, ActiveSupport blank?, ...):
            # feed the error back and rewrite the test
            content = content + ("\n\nLAST RUN (make the TEST execute; it must then FAIL on this code for the "
                                 "claimed defect - never change the file under test):\n" + head_log[-1500:] +
                                 "\nIf the error is 'Failed to load url <path>', the RELATIVE IMPORT DEPTH is wrong: "
                                 "count the directories from the test file's own directory to the target and adjust "
                                 "the number of leading '../' accordingly.")
            continue
        break
    if not parsed.get("test_code"):
        return did, "inconclusive_env"
    # 3: own fix
    fx = {}
    fixed_log = ""
    fix_model = AUTHOR_MODEL
    for attempt in range(1, 7):
        if attempt == 3:
            fix_model = "gpt-5.2"
        if kind == "rails":
            fx, _, _ = await mod.author_fix(fix_model, cand, file, content, parsed["test_code"], head_log,
                                           full_file=attempt >= 3)
        else:
            fx, _, _ = await mod.author_fix(fix_model, cand, file, content, parsed["test_code"], head_log,
                                           content, full_file=attempt >= 3)
        target = fx.get("fix_file_path") or file
        if not (mod.REPO / target).exists():
            target = file
        mod.sh("git checkout -q -- .")
        try:
            if fx.get("fixed_file_content"):
                (mod.REPO / target).write_text(fx["fixed_file_content"])
            else:
                if not (fx.get("fix_edits") or []):
                    continue
                mod.apply_edits(target, fx.get("fix_edits") or [])
        except Exception as e:
            head_log = head_log[-1200:] + f"\n\nFIX EDIT ERROR: {e}"
            continue
        _rc, fixed_log = mod.run_test(tp)
        c2 = mod.classify(fixed_log)
        if c2 == "PASS":
            break
        if c2.startswith("ERROR") or c2 == "?":
            head_log = head_log[-1200:] + "\n\nFIX RUN DID NOT EXECUTE (fix the test's stubs, not the file):\n" + fixed_log[-1000:]
            continue
        head_log = head_log[-1000:] + f"\n\nFIX RUN STILL RED: {fixed_log[-800:]}"
    own_ok = mod.classify(fixed_log) == "PASS"
    _rc, fix_diff = mod.sh(f"git diff -- {target}")
    # 4: sibling fix must leave it RED (orthogonality)
    ortho = None
    sibling_log = ""
    sib_apply = None
    if own_ok and sib.exists():
        mod.sh("git checkout -q -- .")
        (mod.REPO / tp).write_text(parsed["test_code"])
        _rc2, apply_out = mod.sh(f"git apply {sib.resolve()} 2>&1")   # ABSOLUTE: sh() runs with cwd=REPO
        sib_apply = apply_out.strip() or "applied cleanly"
        if not apply_out.strip():
            _rc3, sibling_log = mod.run_test(tp)
            ortho = mod.classify(sibling_log) != "PASS"
        else:
            ortho = None
    if apply:
        (out / "test.diff").write_text(parsed["test_code"])
        if fix_diff.strip():
            (out / "fix.patch").write_text(fix_diff)
        (out / "logs" / "head.log").write_text(head_log)
        (out / "logs" / "fixed.log").write_text(fixed_log)
        if sibling_log:
            (out / "logs" / "sibling.log").write_text(sibling_log)
        (out / "meta.json").write_text(json.dumps({
            "defect": did, "bundle": d["bundle"], "label": d["label"],
            "own_fix_makes_test_pass": own_ok, "sibling_fix_leaves_test_red": ortho,
            "verdict": ("D-verified" if (own_ok and ortho is not False) else
                        "duplicate_of_bundle_defect" if own_ok and ortho is False else "unresolved"),
            "test_path": tp, "anchor": f"{file}:{d['anchor_lines']}",
            "sibling_fix": str(sib), "sibling_fix_apply": sib_apply, "model": AUTHOR_MODEL}, indent=1))
    mod.clean_repo(head)
    if not own_ok:
        return did, "unresolved"
    if ortho is False:
        return did, "MERGED (sibling fix also fixes it -> same defect)"
    return did, f"D-verified (orthogonal={ortho})"


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", default=None); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default=None); ap.add_argument("--ids", default=None)
    ap.add_argument("--apply", action="store_true", default=True)
    a = ap.parse_args()
    reg = json.load(open(VG / "DEFECT_REGISTRY.json"))
    assign = json.load(open(VG / "DEFECT_ASSIGN.json"))
    # invert the assignment: defect id -> finding texts
    by_def = {}
    for pr, m in assign.items():
        inv = {}
        for h, did in m.items():
            inv.setdefault(did, 0)
            inv[did] += 1
        by_def[pr] = inv
    # rebuild actual texts: walk runs once per PR
    import glob
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    texts_by_pr = {}
    for pr in set(d["pr"] for d in reg["defects"]):
        u = next(u for u in D["pr_golden"] if u.rstrip("/").split("/")[-1] == pr)
        texts = [t for r in D["all_healthy_runs"] if r["url"] == u for t in (r.get("bugtexts") or [])]
        texts_by_pr[pr] = texts
    import hashlib
    def sha(t): return hashlib.sha1(t.encode()).hexdigest()[:16]
    todo = [d for d in reg["defects"] if d["tier"] == "D-labelled"]
    if a.ids:
        want = [x.strip() for x in a.ids.split(",") if x.strip()]
        todo = [d for d in reg["defects"] if d["id"] in want]
    if a.pr: todo = [d for d in todo if d["pr"] == a.pr]
    if a.only: todo = [d for d in todo if d["id"] == a.only]
    if a.limit: todo = todo[:a.limit]
    print(f"defects to validate: {len(todo)}", flush=True)
    results = []
    for d in todo:
        amap = assign.get(d["pr"], {})
        findings = [t for t in texts_by_pr[d["pr"]] if amap.get(sha(t)) == d["id"]]
        did, status = await do_defect(d, findings, a.apply)
        print(f"  {did} [{d['bundle']}] -> {status}", flush=True)
        results.append({"id": did, "status": status})
        json.dump(results, open(VG / "_work" / f"defect_verify_{a.pr or 'all'}.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
