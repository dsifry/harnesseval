#!/usr/bin/env python3
"""Score the current adjudicator against the FROZEN flip regression set (§3C.5).

Any change to V2_PROMPT / TIEBREAK_PROMPT / the voting or clustering machinery MUST be
scored against tests/fixtures/flip_pairs.json before it lands. Two hard gates:

  1. Determinism: identical normalized text receives exactly ONE verdict (the .env.example
     openssl case — identical wording, `bug` in one run, `true_hallucination` in another —
     is the canonical violation this gate exists to catch).
  2. Prompt contract: the grounded-hallucination rules are present (a hallucination verdict
     requires a cited contradiction; "cannot verify" routes to low-confidence bug; hedged
     wording is not evidence of falsity).

Direction report (not a gate — it is the yield measurement): of the 116 flips labeled
expected=bug, how many now adjudicate `bug`, how many stay `important_non_bug`, how many
still land `hallucination`, how many unresolved.

Usage:
  .venv/bin/python tools/score_flips.py [--judge gpt-5.2] [--concurrency 10] [--k 3] [--limit N]
Exit: 0 when the hard gates hold, 1 otherwise.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import readjudicate3 as rj  # noqa: E402
from harnesseval.dataset.pr_diff import fetch_diff  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixtures/flip_pairs.json"


def prompt_contract_holds() -> list[str]:
    problems = []
    if "CONTRADICTS the finding" not in rj.V2_PROMPT:
        problems.append("V2_PROMPT lost the cited-contradiction requirement")
    if 'return "bug" with confidence < 0.5' not in rj.V2_PROMPT:
        problems.append("V2_PROMPT lost the cannot-verify -> low-confidence bug routing")
    if "NOT evidence of falsity" not in rj.V2_PROMPT:
        problems.append("V2_PROMPT lost the hedged-wording rule")
    if "must quote the specific diff line" not in rj.TIEBREAK_PROMPT:
        problems.append("TIEBREAK_PROMPT lost the ground rules")
    return problems


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="gpt-5.2")
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    problems = prompt_contract_holds()
    if problems:
        print("PROMPT CONTRACT VIOLATIONS:")
        for p in problems:
            print("  -", p)
        return 1

    fixture = json.load(open(FIXTURE))
    flips = fixture["flips"]
    if args.limit:
        flips = flips[:args.limit]

    # collect every text needing adjudication, keyed by (url, normalized text)
    by_url: dict[str, list[str]] = {}
    for f in flips:
        by_url.setdefault(f["url"], []).append(f["issue_text"])
    for g in fixture.get("stability_groups", []):
        for m in g["members"]:
            by_url.setdefault(g["url"], []).append(m["issue_text"])

    sem = asyncio.Semaphore(args.concurrency)
    verdict_by_norm: dict[tuple[str, str], dict] = {}
    n_calls = 0
    for url, texts in sorted(by_url.items()):
        diff = fetch_diff(url)["diff"]
        cids = rj.cluster_texts(texts)
        rep_idx: dict[int, int] = {}
        for i, cid in enumerate(cids):
            rep_idx.setdefault(cid, i)
        results: dict[int, dict] = {}

        async def do_cluster(cid: int, i: int):
            results[cid] = await rj.adjudicate(texts[i], diff, args.judge, sem, k=args.k)

        await asyncio.gather(*[do_cluster(cid, i) for cid, i in rep_idx.items()])
        n_calls += len(rep_idx)
        for t, cid in zip(texts, cids):
            verdict_by_norm[(url, rj.normalize_for_cluster(t))] = results[cid]

    # HARD GATE 1: identical normalized text -> exactly one verdict (checked on OUTPUT)
    gate1_ok = True
    per_flip_verdicts = {}
    for f in flips:
        key = (f["url"], rj.normalize_for_cluster(f["issue_text"]))
        per_flip_verdicts[f["ce_key"] + f"|{f['mrv_dir']}#{f['m_idx']}"] = verdict_by_norm[key]

    # direction report
    dist = Counter(v["verdict"] for v in per_flip_verdicts.values())
    n = len(per_flip_verdicts)
    print(f"flip regression: {n} flips scored with {n_calls} cluster adjudications "
          f"(k={args.k}, judge={args.judge})")
    print(f"  now bug:               {dist.get('bug', 0)}")
    print(f"  now important_non_bug: {dist.get('important_non_bug', 0)}")
    print(f"  still hallucination:   {dist.get('hallucination', 0)}")
    print(f"  unresolved:            {dist.get('unresolved', 0)}")
    for k, v in per_flip_verdicts.items():
        if v["verdict"] == "hallucination":
            print(f"  [still-hallucination] {k}: {v['rationale'][:160]}")
    if not gate1_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
