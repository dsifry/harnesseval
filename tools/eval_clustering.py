#!/usr/bin/env python3
"""Evaluate clustering functions against the labeled same-issue pair set.

Positives: pairs of differently-worded findings that ARE the same underlying issue
(from the CE<->mrv and CE<->new-mrv semantic matching + flip stability groups).
Negatives: same-PR pairs judged different issues.

A clustering function scores a pair by returning True if it would merge them.
Usage: .venv/bin/python tools/eval_clustering.py [--sample N]
"""
from __future__ import annotations
import argparse, json, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import readjudicate3 as rj

EVAL = Path(__file__).resolve().parents[1] / "analysis/cluster_eval_set.json"


def score(pair_scorer, pos, neg, label):
    tp = sum(1 for a, b in pos if pair_scorer(a, b))
    fp = sum(1 for a, b in neg if pair_scorer(a, b))
    rec = tp / max(1, len(pos)); prec = 1 - fp / max(1, len(neg))
    print(f"{label:34s} merge-recall={rec:.3f} ({tp}/{len(pos)})  "
          f"false-merge-rate={1-prec:.3f} ({fp}/{len(neg)})")
    return rec, prec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None)
    a = ap.parse_args()
    d = json.load(open(EVAL))
    pos, neg = d["positives"], d["negatives"]
    if a.sample:
        random.seed(0)
        pos = random.sample(pos, min(a.sample, len(pos)))
        neg = random.sample(neg, min(a.sample, len(neg)))
    print(f"eval set: {len(pos)} positives, {len(neg)} negatives")

    import difflib
    def norm(t): return rj.normalize_for_cluster(t)
    for th in (0.75, 0.65, 0.55, 0.45):
        def sc(a, b, th=th):
            na, nb = norm(a), norm(b)
            return na == nb or difflib.SequenceMatcher(None, na, nb).ratio() >= th
        score(sc, pos, neg, f"difflib@{th} (current=0.75)")

    # token-jaccard baselines
    import re
    def toks(t):
        t = re.sub(r"[^a-z0-9_./]+", " ", norm(t))
        return set(w for w in t.split() if len(w) > 2)
    for th in (0.5, 0.4, 0.3):
        def sc(a, b, th=th):
            ta, tb = toks(a), toks(b)
            return ta and tb and len(ta & tb) / len(ta | tb) >= th
        score(sc, pos, neg, f"token-jaccard@{th}")

    # entity-overlap: shared file path or >=2 shared rare identifiers
    def ents(t):
        toks_ = toks(t)
        files = set(w for w in toks_ if "/" in w or w.endswith((".rb", ".ts", ".js", ".py", ".go", ".tsx", ".es6")))
        idents = set(w for w in toks_ if len(w) > 5 and not w.startswith("http"))
        return files, idents
    def sc_ent(a, b):
        fa, ia = ents(a); fb, ib = ents(b)
        if fa and fa & fb: return True
        return len(ia & ib) >= 2 and len(ia & ib) / max(1, min(len(ia), len(ib))) >= 0.25
    score(sc_ent, pos, neg, "entity-overlap (file or 2+ idents)")


if __name__ == "__main__":
    import asyncio, sys
    if "--hybrid" in sys.argv:
        async def run_hybrid():
            import readjudicate3 as rj
            random.seed(0)
            d2 = json.load(open(EVAL))
            n = 150
            P = random.sample(d2["positives"], n); N = random.sample(d2["negatives"], n)
            sem = asyncio.Semaphore(10)
            pf_P = [p for p in P if rj.prefilter_pair(*p)]
            pf_N = [p for p in N if rj.prefilter_pair(*p)]
            print(f"sampled {n}+{n}; prefilter keeps {len(pf_P)} pos / {len(pf_N)} neg")
            vP, fP = await rj._judge_pairs("gpt-5.2", pf_P, sem)
            vN, fN = await rj._judge_pairs("gpt-5.2", pf_N, sem)
            print(f"parse failures: {fP} pos batches, {fN} neg batches (0 expected)")
            merged_P = sum(vP); merged_N = sum(vN)
            print(f"judge: merged {merged_P}/{len(pf_P)} prefiltered positives, {merged_N}/{len(pf_N)} prefiltered negatives")
            rec = merged_P / n; fmr = merged_N / n
            print(f"END-TO-END: merge-recall={rec:.3f}  false-merge-rate={fmr:.3f}")
            judge_prec = merged_P / max(1, merged_P + merged_N)
            print(f"judge precision on prefiltered pairs: {judge_prec:.3f}")
        asyncio.run(run_hybrid())
    else:
        main()
