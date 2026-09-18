#!/usr/bin/env python3
"""Final gate: is every promoted bundle genuinely a bug the golden set does NOT contain?

The upstream overlap screening ran on pre-promotion clusters; one hand-made pilot bundle bypassed it
and turned out to be a golden duplicate. This gate asks the question directly of the promoted set:
for each bundle, compare its claim against that PR's golden comments and flag any match.

Writes analysis/verified_gold/GOLDEN_GATE.{json,md} and (unless --dry-run) sets
meta.verdict = "golden_duplicate" for matches, removing them from the promoted count.

Usage: .venv/bin/python tools/verified_gold_golden_gate.py [--dry-run]
"""
from __future__ import annotations
import argparse, asyncio, glob, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402

VG = ROOT / "analysis/verified_gold"
PROMOTED = {"confirmed_regression", "behavior_change_not_regression"}
SYSTEM = "You are a strict code-review evaluation auditor. Always respond with valid JSON."
PROMPT = """A benchmark has human-verified GOLDEN findings for this pull request. A separate campaign claims the
following finding is a REAL bug that the golden set MISSED, and has executed a test that demonstrates it.

GOLDEN findings (numbered 0..M-1):
{goldens}

CAMPAIGN CLAIM (title + the reports that support it):
{claim}

Question: does this claim describe THE SAME underlying defect as one of the golden findings (same root
cause in the same code path)? Wording, file-vs-callsite and severity framing may differ; a claim that
merely touches the same file/function, or a different (broader/narrower/adjacent) defect, is NOT a match.

Respond with ONLY JSON:
{{"golden_index": <int or null>, "match": true|false, "confidence": 0.0-1.0, "reason": "one sentence"}}"""


def goldens_for(pr):
    for f in glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json"):
        for e in json.load(open(f)):
            if e["url"] == pr:
                return [c["comment"] for c in e["comments"]]
    return []


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    metas = []
    for mf in sorted(VG.glob("*/B*/meta.json")):
        m = json.loads(mf.read_text())
        if m.get("verdict") in PROMOTED:
            metas.append((mf, m))
    print(f"promoted bundles to gate: {len(metas)}")
    sem = asyncio.Semaphore(8)
    calls = {"n": 0}

    async def one(mf, m):
        pr = str(m.get("pr") or "")
        goldens = goldens_for(pr)
        cand = m.get("candidate") or {}
        claim = (str(cand.get("title")) + "\n" + "\n".join(f"- {r[:300]}" for r in (cand.get("reports") or [])[:5]))[:3000]
        gtxt = "\n".join(f"{j}. {g[:700]}" for j, g in enumerate(goldens))
        async with sem:
            p, _, _, _ = await call_model_json("gpt-5.2", SYSTEM, PROMPT.format(goldens=gtxt, claim=claim),
                                               effort="low", max_tokens=2000)
        calls["n"] += 1
        p = p if isinstance(p, dict) else {}
        gi = p.get("golden_index")
        gi = int(gi) if gi is not None and str(gi).isdigit() and int(gi) < len(goldens) else None
        match = bool(p.get("match")) and gi is not None
        return {"bug_id": m.get("bug_id"), "pr": pr, "match": match, "golden_index": gi if match else None,
                "confidence": p.get("confidence"), "reason": p.get("reason"),
                "title": cand.get("title"), "meta_file": str(mf)}

    res = await asyncio.gather(*[one(mf, m) for mf, m in metas])
    hits = [r for r in res if r["match"]]
    conf = Counter(round(float(r["confidence"]), 1) for r in hits if isinstance(r.get("confidence"), (int, float)))
    print(f"golden-duplicate matches among promoted: {len(hits)}  (confidence of hits: {dict(conf)})")
    for r in hits:
        print(f"   {r['bug_id']} -> golden#{r['golden_index']} ({r['confidence']}) :: {str(r['title'])[:70]}")
        print(f"       {str(r['reason'])[:150]}")
    if not a.dry_run:
        for r in hits:
            mf = Path(r["meta_file"]); m = json.loads(mf.read_text())
            m["verdict"] = "golden_duplicate"
            m["golden_gate"] = {"golden_index": r["golden_index"], "confidence": r["confidence"],
                                "reason": r["reason"], "previous_verdict": "promoted",
                                "agency": "tools/verified_gold_golden_gate.py (final gate on the promoted set)"}
            mf.write_text(json.dumps(m, indent=1))
    out = {"checked": len(res), "matches": len(hits), "confidence": dict(conf),
           "results": [{k: v for k, v in r.items() if k != "meta_file"} for r in res]}
    (VG / "GOLDEN_GATE.json").write_text(json.dumps(out, indent=1))
    lines = ["# Golden-distinctness gate on the promoted set", "",
             f"Checked {len(res)} promoted bundles against each PR's golden comments with judge gpt-5.2.",
             f"**Golden duplicates found: {len(hits)}**", "",
             "| bundle | verdict after gate | golden | confidence | reason |", "|---|---|---|---|---|"]
    for r in hits:
        lines.append(f"| {r['bug_id']} | `golden_duplicate` | #{r['golden_index']} | {r['confidence']} | {str(r['reason'])[:120]} |")
    if not hits:
        lines.append("| (none) | — | — | — | every promoted bundle is golden-distinct |")
    (VG / "GOLDEN_GATE.md").write_text("\n".join(lines) + "\n")
    print("wrote GOLDEN_GATE.{json,md}")


if __name__ == "__main__":
    asyncio.run(main())
