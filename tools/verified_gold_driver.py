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
import argparse, hashlib, json, re, shutil, subprocess, sys, time, asyncio
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
AUTHOR_MODEL = 'deepseek-4.1-flash'   # LunarRoute; recorded per bundle
SYSTEM = "You are a senior TypeScript engineer writing executable regression evidence. Respond with ONLY valid JSON."
TEST_PROMPT = """A code-review campaign claims the following defect in this pull request. Write a vitest
test that FAILS on the current (post-PR) code by asserting the claimed behavior.

CLAIM
  file: {file} (line ~{line})
  title: {title}
  severity: {severity}
  reports (deduplicated; may state the mechanism):
{reports}

CURRENT POST-PR SOURCE (may be an excerpt for large files):
```ts
{content}
```

PR DIFF for this file (context; may be empty):
```diff
{diff}
```

AN EXISTING TEST FROM THIS PACKAGE — follow its conventions (imports, mocking style, dynamic imports):
```ts
{tmpl}
```

REQUIREMENTS
- Import the REAL module (relative path) and execute the real code path.
- The test must FAIL on the current code with an assertion naming the claimed behavior.
- Assert observable behavior (returned values, thrown errors, side effects), not implementation details.
- Put it next to the source: `{dir}/{stem}.verified.test{ext}` (use the SAME extension family as the source: .tsx when the source is .tsx, because JSX is only parsed in .tsx).
- Set env vars BEFORE importing modules that read them at import time (dynamic `await import(...)`).
- Mock only true externals (network, prisma, feature flags) — never the module under test.
- Keep it under ~150 lines.

Respond with ONLY this JSON object (no prose, no code fences):
{{"test_path": "{dir}/{stem}.verified.test{ext}",
  "test_code": "<full test file contents>",
  "claim_restated": "<one sentence>",
  "expected_failure": "<assertion message expected on unfixed code>",
  "confidence": 0.0-1.0}}"""

FIX_PROMPT = """A vitest test demonstrates the defect below and currently FAILS on this code. Produce the MINIMAL
fix as exact-match edits.

CLAIM: {title}
FILE: {file}

TEST (must pass after your fix; do not modify the test):
```ts
{test_code}
```

CURRENT SOURCE (excerpt for large files):
```ts
{content}
```

FAILING TEST OUTPUT (tail):
```
{head_log}
```

RULES
- Return ONLY exact-match edits: each `find` must be a verbatim excerpt of the CURRENT SOURCE and must
  occur EXACTLY ONCE. Include enough surrounding context to be unique.
- Minimal change: fix only what this defect requires; keep everything else byte-identical.
- NEVER return the whole file.

The code to change may live in a DIFFERENT file from the one the test imports (e.g. a schema, helper
or caller in another module) — name that file in `fix_file_path` (an existing repo-relative path).

Respond with ONLY this JSON object (no prose, no code fences):
{{"fix_file_path": "<repo-relative path of the file to edit>",
  "fix_edits": [{{"find": "<verbatim excerpt of THAT file>", "replace": "<corrected excerpt>"}}],
  "explanation": "<one sentence>"}}"""


def sh(cmd, cwd=None, timeout=300):
    """Run a shell command. cwd defaults to the CURRENT module-level REPO (resolved at call
    time — binding it as a default argument silently pinned every parallel stream to the
    first checkout)."""
    p = subprocess.run(cmd, cwd=str(cwd or REPO), shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def clean_repo(head):
    sh(f"git checkout -q -f {head}")
    sh("git checkout -q -- .")
    sh("git clean -qfd -e node_modules -e .yarn -e .yarnrc.yml -e .pnp.cjs")


ENV_CACHE = ROOT / ".cache/verify_env"


def prepare_env():
    """Idempotent preparation of the THROWAWAY verification checkout (disclosed in meta.env_patches):
    - the repo's vitest config may declare coverage provider "c8", which the installed vitest rejects
    - setupVitest.ts imports resize-observer-polyfill; the coverage provider package must be present
    Never touches the campaign's frozen artifacts; only these scratch checkouts."""
    patches = []
    cfg = REPO / "vitest.config.ts"
    if cfg.exists():
        t = cfg.read_text()
        if '"c8"' in t:
            cfg.write_text(t.replace('"c8"', '"v8"'))
            patches.append("vitest.config.ts: coverage provider c8 -> v8")
    ws = REPO / "vitest.workspace.ts"
    if ws.exists():
        t = ws.read_text()
        if "{test,spec}.{ts,js}" in t:
            ws.write_text(t.replace("{test,spec}.{ts,js}", "{test,spec}.{ts,js,tsx}"))
            patches.append("vitest.workspace.ts: include glob widened to {ts,js,tsx} (repo excludes .tsx)")
    for pkg in ("resize-observer-polyfill", "@vitest/coverage-v8"):
        dest = REPO / "node_modules" / pkg
        src = ENV_CACHE / pkg
        if not dest.exists() and src.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest)
            patches.append(f"node_modules: installed missing dev dep {pkg}")
    return patches


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


def _window(content, line, span=140):
    """For large files: the region around the claimed line plus the file head (imports)."""
    lines = content.splitlines()
    try:
        ln = int(line)
    except Exception:
        ln = 0
    if ln <= 0:
        return content[:16000]
    lo, hi = max(0, ln - span), min(len(lines), ln + span)
    # NOTE: no line-number prefixes — the model must be able to copy `find` strings verbatim,
    # and numbering them made every exact-match edit fail.
    return (f"// … file head (1-40 of {len(lines)} lines)\n" + "\n".join(lines[:40])
            + f"\n// … region around the claim (lines {lo + 1}-{hi} of {len(lines)})\n"
            + "\n".join(lines[lo:hi]))


def apply_edits(path, edits):
    """Apply exact-match edits; every `find` must occur exactly once."""
    p = REPO / path
    s = p.read_text()
    for i, e in enumerate(edits):
        f, r = e.get("find"), e.get("replace")
        if not f or r is None:
            raise ValueError(f"edit {i}: missing find/replace")
        if s.count(f) != 1:
            raise ValueError(f"edit {i}: `find` occurs {s.count(f)} times (need exactly 1)")
        s = s.replace(f, r)
    p.write_text(s)


def _template_test(file):
    """Nearest existing *.test.ts from the same package, first ~55 lines, as a conventions anchor."""
    base = REPO / Path(file).parent
    for up in [base] + list(base.parents)[:4]:
        if not str(up).startswith(str(REPO)):
            break
        hits = [h for h in sorted(up.rglob("*.test.ts")) if "node_modules" not in str(h) and h.name != "index.test.ts"]
        if hits:
            try:
                return "\n".join(hits[0].read_text().splitlines()[:55])
            except Exception:
                return ""
    return ""


async def author_test(model, cand, file, content, diff, supplier_dir, stem, extra=""):
    prompt = TEST_PROMPT.format(file=file, line=cand.get("line") or "?", title=cand.get("title") or "",
                                severity=cand.get("severity") or "?",
                                reports="\n".join(f"- {r}" for r in cand.get("reports", [])[:4]),
                                content=content, diff=(diff or "(none)") + extra,
                                tmpl=_template_test(file) or "(no neighbouring test found)",
                                dir=supplier_dir, stem=stem,
                                ext=(".tsx" if file.endswith(".tsx") else ".ts"))
    # reasoning models burn the output budget on large inputs: keep effort low and the budget large,
    # otherwise the call returns EMPTY content with 0 output tokens (observed on 87k-char files).
    parsed, tin, tout, _ = await call_model_json(model, SYSTEM, prompt, effort="low", max_tokens=16000)
    return (parsed if isinstance(parsed, dict) else {}), tin, tout


REFUTE_PROMPT = """A test that was written to demonstrate the claim below PASSED on the UNMODIFIED code.
That means either (a) the claim is false, or (b) the test did not actually exercise the claimed behaviour.

CLAIM
  file: {file}
  title: {title}
  reports:
{reports}

THE TEST THAT PASSED (do not simply repeat it):
```ts
{test_code}
```

RELEVANT SOURCE:
```ts
{content}
```

Write a DIFFERENT, adversarial test that FAILS if the claim is true. Requirements:
- Construct exactly the input/state the claim asserts is mishandled, and assert on the SPECIFIC
  claimed consequence and the SPECIFIC field/path involved (e.g. assert the validation error is about
  that field, or assert the exact returned value), never a generic "something failed".
- Make sure the rest of the input is valid, so a failure cannot come from an unrelated field.
- If the code genuinely handles the claimed case correctly, your test will pass — that is a valid
  outcome, but only if it truly exercises the claim.

Respond with ONLY this JSON object:
{{"test_code": "<full test file contents>",
  "exercises_claim": "one sentence on what input/assertion makes this a genuine test of the claim",
  "claim_refuted": true|false,
  "refutation_evidence": "<if refuted: the exact evidence from the source/test run>",
  "confidence": 0.0-1.0}}"""


async def author_refute(model, cand, file, content, test_code, head_log, supplier_dir, stem):
    prompt = REFUTE_PROMPT.format(file=file, title=cand.get("title") or "",
                                  reports="\n".join(f"- {r}" for r in cand.get("reports", [])[:4]),
                                  test_code=test_code[:5000], content=content)
    parsed, tin, tout, _ = await call_model_json(model, SYSTEM, prompt, effort="low", max_tokens=16000)
    return (parsed if isinstance(parsed, dict) else {}), tin, tout


async def author_fix(model, cand, file, content, test_code, head_log, original_content):
    prompt = FIX_PROMPT.format(title=cand.get("title") or "", file=file, test_code=test_code[:6000],
                               content=content, head_log=head_log[-2500:])
    parsed, tin, tout, _ = await call_model_json(model, SYSTEM, prompt, effort="low", max_tokens=8000)
    return (parsed if isinstance(parsed, dict) else {}), tin, tout


HARNESS_CFG = ".vitest.verify.config.ts"
HARNESS_WS = ".vitest.verify.workspace.ts"
LAST_FIDELITY = {"value": "repo_suite"}


def _write_harness_cfg():
    """Harness-owned vitest config (jsx automatic, tsx included, jsdom, no repo setup files)."""
    (REPO / HARNESS_CFG).write_text(
        'import { defineConfig } from "vitest/config";\n'
        'export default defineConfig({\n'
        '  esbuild: { jsx: "automatic" },\n'
        '  test: { include: ["**/*.verified.test.{ts,tsx}"], environment: "jsdom",\n'
        '          globals: true, setupFiles: [], coverage: { enabled: false } },\n'
        '});\n')


def _run_harness_cfg(bin_, test_path):
    """Run under the harness config. The repo's vitest.workspace.ts takes precedence over --config,
    so it is moved aside for the run and restored afterwards (clean_repo also restores it)."""
    _write_harness_cfg()
    ws, bak = REPO / "vitest.workspace.ts", REPO / "vitest.workspace.ts.harness-bak"
    moved = False
    if ws.exists():
        ws.rename(bak); moved = True
    try:
        return sh(f"{bin_} run {test_path} --reporter=basic --config {HARNESS_CFG}", timeout=420)[1]
    finally:
        if moved and bak.exists():
            bak.rename(ws)


def run_test(test_path):
    """Fidelity ladder:
       tsx targets  -> harness config (the repo workspace excludes .tsx and its tsconfig sets
                       jsx: preserve, which makes JSX unparseable) => repo_suite_harness_config
       other targets -> the repo's own config (repo_suite); if it cannot execute the file at all
                       (excluded by glob, parse error, missing dep), retry under the harness config.
    Env prep is re-applied first: resetting the worktree reverts the config patches."""
    prepare_env()
    bin_ = "./node_modules/.bin/vitest" if (REPO / "node_modules/.bin/vitest").exists() else "yarn vitest"
    if test_path.endswith(".tsx"):
        log = _run_harness_cfg(bin_, test_path)
        LAST_FIDELITY["value"] = "repo_suite_harness_config" if ran(log) else "repo_suite"
        return 0, log
    log = sh(f"{bin_} run {test_path} --reporter=basic", timeout=420)[1]
    broken = (not ran(log)) or ("No test files found" in log) or ("invalid JS syntax" in log) or ("MISSING DEP" in log)
    if broken:
        log2 = _run_harness_cfg(bin_, test_path)
        if ran(log2):
            LAST_FIDELITY["value"] = "repo_suite_harness_config"
            return 0, log2
    LAST_FIDELITY["value"] = "repo_suite"
    return 0, log


def ran(log):
    """True when vitest actually executed (its summary line is present)."""
    return bool(re.search(r"Test Files\s+\d+ (passed|failed)", log)) or bool(re.search(r"Tests\s+\d+", log))


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
        "bug_id": f"{pr}-B{cand['class_index']:02d}", "authoring_model": AUTHOR_MODEL,
        "candidate": cand, "pr": pr, "verdict": verdict, "fidelity": LAST_FIDELITY["value"],
        "three_way": {k: classify(v) for k, v in logs.items()},
        "test_path": test_path, "fix_scope": "minimal fix for the demonstrated instance only",
        "sibling_instances": {"note": "other instances of this class are unverified siblings; fix.patch does not address them"},
        "provenance": {"produced_by": "tools/verified_gold_driver.py",
                       "spec": "analysis/verified_gold/README.md", "date": time.strftime("%Y-%m-%d")},
    }
    if extra:
        meta.update(extra)
    meta.setdefault("env_patches", [])
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    (d / "REPRO.md").write_text(
        f"# REPRO — {cand.get('title')}\n\n**Verdict:** `{verdict}` · repo suite (vitest)\n\n"
        f"```bash\ncd .cache/verify_repos/cal.com && git checkout -f {PR_HEADS[pr][1]}\n"
        f"git apply {d}/test.patch\n"
        f"yarn vitest run {test_path}                       # expected: FAIL\n"
        f"git apply {d}/fix.patch\n"
        f"yarn vitest run {test_path}                       # expected: PASS\n```\n")
    return meta


async def do_candidate(cand, model, k_retry=3, k_fix=4):
    pr = cand["pr_slug"]; base, head = PR_HEADS[pr]
    clean_repo(head)                                  # worktree at head before any check
    file = cand.get("file_resolved") or ""
    exists = bool(file) and sh(f"git cat-file -e {head}:{file}")[0] == 0
    if not exists:
        d = bundle_dir(pr, f"B{cand['class_index']:02d}-{cand['class_slug']}")
        (d / "meta.json").write_text(json.dumps({
            "bug_id": f"{pr}-B{cand['class_index']:02d}", "candidate": cand, "pr": pr,
            "verdict": "unresolved_file",
            "blocker": f"could not pin the finding to a file changed by this PR (card file: {cand.get('file')!r}); needs manual triage",
            "fidelity": "n/a",
            "provenance": {"produced_by": "tools/verified_gold_driver.py",
                           "spec": "analysis/verified_gold/README.md", "date": time.strftime("%Y-%m-%d")}}, indent=1))
        return {"verdict": "unresolved_file"}

    stem = Path(file).stem
    supplier_dir = str(Path(file).parent)
    d = bundle_dir(pr, f"B{cand['class_index']:02d}-{cand['class_slug']}")
    env_patches = prepare_env()
    original = (REPO / file).read_text()
    content = _window(original, cand.get("line"), 60) if len(original) > 9000 else original
    diff = pr_file_diff(cand["pr"], file)
    notes, tin, tout = [], 0, 0
    tp = f"{supplier_dir}/{stem}.verified.test" + (".tsx" if file.endswith(".tsx") else ".ts")
    test_code, head_log, fixed_log, fix_diff = None, "", "", ""

    # ---- 1. author a test that fails on head
    for attempt in range(1, k_retry + 1):
        parsed, i1, o1 = await author_test(model, cand, file, content, diff, supplier_dir, stem)
        tin += i1; tout += o1
        tp = parsed.get("test_path") or tp
        if not parsed.get("test_code"):
            notes.append(f"test attempt {attempt}: incomplete JSON")
            continue
        test_code = parsed["test_code"]
        (REPO / tp).write_text(test_code)
        _rc, head_log = run_test(tp)
        if classify(head_log) == "PASS":
            # Demotion candidate — but a test can pass for the WRONG reason (e.g. an unrelated field
            # makes the payload invalid), so require an adversarial confirmation before recording it.
            first_test = test_code
            conf, i2, o2 = await author_refute(model, cand, file, content, first_test, head_log, supplier_dir, stem)
            tin += i2; tout += o2
            if conf.get("test_code"):
                (REPO / tp).write_text(conf["test_code"])
                _rc2, head_log2 = run_test(tp)
                if classify(head_log2) == "FAIL":
                    notes.append("first test passed on head (likely did not exercise the claim); "
                                 "adversarial test FAILS on head -> claim plausible, continuing to fix")
                    test_code, head_log = conf["test_code"], head_log2
                    break
                clean_repo(head)
                return write_bundle(d, cand, pr, "not_a_bug", {"head": head_log, "head_refutation": head_log2},
                                    conf["test_code"], "", tp,
                                    {"notes": notes, "first_test": first_test[:6000],
                                     "demotion_review": "TWO independent tests pass on the unmodified code ("
                                                        f"adversarial attempt: {str(conf.get('exercises_claim'))[:200]})",
                                     "claim_refuted": conf.get("claim_refuted"),
                                     "refutation_evidence": conf.get("refutation_evidence"),
                                     "model_tokens": {"in": tin, "out": tout}})
            clean_repo(head)
            return write_bundle(d, cand, pr, "not_a_bug_unconfirmed", {"head": head_log}, first_test, "", tp,
                                {"notes": notes, "first_test": first_test[:6000],
                                 "demotion_review": "test passed on unmodified head but the adversarial confirmation could not be produced",
                                 "model_tokens": {"in": tin, "out": tout}})
        if not ran(head_log) and attempt < k_retry:
            notes.append(f"test attempt {attempt}: vitest did not execute (env); retried")
            diff = (diff or "") + "\n\nLAST RUN ERROR (the harness could not run the test):\n" + head_log[-1200:]
            continue
        if re.search(r"Failed to load|Cannot find module|Transform failed|SyntaxError", head_log) and attempt < k_retry:
            notes.append(f"test attempt {attempt}: did not load/compile; retried")
            diff = (diff or "") + "\n\nLAST TEST RUN ERROR (fix the test):\n" + head_log[-1500:]
            continue
        break
    else:
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {}, test_code or "", "", tp,
                            {"notes": notes, "blocker": notes[-1] if notes else "test authoring failed",
                             "env_patches": env_patches, "model_tokens": {"in": tin, "out": tout}})
    if not ran(head_log) or classify(head_log) != "FAIL":
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {"head": head_log}, test_code or "", "", tp,
                            {"notes": notes,
                             "blocker": "head run did not produce a genuine assertion failure (test never executed or could not load)",
                             "env_patches": env_patches, "model_tokens": {"in": tin, "out": tout}})

    # ---- 2. author the minimal fix as exact-match edits
    fixed = False
    for attempt in range(1, k_fix + 1):
        fx, i2, o2 = await author_fix(model, cand, file, content, test_code, head_log, original)
        tin += i2; tout += o2
        edits = fx.get("fix_edits")
        if not edits:
            notes.append(f"fix attempt {attempt}: no fix_edits returned")
            continue
        target = fx.get("fix_file_path") or file     # the defect may live in another module
        if not (REPO / target).exists():
            notes.append(f"fix attempt {attempt}: fix_file_path {target!r} does not exist")
            target = file
        sh("git checkout -q -- .")                      # reset source; keep the (untracked) test
        try:
            apply_edits(target, edits)
        except Exception as e:
            notes.append(f"fix attempt {attempt}: edits rejected for {target}: {e}")
            continue
        _rc, fixed_log = run_test(tp)
        _rc2, fix_diff = sh(f"git diff -- {target}")
        if classify(fixed_log) == "PASS":
            fixed = True
            break
        if not ran(fixed_log):
            notes.append(f"fix attempt {attempt}: vitest did not execute (env); retried")
            continue
        notes.append(f"fix attempt {attempt}: test still failing after fix; retried")
    if not fixed:
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {"head": head_log, "fixed": fixed_log},
                            test_code or "", fix_diff, tp,
                            {"notes": notes, "blocker": notes[-1] if notes else "fix authoring failed",
                             "model_tokens": {"in": tin, "out": tout}})

    # ---- 3. base comparison
    sh(f"git checkout -q -f {base}")          # untracked test file survives
    _rc3, base_log = run_test(tp)             # re-applies env prep for the base revision
    bc = classify(base_log)
    if not ran(base_log) and bc != "N/A_module_absent":
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {"base": base_log, "head": head_log, "fixed": fixed_log},
                            test_code, fix_diff, tp,
                            {"notes": notes, "blocker": "base run did not execute (no vitest summary line)",
                             "model_tokens": {"in": tin, "out": tout}})
    verdict = ("behavior_change_not_regression" if bc == "N/A_module_absent"
               else "confirmed_regression" if bc == "PASS"
               else "defect_present_before_pr")
    clean_repo(head)
    return write_bundle(d, cand, pr, verdict, {"base": base_log, "head": head_log, "fixed": fixed_log},
                        test_code, fix_diff, tp,
                        {"notes": notes, "model_tokens": {"in": tin, "out": tout}})


async def main():
    global REPO, AUTHOR_MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", default="11059")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", type=int, default=None)
    ap.add_argument("--model", default=AUTHOR_MODEL)
    ap.add_argument("--repo", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    AUTHOR_MODEL = a.model
    if a.repo:
        REPO = Path(a.repo)
    print(f"repo={REPO}", flush=True)
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
