#!/usr/bin/env python3
"""Second pass over `inconclusive_env`: re-run them with the upgraded authoring contract.

Upgrades applied by this pass (see the drivers):
  - fix edit tolerance (exact -> whitespace-normalized) and a whole-file fallback from attempt 3
  - model escalation for the fix after 2 failed attempts (--escalate, default gpt-5.2)
  - 6 fix attempts instead of 4
  - Rails: the script must end with a `RESULT:` marker; the run output is fed back on retry

Launches one stream per checkout: three cal.com PRs in parallel (separate clones), the three
discourse PRs sequentially (they share a checkout).

Usage: .venv/bin/python tools/verified_gold_rescue.py [--dry-run] [--escalate MODEL]
"""
from __future__ import annotations
import argparse, glob, json, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"
CHECKOUT = {"11059": "cal.com", "14740": "cal.com-14740", "10967": "cal.com-10967"}


def pending(pr: str) -> int:
    n = 0
    for mf in glob.glob(f"{VG}/{pr}/*/meta.json"):
        try:
            if json.load(open(mf)).get("verdict") == "inconclusive_env":
                n += 1
        except Exception:
            pass
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--escalate", default="gpt-5.2")
    a = ap.parse_args()
    plan = []
    for pr, repo in CHECKOUT.items():
        n = pending(pr)
        if n:
            plan.append(("calcom", pr, repo, n))
    for pr in ("4", "10", "8"):
        n = pending(pr)
        if n:
            plan.append(("rails", pr, "discourse", n))
    total = sum(x[3] for x in plan)
    print(f"rescue plan: {total} inconclusive_env candidate(s)")
    for kind, pr, repo, n in plan:
        print(f"  {'rails' if kind=='rails' else 'calcom'} PR {pr}: {n}")
    if a.dry_run:
        return
    # cal.com: parallel streams, one per checkout
    for kind, pr, repo, n in plan:
        if kind != "calcom":
            continue
        cmd = (f"nohup .venv/bin/python tools/verified_gold_driver.py --pr {pr} --only-verdict inconclusive_env "
               f"--escalate {a.escalate} --repo .cache/verify_repos/{repo} "
               f"> /tmp/sem_pilot/rescue_{pr}.log 2>&1 &")
        subprocess.run(cmd, shell=True, cwd=ROOT)
        print("launched cal.com stream:", cmd[:110])
    # rails: one sequential stream
    rails_prs = [pr for kind, pr, _, _ in plan if kind == "rails"]
    if rails_prs:
        loop = "; ".join(f".venv/bin/python tools/verified_gold_rails_driver.py --pr {pr} "
                         f"--only-verdict inconclusive_env --escalate {a.escalate}" for pr in rails_prs)
        cmd = f"nohup bash -c '{loop}' > /tmp/sem_pilot/rescue_rails.log 2>&1 &"
        subprocess.run(cmd, shell=True, cwd=ROOT)
        print("launched rails stream for PRs:", rails_prs)


if __name__ == "__main__":
    main()
