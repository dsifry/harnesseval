#!/usr/bin/env python3
"""Honest re-adjudication v3: three-way classification + cross-run dedup + grounded
hallucination + k=3 majority vote + provenance stripping.

History of the measurement problem (all diagnosed on run 37fce30f7003, mrv x glm-5.3, PR 11059):
  v0 (original): adjudicator saw diff[:30000] + 1024 max_tokens; every unmatched finding that
     wasn't CONFIRMED a verifiable defect (conf >= 0.7) counted as "hallucination".
     -> 40 of 67 unmatched findings labeled hallucination.
  v1 (binary honest): full diff + 4096 tokens -> 16 hal / 51 real. But the rejections
     concentrated in testing-quality/completeness/scope/architecture lenses — real, specific,
     important review findings that are NOT "verifiable defects in the diff". Counting them as
     hallucinations conflates waste (fake findings) with breadth (real, useful, non-bug).
  v2 (three-way): every unmatched finding is classified as
       bug                — verifiable defect in the diff (golden-matched ones are TP)
       important_non_bug  — real, specific, grounded-in-this-diff review concern that is not a
                            defect: missing tests for new nontrivial behavior, completeness
                            gaps, scope/architecture risk. Cites specific diff code; generic
                            advice does NOT qualify.
       hallucination      — false, misreads the diff, fabricated behavior, pure style nit, vague.
     Judge instruction: plausible-but-unverifiable -> confidence < 0.5, not auto-reject.
  v3 (this tool, handoff 2026-09-08 §3C — benchmark-driven lens upgrade, adjudication
     hardening). v2's residual instability was measured, not assumed: of the 1,340 CE-confirmed
     bugs mrv also reported, mrv's own v2 adjudicator called 98 "important_non_bug" and 18
     "true_hallucination" — near-verbatim same-issue texts getting OPPOSITE verdicts across
     runs (the .env.example openssl key-length finding: identical wording, `bug` in one run,
     `true_hallucination` in another). Drivers: (i) hedged phrasing punished while assertive
     phrasing of the same mechanism is confirmed; (ii) provenance prefixes
     ([confidence:100][severity:P1], "(confidence 75, P2)", lens tags) leak into judged text;
     (iii) the same issue adjudicated independently once per run per phrasing with a
     stochastic judge. Fixes, in order of expected yield:
       1. Adjudicate once per root cause, not per phrasing: --batch clusters every unmatched
          finding across ALL runs of the batch by (PR, near-verbatim normalized text) and
          adjudicates ONE representative per cluster; members inherit the verdict. Identical
          text can no longer flip between runs by construction.
       2. Grounded hallucination: the judge must cite the specific diff line/detail that
          CONTRADICTS the finding before it may return "hallucination"; "cannot verify"
          routes to "bug" with confidence < 0.5 (the existing rule, now stated twice so it
          cannot be missed); hedged wording ("may", "could") is not evidence of falsity.
       3. Majority vote: k adjudications per cluster at temperature 0; a category with >=2
          votes wins; a 3-way disagreement triggers ONE tie-break call that sees all three
          reasonings.
       4. Provenance stripping: bracketed/prefixed confidence-severity metadata and
          lens/persona tags never enter the judged text.
       5. Flip regression suite: tests/test_readjudicate3.py (machinery, no API) and
          score_flips.py over tests/fixtures/flip_pairs.json (the frozen 116-pair flip set
          derived by extract_flip_pairs.py). ANY change to V2/V3_PROMPT must be scored against
          it; zero flips on identical text is the hard gate.
       6. --second-pass: unresolved findings (conf < 0.5 or adjudicator failure) get one
          higher-effort retry before being counted unresolved.

Accounting (unchanged from v2):
  TRUE hallucinations = "hallucination" category  -> the only waste (precision tax)
  hidden findings     = bug_ungold + important_non_bug (both are real hidden findings;
                        reported separately so bug-recall and issue-recall are distinguishable)
  precision           = TP / (TP + true_hallucinations)
  unresolved          = adjudicator failures (reported separately, never a hallucination)

Usage:
  uv run python readjudicate3.py --run <id>                     # one run (dedup within the run)
  uv run python readjudicate3.py --batch <id> [--limit N] [--dry-run]
                                                                # cross-run dedup (fix 1)
  uv run python readjudicate3.py --batch <id> --no-dedup        # v2 behavior (per-finding)
  uv run python readjudicate3.py --batch <id> --second-pass     # fix 6
Output: runs/<id>/readjudication3.json (original summaries untouched); resume-safe.
"""
from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import re
import time
from pathlib import Path

from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.model_router import call_model_json

V2_PROMPT = """You are verifying a code review finding against a PR diff. Classify the finding into exactly one category:

DIFF (unified):
```diff
{diff}
```

FINDING:
{candidate}

Categories:
- "bug": a real, verifiable defect introduced or exposed by this diff (correctness, security, data loss, broken behavior).
- "important_non_bug": a real, SPECIFIC, substantive review concern grounded in this diff that is not a defect — e.g. missing tests for newly added nontrivial logic, an incomplete migration, a scope/architecture risk created by the change. It must cite specific code in the diff. Generic advice ("add more tests", "consider refactoring") is NOT important_non_bug — that is "hallucination"-grade noise for this purpose.
- "hallucination": false, misreads the diff, references behavior that does not exist, pure style/format nit, or too vague to act on.

Rules: judge ONLY what the diff shows. If the finding is plausible but you cannot verify it from the diff, return "bug" with confidence < 0.5 rather than rejecting it.

GROUND RULES for "hallucination" (a hallucination verdict must be grounded, not a default):
- Before returning "hallucination", quote in your reasoning the specific diff line or detail that CONTRADICTS the finding. If you cannot cite a contradiction, do not return "hallucination".
- "I cannot verify this from the diff" is NOT "hallucination" — that is the unverifiable case: return "bug" with confidence < 0.5.
- Hedged wording ("may", "could", "might produce") is NOT evidence of falsity. Verify the MECHANISM the finding describes, not the confidence of its phrasing; a correctly-described mechanism stated hesitantly is the same finding as the same mechanism stated assertively.

Respond with ONLY:
{{"category": "bug|important_non_bug|hallucination", "reasoning": "brief, grounded in the diff; if the verdict is 'hallucination', quote the contradicting diff detail", "confidence": 0.0-1.0}}"""

V2_SYSTEM = "You are a strict code review verifier. Always respond with valid JSON."
TIEBREAK_PROMPT = """You are verifying a code review finding against a PR diff. Three prior verifiers disagreed:

DIFF (unified):
```diff
{diff}
```

FINDING:
{candidate}

The three prior verdicts and reasonings:
{votes}

Categories and ground rules are the same as before:
- "bug": a real, verifiable defect introduced or exposed by this diff.
- "important_non_bug": a real, SPECIFIC, substantive review concern grounded in this diff that is not a defect.
- "hallucination": false, misreads the diff, references behavior that does not exist, pure style/format nit, or too vague to act on. You must quote the specific diff line or detail that CONTRADICTS the finding before you may return it; "cannot verify" routes to "bug" with confidence < 0.5; hedged wording is not evidence of falsity.

Weigh the three reasonings against the diff itself and break the tie. Respond with ONLY:
{{"category": "bug|important_non_bug|hallucination", "reasoning": "brief, grounded in the diff; if 'hallucination', quote the contradicting detail", "confidence": 0.0-1.0}}"""

MAX_TOKENS = 4096
DIFF_LIMIT = 1_000_000  # full diff
CONF_FLOOR = 0.5  # below this, a "bug"/"important" verdict is downgraded to unresolved (unverifiable)
CLUSTER_THRESHOLD = 0.75  # difflib ratio at which two normalized texts are the same root cause

# --- Provenance stripping (fix 4) -----------------------------------------------------------
# Forms observed in the corpus: "[confidence:100][severity:P1] text", "[conf=100,P1] text",
# "text (confidence 75, P2)", "text [lens/architecture]", "[deterministic/gate-name] text".
_PROV_BRACKETS = re.compile(
    r"\[\s*(?:confidence|conf|severity|sev|anchor|effort|model|lens|persona|deterministic"
    r"|metareview-deterministic|metareview-session|compound-persona)"
    r"[^\]]*\]",
    re.IGNORECASE,
)
_PROV_BRACKET_GENERIC = re.compile(r"\[\s*conf(?:idence)?\s*[=:]\s*\d+[^\]]*\]", re.IGNORECASE)
_PROV_PAREN = re.compile(
    r"\(\s*confidence\s*[:=]?\s*\d+\s*(?:[,;]\s*(?:severity\s*[:=]?\s*)?P[0-3]\s*)?\)",
    re.IGNORECASE,
)


def strip_provenance(text: str) -> str:
    """Remove provenance metadata from a finding's text before it is judged.

    Confidence/severity anchors, lens and persona tags are bookkeeping the reviewer attached,
    not evidence about the diff — and they bias the judge twice: a high printed confidence
    nudges toward confirmation while a low one nudges toward rejection, and the tags leak which
    lens produced the finding. Stripped BEFORE clustering too, so the same issue phrased with
    different bookkeeping still lands in one cluster.
    """
    t = _PROV_BRACKETS.sub("", text or "")
    t = _PROV_BRACKET_GENERIC.sub("", t)
    t = _PROV_PAREN.sub("", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def normalize_for_cluster(text: str) -> str:
    """Fold a finding's text to the shape two phrasings of one root cause share."""
    t = strip_provenance(text).lower()
    t = re.sub(r"[`*_#]", "", t)          # markdown emphasis carries no signal
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def cluster_texts(texts: list[str], threshold: float = CLUSTER_THRESHOLD) -> list[int]:
    """Greedy near-verbatim clustering. Returns a cluster id per input (order-stable).

    Deterministic: inputs are compared in list order against already-open cluster
    representatives, so the same multiset of texts always yields the same partition. Two
    texts are the same root cause when their normalized forms are equal, or their
    difflib ratio clears `threshold`. This is what makes identical text structurally
    unable to flip: one cluster, one adjudication, one inherited verdict.
    """
    reps: list[str] = []
    out: list[int] = []
    for t in texts:
        norm = normalize_for_cluster(t)
        best, best_r = -1, 0.0
        for i, r in enumerate(reps):
            ratio = 1.0 if norm == r else difflib.SequenceMatcher(None, norm, r).ratio()
            if ratio > best_r:
                best, best_r = i, ratio
        if best >= 0 and best_r >= threshold:
            out.append(best)
        else:
            reps.append(norm)
            out.append(len(reps) - 1)
    return out


# --- Adjudication (fixes 2 + 3) --------------------------------------------------------------


async def _one_vote(judge: str, prompt: str, sem: asyncio.Semaphore, effort: str = "medium") -> dict:
    """One judge call -> {"category", "confidence", "reasoning"} or {"error": ...}."""
    async with sem:
        try:
            parsed, _, _, _ = await call_model_json(judge, V2_SYSTEM, prompt,
                                                    effort=effort, max_tokens=MAX_TOKENS)
        except Exception as e:  # network/provider failure is a vote error, not a verdict
            return {"error": f"{type(e).__name__}: {str(e)[:120]}"}
        if not parsed:
            return {"error": "unparseable-response"}
        cat = str(parsed.get("category") or "").strip().lower()
        if cat not in ("bug", "important_non_bug", "hallucination"):
            return {"error": f"bad category: {cat!r}"}
        try:
            conf = float(parsed.get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        return {"category": cat, "confidence": conf,
                "reasoning": str(parsed.get("reasoning", ""))[:600]}


def _majority(votes: list[dict]) -> dict | None:
    """k votes -> the majority verdict, or None when the votes disagree with no majority."""
    cats = [v["category"] for v in votes if "category" in v]
    if not cats:
        return None
    counts: dict[str, int] = {}
    for c in cats:
        counts[c] = counts.get(c, 0) + 1
    top, n = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
    if n * 2 > len(cats):
        members = [v for v in votes if v.get("category") == top]
        conf = sum(v["confidence"] for v in members) / len(members)
        return {"category": top, "confidence": conf,
                "reasoning": " | ".join(v["reasoning"] for v in members if v.get("reasoning"))[:600]}
    return None  # disagreement -> caller tie-breaks


async def adjudicate(candidate: str, diff: str, judge: str, sem: asyncio.Semaphore,
                     k: int = 3, second_pass_effort: str | None = None) -> dict:
    """Adjudicate one (provenance-stripped) finding: k votes at temperature 0, majority wins,
    a full disagreement gets one tie-break call that sees all three reasonings.

    Returns the v2-shaped verdict record: {"verdict", "confidence", "rationale", "votes"}.
    """
    cand = strip_provenance(candidate)
    d = diff[:DIFF_LIMIT]
    votes = list(await asyncio.gather(*[_one_vote(judge, V2_PROMPT.format(diff=d, candidate=cand), sem)
                                       for _ in range(k)]))
    merged = _majority([v for v in votes if "category" in v]) if any("category" in v for v in votes) else None
    if merged is None and any("category" in v for v in votes):
        # 3-way disagreement: one tie-break that sees every reasoning (fix 3's second half).
        vote_lines = "\n".join(
            f"- {v.get('category', 'ERROR')} (conf {v.get('confidence', 0):.2f}): {v.get('reasoning', v.get('error', ''))}"
            for v in votes)
        try:
            tb = await _one_vote(judge, TIEBREAK_PROMPT.format(diff=d, candidate=cand, votes=vote_lines),
                                 sem, effort=second_pass_effort or "high")
        except Exception as e:
            tb = {"error": f"{type(e).__name__}: {str(e)[:120]}"}
        merged = tb if "category" in tb else None
    if merged is None:
        return {"verdict": "unresolved", "confidence": None,
                "rationale": "no-majority: " + "; ".join(v.get("error", v.get("category", "?")) for v in votes)[:400],
                "votes": votes}

    cat, conf = merged["category"], merged["confidence"]
    if cat in ("bug", "important_non_bug") and conf < CONF_FLOOR:
        # prompt tells the judge: unverifiable -> low confidence. A low-confidence
        # positive is NOT evidence; count it unresolved rather than hidden gold.
        return {"verdict": "unresolved", "confidence": conf,
                "rationale": f"below CONF_FLOOR ({conf:.2f})", "votes": votes}
    return {"verdict": cat, "confidence": conf, "rationale": merged["reasoning"], "votes": votes}


async def adjudicate_second_pass(record: dict, diff: str, judge: str, sem: asyncio.Semaphore) -> dict:
    """Fix 6: one higher-effort retry for an unresolved verdict before it stays unresolved."""
    return await adjudicate(record["issue_text"], diff, judge, sem, k=1,
                            second_pass_effort="xhigh")


def latest_pass_summaries(batch: str) -> list[tuple[str, dict]]:
    best = {}
    for line in open("runs/registry.jsonl"):
        if batch not in line:
            continue
        d = json.loads(line)
        if d.get("status") != "pass" or not d.get("summary_path"):
            continue
        try:
            s = json.load(open(d["summary_path"]))
        except Exception:
            continue
        if not s.get("url"):
            continue
        best[(d["framework"], d["model"], d["effort"], s["url"])] = (d["run_id"], s)
    return sorted(best.values(), key=lambda t: t[0])


def _record_from(r: dict, verdict: dict, cluster: dict | None = None) -> dict:
    rec = {"issue_text": r["issue_text"], "source_lens": r.get("source_lens"),
           "old_verdict": r.get("primary_judge_verdict"), "new_verdict": verdict.get("verdict", "unresolved"),
           "confidence": verdict.get("confidence"), "rationale": verdict.get("rationale", ""),
           "stripped_text": strip_provenance(r["issue_text"])}
    if cluster:
        rec["cluster"] = cluster
    return rec


def _corrected_block(records: list[dict], tp: int, judge: str, diff_chars: int, wall_s: float,
                     clusters: int | None = None) -> dict:
    from collections import Counter
    n_bug = sum(1 for x in records if x["new_verdict"] == "bug")
    n_imp = sum(1 for x in records if x["new_verdict"] == "important_non_bug")
    n_hal = sum(1 for x in records if x["new_verdict"] == "hallucination")
    n_unres = sum(1 for x in records if x["new_verdict"] == "unresolved")
    flips = Counter((x["old_verdict"], x["new_verdict"]) for x in records)
    out = {
        "n_unmatched": len(records), "rejudged": len(records),
        "n_bug_ungold": n_bug, "n_important": n_imp, "n_true_hallucination": n_hal,
        "n_unresolved": n_unres,
        "n_hidden_findings_unmatched": n_bug + n_imp,
        "waste_precision": round(tp / (tp + n_hal), 4) if (tp + n_hal) else 0.0,
        "flips": {f"{a}->{b}": n for (a, b), n in sorted(flips.items())},
        "judge": judge, "diff_chars": diff_chars, "wall_s": round(wall_s, 1),
    }
    if clusters is not None:
        out["n_clusters"] = clusters
        out["dedup_savings"] = len(records) - clusters
    return out


async def classify_run(run_id: str, s: dict, concurrency: int, k: int = 3,
                       second_pass: bool = False) -> dict | None:
    """Single-run mode: dedup WITHIN the run (identical/near-verbatim texts share one verdict)."""
    out_path = Path(f"runs/{run_id}/readjudication3.json")
    if out_path.exists():
        return json.load(open(out_path))  # resume-safe
    recs = s.get("adjudication_records") or []
    unmatched = [r for r in recs if r.get("primary_judge_verdict") in ("hallucination", "real_but_ungold")]
    if not unmatched:
        return None
    url = s["url"]
    diff = fetch_diff(url)["diff"]
    judge = s.get("adjudicating_judge") or "gpt-5.2"
    tp = s["tp"]

    sem = asyncio.Semaphore(concurrency)
    t0 = time.time()
    texts = [r["issue_text"] for r in unmatched]
    cids = cluster_texts(texts)
    n_clusters = len(set(cids))
    # first occurrence per cluster is its representative — one adjudication per cluster
    rep_idx: dict[int, int] = {}
    for i, cid in enumerate(cids):
        rep_idx.setdefault(cid, i)
    representatives: dict[int, dict] = {}

    async def do_cluster(cid: int, i: int):
        representatives[cid] = await adjudicate(texts[i], diff, judge, sem, k=k)

    await asyncio.gather(*[do_cluster(cid, i) for cid, i in rep_idx.items()])
    if second_pass:
        for cid in list(representatives):
            if representatives[cid]["verdict"] == "unresolved":
                representatives[cid] = await adjudicate_second_pass(
                    {"issue_text": texts[rep_idx[cid]]}, diff, judge, sem)
    records = [_record_from(r, representatives[cid], {"id": cid, "size": cids.count(cid)})
               for r, cid in zip(unmatched, cids)]
    obj = {"run_id": run_id, "url": s.get("url"), "framework": s.get("framework"),
           "model": s.get("model"), "effort": s.get("effort"),
           "adjudicator_version": 3,
           "original": {"tp": s.get("tp"), "fn": s.get("fn"),
                        "n_real_ungold": s.get("n_real_ungold", 0),
                        "n_hallucination": s.get("n_hallucination", 0),
                        "adj_p": s.get("adjudicated_precision"), "incr": s.get("incremental_recall")},
           "corrected": _corrected_block(records, tp, judge, len(diff), time.time() - t0, n_clusters),
           "records": records}
    out_path.write_text(json.dumps(obj, indent=1))
    return obj


async def classify_batch_dedup(batch: str, targets: list[tuple[str, dict]], concurrency: int,
                               k: int = 3, second_pass: bool = False) -> None:
    """Fix 1: adjudicate once per root cause across the WHOLE batch.

    Every unmatched finding from every target run is clustered by (PR, normalized text);
    one representative per cluster is adjudicated (k-vote majority); every member record,
    in every run, inherits the cluster's verdict. The same issue phrased by two models at
    two efforts can no longer receive opposite verdicts, and the judge-call count drops by
    the dedup savings reported per run.
    """
    # 1. collect (run, record, text) per url
    by_url: dict[str, list[tuple[str, dict, str]]] = {}
    diffs: dict[str, str] = {}
    judges: dict[str, str] = {}
    for rid, s in targets:
        url = s["url"]
        diffs.setdefault(url, fetch_diff(url)["diff"])
        judges.setdefault(url, s.get("adjudicating_judge") or "gpt-5.2")
        for r in s.get("adjudication_records") or []:
            if r.get("primary_judge_verdict") in ("hallucination", "real_but_ungold"):
                by_url.setdefault(url, []).append((rid, r, r["issue_text"]))

    sem = asyncio.Semaphore(concurrency)
    t0 = time.time()
    total_calls = 0
    for url, items in sorted(by_url.items()):
        texts = [t for _, _, t in items]
        cids = cluster_texts(texts)
        n_clusters = len(set(cids))
        rep_idx: dict[int, int] = {}
        for i, cid in enumerate(cids):
            rep_idx.setdefault(cid, i)
        verdicts: dict[int, dict] = {}

        async def do_cluster(cid: int, i: int):
            verdicts[cid] = await adjudicate(texts[i], diffs[url], judges[url], sem, k=k)

        await asyncio.gather(*[do_cluster(cid, i) for cid, i in rep_idx.items() if cid not in verdicts])
        total_calls += len(rep_idx)
        if second_pass:
            for cid, v in list(verdicts.items()):
                if v["verdict"] == "unresolved":
                    verdicts[cid] = await adjudicate_second_pass({"issue_text": texts[rep_idx[cid]]},
                                                                 diffs[url], judges[url], sem)
        sizes: dict[int, int] = {}
        for cid in cids:
            sizes[cid] = sizes.get(cid, 0) + 1

        # 2. write each run's readjudication3.json with inherited verdicts
        per_run: dict[str, list[dict]] = {}
        for (rid, r, t), cid in zip(items, cids):
            per_run.setdefault(rid, []).append(_record_from(r, verdicts[cid], {"id": cid, "size": sizes[cid]}))
        for rid, records in per_run.items():
            s = next(s for r2, s in targets if r2 == rid)
            tp = s["tp"]
            out_path = Path(f"runs/{rid}/readjudication3.json")
            obj = {"run_id": rid, "url": s.get("url"), "framework": s.get("framework"),
                   "model": s.get("model"), "effort": s.get("effort"),
                   "adjudicator_version": 3, "cross_run_dedup": {"batch": batch, "url": url,
                                                                 "n_clusters": n_clusters},
                   "original": {"tp": s.get("tp"), "fn": s.get("fn"),
                                "n_real_ungold": s.get("n_real_ungold", 0),
                                "n_hallucination": s.get("n_hallucination", 0),
                                "adj_p": s.get("adjudicated_precision"), "incr": s.get("incremental_recall")},
                   "corrected": _corrected_block(records, tp, judges[url], len(diffs[url]),
                                                 time.time() - t0, n_clusters),
                   "records": records}
            out_path.write_text(json.dumps(obj, indent=1))
            c = obj["corrected"]
            print(f"  {rid[:8]} {s.get('framework', '?')[:14]}/{s.get('model', '')[:16]}"
                  f" clusters {n_clusters} for {len(records)} findings"
                  f" hal->{c['n_true_hallucination']} bug+{c['n_bug_ungold']}"
                  f" important+{c['n_important']} unres {c['n_unresolved']}", flush=True)
    print(f"[v3] {total_calls} cluster adjudications (k={k}) for {sum(len(v) for v in by_url.values())}"
          f" findings across {len(by_url)} PRs in {time.time() - t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--batch", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=15)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-dedup", action="store_true",
                    help="v2 behavior: adjudicate every finding per-run, no cross-run clustering")
    ap.add_argument("--k", type=int, default=3, help="votes per adjudication (majority wins)")
    ap.add_argument("--second-pass", action="store_true",
                    help="one higher-effort retry for unresolved verdicts before they stay unresolved")
    args = ap.parse_args()

    if args.run:
        s = json.load(open(f"runs/{args.run}/summary.json"))
        r = asyncio.run(classify_run(args.run, s, args.concurrency, k=args.k,
                                     second_pass=args.second_pass))
        print(json.dumps(r["corrected"], indent=1) if r else "nothing to classify")
        return

    if not args.batch:
        raise SystemExit("either --run or --batch required")
    targets = [(rid, s) for rid, s in latest_pass_summaries(args.batch)
               if (s.get("n_hallucination", 0) + s.get("n_real_ungold", 0)) > 0]
    if args.limit:
        targets = targets[:args.limit]
    total = sum(s.get("n_hallucination", 0) + s.get("n_real_ungold", 0) for _, s in targets)
    print(f"[v3] {len(targets)} runs, {total} unmatched findings to classify (batch {args.batch})")
    if args.dry_run:
        for rid, s in targets:
            print(f"  {rid[:8]} {s.get('framework','?')[:16]}/{s.get('model','?')[:20]}/{s.get('effort')}")
        return
    if args.no_dedup:
        for i, (rid, s) in enumerate(targets):
            out = Path(f"runs/{rid}/readjudication3.json")
            if out.exists():
                continue
            try:
                r = asyncio.run(classify_run(rid, s, args.concurrency, k=args.k,
                                             second_pass=args.second_pass))
                if r:
                    c = r["corrected"]
                    print(f"  [{i+1}/{len(targets)}] {rid[:8]} {s.get('framework','?')[:14]}/{s.get('model','')[:16]}"
                          f" hal {s.get('n_hallucination')}->{c['n_true_hallucination']}"
                          f" bug+{c['n_bug_ungold']} important+{c['n_important']}"
                          f" unres {c['n_unresolved']} ({c['wall_s']}s)", flush=True)
            except Exception as e:
                print(f"  [{i+1}/{len(targets)}] {rid[:8]} ERROR {type(e).__name__}: {str(e)[:120]}", flush=True)
        return
    asyncio.run(classify_batch_dedup(args.batch, targets, args.concurrency, k=args.k,
                                     second_pass=args.second_pass))


if __name__ == "__main__":
    main()
