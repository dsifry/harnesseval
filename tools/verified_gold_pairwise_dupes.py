#!/usr/bin/env python3
"""Per-PR duplicate check WITHIN the verified hidden gold set.

The upstream merge passes clustered findings; the golden gate checks the promoted set against the
golden comments. Neither checks whether two *promoted* bundles describe the same underlying defect.
That is what this does: per PR, build candidate pairs (shared resolved file, or token overlap on
title+reports), then ask the judge whether the pair is the same root cause in the same code path.

Writes analysis/verified_gold/PAIRWISE_DUPES.{json,md}. Read-only w.r.t. verdicts unless --apply.

Usage: .venv/bin/python tools/verified_gold_pairwise_dupes.py [--threshold 0.3] [--apply]
"""
from __future__ import annotations
import argparse, asyncio, glob, json, re, sys
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harnesseval.model_router import call_model_json  # noqa: E402

VG = ROOT / "analysis/verified_gold"
PROMOTED = {"confirmed_regression", "behavior_change_not_regression"}
SYSTEM = "You are a strict code-review deduplicator. Always respond with valid JSON."
PROMPT = """Two findings were independently verified as real bugs in the same pull request. Decide whether
they are THE SAME underlying defect (same root cause in the same code path) or two different defects.

FINDING A
  file: {fa}
  claim: {ta}

FINDING B
  file: {fb}
  claim: {tb}

Same defect means: two descriptions/reportings of one root cause. Different wording, different call
site, or different severity framing can still be the same defect. Two distinct defects — even in the
same function or file — are NOT the same.

Respond with ONLY JSON:
{{"same": true|false, "confidence": 0.0-1.0, "reason": "one sentence"}}"""


def toks(s):
    return {w for w in re.findall(r"[a-z0-9_]{4,}", (s or "").lower())}


VOTES = VG / "PAIRWISE_VOTES.json"


def load_votes():
    return json.loads(VOTES.read_text()) if VOTES.exists() else {}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--threshold", type=float, default=0.3)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--min-votes", type=int, default=2, help="affirmative votes required to act on a pair")
    a = ap.parse_args()
    by_pr = defaultdict(list)
    for mf in sorted(VG.glob("*/B*/meta.json")):
        m = json.loads(mf.read_text())
        if m.get("verdict") in PROMOTED:
            c = m.get("candidate") or {}
            claim = (str(c.get("title")) + " || " + " ".join(str(r)[:200] for r in (c.get("reports") or [])[:3]))[:1200]
            by_pr[(m.get("bug_id") or "").split("-")[0]].append(
                {"bug_id": m.get("bug_id"), "file": (c.get("file_resolved") or c.get("file") or ""), "claim": claim,
                 "meta": str(mf)})
    pairs = []
    for pr, items in by_pr.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                A, B = items[i], items[j]
                ta, tb = toks(A["claim"]), toks(B["claim"])
                jac = len(ta & tb) / max(1, len(ta | tb))
                same_file = bool(A["file"]) and A["file"] == B["file"]
                if same_file or jac >= a.threshold:
                    pairs.append((pr, A, B, same_file, jac))
    print(f"promoted per PR: {dict(Counter(len(v) for v in by_pr.values()))}  total {sum(len(v) for v in by_pr.values())}")
    print(f"candidate pairs to adjudicate: {len(pairs)} (same-file: {sum(1 for p in pairs if p[3])})")
    sem = asyncio.Semaphore(8)
    async def one(pr, A, B, same_file, jac):
        async with sem:
            p, _, _, _ = await call_model_json("gpt-5.2", SYSTEM,
                PROMPT.format(fa=A["file"], ta=A["claim"], fb=B["file"], tb=B["claim"]),
                effort="low", max_tokens=600)
        p = p if isinstance(p, dict) else {}
        return {"pr": pr, "a": A["bug_id"], "b": B["bug_id"], "same_file": same_file, "jaccard": round(jac, 3),
                "same": bool(p.get("same")), "confidence": p.get("confidence"), "reason": p.get("reason"),
                "a_meta": A["meta"], "b_meta": B["meta"]}
    async def run_all():
        return await asyncio.gather(*[one(*p) for p in pairs])
    out = asyncio.run(run_all())
    hits = [r for r in out if r["same"]]
    # ---- accumulate votes (the pairwise judge is not deterministic: the same pairs were judged
    # duplicate in one pass and distinct in the next, so act on a majority of repeated passes)
    votes = load_votes()
    for r in out:
        k = f"{r['pr']}|{r['a']}|{r['b']}"
        v = votes.setdefault(k, {"yes": 0, "no": 0, "reasons": []})
        v["yes" if r["same"] else "no"] += 1
        if r["same"] and r.get("reason"):
            v["reasons"].append(str(r["reason"])[:200])
    VOTES.write_text(json.dumps(votes, indent=1))
    confirmed = {k for k, v in votes.items() if v["yes"] >= a.min_votes}
    print(f"vote tally: {len(votes)} pairs judged at least once; {len(confirmed)} with >= {a.min_votes} affirmative votes")
    print(f"duplicate pairs found: {len(hits)}")
    for r in sorted(hits, key=lambda r: -(r.get('confidence') or 0)):
        print(f"  PR {r['pr']}: {r['a']} == {r['b']} (conf {r['confidence']}, same_file={r['same_file']}, j={r['jaccard']})")
        print(f"      {str(r['reason'])[:150]}")
    (VG / "PAIRWISE_DUPES.json").write_text(json.dumps({"checked_pairs": len(pairs), "duplicates": len(hits), "results": out}, indent=1))
    L = ["# Within-PR duplicate check of the verified hidden gold set", "",
         f"Adjudicated {len(pairs)} candidate pairs (pre-filtered by shared file or >= {a.threshold} token overlap).",
         f"**Duplicate pairs found: {len(hits)}**", "",
         "| PR | bundle A | bundle B | confidence | reason |", "|---|---|---|---|---|"]
    for r in hits:
        L.append(f"| {r['pr']} | {r['a']} | {r['b']} | {r['confidence']} | {str(r['reason'])[:110]} |")
    if not hits:
        L.append("| — | — | — | — | every promoted bundle is a distinct defect |")
    (VG / "PAIRWISE_DUPES.md").write_text("\n".join(L) + "\n")
    to_apply = [r for r in hits if f"{r['pr']}|{r['a']}|{r['b']}" in confirmed] if a.apply else []
    if a.apply:
        for r in to_apply:                   # keep the first, mark the second as a duplicate of it
            mf = Path(r["b_meta"]); m = json.loads(mf.read_text())
            m["verdict"] = "duplicate_of"
            m["duplicate_of"] = {"bug_id": r["a"], "confidence": r["confidence"], "reason": r["reason"],
                                 "agency": "tools/verified_gold_pairwise_dupes.py"}
            mf.write_text(json.dumps(m, indent=1))
        print(f"applied: {len(to_apply)} bundle(s) marked duplicate_of")


if __name__ == "__main__":
    main()
