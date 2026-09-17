#!/usr/bin/env python3
"""Verified-hidden-gold driver: produce executable evidence bundles per candidate.

Per candidate (cal.com / repo-suite fidelity):
  1. settle the checkout on the PR head commit (clean tree)
  2. ask a model to author a vitest test that fails on the head code by asserting the argued behavior,
     plus the full corrected content of the source file (minimal fix)
  3. run the test on head -> expect FAIL (retry authoring on load/compile errors, max k)
  4. write the fixed source, run again -> expect PASS
  5. run the test at base -> PASS (confirmed_regression) or module-absent (behavior_change_not_regression)
  6. write the bundle: test.patch, fix.patch, logs/{base,head,fixed}.log, meta.json, REPRO.md

Verdicts: confirmed_regression | behavior_change_not_regression | not_a_bug (demotion candidate) |
inconclusive_env. Every attempted candidate produces a bundle.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, time, asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402

REPO = ROOT / ".cache/verify_repos/cal.com"
BUNDLE_ROOT = ROOT / "analysis/verified_gold"
PR_HEADS = {
    "11059": ("bc89fe00ea84d20bedcec782f0701b9711dc8201", "9fde0e906897cc0f4f71793f647dd629faba3317"),
    "14740": ("b004587262e8221083bafbe9a0c515e7becaa7b3", "92f44dcea7ff19e9123a30c63c167a2938df5a55"),
    "10967": ("a308075bc39b77ed7059b0cae9d443d669a7bf98", "de628295646d0848226618108a52f2f1e5d04ac0"),
}
SYSTEM = "You are a senior TypeScript engineer writing executable regression evidence. Respond with ONLY valid JSON."
PROMPT = """A code-review campaign claims the following defect in this pull request. Turn the claim into
EXECUTABLE EVIDENCE: a vitest test that FAILS on the current (post-PR) code by asserting the claimed
behavior, plus the MINIMAL source fix that makes it pass.

CLAIM
  file: {file} (line ~{line})
  title: {title}
  severity: {severity}
  reports (deduplicated; may state the mechanism):
{reports}

CURRENT POST-PR SOURCE of {file}:
```ts
{content}
```

PR DIFF for this file (context; may be empty):
```diff
{diff}
```

REQUIREMENTS
- Import the REAL module with a relative path and execute the real code path.
- The test must FAIL on the current code with an assertion naming the claimed behavior, and PASS once the
  minimal fix is applied. Assert observable behavior (returned values, thrown errors, side effects).
- Put the test next to the source: same directory, name `{stem}.verified.test.ts`.
- Set env vars BEFORE importing modules that read them at import time (dynamic `await import(...)`).
- Mock only true externals (network, prisma, feature flags) — never the module under test.
- The fix must be MINIMAL: change only what the claimed defect requires.

Respond with ONLY this JSON object:
{{"test_path": "{dir}/{stem}.verified.test.ts",
  "test_code": "<full test file contents>",
  "fixed_file_path": "{file}",
  "fixed_file_content": "<full corrected source file contents>",
  "claim_restated": "<one sentence: the behavior the test demonstrates>",
  "expected_failure": "<assertion message expected on unfixed code>",
  "confidence": 0.0-1.0}}"""


def sh(cmd, cwd=REPO, timeout=300):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def clean_repo(head):
    sh(f"git checkout -q -f {head}")
    sh("git checkout -q -- .")
    sh("git clean -qfd -e node_modules -e .yarn -e .yarnrc.yml -e .pnp.cjs")


def bundle_dir(pr, slug):
    d = BUNDLE_ROOT / pr / slug
    (d / "logs").mkdir(parents=True, exist_ok=True)
    return d


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pr_file_diff(pr_url, file):
    import glob as _g
    for f in _g.glob(str(ROOT / ".cache/pr_diffs/*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if d.get("url") != pr_url:
            continue
        for fl in d.get("files") or []:
            if fl.get("filename") == file:
                return (fl.get("patch") or "")[:8000]
    return ""


async def author(model, cand, file, content, diff, supplier_dir, stem):
    prompt = PROMPT.format(file=file, line=cand.get("line") or "?", title=cand.get("title") or "",
                           severity=cand.get("severity") or "?",
                           reports="\n".join(f"- {r}" for r in cand.get("reports", [])[:6]),
                           content=content[:14000], diff=diff or "(none)",
                           dir=supplier_dir, stem=stem)
    parsed, tin, tout, _ = await call_model_json(model, SYSTEM, prompt, effort="medium", max_tokens=8000)
    return (parsed if isinstance(parsed, dict) else {}), tin, tout


def run_test(test_path):
    return sh(f"yarn vitest run {test_path} --reporter=basic", timeout=420)


def classify(log):
    if re.search(r"Test Files\s+1 passed", log):
        return "PASS"
    if re.search(r"Failed to load url|Cannot find module", log):
        return "N/A_module_absent"
    if re.search(r"Test Files\s+1 failed|AssertionError", log):
        return "FAIL"
    return "?"


def write_bundle(d, cand, pr, verdict, logs, test_code, fix_diff, test_path, extra=None):
    (d / "test.patch").write_text(test_code)
    if fix_diff:
        (d / "fix.patch").write_text(fix_diff)
    for k, v in logs.items():
        (d / "logs" / f"{k}.log").write_text(v)
    meta = {
        "bug_id": f"{pr}-B{cand['class_index']:02d}",
        "candidate": cand, "pr": pr, "verdict": verdict, "fidelity": "repo_suite",
        "three_way": {k: classify(v) for k, v in logs.items()},
        "test_path": test_path, "fix_scope": "minimal fix for the demonstrated instance only",
        "sibling_instances": {"note": "other instances of this class are unverified siblings; fix.patch does not address them"},
        "provenance": {"produced_by": "tools/verified_gold_driver.py",
                       "spec": "analysis/verified_gold/README.md", "date": time.strftime("%Y-%m-%d")},
    }
    if extra:
        meta.update(extra)
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    (d / "REPRO.md").write_text(
        f"# REPRO — {cand.get('title')}\n\n**Verdict:** `{verdict}` · repo suite (vitest)\n\n"
        f"```bash\ncd .cache/verify_repos/cal.com && git checkout -f {PR_HEADS[pr][1]}\n"
        f"git apply {d}/test.patch\n"
        f"yarn vitest run {test_path}                       # expected: FAIL\n"
        f"git apply {d}/fix.patch\n"
        f"yarn vitest run {test_path}                       # expected: PASS\n```\n")
    return meta


async def do_candidate(cand, model, k_retry=3):
    pr = cand["pr_slug"]; base, head = PR_HEADS[pr]
    file = cand.get("file") or ""
    if not file or file == "?" or not (REPO / file).exists():
        return None
    stem = Path(file).stem
    supplier_dir = str(Path(file).parent)
    d = bundle_dir(pr, f"B{cand['class_index']:02d}-{cand['class_slug']}")
    clean_repo(head)
    content = (REPO / file).read_text()
    diff = pr_file_diff(cand["pr"], file)
    notes, tin, tout = [], 0, 0
    for attempt in range(1, k_retry + 1):
        parsed, i1, o1 = await author(model, cand, file, content, diff, supplier_dir, stem)
        tin += i1; tout += o1
        tp = parsed.get("test_path") or f"{supplier_dir}/{stem}.verified.test.ts"
        if not parsed.get("test_code") or not parsed.get("fixed_file_content"):
            notes.append(f"attempt {attempt}: model returned incomplete JSON")
            continue
        (REPO / tp).write_text(parsed["test_code"])
        _rc, head_log = run_test(tp)
        if classify(head_log) == "PASS":
            clean_repo(head)
            return write_bundle(d, cand, pr, "not_a_bug", {"head": head_log}, parsed["test_code"], "", tp,
                                {"notes": notes,
                                 "demotion_review": "test passes on unmodified head: no observable behaviour change demonstrated",
                                 "model_tokens": {"in": tin, "out": tout}})
        if re.search(r"Failed to load|Cannot find module|Transform failed|SyntaxError", head_log) and attempt < k_retry:
            notes.append(f"attempt {attempt}: test could not load/compile; retried")
            diff = (diff or "") + "\n\nLAST TEST RUN ERROR (fix the test):\n" + head_log[-1500:]
            continue
        (REPO / file).write_text(parsed["fixed_file_content"])
        _rc2, fixed_log = run_test(tp)
        _rc3, fix_diff = sh(f"git diff -- {file}")
        if classify(fixed_log) != "PASS" and attempt < k_retry:
            notes.append(f"attempt {attempt}: fix did not make the test pass; retried")
            sh("git checkout -q -- .")
            diff = (diff or "") + "\n\nFIX RUN ERROR (fix the source):\n" + fixed_log[-1500:]
            continue
        _rc4, base_log = sh(f"git checkout -q -f {base} && yarn vitest run {tp} --reporter=basic", timeout=420)
        bc = classify(base_log)
        verdict = ("behavior_change_not_regression" if bc == "N/A_module_absent"
                   else "confirmed_regression" if bc == "PASS"
                   else "defect_present_before_pr")   # base already fails on the same assertion
        clean_repo(head)
        return write_bundle(d, cand, pr, verdict, {"base": base_log, "head": head_log, "fixed": fixed_log},
                            parsed["test_code"], fix_diff, tp,
                            {"notes": notes, "claim_restated": parsed.get("claim_restated"),
                             "expected_failure": parsed.get("expected_failure"),
                             "model_confidence": parsed.get("confidence"),
                             "model_tokens": {"in": tin, "out": tout}})
    clean_repo(head)
    return write_bundle(d, cand, pr, "inconclusive_env", {}, "", "", "",
                        {"notes": notes, "blocker": notes[-1] if notes else "authoring failed"})


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", default="11059")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--model", default="gpt-5.2")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    global REPO
    REPO = Path(a.repo)
    man = json.load(open(BUNDLE_ROOT / "_work/calcom_candidates.json"))
    cands = [c for c in man if c["pr_slug"] == a.pr]
    if a.only is not None:
        cands = [c for c in cands if c["class_index"] == a.only]
    if a.limit:
        cands = cands[:a.limit]
    # resume-safe: skip candidates that already have a bundle unless --force
    if not a.force:
        before = len(cands)
        cands = [c for c in cands
                 if not (BUNDLE_ROOT / c["pr_slug"] / f"B{c['class_index']:02d}-{c['class_slug']}" / "meta.json").exists()]
        if before != len(cands):
            print(f"skipping {before - len(cands)} already-bundled candidate(s); {len(cands)} to run", flush=True)
    index = []
    for i, c in enumerate(cands, 1):
        t0 = time.time()
        try:
            m = await do_candidate(c, a.model)
            status = (m or {}).get("verdict", "skipped_no_file")
        except Exception as e:
            status = f"error: {type(e).__name__}: {e}"
        print(f"[{i}/{len(cands)}] {c['pr_slug']}#{c['class_index']} {c['class_slug'][:44]:46s} {status} ({time.time()-t0:.0f}s)", flush=True)
        index.append({"pr": c["pr_slug"], "class_index": c["class_index"], "slug": c["class_slug"], "verdict": status})
        json.dump(index, open(BUNDLE_ROOT / f"_work/progress_calcom_{a.pr}.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
