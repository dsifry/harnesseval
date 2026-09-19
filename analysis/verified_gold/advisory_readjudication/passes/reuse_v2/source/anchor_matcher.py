#!/usr/bin/env python3
"""Anchor-corroborated golden matcher (AUXILIARY instrument — never the official score).

Runs alongside the frozen golden matcher (judge.py JUDGE_PROMPT, text-only).
For every golden the official matcher left unmatched, this tool:
  1. extracts location references from the golden text (paths, file:line, backticked symbols)
  2. pools candidates whose typed anchor (file:start-end) or text touches those references
  3. asks a location-aware judge: golden text + golden refs + candidate text + candidate
     anchor + the actual diff snippet at the anchor (micro-context) -> same issue?
  4. reports each official-miss with the auxiliary verdict and reasoning.

Output: never replaces the official recall. Published only as
"official X / anchor-corroborated Y" pairs.
"""
import argparse, asyncio, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.model_router import call_model_json

AUX_PROMPT = """You are a code-review evaluation auditor with LOCATION CONTEXT that the
primary text-only matcher did not have. Determine if the candidate issue matches the
golden (expected) reviewer comment.

Golden Comment (the issue we're looking for):
{golden}

Golden's location references (extracted mechanically): {grefs}

Candidate Issue (from the tool's review):
{candidate}

Candidate's validated anchor (file:start-end, machine-verified against the diff):
{anchor}

Actual diff content at the candidate's anchor (micro-context):
{snippet}

Instructions:
- Determine if the candidate identifies the SAME underlying issue as the golden comment.
- Use the location context as CORROBORATION, not as a gate: matching locations raise
  confidence; disjoint locations do not by themselves disprove a match (cause sites and
  consequence sites differ legitimately).
- Accept semantic matches — different wording is fine if it is the same problem.
- Be strict about claim DIRECTION: if the golden and the candidate describe opposite
  manifestations of a similar pattern (e.g. golden: stale grants allow revoked access;
  candidate: stale denials lock users out), that is a DIFFERENT issue — no match.

Respond with ONLY a JSON object:
{{"reasoning": "brief explanation citing the location and claim comparison", "match": true/false, "confidence": 0.0-1.0}}"""

AUX_SYSTEM = "You are a precise code review evaluation auditor. Always respond with valid JSON."

_LOC_RE = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4})(?::(\d+)(?:-(\d+))?)?")

def golden_refs(text: str) -> list[str]:
    refs = [m.group(0) for m in _LOC_RE.finditer(text)]
    ticks = re.findall(r"`([^`\n]{2,60})`", text)
    camel = [w for w in re.findall(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+\b", text) if len(w) >= 6]
    snake = [w for w in re.findall(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", text) if len(w) >= 6]
    seen, out = set(), []
    for r in refs + [t for t in ticks if len(t) > 3] + camel + snake:
        if r.lower() not in seen:
            seen.add(r.lower()); out.append(r)
    return out[:12]

def anchor_of(finding: dict) -> tuple[str, int, int] | None:
    raw = finding.get("raw") or ""
    m = re.match(r"^(.+?):(\d+)-(\d+)$", raw.strip())
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    return None

def diff_snippet(diff: str, file: str, start: int, end: int, pad: int = 6, cap: int = 40) -> str:
    """Extract diff lines for `file` whose new-side range overlaps [start-pad, end+pad]."""
    out, cur, keep = [], None, False
    newline = 0
    for line in diff.splitlines():
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            cur = m.group(1).strip()
            keep = False
            continue
        h = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line) if cur == file else None
        if h:
            hs = int(h.group(1)); he = hs + int(h.group(2) or "1") - 1
            keep = (hs <= end + pad) and (he + pad >= start)
            newline = hs - 1
            if keep:
                out.append(line)
            continue
        if keep and cur == file:
            if line.startswith("+"):
                newline += 1
            elif line.startswith(" "):
                newline += 1
            out.append(line)
        if len(out) >= cap:
            break
    return "\n".join(out[:cap]) or "(no overlapping hunk found)"

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--model", default="glm-5.3-background")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--judge", default="gpt-5.2")
    ap.add_argument("--max-candidates", type=int, default=6)
    ap.add_argument("--out", default="analysis/anchor_matcher_report.json")
    args = ap.parse_args()

    sem = asyncio.Semaphore(10)
    report = []
    runs = []
    for f in glob.glob("runs/*/summary.json"):
        try: s = json.load(open(f))
        except Exception: continue
        if (s.get("run_batch") == args.batch and s.get("framework") == "metareview-realistic"
                and s.get("model") == args.model and s.get("effort") == args.effort and s.get("url")):
            runs.append((f, s))

    async def judge_one(golden, grefs, cand, anchor, snippet):
        prompt = AUX_PROMPT.format(golden=golden, grefs=", ".join(grefs) or "(none extracted)",
                                    candidate=cand, anchor=anchor or "(none)", snippet=snippet)
        try:
            parsed, _, _, _ = await call_model_json(args.judge, AUX_SYSTEM, prompt,
                                                     effort="medium", max_tokens=400)
            return parsed
        except Exception as e:
            return {"match": False, "confidence": 0.0, "reasoning": f"error: {e}"}

    for run_path, s in runs:
        unmatched = [g for g in s.get("per_golden_matches", []) if not g.get("matched_candidate")]
        if not unmatched:
            continue
        findings = s.get("findings", [])
        diff = fetch_diff(s["url"])["diff"]
        # rj3 verdicts by issue text (for the fallback pool: only adjudicated-real bugs)
        # use the run's OWN adjacent rj3 file — never glob-scan (other batches share URLs)
        bug_verdict_texts = set()
        adj_rj3 = run_path.replace("summary.json", "readjudication3.json")
        if os.path.exists(adj_rj3):
            try:
                c = json.load(open(adj_rj3))
                for rec in c.get("records", []):
                    if rec.get("new_verdict") == "bug":
                        bug_verdict_texts.add(rec.get("issue_text"))
            except Exception:
                pass
        for g in unmatched:
            golden = g.get("golden_comment", "")
            grefs = golden_refs(golden)
            # candidate pool: anchor in a referenced file, or text contains a ref/symbol overlap
            pool = []
            for fd in findings:
                a = anchor_of(fd)
                t = fd.get("issue_text", "")
                if a and any(r.split(":")[0] == a[0] or r.split(":")[0].rstrip("0123456789-") == a[0]
                             for r in grefs if "." in r):
                    pool.append((fd, a, "anchor-in-ref"))
                elif any(r.lower() in t.lower() for r in grefs if len(r) > 4):
                    pool.append((fd, a, "text-ref"))
            if not pool:
                # fallback: pure-prose golden — pool the adjudicated-real bugs (capped)
                pool = [(fd, anchor_of(fd), "fallback-bug-verdict")
                        for fd in findings if fd.get("issue_text") in bug_verdict_texts][:args.max_candidates]
            pool = pool[:args.max_candidates]
            best = None
            best_any = None
            for fd, a, why in pool:
                snippet = diff_snippet(diff, a[0], a[1], a[2]) if a else ""
                async with sem:
                    v = await judge_one(golden, grefs, fd.get("issue_text", ""),
                                        f"{a[0]}:{a[1]}-{a[2]}" if a else None, snippet)
                if best_any is None or (v.get("confidence", 0) > best_any[0].get("confidence", 0)):
                    best_any = (v, fd, a, why)
                if v.get("match") and (best is None or (v.get("confidence", 0) > best[0].get("confidence", 0))):
                    best = (v, fd, a, why)
            shown = best or best_any
            report.append({
                "pr": s["url"].rstrip("/").rsplit("/", 1)[-1],
                "category": g.get("category"), "severity": g.get("severity"),
                "golden": golden[:160],
                "pool_size": len(pool),
                "pool_reason": pool[0][2] if pool else "none",
                "aux_match": bool(best),
                "aux_confidence": shown[0].get("confidence") if shown else None,
                "aux_reasoning": shown[0].get("reasoning") if shown else None,
                "candidate": shown[1].get("issue_text", "")[:160] if shown else None,
                "anchor": (f"{shown[2][0]}:{shown[2][1]}-{shown[2][2]}" if shown and shown[2] else None),
            })
            print(f"PR {report[-1]['pr']:>6s} [{g.get('category')}] pool={len(pool)} "
                  f"aux_match={report[-1]['aux_match']} conf={report[-1]['aux_confidence']}", flush=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(report, open(args.out, "w"), indent=1)
    n = len(report); m = sum(1 for r in report if r["aux_match"])
    print(f"\nAUX REPORT: {m}/{n} official-missed goldens got an anchor-corroborated match "
          f"(auxiliary only — official recall unchanged)")

if __name__ == "__main__":
    asyncio.run(main())
