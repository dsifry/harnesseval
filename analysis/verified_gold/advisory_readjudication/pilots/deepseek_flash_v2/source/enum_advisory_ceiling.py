#!/usr/bin/env python3
"""Enumerate the advisory-worthy-concern ceiling per PR, independently of both harnesses.

For each selected PR, claude-opus-4.5 (OAuth CLI) reads ONLY the diff and enumerates
every concern meeting the ratified advisory bar: true/factual, actionable or
decision-relevant, not a style nit, not a correctness bug. Output per PR:
analysis/advisory_ceiling/<prnum>.json  {"concerns": [{advisory, kind, why}]}

Stratification: PRs picked across the mrv advisory-count distribution (0 / 1-2 / 3+)
and diff sizes, so the ceiling covers both "should we be silent?" and "how much
are we missing?" cases.
"""
import asyncio, glob, json, os, re, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harnesseval.cli_backends import _claude_cli
from harnesseval.dataset.pr_diff import fetch_diff

BAR = """You are auditing a pull-request diff to enumerate ADVISORY-level concerns — observations
that are true and worth a staff maintainer's attention, but are NOT correctness bugs.

The bar for an advisory (all must hold):
- TRUE: factually accurate about this diff and its surrounding code.
- DECISION-RELEVANT: a maintainer would want to know when reviewing or shipping this change.
- NOT A BUG: it does not describe incorrect behavior introduced by the change (those go to a different channel).
- NOT STYLE: no formatting/naming/preference nits.

Typical kinds (non-exhaustive): test-coverage gap, migration/re-run hazard, deploy/version-skew
risk, API-contract or backward-compatibility note, performance consideration, observability gap,
security-hardening note, documentation/UX inconsistency.

Enumerate EVERY concern in this diff that meets the bar — one entry each, no matter how many.
If the diff contains none, return an empty list. Do NOT pad. Do NOT merge distinct concerns.
For each: a one-sentence advisory (what + why it matters), a kind from the list above
(or "other"), and the concrete trigger in the diff."""

DIFF_CAP = 60000

def pick_prs():
    """mrv advisory counts + diff sizes across the 50-PR cell; stratify."""
    per = {}
    for f in glob.glob("runs/*/summary.json"):
        try: s = json.load(open(f))
        except Exception: continue
        if (s.get("run_batch") == "20260908-mrv0111-bg-lh" and s.get("framework") == "metareview-realistic"
                and s.get("model") == "glm-5.3-background" and s.get("effort") == "low"):
            d = os.path.dirname(f)
            c = json.load(open(os.path.join(d, "readjudication3.json")))
            gm = set(g.get("matched_candidate") for g in s.get("per_golden_matches", []) if g.get("matched_candidate"))
            cl = {}
            for r in c["records"]:
                cid = (r["cluster"] or {}).get("id") if isinstance(r["cluster"], dict) else r.get("cluster")
                e = cl.setdefault(cid, {"gold": False, "imp": False})
                if r["issue_text"] in gm: e["gold"] = True
                if r.get("new_verdict") == "important_non_bug": e["imp"] = True
            adv = sum(1 for e in cl.values() if e["imp"] and not e["gold"])
            per[s["url"]] = dict(mrv_adv=adv, dchars=c["corrected"].get("diff_chars", 0),
                                 prnum=s["url"].rstrip("/").rsplit("/", 1)[-1],
                                 repo="/".join(s["url"].split("/")[3:5]))
    buckets = {"zero": [], "mid": [], "high": []}
    for url, v in per.items():
        (buckets["zero"] if v["mrv_adv"] == 0 else buckets["mid"] if v["mrv_adv"] <= 2 else buckets["high"]).append((url, v))
    # within each bucket, spread by diff size; take 5 zero / 6 mid / 4 high
    picks = []
    for name, k in (("zero", 5), ("mid", 6), ("high", 4)):
        b = sorted(buckets[name], key=lambda t: t[1]["dchars"])
        step = max(1, len(b) // k)
        picks += [b[i] for i in range(0, len(b), step)][:k]
    return picks

def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

async def main():
    picks = pick_prs()
    print(f"stratified picks: {len(picks)} PRs")
    for url, v in picks:
        print(f"  PR {v['prnum']:>6s}  mrv_adv={v['mrv_adv']}  diff={v['dchars']}c")
    sem = asyncio.Semaphore(3)
    outdir = Path("analysis/advisory_ceiling"); outdir.mkdir(exist_ok=True)

    async def one(url, v):
        out = outdir / f"pr{v['prnum']}_{hash(url) % 100000:05d}.json"
        if out.exists():
            print(f"PR {v['prnum']}: already enumerated, skip"); return
        try:
            diff = fetch_diff(url)["diff"][:DIFF_CAP]
        except Exception as e:
            print(f"PR {v['prnum']}: diff fetch failed {e}"); return
        prompt = (f"{BAR}\n\n=== DIFF ===\n{diff}\n\n"
                  'Return JSON only: {"concerns": [{"advisory": str, "kind": str, "why": str}]}')
        async with sem:
            try:
                text, _, _ = await _claude_cli("opus", "medium", prompt, "You are a precise code-review auditor.")
                d = extract_json(text) or {}
                cons = d.get("concerns", [])
            except Exception as e:
                print(f"PR {v['prnum']}: cli failed {type(e).__name__}: {str(e)[:120]}"); return
        out.write_text(json.dumps(dict(url=url, mrv_adv=v["mrv_adv"], dchars=v["dchars"],
                                       concerns=cons), indent=1))
        kinds = collections.Counter(c.get("kind") for c in cons)
        print(f"PR {v['prnum']:>6s}: ceiling={len(cons)}  kinds={dict(kinds)}", flush=True)

    await asyncio.gather(*[one(u, v) for u, v in picks])
    done = list(outdir.glob("*.json"))
    tot = sum(len(json.load(open(f)).get("concerns", [])) for f in done)
    print(f"\nDONE: {len(done)} PRs, total ceiling concerns={tot}, mean={tot/max(1,len(done)):.1f}/PR")

if __name__ == "__main__":
    asyncio.run(main())
