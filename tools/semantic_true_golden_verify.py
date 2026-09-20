#!/usr/bin/env python3
"""Verify the true-golden set: (1) stricter re-merge of cluster reps, (2) golden-overlap check.

Two defects the pilot could not rule out:
  A. UNDER-MERGE: clusters may still describe one underlying bug (paraphrase splits) —
     the 359 count is an upper bound.
  B. GOLDEN OVERLAP: a "beyond-golden" cluster may actually describe a bug that IS in the
     original golden set (the text-only official matcher missed it, so the adjudicator
     classified it real_but_ungold). Counting it as both a golden AND a new cluster inflates
     BOTH the denominator (42 + 359) and the cell's credit (golden TP + own clusters).

Pipeline (judge gpt-5.2):
  1. Load each PR's pilot clusters (finding_to_cluster) -> representative text per cluster.
  2. Re-merge the representatives within each PR (stricter "same underlying issue" prompt,
     chunked + rep merge) -> merged groups.
  3. For each merged group, ask: does this describe the same underlying issue as one of the
     PR's GOLDEN comments? -> golden_index or null.
  4. Write analysis/semantic_true_golden_verify_<pr>.json with:
       clusters: [{merge_group, golden_index, n_findings, n_cells, found_by, example}]
       stats: n_clusters_raw, n_merged, n_golden_overlap, n_verified_additional
     and a global summary file analysis/semantic_true_golden_verify_summary.json.

Usage:
  .venv/bin/python tools/semantic_true_golden_verify.py --pr https://github.com/calcom/cal.com/pull/11059
  .venv/bin/python tools/semantic_true_golden_verify.py --all
"""
from __future__ import annotations
import argparse, asyncio, glob, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json

SYSTEM = "You are a precise code-review deduplicator. Always respond with valid JSON."

MERGE_PROMPT = """Below are bug descriptions extracted from code reviews of ONE pull request. Some may describe
the SAME underlying defect (same root cause), worded differently or reported at different locations.

Descriptions (numbered 0..N-1):
{reps}

Group them so that each group contains only descriptions of the SAME underlying defect. Two reports about
different defects (even in the same function or file) are different groups.

Respond with ONLY a JSON object mapping each index to a group number (0-based):
{{"0": 0, "1": 0, "2": 1, ...}}"""

OVERLAP_PROMPT = """A benchmark has a set of GOLDEN (human-verified expected) review findings for this pull request.
Below is also a cluster of automated-review findings that our system classified as a REAL bug NOT in the
golden set. Determine whether this cluster actually describes the SAME underlying defect as one of the
golden findings (the original matcher may have missed it because the wording differs).

GOLDEN findings (numbered 0..M-1):
{goldens}

CLUSTER of automated findings (all describe one underlying defect):
{cluster}

Respond with ONLY a JSON object:
{{"golden_index": <int or null>, "same_issue": true|false, "confidence": 0.0-1.0, "reason": "one sentence"}}
Set golden_index to the matching golden's number if the cluster describes the same underlying defect as
that golden; null if the cluster is genuinely a DIFFERENT defect from every golden."""


def goldens_for(pr: str):
    for f in (glob.glob(f"{ROOT}/analysis/inputs/golden_comments/*.json")
              or glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json")):
        for e in json.load(open(f)):
            if e["url"] == pr:
                return [{"comment": c["comment"], "severity": c.get("severity"), "category": c.get("category"),
                         "file": c.get("file") or c.get("path"), "line": c.get("line") or c.get("start_line")}
                        for c in e["comments"]]
    return []


async def verify(pr: str, judge: str, chunk: int):
    slug = pr.rstrip("/").split("/")[-1]
    pil = json.load(open(ROOT / f"analysis/exp_union_semantic_pilot_{slug}.json"))
    cards = {c["cluster"]: c for c in json.load(open(ROOT / f"analysis/semantic_true_golden_{slug}.json"))["cards"]}
    f2c = {int(k): v for k, v in pil["finding_to_cluster"].items()}
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    runs = [r for r in D["all_healthy_runs"] if r["url"] == pr]
    per_run = {r["run_id"]: (r.get("bugtexts") or [], r) for r in runs}
    flat = [(rid, t) for rid, (ts, _r) in per_run.items() for t in ts]

    mem = defaultdict(list)
    finders = defaultdict(set)
    for i, (rid, t) in enumerate(flat):
        k = f2c[i]
        if t not in mem[k]:
            mem[k].append(t)          # unique texts, order-stable
        finders[k].add("|".join((per_run[rid][1]["model"], per_run[rid][1]["framework"], per_run[rid][1]["effort"])))

    raw = sorted(mem)
    reps = [min(mem[k], key=len) for k in raw]
    goldens = goldens_for(pr)
    print(f"PR {slug}: {len(raw)} raw clusters, {len(goldens)} goldens")

    calls = {"n": 0, "tin": 0, "tout": 0}
    sem = asyncio.Semaphore(8)

    async def llm(prompt):
        async with sem:
            parsed, tin, tout, _ = await call_model_json(judge, SYSTEM, prompt, effort="medium", max_tokens=4096)
        calls["n"] += 1; calls["tin"] += tin; calls["tout"] += tout
        return parsed if isinstance(parsed, dict) else {}

    # ---- phase 1: merge reps within the PR
    def group_from_ids(order, ids):
        by = defaultdict(list)
        for i, cid in zip(order, ids):
            by[int(cid) if str(cid).isdigit() else i].append(i)
        return list(by.values())

    async def merge_span(idx_list):
        order = idx_list
        body = "\n".join(f"{j}. {reps[i][:500]}" for j, i in enumerate(order))
        parsed = await llm(MERGE_PROMPT.format(reps=body))
        ids = [parsed.get(str(j), j) for j in range(len(order))]
        return group_from_ids(order, ids)

    spans = [list(range(a, min(a + chunk, len(raw)))) for a in range(0, len(raw), chunk)]
    chunk_groups = await asyncio.gather(*[merge_span(s) for s in spans])
    groups = [g for gs in chunk_groups for g in gs]
    # merge-group → member raw indices
    grp_members = [[raw[i] for i in g] for g in groups]
    # second round on group reps (cross-chunk)
    if len(grp_members) > 1:
        order = list(range(len(grp_members)))
        body = "\n".join(f"{j}. {reps[raw.index(grp_members[j][0])][:500]}" for j in order)
        parsed = await llm(MERGE_PROMPT.format(reps=body))
        merged2 = defaultdict(list)
        for j in order:
            cid = parsed.get(str(j), j)
            merged2[int(cid) if str(cid).isdigit() else j].append(j)
        new = []
        for _, js in merged2.items():
            new.append([m for j in js for m in grp_members[j]])
        grp_members = new
    print(f"  merged: {len(raw)} -> {len(grp_members)} groups ({calls['n']} judge calls so far)")

    # ---- phase 2: golden-overlap check per merged group
    async def overlap(members):
        rep = min((reps[raw.index(m)] for m in members), key=len)
        gtxt = "\n".join(f"{j}. [{g['severity']}/{g['category']}] {g['comment'][:700]}" for j, g in enumerate(goldens))
        parsed = await llm(OVERLAP_PROMPT.format(goldens=gtxt, cluster=rep[:900]))
        gi = parsed.get("golden_index")
        try:
            gi = int(gi) if gi is not None and str(gi).isdigit() else None
        except Exception:
            gi = None
        return {"golden_index": gi, "same_issue": bool(parsed.get("same_issue")),
                "confidence": parsed.get("confidence"), "reason": parsed.get("reason")}

    ov = await asyncio.gather(*[overlap(m) for m in grp_members])

    out_clusters = []
    for members, o in zip(grp_members, ov):
        nf = sum(len(mem[m]) for m in members)
        cells = set()
        for m in members:
            cells |= finders[m]
        ex = min((min(mem[m], key=len) for m in members), key=len)
        out_clusters.append({"merge_group": [m for m in members], "golden_index": o["golden_index"],
                             "same_issue": o["same_issue"], "confidence": o["confidence"],
                             "reason": o["reason"], "n_findings": nf, "n_cells": len(cells),
                             "found_by": sorted(cells), "example": ex[:400]})
    n_over = sum(1 for c in out_clusters if c["golden_index"] is not None)
    stats = {"n_clusters_raw": len(raw), "n_merged": len(grp_members), "n_golden_overlap": n_over,
             "n_verified_additional": len(grp_members) - n_over}
    print(f"PR {slug}: merged {len(grp_members)}, golden-overlap {n_over}, verified additional {stats['n_verified_additional']} "
          f"| judge calls {calls['n']}, tokens {calls['tin']:,}/{calls['tout']:,}")

    json.dump({"pr": pr, "judge_model": judge, "stats": stats, "clusters": out_clusters,
               "n_goldens": len(goldens), "tokens_in": calls["tin"], "tokens_out": calls["tout"]},
              open(ROOT / f"analysis/semantic_true_golden_verify_{slug}.json", "w"), indent=1)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--judge", default="gpt-5.2"); ap.add_argument("--chunk", type=int, default=60)
    a = ap.parse_args()
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    top6 = sorted(D["pr_golden"], key=lambda u: (-D["pr_golden"][u]["sev_weight"], -D["pr_golden"][u]["n_comments"]))[:6]
    prs = [a.pr] if a.pr else (top6 if a.all else [])
    assert prs, "pass --pr or --all"
    t0 = time.time()
    for pr in prs:
        await verify(pr, a.judge, a.chunk)
    tot = {}
    for pr in prs:
        slug = pr.rstrip("/").split("/")[-1]
        tot[slug] = json.load(open(ROOT / f"analysis/semantic_true_golden_verify_{slug}.json"))["stats"]
    json.dump(tot, open(ROOT / "analysis/semantic_true_golden_verify_summary.json", "w"), indent=1)
    print("SUMMARY:", json.dumps(tot, indent=1))
    print(f"wall {time.time()-t0:.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
