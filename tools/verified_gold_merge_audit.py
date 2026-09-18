#!/usr/bin/env python3
"""Merge audit: does every promoted bundle really describe ONE underlying defect?

A mis-merged cluster both fabricates demotions and hides real candidates (8-B00 merged 94 pagination
findings, 30 response-shape findings and 13 `visible`-param findings into one "candidate"). This asks
the judge directly, per promoted bundle, and records the distinct defects it finds.

Writes analysis/verified_gold/MERGE_AUDIT.{json,md}. Does not modify verdicts (the split is a
separate, deliberate step).

Usage: .venv/bin/python tools/verified_gold_merge_audit.py [--sample 8]
"""
from __future__ import annotations
import argparse, asyncio, glob, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402

VG = ROOT / "analysis/verified_gold"
PROMOTED = {"confirmed_regression", "behavior_change_not_regression"}
SYSTEM = "You are a strict code-review deduplicator. Respond with ONLY valid JSON."
PROMPT = """Below are automated-review findings that a clustering step grouped as ONE underlying defect.

Findings (numbered):
{items}

Do they all describe the SAME underlying defect (same root cause)? Different symptoms of one root cause
count as the same; genuinely different defects (different root cause, different behaviour, different fix)
do NOT.

Respond with ONLY JSON:
{{"one_defect": true|false, "n_distinct": <int>, "distinct_defects": ["<short label>", ...],
  "explanation": "one sentence"}}"""


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sample", type=int, default=8)
    ap.add_argument("--model", default='deepseek-4.1-flash')
    a = ap.parse_args()
    bundles = [mf for mf in sorted(VG.glob("*/B*/meta.json"))
               if json.loads(mf.read_text()).get("verdict") in PROMOTED]
    print(f"promoted bundles to audit: {len(bundles)}")
    sem = asyncio.Semaphore(8)
    calls = {"n": 0}

    async def one(mf):
        m = json.loads(mf.read_text())
        pr = (m.get("bug_id") or "").split("-")[0]; idx = int(m["bug_id"].split("B")[1])
        items = []
        try:
            v = json.load(open(VG.parent / f"semantic_true_golden_verify_{pr}.json"))
            pil = json.load(open(VG.parent / f"exp_union_semantic_pilot_{pr}.json"))
            f2c = {int(x): c for x, c in pil["finding_to_cluster"].items()}
            D = json.load(open(VG.parent / "final_report_dataset.json"))
            runs = [r for r in D["all_healthy_runs"] if r["url"] == pil["pr"]]
            flat = [t for r in runs for t in (r.get("bugtexts") or [])]
            seen = set()
            for i, t in enumerate(flat):
                if f2c.get(i) in v["clusters"][idx]["merge_group"] and t[:50] not in seen:
                    seen.add(t[:50]); items.append(t[:300])
        except Exception as e:
            return {"bug_id": m.get("bug_id"), "error": f"{type(e).__name__}: {e}"}
        if len(items) <= 1:
            return {"bug_id": m.get("bug_id"), "one_defect": True, "n_distinct": 1, "items": len(items)}
        step = max(1, len(items) // a.sample)
        sample = items[::step][:a.sample]
        body = "\n".join(f"{j}. {t}" for j, t in enumerate(sample))
        async with sem:
            p, _, _, _ = await call_model_json(a.model, SYSTEM, PROMPT.format(items=body),
                                               effort="low", max_tokens=2000)
        calls["n"] += 1
        p = p if isinstance(p, dict) else {}
        return {"bug_id": m.get("bug_id"), "title": (m.get("candidate") or {}).get("title"),
                "n_findings": (m.get("candidate") or {}).get("n_findings"), "items": len(items),
                "one_defect": bool(p.get("one_defect")), "n_distinct": p.get("n_distinct"),
                "distinct_defects": p.get("distinct_defects"), "explanation": p.get("explanation")}

    res = await asyncio.gather(*[one(mf) for mf in bundles])
    flagged = [r for r in res if r.get("one_defect") is False]
    print(f"flagged as multi-defect: {len(flagged)} of {len(res)}  ({calls['n']} judge calls)")
    for r in sorted(flagged, key=lambda r: -(r.get("n_distinct") or 0)):
        print(f"  {r['bug_id']} — {r.get('n_findings')} findings, {r.get('n_distinct')} distinct: "
              f"{'; '.join((r.get('distinct_defects') or [])[:3])[:150]}")
    (VG / "MERGE_AUDIT.json").write_text(json.dumps({"audited": len(res), "flagged": len(flagged), "results": res}, indent=1))
    lines = ["# Merge audit — does each promoted bundle describe one defect?", "",
             f"Audited {len(res)} promoted bundles with judge {a.model}. **Flagged as multi-defect: {len(flagged)}**", "",
             "| bundle | findings | distinct | labels |", "|---|---|---|---|"]
    for r in sorted(flagged, key=lambda r: -(r.get("n_distinct") or 0)):
        lines.append(f"| {r['bug_id']} | {r.get('n_findings')} | {r.get('n_distinct')} | {'; '.join((r.get('distinct_defects') or [])[:3])[:140]} |")
    (VG / "MERGE_AUDIT.md").write_text("\n".join(lines) + "\n")
    print("wrote MERGE_AUDIT.{json,md}")


if __name__ == "__main__":
    asyncio.run(main())
