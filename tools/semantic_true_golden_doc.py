#!/usr/bin/env python3
"""Compile the VERIFIED true-golden-set evidence pack (§10c) into a human-auditable doc.

Reads:
  analysis/semantic_true_golden_verify_<pr>.json   re-merged groups (raw→group mapping)
  analysis/semantic_overlap_locked_<pr>.json       locked status: golden-overlap vs additional
  analysis/semantic_true_golden_<pr>.json          per-raw-cluster verification cards
  analysis/exp_union_semantic_pilot_<pr>.json      raw cluster membership
Writes analysis/TRUE_GOLDEN_EVIDENCE.md:
  - methodology + provenance (adjudication gate → semantic merge → stricter re-merge →
    finding-level golden-overlap → lock/tie-break)
  - per PR: bug index (GOLDEN-duplicate vs verified-additional), verification cards for the
    additional bugs, and the golden-duplicates that were REMOVED (with the golden they duplicate)
  - harness blind spots: verified additional bugs found by no harness cell
Usage: .venv/bin/python tools/semantic_true_golden_doc.py
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ["11059", "4", "10", "8", "14740", "10967"]
PR_FULL = {"11059": "https://github.com/calcom/cal.com/pull/11059",
           "4": "https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4",
           "10": "https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10",
           "8": "https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8",
           "14740": "https://github.com/calcom/cal.com/pull/14740",
           "10967": "https://github.com/calcom/cal.com/pull/10967"}
SHORT = {"claude-fable-5-1": "fable", "claude-opus-5": "opus", "claude-sonnet-5": "sonnet",
         "glm-5.3-flash-background": "glm-flash", "glm-5.3-vision-background": "glm-vis",
         "gpt-5.6-sol": "sol", "gpt-5.6-terra": "terra", "gpt-6-astra": "astra"}
FWS = {"vanilla-engineered": "van", "compound-realistic": "CE", "metareview-realistic": "MRV"}
HARNESS = {"compound-realistic", "metareview-realistic"}


def goldens_for(pr):
    import glob
    for f in (glob.glob(f"{ROOT}/analysis/inputs/golden_comments/*.json")
              or glob.glob(f"{ROOT}/third_party/code-review-benchmark/offline/golden_comments/*.json")):
        for e in json.load(open(f)):
            if e["url"] == pr:
                return [c["comment"] for c in e["comments"]]
    return []


def cells_str(found_by):
    by = defaultdict(list)
    for c in found_by:
        m, fw, e = c.split("|")
        if fw not in HARNESS:
            continue
        by[m].append(f"{FWS[fw]}·{e}")
    if not by:
        v = sorted({f"{SHORT.get(c.split('|')[0], c.split('|')[0])}"
                    for c in found_by if c.split('|')[1] == 'vanilla-engineered'})
        return "**no harness cell** — vanilla only: " + (", ".join(v) if v else "none")
    return "; ".join(f"{SHORT.get(m, m)}: {', '.join(sorted(by[m]))}" for m in sorted(by))


def main():
    L = []
    A = L.append
    per = {}
    for s in SLUGS:
        v = json.load(open(ROOT / f"analysis/semantic_true_golden_verify_{s}.json"))
        lock = json.load(open(ROOT / f"analysis/semantic_overlap_locked_{s}.json"))
        cards = {c["cluster"]: c for c in json.load(open(ROOT / f"analysis/semantic_true_golden_{s}.json"))["cards"]}
        goldens = goldens_for(PR_FULL[s])
        groups = []
        for gi, vc in enumerate(v["clusters"]):
            lc = lock["clusters"][gi] if gi < len(lock["clusters"]) else {}
            member_cards = [cards[r] for r in vc["merge_group"] if r in cards]
            best = max(member_cards, key=lambda c: (c.get("confidence") or 0, c.get("n_findings") or 0)) if member_cards else None
            groups.append({"gi": gi, "golden": lc.get("locked_golden"), "card": best,
                           "n_findings": vc["n_findings"], "n_cells": vc["n_cells"],
                           "found_by": vc["found_by"], "example": vc["example"]})
        per[s] = {"groups": groups, "goldens": goldens,
                  "n_over": sum(1 for g in groups if g["golden"] is not None)}
    tot_g = sum(len(p["goldens"]) for p in per.values())
    tot_add = sum(len(p["groups"]) - p["n_over"] for p in per.values())
    tot_over = sum(p["n_over"] for p in per.values())

    A("# The True Golden Set — verified evidence pack (§10c)")
    A("")
    A("**What this is.** Every confirmed-bug finding from the whole campaign (all models × frameworks ×")
    A("efforts; 2,416 healthy runs) on the six hardest PRs, taken through: (1) the adjudication gate")
    A("(hallucinations and important_non_bug excluded), (2) an LLM semantic merge of same-defect")
    A("paraphrases, (3) a stricter whole-PR re-merge with the same judge, (4) a **finding-level**")
    A("golden-overlap check — a cluster is a duplicate of a golden only if a single member finding is")
    A("that golden's exact defect — and (5) a strict tie-break of low-confidence overlaps.")
    A("")
    A(f"**Verified set: {tot_g} goldens + {tot_add} additional real bugs = {tot_g + tot_add} distinct bugs.**")
    A(f"{tot_over} clusters were verified duplicates of a golden and are **excluded** from the additional set")
    A("(counting them would double-count: the golden is already in the denominator). Every additional bug")
    A("below carries a judge-produced verification card: location (`file:start–end`), a why-real")
    A("explanation quoting the code, replication steps, and the exact cells that found it. Bugs found by")
    A("**no harness cell** are called out — those are the blind spots, and they are a different class of")
    A("defect (performance, test quality, framework idioms) than the correctness/security bugs the lenses")
    A("target. Residual under-merge or mis-attribution is possible; the artifacts are the record.")
    A("")
    A("**Provenance.** Judges: gpt-5.2, 2026-09-17. Artifacts: `analysis/exp_union_semantic_pilot_<pr>.json`")
    A("(semantic merge), `analysis/semantic_true_golden_verify_<pr>.json` (re-merge + first-pass overlap),")
    A("`analysis/semantic_overlap_finding_<pr>.json` (finding-level), `analysis/semantic_overlap_locked_<pr>.json`")
    A("(locked status), `analysis/semantic_true_golden_<pr>.json` (cards). Adjudication verdicts are the")
    A("frozen instruments and are untouched. LLM steps are not deterministic; the stored artifacts are the")
    A("record.")
    A("")
    A("| PR | goldens | verified additional | verified universe | clusters merged | golden-duplicates removed |")
    A("|---|---|---|---|---|---|")
    for s in SLUGS:
        p = per[s]
        A(f"| [{s}]({PR_FULL[s]}) | {len(p['goldens'])} | **{len(p['groups']) - p['n_over']}** | "
          f"{len(p['goldens']) + len(p['groups']) - p['n_over']} | {len(p['groups'])} | {p['n_over']} |")
    A(f"| **total** | **{tot_g}** | **{tot_add}** | **{tot_g + tot_add}** | "
      f"{sum(len(p['groups']) for p in per.values())} | {tot_over} |")
    A("")

    # harness blind spots
    blinds = [(s, g) for s in SLUGS for g in per[s]["groups"]
              if g["golden"] is None and not {x.split("|")[1] for x in g["found_by"]} & HARNESS]
    A(f"## Harness blind spots — {len(blinds)} verified bugs no harness cell found")
    A("")
    for s, g in blinds:
        c = g["card"] or {}
        A(f"- **[{s}] {c.get('title', g['example'][:90])}** — `{c.get('file','?')}`"
          + (f":{c.get('startline')}–{c.get('endline')}" if c.get("startline") else "")
          + f" · {g['n_findings']} findings, {g['n_cells']} cells (vanilla only)")
    A("")

    for s in SLUGS:
        p = per[s]
        add = [g for g in p["groups"] if g["golden"] is None]
        over = [g for g in p["groups"] if g["golden"] is not None]
        A("---")
        A("")
        A(f"## PR {s} — {len(add)} additional real bugs ({len(p['goldens'])} goldens; "
          f"{len(over)} golden-duplicates removed)")
        A(f"(<{PR_FULL[s]}>)")
        A("")
        A("### Additional bugs (evidence cards)")
        A("")
        for i, g in enumerate(add, 1):
            c = g["card"] or {}
            f_ = c.get("file") or "?"
            loc = f"`{f_}:{c.get('startline')}–{c.get('endline')}`" if c.get("startline") else f"`{f_}`"
            hc = {x.split("|")[1] for x in g["found_by"]}
            blind = "" if hc & HARNESS else " · ⚠️ **no harness cell found this**"
            A(f"#### A{i} — {c.get('title','(untitled)')}")
            A("")
            A(f"**Location:** {loc}  ·  **Severity:** {c.get('severity','?')}  ·  "
              f"**Judge confidence:** {(c.get('confidence') or 0):.2f}  ·  {g['n_findings']} findings, "
              f"{g['n_cells']} cells{blind}")
            A("")
            if c.get("why_real"):
                A(f"**Why this is real.** {c['why_real']}")
                A("")
            if c.get("replication"):
                A(f"**How to replicate.** {c['replication']}")
                A("")
            A(f"**Found by:** {cells_str(g['found_by'])}")
            A("")
        A("### Golden-duplicates removed (would double-count)")
        A("")
        if not over:
            A("(none)")
            A("")
        for g in over:
            c = g["card"] or {}
            A(f"- **duplicate of golden #{g['golden']}** — “{p['goldens'][g['golden']][:160]}…”")
            A(f"  - cluster: {c.get('title','(untitled)')} (`{c.get('file','?')}`), "
              f"{g['n_findings']} findings, {g['n_cells']} cells")
        A("")

    out = ROOT / "analysis/TRUE_GOLDEN_EVIDENCE.md"
    out.write_text("\n".join(L))
    print(f"wrote {out} ({len(L)} lines, {tot_add} additional bugs, {tot_over} golden-duplicates)")


if __name__ == "__main__":
    main()
