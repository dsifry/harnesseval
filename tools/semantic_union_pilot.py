#!/usr/bin/env python3
"""Semantic-merge pilot for the expanded-gold union (ONE PR, read-only, NOT frozen).

Problem this addresses: the frozen expanded-gold union (compute §10) keys each confirmed-bug
finding by its own file:start-end anchor or a near-verbatim text cluster. Paraphrases of the
same underlying bug therefore become SEPARATE keys, so per-PR union sizes (513-981) vastly
overcount the true distinct-bug count, making recall_exp levels 5-10x conservative.

This pilot reuses the machinery we already built:
- dedup_bugs_llm (branch sdlc-loop-experiment, harnesseval/sdlc_loop.py): file-grouped
  LLM clustering — ONE call per file, judge clusters same-underlying-issue reports.
- anchor_matcher.py's _LOC_RE: extracts file refs from prose findings (mid-text mentions).

Pipeline (judge = gpt-5.2, the rj3 adjudicator model):
  1. Collect every confirmed-bug finding for the PR across ALL healthy runs (same universe
     as compute §10: rj3 'bug' / in-run 'real_but_ungold').
  2. Exact-dedupe on normalize_for_cluster (rj3) — pure payload reduction.
  3. Group by file: leading anchor, else first _LOC_RE file mention, else 'unknown'.
  4. Per file group, chunked LLM clustering (chunks of --chunk); groups with multiple chunks
     get a representative-merge call; then cross-file merge rounds on cluster representatives
     until fixpoint (catches prose-vs-anchor duplicates of one bug).
  5. Write analysis/exp_union_semantic_pilot_<pr>.json: per-unique-finding global cluster id,
     cluster summaries, cost, and recall_exp recomputed per selected cell.

Usage:
  .venv/bin/python tools/semantic_union_pilot.py --pr https://github.com/calcom/cal.com/pull/11059
"""
from __future__ import annotations
import argparse, asyncio, json, re, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import readjudicate3 as rj                      # normalize_for_cluster (frozen instrument)
from harnesseval.model_router import call_model_json

# anchor_matcher.py _LOC_RE (frozen instrument — same extraction pattern)
_LOC_RE = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4})(?::(\d+)(?:-(\d+))?)?")
# compute §10 _ANCHOR_RE — leading anchor only
_LEAD_RE = re.compile(r"^([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4}):(\d+)(?:-(\d+))?")

# dedup_bugs_llm prompt, verbatim structure (branch sdlc-loop-experiment)
DEDUP_SYSTEM = "You are a precise code review deduplicator. Always respond with valid JSON."
DEDUP_PROMPT = """You are grouping duplicate bug reports. The following bug reports all concern the same file: {file}

Bugs (numbered 0..N-1):
{bugs}

Group them into clusters where each cluster represents the SAME underlying issue (different wording
for the same problem). Bugs about genuinely different issues go in separate clusters.

Respond with ONLY a JSON object mapping each bug index to a cluster number (0-based):
{{"0": 0, "1": 0, "2": 1, "3": 0, ...}}
where bugs with the same cluster number are duplicates of each other."""

MERGE_PROMPT = """You are merging bug-report clusters from a code review of one pull request.
Each line below is a REPRESENTATIVE bug description from one cluster (clusters were formed within
single files; duplicates may also exist ACROSS files because the same root cause can be reported
against a cause site in one file and a consequence site in another).

Representatives (numbered 0..N-1):
{reps}

Decide which of these are the SAME underlying issue (same root cause — different wording,
different file, or different severity framing are still the same issue; two genuinely different
defects are NOT). Respond with ONLY a JSON object mapping each index to a group number (0-based):
{{"0": 0, "1": 0, "2": 1, ...}}
where indexes with the same group number are the same underlying issue."""


def file_of(text: str) -> str:
    m = _LEAD_RE.match(text)
    if m:
        return m.group(1)
    for m in _LOC_RE.finditer(text):
        if "." in m.group(1):
            return m.group(1)
    return "unknown"


def normalize_map(items: list[str]) -> tuple[list[str], list[int]]:
    """Exact-dedupe on rj3 normalize_for_cluster; returns (uniq_texts, orig->uniq idx)."""
    uniq, idx, back = [], [], {}
    for t in items:
        nt = rj.normalize_for_cluster(t)
        if nt not in back:
            back[nt] = len(uniq); uniq.append(t)
        idx.append(back[nt])
    return uniq, idx


async def run(pr: str, judge_model: str, chunk: int):
    D = json.load(open(ROOT / "analysis/final_report_dataset.json"))
    runs = [r for r in D["all_healthy_runs"] if r["url"] == pr]
    per_run = {r["run_id"]: r.get("bugtexts") or [] for r in runs}
    flat = [(rid, t) for rid, ts in per_run.items() for t in ts]
    if not flat:
        print(f"no confirmed-bug findings for {pr}"); return
    gold = D["pr_golden"][pr]["n_comments"]
    print(f"PR {pr.split('/')[-1]}: {len(runs)} runs, {len(flat)} confirmed-bug findings, {gold} goldens")

    uniq, to_uniq = normalize_map([t for _, t in flat])
    print(f"after exact normalize-dedupe: {len(uniq)} unique texts")

    calls = {"n": 0, "tin": 0, "tout": 0}
    sem = asyncio.Semaphore(8)

    async def llm_cluster(texts: list[str], prompt: str) -> list[int]:
        """One judge call; returns a local cluster id per text."""
        n = len(texts)
        if n <= 1:
            return [0] * n
        async with sem:
            parsed, tin, tout, _ = await call_model_json(
                judge_model, DEDUP_SYSTEM, prompt, effort="medium", max_tokens=4096)
        calls["n"] += 1; calls["tin"] += tin; calls["tout"] += tout
        out = []
        for i in range(n):
            v = parsed.get(str(i)) if isinstance(parsed, dict) else None
            out.append(int(v) if isinstance(v, int) or (isinstance(v, str) and v.isdigit()) else i)
        return out

    uf_parent = list(range(len(uniq)))

    def find(x):
        while uf_parent[x] != x:
            uf_parent[x] = uf_parent[uf_parent[x]]; x = uf_parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            uf_parent[rb] = ra

    def union_group(members: list[int]):
        for m in members[1:]:
            union(members[0], m)

    # ---- phase A: per-file chunked clustering (all chunks in parallel)
    groups = defaultdict(list)
    for ui, t in enumerate(uniq):
        groups[file_of(t)].append(ui)
    print(f"file groups: {len(groups)}; largest: {sorted(((len(v), k) for k, v in groups.items()), reverse=True)[:5]}")

    chunk_jobs = []          # (file, ordered members of this chunk)
    for f, members in sorted(groups.items()):
        ms = sorted(members, key=lambda i: uniq[i])
        for k in range(0, len(ms), chunk):
            chunk_jobs.append((f, ms[k:k + chunk]))

    async def cluster_chunk(f, order):
        ids = await llm_cluster([uniq[i][:600] for i in order],
                                DEDUP_PROMPT.format(file=f, bugs="\n".join(f"{j}. {uniq[i][:600]}" for j, i in enumerate(order))))
        by = defaultdict(list)
        for i, cid in zip(order, ids):
            by[cid].append(i)
        reps = []
        for cid, mem in by.items():
            union_group(mem)
            reps.append(min(mem, key=lambda i: len(uniq[i])))  # canonical rep: shortest text
        return f, reps

    chunk_results = await asyncio.gather(*[cluster_chunk(f, o) for f, o in chunk_jobs])

    # ---- phase B: per-file representative merge (across that file's chunks)
    per_file_reps = defaultdict(list)
    for f, reps in chunk_results:
        per_file_reps[f].extend(reps)

    async def merge_reps(order, tag):
        if len(order) <= 1:
            return
        ids = await llm_cluster([uniq[i][:400] for i in order], MERGE_PROMPT.format(reps="\n".join(f"{j}. {uniq[i][:400]}" for j, i in enumerate(order))))
        by = defaultdict(list)
        for i, cid in zip(order, ids):
            by[cid].append(i)
        for cid, mem in by.items():
            union_group(mem)

    await asyncio.gather(*[merge_reps(sorted(reps, key=lambda i: uniq[i]), f) for f, reps in per_file_reps.items() if len(reps) > 1])

    # ---- phase C: cross-file merge rounds until fixpoint (max 3)
    for rnd in range(3):
        reps = sorted({find(i) for i in range(len(uniq))}, key=lambda i: uniq[i])
        if len(reps) <= 1:
            break
        before = len(reps)
        jobs = [merge_reps(reps[k:k + chunk], f"cross-file r{rnd+1}") for k in range(0, len(reps), chunk)]
        await asyncio.gather(*jobs)
        after = len({find(i) for i in range(len(uniq))})
        print(f"cross-file round {rnd+1}: {before} -> {after} clusters")
        if after == before:
            break

    # ---- assemble output
    clusters = defaultdict(list)
    for ui in range(len(uniq)):
        clusters[find(ui)].append(ui)
    ordered = sorted(clusters.items(), key=lambda kv: (-len(kv[1]), uniq[min(kv[1], key=lambda i: len(uniq[i]))]))
    cid_of, summaries = {}, []
    for k, (root, mem) in enumerate(ordered):
        for m in mem:
            cid_of[m] = k
        rep_text = uniq[min(mem, key=lambda i: len(uniq[i]))]
        summaries.append({"cluster": k, "example": rep_text[:400]})

    n_findings_per_cluster = defaultdict(int)
    n_runs_per_cluster = defaultdict(set)
    for (rid, t), ui in zip(flat, to_uniq):
        c = cid_of[ui]
        n_findings_per_cluster[c] += 1
        n_runs_per_cluster[c].add(rid)
    for s in summaries:
        s["n_findings"] = n_findings_per_cluster[s["cluster"]]
        s["n_runs"] = len(n_runs_per_cluster[s["cluster"]])

    union_sem = len(clusters)
    print(f"\nSEMANTIC UNION: {union_sem} distinct bugs (goldens={gold}; frozen key-union for this PR was 981)")
    print(f"judge: {calls['n']} calls, {calls['tin']:,} in / {calls['tout']:,} out tokens")

    # ---- per-cell recall under the semantic union (selected runs on this PR)
    run_uniq = {rid: [to_uniq[i] for i, (r2, _) in enumerate(flat) if r2 == rid] for rid in per_run}
    sel = [r for r in D["selected_runs"] if r["url"] == pr]
    print(f"\n{'cell':46s} {'tp_gold':>7s} {'own_cl':>6s} {'recall_sem':>10s}")
    cell_out = []
    for r in sorted(sel, key=lambda r: (r["model"], r["framework"], r["effort"])):
        own_sem = {cid_of[u] for u in run_uniq[r["run_id"]]}
        tp_sem = r["tp"] + len(own_sem)
        rec = tp_sem / (gold + union_sem)
        cell_out.append({"model": r["model"], "framework": r["framework"], "effort": r["effort"],
                         "tp_golden": r["tp"], "own_clusters": len(own_sem),
                         "tp_sem": tp_sem, "recall_sem": rec})
        print(f"{r['model'][:22]+'·'+r['framework'][:8]+'·'+r['effort']:46s} {r['tp']:7d} {len(own_sem):6d} {rec:10.3f}")

    out = {
        "pr": pr, "judge_model": judge_model, "judge_calls": calls["n"],
        "tokens_in": calls["tin"], "tokens_out": calls["tout"],
        "n_runs": len(runs), "n_findings": len(flat), "n_unique_texts": len(uniq),
        "goldens": gold, "semantic_union_size": union_sem,
        "clusters": summaries,
        "cells": cell_out,
        "finding_to_cluster": {str(i): cid_of[ui] for i, ui in enumerate(to_uniq)},
    }
    slug = pr.rstrip("/").split("/")[-1]
    path = ROOT / f"analysis/exp_union_semantic_pilot_{slug}.json"
    json.dump(out, open(path, "w"), indent=1)
    print(f"\nwrote {path}")
    print("\nclusters (n findings / n runs — example):")
    for s in summaries:
        print(f"  #{s['cluster']:3d} [{s['n_findings']:4d}f/{s['n_runs']:2d}r] {s['example'][:110]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True)
    ap.add_argument("--judge", default="gpt-5.2")
    ap.add_argument("--chunk", type=int, default=60)
    a = ap.parse_args()
    t0 = time.time()
    asyncio.run(run(a.pr, a.judge, a.chunk))
    print(f"wall: {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
