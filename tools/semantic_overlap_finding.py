#!/usr/bin/env python3
"""Finding-level golden-overlap check (supersedes both earlier overlap passes).

Why: judging a CLUSTER REPRESENTATIVE against a golden is unreliable in both directions —
the first pass over-matched (49, generous), an adversarial strict pass under-matched (11,
because a cluster representative is broader than any one golden and the prompt punished
"broader/narrower"). Double counting happens exactly when a FINDING inside the cluster is the
same defect as a golden, so judge at the finding level: for each cluster, present up to K
deduplicated member findings plus all of the PR's goldens, and ask whether any single finding
is the same underlying defect as one golden (same root cause, same code path).

Output per PR: analysis/semantic_overlap_finding_<pr>.json
  clusters: [{golden_index, finding_index, match, confidence, reason, ...}]
  stats:    {n_merged, n_overlap, n_verified_additional}
Plus analysis/semantic_overlap_finding_summary.json.

Usage: .venv/bin/python tools/semantic_overlap_finding.py [--pr URL | --all] [--k 8]
"""
from __future__ import annotations
import argparse, asyncio, glob, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json

SYSTEM = "You are a strict code-review evaluation auditor. Always respond with valid JSON."
PROMPT = """A benchmark lists GOLDEN (human-verified) review findings for this pull request. Below is a
cluster of automated-review findings that our system grouped as ONE defect. Decide whether any SINGLE
finding in the cluster describes THE SAME underlying defect as one of the goldens.

GOLDENS (numbered 0..M-1):
{goldens}

CLUSTER FINDINGS (numbered 0..N-1):
{findings}

"Same defect" = same root cause in the same code path. A finding that merely touches the same file,
function, or feature, or that describes a different (adjacent / broader / narrower) defect, does NOT
count. Judge each finding independently; the answer is true if at least one finding is the same defect
as one golden.

Respond with ONLY JSON:
{{"golden_index": <int or null>, "finding_index": <int or null>, "match": true|false,
  "confidence": 0.0-1.0, "reason": "one sentence"}}"""


def goldens_for(pr):
    for f in (glob.glob(f"{ROOT}/analysis/inputs/golden_comments/*.json")
              or glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json")):
        for e in json.load(open(f)):
            if e["url"] == pr:
                return [c["comment"] for c in e["comments"]]
    return []


async def run(pr, judge, k):
    slug = pr.rstrip("/").split("/")[-1]
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
    # merged group -> member raw clusters -> candidate findings (dedup, longest-first diversity)
    goldens = goldens_for(pr)
    calls = {"n": 0}
    sem = asyncio.Semaphore(8)

    async def llm(prompt):
        async with sem:
            parsed, _, _, _ = await call_model_json(judge, SYSTEM, prompt, effort="medium", max_tokens=900)
        calls["n"] += 1
        return parsed if isinstance(parsed, dict) else {}

    async def one(gi, g):
        # collect findings across the group's raw clusters: take up to k, preferring distinct openings
        seen, picks = set(), []
        for r in g["merge_group"]:
            for t in sorted(mem[r], key=len):
                key = t[:40].lower()
                if key in seen:
                    continue
                seen.add(key); picks.append(t)
                if len(picks) >= k:
                    break
            if len(picks) >= k:
                break
        gtxt = "\n".join(f"{j}. {gtext[:500]}" for j, gtext in enumerate(goldens))
        ftxt = "\n".join(f"{j}. {t[:450]}" for j, t in enumerate(picks))
        p = await llm(PROMPT.format(goldens=gtxt, findings=ftxt))
        gi_ = p.get("golden_index")
        gi_ = int(gi_) if gi_ is not None and str(gi_).isdigit() and int(gi_) < len(goldens) else None
        m = bool(p.get("match")) and gi_ is not None
        return gi, {"golden_index": gi_ if m else None, "finding_index": p.get("finding_index") if m else None,
                    "first_pass_golden": v["clusters"][gi]["golden_index"], "match": m,
                    "confidence": p.get("confidence"), "reason": p.get("reason"),
                    "n_findings": v["clusters"][gi]["n_findings"], "n_cells": v["clusters"][gi]["n_cells"],
                    "found_by": v["clusters"][gi]["found_by"], "example": v["clusters"][gi]["example"][:200]}

    res = dict(await asyncio.gather(*[one(i, g) for i, g in enumerate(v["clusters"])]))
    clusters = [res[i] for i in range(len(v["clusters"]))]
    n_over = sum(1 for c in clusters if c["match"])
    stats = {"n_merged": v["stats"]["n_merged"], "n_overlap_finding": n_over,
             "n_verified_additional_finding": v["stats"]["n_merged"] - n_over,
             "n_overlap_first_pass": v["stats"]["n_golden_overlap"], "n_goldens": len(goldens)}
    print(f"PR {slug}: merged {stats['n_merged']}, overlap(finding-level) {n_over} "
          f"[first-pass {stats['n_overlap_first_pass']}], verified additional {stats['n_verified_additional_finding']} "
          f"({calls['n']} calls)")
    json.dump({"pr": pr, "judge_model": judge, "stats": stats, "clusters": clusters},
              open(ROOT / f"analysis/semantic_overlap_finding_{slug}.json", "w"), indent=1)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--judge", default="gpt-5.2"); ap.add_argument("--k", type=int, default=8)
    a = ap.parse_args()
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    top6 = sorted(D["pr_golden"], key=lambda u: (-D["pr_golden"][u]["sev_weight"], -D["pr_golden"][u]["n_comments"]))[:6]
    prs = [a.pr] if a.pr else (top6 if a.all else [])
    assert prs, "pass --pr or --all"
    t0 = time.time(); tot = {}
    for pr in prs:
        await run(pr, a.judge, a.k)
        slug = pr.rstrip("/").split("/")[-1]
        tot[slug] = json.load(open(ROOT / f"analysis/semantic_overlap_finding_{slug}.json"))["stats"]
    T = {"n_merged": sum(v["n_merged"] for v in tot.values()),
         "n_overlap_finding": sum(v["n_overlap_finding"] for v in tot.values()),
         "n_verified_additional_finding": sum(v["n_verified_additional_finding"] for v in tot.values())}
    json.dump({"per_pr": tot, "total": T}, open(ROOT / "analysis/semantic_overlap_finding_summary.json", "w"), indent=1)
    print("TOTAL:", json.dumps(T, indent=1), f"| wall {time.time()-t0:.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
