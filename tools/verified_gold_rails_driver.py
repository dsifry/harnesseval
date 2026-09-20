#!/usr/bin/env python3
"""Rails half of the verified-hidden-gold campaign — `standalone_real_code` fidelity.

The 2013-2015 discourse-graphite PRs cannot run their own suite (Rails 4.2 from a git ref, no
.ruby-version, native gems). This driver instead executes the REAL post-PR file with stubbed
collaborators:

  test  = a standalone Ruby script that
            (a) defines minimal stubs for the collaborators the code touches,
            (b) loads the REAL file under test (relative path, never stubbed),
            (c) prints a single marker line `RESULT: PASS` or `RESULT: FAIL: <why>`
  run   = `ruby -I<repo-root> <test>` in the checkout at the PR's head commit
  three-way: head -> base -> head+minimal fix, exactly as the cal.com driver

Verdicts/bundles are identical to the cal.com driver (see analysis/verified_gold/README.md), with
`fidelity: standalone_real_code` recorded in every meta.json.

Usage:
  .venv/bin/python tools/verified_gold_rails_driver.py --pr 4 --limit 2
  .venv/bin/python tools/verified_gold_rails_driver.py --build-manifest
"""
from __future__ import annotations
import argparse, glob, hashlib, json, os, re, shutil, subprocess, sys, time, asyncio
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402

REPO = ROOT / ".cache/verify_repos/discourse"
BUNDLE_ROOT = ROOT / "analysis/verified_gold"
MANIFEST = BUNDLE_ROOT / "_work/rails_candidates.json"
PR_HEADS = {  # pr_slug -> (base, head)
    "4": ("62db063e1e1abe691313ab42682a68f796d63769", "4f8aed295a29954023b2849c060ef4fb299d1b5d"),
    "10": ("913c3d6f636d02b3dd6c2c022ca1af2bec95d752", "d1c69189f3c90ecf56013a8da904da9bff9a8e19"),
    "8": ("4975fc28903a84418f546b2809370f19abf10e08", "060cda77729cb1c4a827560e09e89a7b22078ba9"),
}
AUTHOR_MODEL = "deepseek-4.1-flash-background"       # LunarRoute; validity of the output is what matters
SYSTEM = "You are a senior Ruby engineer writing executable regression evidence. Respond with ONLY valid JSON."

TEST_PROMPT = """A code-review campaign claims the following defect in a 2015-era Rails codebase. Write a STANDALONE
Ruby test that demonstrates the claimed behaviour on the REAL file — no Rails app, no database.

CLAIM
  file: {file} (line ~{line})
  title: {title}
  reports (deduplicated):
{reports}

CURRENT POST-PR SOURCE of {file}:
```ruby
{content}
```

REQUIREMENTS
- The script must `require` the REAL file with a relative path; never redefine the class under test.
- Define the minimum stubs needed for it to load and run (e.g. a fake ActiveRecord::Base with the
  class macros used, I18n, Digest) and let the code under test be the only real logic exercised.
- Assert observable behaviour (returned values, raised exceptions, side effects).
- Print EXACTLY one final marker line: `RESULT: PASS` when the claimed defect is absent (i.e. the code
  behaves correctly) and `RESULT: FAIL: <reason>` when the claimed defect is present.
- Keep it under ~120 lines. It will be run as: `ruby -I. <this file>` from the repo root.

Respond with ONLY this JSON object (no prose, no fences):
{{"test_path": "spec/verify/{stem}_verify.rb",
  "test_code": "<full ruby script>",
  "claim_restated": "<one sentence>",
  "expected_marker": "FAIL on the post-PR code",
  "confidence": 0.0-1.0}}"""

FIX_PROMPT = """A standalone Ruby test demonstrates the defect below and currently reports FAIL. Produce the
MINIMAL fix as exact-match edits to the real file.

CLAIM: {title}
FILE: {file}

TEST (must report PASS afterwards; do not modify it):
```ruby
{test_code}
```

CURRENT SOURCE (excerpt for large files):
```ruby
{content}
```

TEST OUTPUT:
```
{head_log}
```

CANDIDATE FILES THAT DEFINE THE IDENTIFIERS IN THE CLAIM (the defect may be in ANY of these —
name the right one in fix_file_path):
{symbol_files}

RULES
{shape}
- Minimal change: fix only what this defect requires.
- Return `fixed_file_content` with the COMPLETE corrected file instead of `fix_edits`, if asked to.

Respond with ONLY this JSON object (no prose, no fences):
{{"fix_file_path": "{file}",
  "fix_edits": [{{"find": "<verbatim excerpt>", "replace": "<corrected excerpt>"}}],
  "fixed_file_content": "<complete corrected file — only when asked>",
  "explanation": "<one sentence>"}}"""


MODEL_TIMEOUT = 240   # seconds; LunarRoute calls occasionally hang (observed 10+ min stalls)


async def call_model_json_bounded(*args, **kwargs):
    """call_model_json with a hard timeout: a hung call must not wedge a stream. On timeout the
    caller sees the same empty-result shape it already handles as a retryable authoring failure."""
    try:
        return await asyncio.wait_for(call_model_json(*args, **kwargs), timeout=MODEL_TIMEOUT)
    except asyncio.TimeoutError:
        return {}, 0, 0, {}


SYMBOL_STOP = {"should","would","could","because","when","with","from","this","that","have","been",
               "does","doesn","isn","aren","rather","instead","always","never","error","missing",
               "without","before","after","return","value","values","which","there","their","about"}

def defining_files(cand, limit=3):
    """Files under the checkout that DEFINE the identifiers named in the claim. The defect often lives
    in a callee (schema/helper) while the candidate resolved to the caller, which is the single largest
    cause of 'edits rejected' / 'fix did not converge'."""
    text = (str(cand.get("title")) + " " + " ".join((cand.get("reports") or [])[:6]))
    toks = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{5,}", text)
            if t.lower() not in SYMBOL_STOP]
    seen, terms = set(), []
    for t in toks:
        if t.lower() not in seen:
            seen.add(t.lower()); terms.append(t)
    hits = {}
    for term in terms[:6]:
        try:
            _rc, out = sh(f"grep -rl --include='*.rb' --exclude-dir=node_modules --exclude-dir=.git {term} . | head -12")
            for f in (out or "").splitlines():
                f = f.strip().lstrip("./")
                if f: hits[f] = hits.get(f, 0) + 1
        except Exception as e:                    # never fail silently: this is what fed the fix author
            print(f"  (defining_files: grep for {term!r} failed: {type(e).__name__} {e})", flush=True)
    ranked = sorted(hits.items(), key=lambda kv: -kv[1])[:limit]
    return [f for f, _ in ranked]


def sh(cmd, cwd=None, timeout=300):
    try:
        p = subprocess.run(cmd, cwd=str(cwd or REPO), shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or ""))
        return 124, f"TIMEOUT: command did not finish within {timeout}s\n{out}"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def clean_repo(head):
    sh(f"git checkout -q -f {head}")
    sh("git checkout -q -- .")
    sh("git clean -qfd")


def bundle_dir(pr, slug):
    d = BUNDLE_ROOT / pr / slug
    (d / "logs").mkdir(parents=True, exist_ok=True)
    return d


def classify(log):
    if re.search(r"^RESULT: PASS", log, re.M):
        return "PASS"
    if re.search(r"^RESULT: FAIL", log, re.M):
        return "FAIL"
    m = re.search(r"(NameError|LoadError|NoMethodError|SyntaxError|uninitialized constant)", log)
    return f"ERROR:{m.group(1)}" if m else "?"


def run_test(test_path):
    return sh(f"ruby -I. {test_path}", timeout=120)


async def author_test(model, cand, file, content, supplier_dir, stem):
    prompt = TEST_PROMPT.format(file=file, line=cand.get("line") or "?", title=cand.get("title") or "",
                                reports="\n".join(f"- {r}" for r in cand.get("reports", [])[:4]),
                                content=content[:12000], stem=stem)
    parsed, tin, tout, _ = await call_model_json_bounded(model, SYSTEM, prompt, effort="low", max_tokens=12000)
    return (parsed if isinstance(parsed, dict) else {}), tin, tout


async def author_fix(model, cand, file, content, test_code, head_log, full_file=False):
    defs = defining_files(cand)
    blocks = []
    for f in defs:
        try:
            blocks.append(f"--- {f} ---\n" + (REPO / f).read_text()[:4000])
        except Exception:
            pass
    symbol_files = "\n\n".join(blocks) or "(grep found no defining file)"
    shape = ('- Return `fixed_file_content` with the COMPLETE corrected file (exact-match edits have failed twice).'
             if full_file else
             '- Return ONLY exact-match edits: each `find` must be a verbatim excerpt of the CURRENT SOURCE and\n'
             '  must occur EXACTLY ONCE. Include enough context to be unique.')
    prompt = FIX_PROMPT.format(title=cand.get("title") or "", file=file, test_code=test_code[:5000],
                               content=content[:9000], head_log=head_log[-2000:],
                               symbol_files=symbol_files, shape=shape)
    parsed, tin, tout, _ = await call_model_json_bounded(model, SYSTEM, prompt, effort="low", max_tokens=8000)
    return (parsed if isinstance(parsed, dict) else {}), tin, tout


def _norm_ws(t: str) -> str:
    return "\n".join(ln.rstrip() for ln in t.strip("\n").splitlines())


def apply_edits(path, edits):
    """Exact match, then whitespace-normalized match; reject loudly if not uniquely locatable."""
    p = REPO / path
    s = p.read_text()
    for i, e in enumerate(edits):
        f, r = e.get("find"), e.get("replace")
        if not f or r is None:
            raise ValueError(f"edit {i}: missing find/replace")
        if s.count(f) == 1:
            s = s.replace(f, r); continue
        parts = _norm_ws(s).split(_norm_ws(f))
        if len(parts) == 2:
            s = parts[0] + _norm_ws(r) + parts[1]; continue
        raise ValueError(f"edit {i}: find not uniquely locatable (exact {s.count(f)}, normalized {len(parts)-1})")
    p.write_text(s)


def write_bundle(d, cand, pr, verdict, logs, test_code, fix_diff, test_path, extra=None):
    (d / "test.patch").write_text(test_code)
    if fix_diff:
        (d / "fix.patch").write_text(fix_diff)
    for k, v in logs.items():
        (d / "logs" / f"{k}.log").write_text(v)
    meta = {"bug_id": f"{pr}-B{cand['class_index']:02d}", "authoring_model": AUTHOR_MODEL,
            "candidate": cand, "pr": pr, "verdict": verdict, "fidelity": "standalone_real_code",
            "three_way": {k: classify(v) for k, v in logs.items()}, "test_path": test_path,
            "fix_scope": "minimal fix for the demonstrated instance only",
            "sibling_instances": {"note": "other instances of this class are unverified siblings"},
            "provenance": {"produced_by": "tools/verified_gold_rails_driver.py",
                           "spec": "analysis/verified_gold/README.md", "date": time.strftime("%Y-%m-%d")}}
    if extra:
        meta.update(extra)
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    (d / "REPRO.md").write_text(
        f"# REPRO — {cand.get('title')}\n\n**Verdict:** `{verdict}` · standalone_real_code (real file, stubbed collaborators)\n\n"
        f"```bash\ncd .cache/verify_repos/discourse && git checkout -f {PR_HEADS[pr][1]}\n"
        f"mkdir -p $(dirname {test_path}) && cp {d}/test.patch {test_path}\n"
        f"ruby -I. {test_path}        # expect: RESULT: FAIL on head\n"
        f"git apply {d}/fix.patch && ruby -I. {test_path}   # expect: RESULT: PASS\n```\n")
    return meta


async def do_candidate(cand, model, k_retry=3, k_fix=6, escalate=None):
    pr = cand["pr_slug"]; base, head = PR_HEADS[pr]
    clean_repo(head)
    file = cand.get("file_resolved") or ""
    if not file or sh(f"git cat-file -e {head}:{file}")[0] != 0:
        d = bundle_dir(pr, f"B{cand['class_index']:02d}-{cand['class_slug']}")
        (d / "meta.json").write_text(json.dumps({
            "bug_id": f"{pr}-B{cand['class_index']:02d}", "candidate": cand, "pr": pr,
            "verdict": "unresolved_file", "fidelity": "n/a",
            "blocker": f"could not pin the finding to a file changed by this PR ({cand.get('file')!r})",
            "provenance": {"produced_by": "tools/verified_gold_rails_driver.py"}}, indent=1))
        return {"verdict": "unresolved_file"}

    stem = Path(file).stem
    supplier_dir = str(Path(file).parent)
    d = bundle_dir(pr, f"B{cand['class_index']:02d}-{cand['class_slug']}")
    original = (REPO / file).read_text()
    content = original if len(original) <= 12000 else original[:12000]
    notes, tin, tout = [], 0, 0
    tp = f"spec/verify/{stem}_verify.rb"
    test_code, head_log, fixed_log, fix_diff = None, "", "", ""
    head_test_sha = None

    for attempt in range(1, k_retry + 1):
        parsed, i1, o1 = await author_test(model, cand, file, content, supplier_dir, stem)
        tin += i1; tout += o1
        tp = parsed.get("test_path") or tp
        if not parsed.get("test_code"):
            notes.append(f"test attempt {attempt}: incomplete JSON")
            continue
        test_code = parsed["test_code"]
        head_test_sha = hashlib.sha256(test_code.encode()).hexdigest()
        (REPO / tp).parent.mkdir(parents=True, exist_ok=True)
        (REPO / tp).write_text(test_code)
        _rc, head_log = run_test(tp)
        c = classify(head_log)
        if head_log.startswith("TIMEOUT") and attempt < k_retry:
            notes.append(f"test attempt {attempt}: the test hung (did not finish) — retried")
            content = (content if content.endswith("\n") else content + "\n") + (
                "\n\nLAST RUN HUNG (timeout). The test must not perform real I/O: mock network calls, the DB, "
                "and timers; assert on the mocked behaviour instead.")
            continue
        if c == "PASS":
            clean_repo(head)
            return write_bundle(d, cand, pr, "not_a_bug", {"head": head_log}, test_code, "", tp,
                                {"notes": notes, "demotion_review": "standalone test reports PASS on the unmodified post-PR code",
                                 "model_tokens": {"in": tin, "out": tout}})
        if (c.startswith("ERROR") or c == "?") and attempt < k_retry:
            notes.append(f"test attempt {attempt}: {c}; the script must print a RESULT: marker — retried")
            content = (original[:12000] +
                       "\n\nLAST RUN OUTPUT (the script must end with exactly one line 'RESULT: PASS' or "
                       "'RESULT: FAIL: <why>', and must not raise; fix the script/stubs, never the file under test):\n"
                       + head_log[-1500:])
            continue
        break
    else:
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {}, test_code or "", "", tp,
                            {"notes": notes, "blocker": notes[-1] if notes else "test authoring failed",
                             "model_tokens": {"in": tin, "out": tout}})
    if classify(head_log) != "FAIL":
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {"head": head_log}, test_code or "", "", tp,
                            {"notes": notes, "blocker": f"head run did not report the claimed defect ({classify(head_log)})",
                             "model_tokens": {"in": tin, "out": tout}})

    fixed = False
    fix_model = model
    for attempt in range(1, k_fix + 1):
        if escalate and attempt == 3:
            fix_model = escalate
            notes.append(f"fix attempt {attempt}: escalating fix authoring to {fix_model}")
        fx, i2, o2 = await author_fix(fix_model, cand, file, content, test_code, head_log, full_file=attempt >= 3)
        tin += i2; tout += o2
        edits = fx.get("fix_edits")
        target = fx.get("fix_file_path") or file
        if not edits and not fx.get("fixed_file_content"):
            notes.append(f"fix attempt {attempt}: no fix returned")
            continue
        if not (REPO / target).exists():
            target = file
        sh("git checkout -q -- .")
        try:
            if fx.get("fixed_file_content"):
                (REPO / target).write_text(fx["fixed_file_content"])
            else:
                apply_edits(target, edits)
        except Exception as e:
            notes.append(f"fix attempt {attempt}: edits rejected for {target}: {e}")
            continue
        _rc, fixed_log = run_test(tp)
        _rc2, fix_diff = sh(f"git diff -- {target}")
        if classify(fixed_log) == "PASS":
            fixed = True
            break
        notes.append(f"fix attempt {attempt}: test still reports FAIL after the fix; retried")
    if not fixed:
        clean_repo(head)
        return write_bundle(d, cand, pr, "inconclusive_env", {"head": head_log, "fixed": fixed_log},
                            test_code or "", fix_diff, tp,
                            {"notes": notes, "blocker": notes[-1] if notes else "fix authoring failed",
                             "model_tokens": {"in": tin, "out": tout}})

    sh(f"git checkout -q -f {base}")
    base_test_sha = hashlib.sha256(test_code.encode()).hexdigest()
    _rc3, base_log = run_test(tp)
    bc = classify(base_log)
    verdict = ("behavior_change_not_regression" if bc.startswith("ERROR")
               else "confirmed_regression" if bc == "PASS"
               else "defect_present_before_pr")
    clean_repo(head)
    return write_bundle(d, cand, pr, verdict, {"base": base_log, "head": head_log, "fixed": fixed_log},
                        test_code, fix_diff, tp,
                        {"notes": notes, "test_sha": {"head": head_test_sha, "base": base_test_sha},
                         "model_tokens": {"in": tin, "out": tout}})


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", default="4"); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", type=int, default=None); ap.add_argument("--model", default=AUTHOR_MODEL)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--escalate", default=None, help="stronger model to use for the fix after 2 failed attempts")
    ap.add_argument("--only-verdict", default=None, help="re-run only candidates whose existing bundle has this verdict")
    a = ap.parse_args()
    cands = [c for c in json.load(open(MANIFEST)) if c["pr_slug"] == a.pr]
    if a.only is not None:
        cands = [c for c in cands if c["class_index"] == a.only]
    if a.limit:
        cands = cands[:a.limit]
    if a.only_verdict:
        import glob as _g
        keep_idx = set()
        for mf in _g.glob(f'{BUNDLE_ROOT}/{a.pr}/*/meta.json'):
            try:
                mm = json.load(open(mf))
            except Exception:
                continue
            if mm.get("verdict") == a.only_verdict:
                bid = mm.get("bug_id") or ""
                if "B" in bid:
                    keep_idx.add(int(bid.split("B")[1]))
        cands = [c for c in cands if c["class_index"] in keep_idx]
        print(f"selected {len(cands)} candidate(s) with verdict {a.only_verdict}", flush=True)
    elif not a.force:
        cands = [c for c in cands if not (BUNDLE_ROOT / c["pr_slug"] / f"B{c['class_index']:02d}-{c['class_slug']}" / "meta.json").exists()]
    print(f"repo={REPO} pr={a.pr} candidates={len(cands)}", flush=True)
    index = []
    for i, c in enumerate(cands, 1):
        t0 = time.time()
        try:
            m = await do_candidate(c, a.model, escalate=a.escalate)
            status = (m or {}).get("verdict", "skipped")
        except Exception as e:
            status = f"error: {type(e).__name__}: {e}"
        print(f"[{i}/{len(cands)}] {c['pr_slug']}#{c['class_index']} {c['class_slug'][:44]:46s} {status} ({time.time()-t0:.0f}s)", flush=True)
        index.append({"pr": c["pr_slug"], "class_index": c["class_index"], "slug": c["class_slug"], "verdict": status})
        json.dump(index, open(BUNDLE_ROOT / f"_work/progress_rails_{a.pr}.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
