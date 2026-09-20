#!/usr/bin/env python3
"""Lock the golden-overlap set: tie-break the low-confidence finding-level overlaps.

The finding-level pass (258 clusters) flagged 60 overlaps; 46 sat at confidence >= 0.8 and 14
at <= 0.7 (mixed quality). This tool re-judges ONLY the low-confidence cases, with the specific
finding text against the specific golden, strictly ("same root cause, same code path; adjacent
is not the same"). Output locks a status per cluster: overlap (a golden) vs verified-additional.

Writes analysis/semantic_overlap_locked_<pr>.json (+ _summary.json):
  clusters: [{locked_match, locked_golden, tie_break, confidence, reason, ...}]
  stats:    {n_merged, n_locked_overlap, n_locked_additional}

Usage: .venv/bin/python tools/semantic_overlap_lock.py [--pr URL | --all] [--conf 0.8]
"""
from __future__ import annotations
import argparse, asyncio, glob, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json

SYSTEM = "You are a strict code-review evaluation auditor. Always respond with valid JSON."
TIE = """Is the candidate finding the SAME underlying defect as the golden finding?

GOLDEN (human-verified):
{golden}

CANDIDATE finding:
{finding}

Answer strictly: "same" requires the same root cause in the same code path. A candidate that merely
touches the same file/function/feature, or describes an adjacent/broader/narrower defect, is NOT the
same. When genuinely unsure, answer false.

Respond with ONLY JSON:
{{"same": true|false, "confidence": 0.0-1.0, "reason": "one sentence"}}"""


def goldens_for(pr):
    for f in (glob.glob(f"{ROOT}/analysis/inputs/golden_comments/*.json")
              or glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json")):
        for e in json.load(open(f)):
            if e["url"] == pr:
                return [c["comment"] for c in e["comments"]]
    return []


async def run(pr, judge, conf_th):
    slug = pr.rstrip("/").split("/")[-1]
    find = json.load(open(ROOT / f"analysis/semantic_overlap_finding_{slug}.json"))
    v = json.load(open(ROOT / f"analysis/semantic_true_golden_verify_{slug}.json"))
    pil = json.load(open(ROOT / f"analysis/exp_union_semantic_pilot_{slug}.json"))
    f2c = {int(a): b for a, b in pil["finding_to_cluster"].items()}
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    runs = [r for r in D["all_healthy_runs"] if r["url"] == pr]
    flat = [t for r in runs for t in (r.get("bugtexts") or [])]
    mem = defaultdict(list)
    for i, t in enumerate(flat):
        c = f2c[i]
        if t not in mem[c]:
            mem[c].append(t)
    goldens = goldens_for(pr)

    def picks_for(gi, k=8):
        seen, picks = set(), []
        for r in v["clusters"][gi]["merge_group"]:
            for t in sorted(mem[r], key=len):
                key = t[:40].lower()
                if key in seen:
                    continue
                seen.add(key); picks.append(t)
                if len(picks) >= k:
                    break
            if len(picks) >= k:
                break
        return picks

    sem = asyncio.Semaphore(8)
    calls = {"n": 0}

    async def tie(cluster):
        gi = cluster["golden_index"]
        idx = cluster.get("finding_index")
        pick = None
        try:
            picks = picks_for(cluster.get("_gi", 0))
            if idx is not None and int(idx) < len(picks):
                pick = picks[int(idx)]
        except Exception:
            pick = None
        if pick is None:
            pick = cluster["example"]
        async with sem:
            p, _, _, _ = await call_model_json(judge, SYSTEM,
                TIE.format(golden=goldens[gi][:1000], finding=pick[:800]), effort="medium", max_tokens=600)
        calls["n"] += 1
        p = p if isinstance(p, dict) else {}
        return {"same": bool(p.get("same")), "confidence": p.get("confidence"), "reason": p.get("reason"), "judged_finding": pick[:300]}

    todo = []
    for i, c in enumerate(find["clusters"]):
        c["_gi"] = i
        if c["match"] and isinstance(c.get("confidence"), (int, float)) and c["confidence"] < conf_th:
            todo.append(c)
    results = await asyncio.gather(*[tie(c) for c in todo]) if todo else []
    for c, r in zip(todo, results):
        c["_tie"] = r
    out = []
    for c in find["clusters"]:
        if c["match"] and isinstance(c.get("confidence"), (int, float)) and c["confidence"] < conf_th:
            t = c.get("_tie") or {}
            locked = bool(t.get("same"))
            out.append({"cluster": c.get("_gi"), "locked_match": locked,
                        "locked_golden": c["golden_index"] if locked else None,
                        "confidence": t.get("confidence", c.get("confidence")), "reason": t.get("reason"),
                        "tie_break": True, "first_level_conf": c.get("confidence"), "example": c["example"],
                        "n_findings": c["n_findings"], "n_cells": c["n_cells"], "found_by": c["found_by"]})
        else:
            out.append({"cluster": c.get("_gi"), "locked_match": bool(c["match"]),
                        "locked_golden": c["golden_index"] if c["match"] else None,
                        "confidence": c.get("confidence"), "reason": c.get("reason"), "tie_break": False,
                        "first_level_conf": c.get("confidence"), "example": c["example"],
                        "n_findings": c["n_findings"], "n_cells": c["n_cells"], "found_by": c["found_by"]})
    n_over = sum(1 for c in out if c["locked_match"])
    n_tb_flip = sum(1 for c in out if c["tie_break"] and not c["locked_match"])
    stats = {"n_merged": len(out), "n_locked_overlap": n_over, "n_locked_additional": len(out) - n_over,
             "n_tie_breaks": len(todo), "n_tie_flips_to_additional": n_tb_flip,
             "conf_threshold": conf_th, "n_first_level_overlap": find["stats"]["n_overlap_finding"]}
    print(f"PR {slug}: merged {len(out)}, locked overlap {n_over} (first-level {find['stats']['n_overlap_finding']}, "
          f"tie-breaks {len(todo)} -> {n_tb_flip} flipped to additional), verified additional {stats['n_locked_additional']}")
    json.dump({"pr": pr, "judge_model": judge, "stats": stats, "clusters": out},
              open(ROOT / f"analysis/semantic_overlap_locked_{slug}.json", "w"), indent=1)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--judge", default="gpt-5.2"); ap.add_argument("--conf", type=float, default=0.8)
    a = ap.parse_args()
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    top6 = sorted(D["pr_golden"], key=lambda u: (-D["pr_golden"][u]["sev_weight"], -D["pr_golden"][u]["n_comments"]))[:6]
    prs = [a.pr] if a.pr else (top6 if a.all else [])
    assert prs, "pass --pr or --all"
    t0 = time.time(); tot = {}
    for pr in prs:
        await run(pr, a.judge, a.conf)
        slug = pr.rstrip("/").split("/")[-1]
        tot[slug] = json.load(open(ROOT / f"analysis/semantic_overlap_locked_{slug}.json"))["stats"]
    T = {"n_merged": sum(v["n_merged"] for v in tot.values()),
         "n_locked_overlap": sum(v["n_locked_overlap"] for v in tot.values()),
         "n_locked_additional": sum(v["n_locked_additional"] for v in tot.values())}
    json.dump({"per_pr": tot, "total": T}, open(ROOT / "analysis/semantic_overlap_locked_summary.json", "w"), indent=1)
    print("TOTAL:", json.dumps(T, indent=1), f"| wall {time.time()-t0:.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
