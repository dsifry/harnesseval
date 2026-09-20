#!/usr/bin/env python3
"""Strict re-check of the golden-overlap judgments (the verify pass over-matched).

The first-pass overlap judge was generous: 11 goldens were matched by >1 merged cluster, and
18/49 overlaps sat at confidence <= 0.7. This tool re-asks each flagged pair adversarially
("the SAME defect, not merely the same file/area/feature"), then resolves goldens matched by
several candidates (at most one candidate can be the same defect as a single golden).

Outputs per PR: analysis/semantic_overlap_strict_<pr>.json with, per merged cluster:
  strict_golden: int|null   (the golden it is the same defect as, after strict review)
and locked stats: n_merged, n_overlap_strict, n_verified_additional_strict.
Plus analysis/semantic_overlap_strict_summary.json.

Usage: .venv/bin/python tools/semantic_overlap_strict.py [--pr URL | --all]
"""
from __future__ import annotations
import argparse, asyncio, glob, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json

SYSTEM = "You are a strict code-review evaluation auditor. Always respond with valid JSON."

STRICT = """Are these two code-review findings THE SAME underlying defect?

GOLDEN (human-verified expected finding):
{golden}

CANDIDATE (clustered automated findings, all one claimed defect):
{cand}

Answer strictly:
- "same" requires the SAME root cause in the SAME code path — the same defect.
- The same file, function, feature area, or a related-but-distinct defect is NOT the same.
- A candidate that is broader or narrower than the golden (e.g. covers several defects incl. the
  golden's) is NOT the same defect.

Respond with ONLY JSON:
{{"same": true|false, "confidence": 0.0-1.0, "reason": "one sentence"}}"""

MULTI = """A single human-verified GOLDEN finding is below, together with several CANDIDATE defects that
were each independently flagged as possibly the same as that golden. At most ONE candidate can be the
same defect as the golden (the golden is one bug).

GOLDEN:
{golden}

CANDIDATES (numbered):
{cands}

Choose the single candidate that is the SAME underlying defect as the golden, or null if none is.
Also list any candidate pairs that are the same defect as EACH OTHER.

Respond with ONLY JSON:
{{"golden_match_index": <int or null>, "confidence": 0.0-1.0, "reason": "one sentence",
 "same_as_each_other": [[i, j], ...]}}"""


def goldens_for(pr):
    for f in (glob.glob(f"{ROOT}/analysis/inputs/golden_comments/*.json")
              or glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json")):
        for e in json.load(open(f)):
            if e["url"] == pr:
                return [c["comment"] for c in e["comments"]]
    return []


async def run(pr, judge):
    slug = pr.rstrip("/").split("/")[-1]
    v = json.load(open(ROOT / f"analysis/semantic_true_golden_verify_{slug}.json"))
    goldens = goldens_for(pr)
    calls = {"n": 0}
    sem = asyncio.Semaphore(8)

    async def llm(prompt):
        async with sem:
            parsed, _, _, _ = await call_model_json(judge, SYSTEM, prompt, effort="medium", max_tokens=800)
        calls["n"] += 1
        return parsed if isinstance(parsed, dict) else {}

    flagged = [i for i, c in enumerate(v["clusters"]) if c["golden_index"] is not None]
    async def strict(i):
        c = v["clusters"][i]
        p = await llm(STRICT.format(golden=goldens[c["golden_index"]][:1200], cand=c["example"][:900]))
        return i, {"same": bool(p.get("same")), "confidence": p.get("confidence"), "reason": p.get("reason")}
    res = dict(await asyncio.gather(*[strict(i) for i in flagged]))

    # multi-match resolution: for each golden still claimed by >1 strictly-confirmed cluster
    by_golden = defaultdict(list)
    for i in flagged:
        if res[i]["same"]:
            by_golden[v["clusters"][i]["golden_index"]].append(i)
    for g, idxs in by_golden.items():
        if len(idxs) < 2:
            continue
        cands = "\n".join(f"{j}. {v['clusters'][i]['example'][:500]}" for j, i in enumerate(idxs))
        p = await llm(MULTI.format(golden=goldens[g][:1000], cands=cands))
        keep = p.get("golden_match_index")
        keep = int(keep) if keep is not None and str(keep).isdigit() and int(keep) < len(idxs) else None
        for j, i in enumerate(idxs):
            if keep is not None and j != keep:
                res[i]["same"] = False
                res[i]["reason"] = f"(multi-match resolution: golden #{g} assigned to another cluster) " + str(res[i].get("reason"))
        res[idxs[keep]]["reason"] = f"(multi-match winner for golden #{g}) " + str(res[idxs[keep]].get("reason")) if keep is not None else res[idxs[keep]].get("reason")

    out = []
    for i, c in enumerate(v["clusters"]):
        r = res.get(i) or {"same": False, "confidence": None, "reason": None}
        out.append({"cluster": i, "n_findings": c["n_findings"], "n_cells": c["n_cells"],
                    "strict_golden": c["golden_index"] if r["same"] else None,
                    "first_pass_golden": c["golden_index"],
                    "confidence": r.get("confidence"), "reason": r.get("reason"),
                    "example": c["example"][:200], "found_by": c["found_by"]})
    n_over = sum(1 for c in out if c["strict_golden"] is not None)
    stats = {"n_merged": v["stats"]["n_merged"], "n_overlap_first_pass": v["stats"]["n_golden_overlap"],
             "n_overlap_strict": n_over, "n_verified_additional_strict": v["stats"]["n_merged"] - n_over,
             "n_goldens": len(goldens)}
    print(f"PR {slug}: merged {stats['n_merged']}, overlap first-pass {stats['n_overlap_first_pass']} -> strict {n_over}, "
          f"verified additional {stats['n_verified_additional_strict']} ({calls['n']} calls)")
    json.dump({"pr": pr, "judge_model": judge, "stats": stats, "clusters": out},
              open(ROOT / f"analysis/semantic_overlap_strict_{slug}.json", "w"), indent=1)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr"); ap.add_argument("--all", action="store_true"); ap.add_argument("--judge", default="gpt-5.2")
    a = ap.parse_args()
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    top6 = sorted(D["pr_golden"], key=lambda u: (-D["pr_golden"][u]["sev_weight"], -D["pr_golden"][u]["n_comments"]))[:6]
    prs = [a.pr] if a.pr else (top6 if a.all else [])
    assert prs, "pass --pr or --all"
    t0 = time.time()
    tot = {}
    for pr in prs:
        await run(pr, a.judge)
        slug = pr.rstrip("/").split("/")[-1]
        tot[slug] = json.load(open(ROOT / f"analysis/semantic_overlap_strict_{slug}.json"))["stats"]
    T = {"n_merged": sum(v["n_merged"] for v in tot.values()),
         "n_overlap_strict": sum(v["n_overlap_strict"] for v in tot.values()),
         "n_verified_additional_strict": sum(v["n_verified_additional_strict"] for v in tot.values())}
    json.dump({"per_pr": tot, "total": T}, open(ROOT / "analysis/semantic_overlap_strict_summary.json", "w"), indent=1)
    print("TOTAL:", json.dumps(T, indent=1), f"| wall {time.time()-t0:.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
