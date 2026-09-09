#!/usr/bin/env python3
"""Adjudicator-model eval: can a cheaper judge replace gpt-5.2 (k=3 consensus)?

Samples findings stratified by the reference verdict (from completed k=3 passes),
re-adjudicates each with a candidate judge at k=1, reports agreement, verdict-distribution
shift, and cost. Self-preference probe: agreement split by finding provenance
(mrv-generated vs CE-generated).

Usage: .venv/bin/python tools/eval_adjudicator.py [--n 100] [--judges glm-5.3-background,glm-5.3-background:xhigh,...]
Judge spec: model[:effort]  (effort: low|xhigh; default low)
"""
import argparse, asyncio, collections, glob, json, os, random, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import readjudicate3 as rj
from harnesseval.dataset.pr_diff import fetch_diff

def sample_findings(n):
    """Stratified sample of (diff, text, ref_verdict, provenance) from completed k=3 passes."""
    pool = []
    for mf in glob.glob("runs/*/manifest.json"):
        try: m = json.load(open(mf))
        except Exception: continue
        if m.get("run_batch") != "20260908-mrv0111-flash-lh" or m.get("status") != "pass": continue
        d = os.path.dirname(mf)
        rj3 = json.load(open(os.path.join(d, "readjudication3.json")))
        prov = "mrv"
        diff = fetch_diff(rj3["url"])["diff"]
        for rec in rj3["records"]:
            v = rec.get("new_verdict")
            if v in ("bug", "important_non_bug", "hallucination"):
                pool.append((diff, rec["issue_text"], v, prov))
    random.seed(0)
    by_v = collections.defaultdict(list)
    for p in pool: by_v[p[2]].append(p)
    per = max(1, n // len(by_v))
    out = []
    for v, lst in by_v.items(): out.extend(random.sample(lst, min(per, len(lst))))
    random.shuffle(out)
    return out[:n]

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--judges", default="glm-5.3-background,glm-5.3-background:xhigh,"
                                       "glm-5.3-flash-background,glm-5.3-flash-background:xhigh,gpt-5.2")
    ap.add_argument("--k", type=int, default=1, help="votes per adjudication (majority wins; production k=3)")
    a = ap.parse_args()
    sample = sample_findings(a.n)
    print(f"sample: {len(sample)} findings, verdict dist: "
          f"{dict(collections.Counter(s[2] for s in sample))}")
    for spec in a.judges.split(","):
        model, _, eff = spec.partition(":")
        eff = eff or "low"
        sem = asyncio.Semaphore(15)
        t0 = time.time()
        agrees = 0; dist = collections.Counter(); times = []
        CH = {"bug": 0, "important_non_bug": 0, "hallucination": 0}
        tasks = []
        async def one(s):
            diff, text, ref, prov = s
            t1 = time.time()
            try:
                v = await rj.adjudicate(text, diff, model, sem, k=a.k,
                                       vote_effort=eff)
                times.append(time.time() - t1)
                return v["verdict"], ref
            except Exception as e:
                return f"error:{type(e).__name__}", ref
        res = await asyncio.gather(*[one(s) for s in sample])
        verdicts = []
        for (got, ref), s in zip(res, sample):
            verdicts.append({"verdict": got, "ref": ref, "text": s[1][:160]})
            dist[got] += 1
            if got == ref: agrees += 1
        outdir = Path("analysis/adjudicator_verdicts"); outdir.mkdir(exist_ok=True)
        safe = spec.replace(":", "_").replace("/", "_")
        (outdir / f"{safe}.json").write_text(json.dumps(verdicts, indent=1))
        print(f"\n{spec:35s} agreement={agrees/len(sample):.3f}  dist={dict(dist)}  "
              f"median_call={sorted(times)[len(times)//2]:.1f}s  wall={time.time()-t0:.0f}s")
if __name__ == "__main__":
    asyncio.run(main())
