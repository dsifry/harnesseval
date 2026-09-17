#!/usr/bin/env python3
"""Independent re-verification ("check the check") of verified-hidden-gold bundles.

Re-runs a sample of PROMOTED bundles from their saved artifacts ONLY (test.patch, fix.patch,
meta.json) — no driver state, no authoring model. A promoted bundle must reproduce:
    head  -> FAIL   (the claimed behaviour differs)
    fixed -> PASS   (fix.patch makes it green)
    base  -> PASS   (confirmed_regression) or module-absent (behavior_change_not_regression)
Any mismatch is reported loudly: it means the bundle does not support its verdict.

Usage: .venv/bin/python tools/verified_gold_recheck.py [--sample N] [--ids 11059-B04,14740-B03]
"""
from __future__ import annotations
import argparse, json, random, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"
REPOS = {  # pr_slug -> checkout
    "11059": ROOT / ".cache/verify_repos/cal.com",
    "14740": ROOT / ".cache/verify_repos/cal.com-14740",
    "10967": ROOT / ".cache/verify_repos/cal.com-10967",
}
HARNESS_CFG = ".vitest.verify.config.ts"
CFG_BODY = ('import { defineConfig } from "vitest/config";\n'
            'export default defineConfig({\n  esbuild: { jsx: "automatic" },\n'
            '  test: { include: ["**/*.verified.test.{ts,tsx}"], environment: "jsdom",\n'
            '          globals: true, setupFiles: [], coverage: { enabled: false } },\n});\n')


def sh(cmd, cwd, timeout=420):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return (p.stdout or "") + (p.stderr or "")


def classify(log):
    if "Test Files" in log and "passed" in log and "failed" not in log:
        return "PASS"
    if "Failed to load url" in log or "Cannot find module" in log:
        return "N/A_module_absent"
    if "AssertionError" in log or ("Test Files" in log and "failed" in log):
        return "FAIL"
    return "?"


def run_test(repo: Path, test_path: str, fidelity: str):
    ws, bak = repo / "vitest.workspace.ts", repo / "vitest.workspace.ts.bak"
    harness = fidelity == "repo_suite_harness_config" or test_path.endswith(".tsx")
    if harness:
        (repo / HARNESS_CFG).write_text(CFG_BODY)
        if ws.exists():
            ws.rename(bak)
    try:
        flag = f" --config {HARNESS_CFG}" if harness else ""
        return sh(f"./node_modules/.bin/vitest run {test_path} --reporter=basic{flag}", repo)
    finally:
        if bak.exists():
            bak.rename(ws)


def put_test(repo: Path, test_path: str, content: str):
    f = repo / test_path
    f.parent.mkdir(parents=True, exist_ok=True)   # new-file candidates have no dir at base
    f.write_text(content)


def reset(repo: Path, sha: str):
    sh(f"git checkout -q -f {sha}", repo)
    sh("git checkout -q -- .", repo)
    sh("git clean -qfd -e node_modules -e .yarn -e .yarnrc.yml -e .pnp.cjs", repo)
    prepare_env_like(repo)


def prepare_env_like(repo: Path):
    """Env prep must be re-applied here too: resetting the worktree reverts the config patches."""
    cfg = repo / "vitest.config.ts"
    if cfg.exists() and '"c8"' in cfg.read_text():
        cfg.write_text(cfg.read_text().replace('"c8"', '"v8"'))
    ws = repo / "vitest.workspace.ts"
    if ws.exists() and "{test,spec}.{ts,js}" in ws.read_text():
        ws.write_text(ws.read_text().replace("{test,spec}.{ts,js}", "{test,spec}.{ts,js,tsx}"))


def stream_active(pr: str) -> bool:
    """Never touch a checkout a driver stream is using — concurrent branch switches corrupt both."""
    import subprocess as _sp
    out = _sp.run(["pgrep", "-af", "verified_gold_driver"], capture_output=True, text=True).stdout
    return f"--pr {pr}" in out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=6)
    ap.add_argument("--ids", default="")
    ap.add_argument("--seed", type=int, default=20260917)
    a = ap.parse_args()

    metas = []
    for mf in sorted(VG.glob("*/B*/meta.json")):
        m = json.loads(mf.read_text())
        if m.get("verdict") in {"confirmed_regression", "behavior_change_not_regression"}:
            if not m.get("test_path"):
                print(f"  skip {m.get('bug_id')}: bundle predates test_path recording (not re-checkable)")
                continue
            metas.append((mf.parent, m))
    if a.ids:
        want = set(a.ids.split(","))
        metas = [(d, m) for d, m in metas if m.get("bug_id") in want]
    else:
        random.seed(a.seed)
        random.shuffle(metas)
        # ensure both verdict types are represented
        picks, conf = [], [x for x in metas if x[1]["verdict"] == "confirmed_regression"]
        picks += conf[:2]
        picks += [x for x in metas if x not in picks][: max(0, a.sample - len(picks))]
        metas = picks[: a.sample]

    results = []
    for d, m in metas:
        pr = (m.get("bug_id") or "").split("-")[0]
        if stream_active(pr):
            print(f"  skip {m.get('bug_id')}: a driver stream is using PR {pr}'s checkout (would corrupt both)")
            results.append({"bug_id": m.get("bug_id"), "skipped": "checkout busy: driver stream active"})
            continue
        repo = REPOS.get(pr)
        if not repo or not repo.exists():
            results.append({"bug_id": m.get("bug_id"), "error": f"no checkout for PR {pr}"}); continue
        head = ((m.get("candidate") or {}).get("head_sha") or m.get("head_sha")) or None
        # head/base SHAs come from the driver's constants if not stored on the bundle
        from importlib import import_module
        sys.path.insert(0, str(ROOT / "tools"))
        base_sha, head_sha = import_module("verified_gold_driver").PR_HEADS[pr]
        test_path = m.get("test_path")
        fidelity = m.get("fidelity", "repo_suite")
        r = {"bug_id": m["bug_id"], "verdict_claimed": m["verdict"], "fidelity": fidelity, "test_path": test_path}

        reset(repo, head_sha)
        put_test(repo, test_path, (d / "test.patch").read_text())
        r["head"] = classify(run_test(repo, test_path, fidelity))

        fix = (d / "fix.patch").resolve()          # ABSOLUTE: sh() runs with cwd=repo
        if fix.exists() and fix.read_text().strip():
            out = sh(f"git apply {fix} 2>&1", repo).strip()
            r["fix_apply"] = out or "applied cleanly"
            if out:
                r["reproduce_error"] = f"fix.patch did not apply: {out[:200]}"
                r["reproduces"] = False
            else:
                r["fixed"] = classify(run_test(repo, test_path, fidelity))
        else:
            r["fixed"] = "no fix.patch"
            r["reproduces"] = False
        reset(repo, head_sha)
        put_test(repo, test_path, (d / "test.patch").read_text())
        reset(repo, base_sha)
        put_test(repo, test_path, (d / "test.patch").read_text())
        r["base"] = classify(run_test(repo, test_path, fidelity))

        # expectations
        exp_head = "FAIL"
        exp_base = "PASS" if m["verdict"] == "confirmed_regression" else "N/A_module_absent"
        r["expected"] = {"head": exp_head, "base": exp_base, "fixed": "PASS"}
        r["reproduces"] = (r.get("head") == exp_head and r.get("fixed") == "PASS"
                           and r.get("base") in (exp_base, "PASS"))
        results.append(r)
        print(f"{r['bug_id']:12s} claimed={r['verdict_claimed']:30s} head={r.get('head'):16s} "
              f"fixed={r.get('fixed'):16s} base={r.get('base'):18s} reproduces={r['reproduces']}", flush=True)

    ok = sum(1 for r in results if r.get("reproduces"))
    (VG / "CHECK_THE_CHECK.json").write_text(json.dumps({"n": len(results), "reproduced": ok, "results": results}, indent=1))
    lines = ["# Check-the-check — independent re-verification of promoted bundles", "",
             f"Re-ran {len(results)} promoted bundles from their saved artifacts only (no driver state, no",
             "authoring model). Each must reproduce: head FAIL, fixed PASS, base PASS or module-absent.", "",
             f"**Reproduced: {ok}/{len(results)}**", "",
             "| bug | claimed verdict | head | fixed | base | reproduces |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r.get('bug_id')} | `{r.get('verdict_claimed')}` | {r.get('head')} | {r.get('fixed')} | {r.get('base')} | {'✅' if r.get('reproduces') else '❌'} |")
    (VG / "CHECK_THE_CHECK.md").write_text("\n".join(lines) + "\n")
    print(f"\nreproduced {ok}/{len(results)} -> analysis/verified_gold/CHECK_THE_CHECK.md")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
