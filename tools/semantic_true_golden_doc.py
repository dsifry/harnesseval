#!/usr/bin/env python3
"""Compile the True Golden Set evidence pack into a human-auditable markdown doc.

Reads analysis/semantic_true_golden_<pr>.json (verification cards, tools/semantic_union_evidence.py)
plus the pilot cluster maps, and writes analysis/TRUE_GOLDEN_EVIDENCE.md:

  - methodology + provenance header
  - per-PR summary table (goldens vs true-set size, coverage stats)
  - per-PR coverage matrix: which cells found which bugs (compact)
  - the full bug list: every distinct real bug with file:startline-endline, why_real
    (cites code), replication steps, severity, and the exact models/frameworks/efforts
    that found it — so a human can open the code, reproduce the bug, and verify both
    the bug and any reviewer's claim to have found it.

Usage: .venv/bin/python tools/semantic_true_golden_doc.py
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ["11059", "4", "10", "8", "14740", "10967"]
PR_FULL = {
    "11059": "https://github.com/calcom/cal.com/pull/11059",
    "4": "https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4",
    "10": "https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10",
    "8": "https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8",
    "14740": "https://github.com/calcom/cal.com/pull/14740",
    "10967": "https://github.com/calcom/cal.com/pull/10967",
}
SHORT = {"claude-fable-5-1": "fable", "claude-opus-5": "opus", "claude-sonnet-5": "sonnet",
         "glm-5.3-flash-background": "glm-flash", "glm-5.3-vision-background": "glm-vis",
         "gpt-5.6-sol": "sol", "gpt-5.6-terra": "terra", "gpt-6-astra": "astra"}
FWS = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV"}


def cells_found_str(found_by):
    parts = []
    by_model = defaultdict(list)
    for c in found_by:
        m, fw, e = c.split("|")
        by_model[m].append(f"{FWS[fw]}·{e}")
    for m in sorted(by_model):
        parts.append(f"{SHORT.get(m, m[:10])}: {', '.join(sorted(by_model[m]))}")
    return "; ".join(parts) if parts else "(none)"


def main():
    L = []
    A = L.append
    total_cards = total_nd = 0
    per_pr = {}
    for s in SLUGS:
        d = json.load(open(ROOT / f"analysis/semantic_true_golden_{s}.json"))
        per_pr[s] = d
        total_cards += d["n_clusters"]
        total_nd += sum(1 for c in d["cards"] if not c.get("distinct", True))

    A("# The True Golden Set — evidence pack (top-6 PRs)")
    A("")
    A("**What this is.** For each of the six hardest benchmark PRs, every confirmed-bug finding from")
    A("the ENTIRE campaign (all models × frameworks × efforts; 2,416 healthy runs) was deduplicated")
    A("by an LLM judge into distinct REAL bugs. Every finding admitted here passed the adjudication")
    A("gate first — hallucinations and important_non_bug (nitpick) findings were excluded before")
    A("clustering. The result is the **true golden set**: the full upper bound of actual bugs in these")
    A("PRs, including everything the original Martian golden set missed.")
    A("")
    A(f"**Counts.** {total_cards} distinct real bugs across the 6 PRs (vs 42 goldens).")
    A(f"**Verification.** Each bug below carries a judge-produced verification card: location")
    A(f"(file:startline–endline, post-PR line numbers), a why-real explanation quoting the offending")
    A("code, and concrete replication steps. 10 cards are flagged `distinct=false` (the cluster may")
    A("contain two bugs) — kept for transparency. Open the code at the cited lines and follow the")
    A("replication steps to verify for yourself that this is a real bug, not a hallucination.")
    A("")
    A("**Provenance.** Clustering: judge gpt-5.2, file-grouped `dedup_bugs_llm` prompt (branch")
    A("`sdlc-loop-experiment`), chunked per-file + cross-file merge to fixpoint; artifacts")
    A("`analysis/exp_union_semantic_pilot_<pr>.json` (2026-09-17, rj3-fixed dataset). Verification")
    A("cards: judge gpt-5.2 grounded in the PR patch (`gh`-cached diffs); artifacts")
    A("`analysis/semantic_true_golden_<pr>.json`. LLM steps are not deterministic; the stored")
    A("artifacts are the record. Adjudication verdicts (the gate) are the frozen rj3/in-run")
    A("instruments and are untouched.")
    A("")
    A("| PR | goldens | true bugs | findings clustered | cells that found ≥1 |")
    A("|---|---|---|---|---|")
    for s in SLUGS:
        d = per_pr[s]
        pilot = json.load(open(ROOT / f"analysis/exp_union_semantic_pilot_{s}.json"))
        ncells = len({c for card in d["cards"] for c in card["found_by"]})
        A(f"| [{s}]({PR_FULL[s]}) | {pilot['goldens']} | **{d['n_clusters']}** | {pilot['n_findings']:,} | {ncells} |")
    A("")

    for s in SLUGS:
        d = per_pr[s]
        pilot = json.load(open(ROOT / f"analysis/exp_union_semantic_pilot_{s}.json"))
        A("---")
        A("")
        A(f"## PR {s} — {d['n_clusters']} distinct real bugs ({pilot['goldens']} goldens + "
          f"{d['n_clusters'] - pilot['goldens']} the goldens missed)")
        A(f"(<{PR_FULL[s]}>)")
        A("")
        A("### Bug index")
        A("")
        A("| # | sev | location | title | found by (cells) |")
        A("|---|---|---|---|---|")
        for i, c in enumerate(d["cards"], 1):
            f_ = c.get("file") or "?"
            loc = f"`{f_}:{c['startline']}–{c['endline']}`" if c.get("startline") else f"`{f_}`"
            title = (c.get("title") or "(untitled)").replace("|", "\\|")
            A(f"| B{i} | {c.get('severity','?')} | {loc} | {title} | {c['n_cells']} |")
        A("")
        A("### Verification cards")
        A("")
        for i, c in enumerate(d["cards"], 1):
            A(f"#### B{i} — {(c.get('title') or '(untitled)')}")
            A("")
            f_ = c.get("file") or "?"
            loc = (f"**Location:** `{f_}:{c['startline']}–{c['endline']}`"
                   if c.get("startline") else f"**Location:** `{f_}` (exact lines not in diff)")
            A(loc + f"  ·  **Severity:** {c.get('severity','?')}  ·  **Judge confidence:** {c.get('confidence',0):.2f}"
              + ("  ·  ⚠️ `distinct=false` (cluster may span two bugs)" if not c.get("distinct", True) else ""))
            A("")
            A(f"**Why this is real.** {c.get('why_real','(missing)')}")
            A("")
            if c.get("replication"):
                A(f"**How to replicate.** {c.get('replication','')}")
                A("")
            A(f"**Found by** {c['n_cells']} cells ({c['n_reports']} distinct report texts, "
              f"{c['n_findings']} findings): {cells_found_str(c['found_by'])}")
            A("")

    out = ROOT / "analysis/TRUE_GOLDEN_EVIDENCE.md"
    out.write_text("\n".join(L))
    print(f"wrote {out} ({len(L)} lines)")


if __name__ == "__main__":
    main()
