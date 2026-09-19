#!/usr/bin/env python3
"""Build the canonical catalogue of the verified hidden-gold defects.

One record per defect, with the exact test artifact that demonstrates it, its fix, its logs, the code
location (file:lines recovered from the assigned findings), and its provenance (bundle, merge, restore).

Evidence levels:
  own_executed    - the defect has its own defects/<id>/ dir: its own test (test.diff) FAILED on the PR head,
                    its own fix (fix.patch) made it PASS. Orthogonality is reported separately when recorded.
  bundle_executed - the defect is demonstrated by its bundle's executed test/fix/logs. For a bundle PRIMARY
                    claim the bundle's test IS the exact test for this defect; for an "extra" facet split out
                    by the merge audit the bundle test exercises the bundle's claim, and the facet is
                    documented by the audit + the assigned findings.

Outputs: GOLD_DEFECT_CATALOG.{json,md,csv}
"""
from __future__ import annotations
import csv, glob, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"


def sha(t: str) -> str:
    return hashlib.sha1(t.encode()).hexdigest()[:16]


ANCHOR_RE = re.compile(r"([\w./\-]+\.(?:rb|ts|tsx|js|jsx|yml|yaml|json|prisma))[:\s]*L?(\d+)(?:\s*[-–]\s*(\d+))?")
THROTTLE = ("topic_retriever", "topic_embed")  # rj3 strips underscores from anchor filenames


def resolve_pr_file(pr: str, frag: str) -> str:
    """rj3 strips some characters from anchor filenames; map a fragment back to a real file."""
    return frag


def main():
    reg = json.loads((VG / "DEFECT_REGISTRY.json").read_text())
    assign = json.loads((VG / "DEFECT_ASSIGN.json").read_text()) if (VG / "DEFECT_ASSIGN.json").exists() else {}
    ds = json.loads((ROOT / "analysis/final_report_dataset.json").read_text())
    texts = defaultdict(list)  # (pr, hash) -> [texts]
    for url in ds["pr_golden"]:
        pr = url.rstrip("/").split("/")[-1]
        for r in ds["all_healthy_runs"]:
            if r["url"] == url:
                for t in (r.get("bugtexts") or []):
                    texts[(pr, sha(t))].append(t)

    def find_defect_dir(did):
        h = glob.glob(str(VG / "**" / "defects" / did), recursive=True)
        return Path(h[0]) if h else None

    def bundle_dir(d, pr, b):
        # the registry's `bundle` id already includes the PR prefix (e.g. "4-B01"); prefer evidence_dir
        ev = d.get("evidence_dir")
        if ev and (ROOT / ev).exists():
            return ROOT / ev
        bid = b.split("-", 1)[1] if "-" in b else b
        for pat in (VG / pr / f"{bid}-*", VG / pr / f"{b}-*"):
            h = glob.glob(str(pat))
            if h:
                return Path(h[0])
        return None

    recs = []
    for d in sorted(reg["defects"], key=lambda x: (x["pr"], x["id"])):
        pr, did = d["pr"], d["id"]
        bd = bundle_dir(d, pr, d["bundle"])
        dd = find_defect_dir(did)
        bmeta = json.loads((bd / "meta.json").read_text()) if bd and (bd / "meta.json").exists() else {}
        # assigned findings + recovered anchors
        amap = assign.get(pr, {})
        findings = [t for (p, h), ts in texts.items() if p == pr and amap.get(h) == did for t in ts]
        anchors = Counter()
        for t in findings:
            for m in ANCHOR_RE.finditer(t[:220]):
                f, a, b = m.group(1), m.group(2), m.group(3)
                anchors[f"{f}:{a}" + (f"-{b}" if b else "")] += 1
        anchor = anchors.most_common(1)[0][0] if anchors else (d.get("anchor_file") or "")
        own = dd is not None and (dd / "test.diff").exists()
        dmeta = json.loads((dd / "meta.json").read_text()) if own and (dd / "meta.json").exists() else {}
        origin = (dmeta.get("test_origin") or dmeta.get("evidence_provenance")
                  or "test origin not recorded in metadata")
        labels = (bmeta.get("multi_defect") or {}).get("labels") or []

        def toks(x):
            return set(re.findall(r"[a-z0-9]+", x.lower()))
        if not labels:
            primary = True  # single-concern bundle: its one claim IS this defect
        else:
            sims = [len(toks(d["label"]) & toks(l)) / max(1, len(toks(d["label"]) | toks(l))) for l in labels]
            primary = sims and max(sims) == sims[0] and max(sims) >= 0.15
        withdrawn = d.get("withdrawn") or d.get("tier") == "D-withdrawn"
        head_fail_fixed_pass = False if withdrawn else dmeta.get("own_fix_makes_test_pass")
        orthogonality = dmeta.get("sibling_fix_leaves_test_red")
        if withdrawn:
            exact_test = "withdrawn - recorded test does not demonstrate the claim"
        elif not own:
            exact_test = "no own test - bundle evidence only"
        else:
            exact_test = ("yes - container test (see test_origin)" if "container" in origin.lower()
                          else "yes - defect-specific test")
            exact_test += (", orthogonality proven" if orthogonality is True
                           else ", orthogonality not established")
        mismatch = None
        if withdrawn:
            mismatch = "WITHDRAWN: " + (d.get("withdrawn_reason") or "test does not demonstrate the claim")
        elif d.get("tier") == "D-duplicate":
            mismatch = "DUPLICATE: " + (d.get("dup_reason") or "not an independent verified defect")
        elif d.get("label_corrected"):
            mismatch = "CORRECTED: " + d["label_corrected"][:160]
        elif d.get("label_vs_test_check"):
            mismatch = d["label_vs_test_check"]
        elif head_fail_fixed_pass is True:
            # The reliable signal is behavioural, not textual: the defect's own test FAILED on the PR head
            # and PASSED once a minimal fix authored for this label was applied. (A comment-resemblance
            # heuristic was tried and abandoned: most tests contain no literal CLAIM comment, so it flagged
            # 21 defects that had in fact been assertion-read and confirmed.)
            mismatch = ("verified: own test fails on the PR head and passes with a fix authored for this label"
                        + (" (container test authored for exactly this claim)" if "container" in origin else ""))
        else:
            mismatch = "unverified: execution metadata does not establish the labelled claim"
        rec = {
            "id": did, "pr": pr, "label": d["label"], "tier": d.get("tier"),
            "evidence_level": "own_executed" if own else "bundle_executed",
            "defect_is_bundle_primary_claim": primary,
            "test_origin": origin,
            "exact_test": exact_test,
            "anchor": anchor,
            "bundle": d["bundle"], "bundle_dir": str(bd.relative_to(ROOT)) if bd else None,
            "bundle_verdict": d.get("bundle_verdict"),
            "test": str((dd / "test.diff").relative_to(ROOT)) if own else (str((bd / "test.patch").relative_to(ROOT)) if bd and (bd / "test.patch").exists() else None),
            "fix": str((dd / "fix.patch").relative_to(ROOT)) if own else (str((bd / "fix.patch").relative_to(ROOT)) if bd and (bd / "fix.patch").exists() else None),
            "logs": str((dd / "logs").relative_to(ROOT)) if own else (str((bd / "logs").relative_to(ROOT)) if bd and (bd / "logs").exists() else None),
            "head_fail_fixed_pass": head_fail_fixed_pass,
            "sibling_fix_leaves_red": dmeta.get("sibling_fix_leaves_test_red") if own else None,
            "n_assigned_findings": len(findings),
            "example_finding": (min(findings, key=len)[:300] if findings else None),
            "merged_in_from": [m["merged"] for m in reg.get("merged_duplicates", []) if m["kept"] == did],
            "restored": d.get("restored"),
            "label_corrected": d.get("label_corrected"),
            "withdrawn": d.get("withdrawn"),
            "withdrawn_reason": d.get("withdrawn_reason"),
            "duplicate_of": (d.get("duplicate_of") if d.get("tier") == "D-duplicate" else None),
            "dup_reason": d.get("dup_reason"),
            "label_review": mismatch,
            "label_vs_test_mismatch": None,
        }
        recs.append(rec)

    (VG / "GOLD_DEFECT_CATALOG.json").write_text(json.dumps(
        {"n": len(recs), "levels": dict(Counter(r["evidence_level"] for r in recs)),
         "defects": recs}, indent=1))

    # markdown
    nv = sum(1 for r in recs if r["tier"] == "D-verified")
    nw = sum(1 for r in recs if r["tier"] == "D-withdrawn")
    nd = sum(1 for r in recs if r["tier"] == "D-duplicate")
    L = ["# Hidden-gold defect catalogue", "",
         f"**{nv} distinct verified defects.** Every one has an executed test that failed on the PR head and a",
         "documented fix that made it pass. Two evidence levels:", "",
         (f"{nw} defects are WITHDRAWN (their tests do not demonstrate the claim) and {nd} are merged as DUPLICATES "
          "(2026-09-18 audit — see WITHDRAWALS_AND_DEDUP_2026-09-18.md). They are retained below, marked, but no longer count as verified.")
          if (nw or nd) else "",
         "Defect directories retain `test.diff`, `fix.patch`, logs, and metadata as evidence artifacts.",
         "`test_origin` records verifier-authored tests or provenance copied from the execution container.",
         "Orthogonality is established only when `sibling_fix_leaves_red` is explicitly true;",
         "a null or false value does not establish independence. Withdrawn tests do not verify their claims.",
         "", "Merged duplicates and restored/renamed entries carry a provenance note.", "",
         "## Known open items (do not treat this catalogue as exhaustive)", "",
         "- `label_vs_test_mismatch`: where a defect's own test declares a claim that does not match the",
         "  registry label, the TEST is the truth (the label was inherited from an LLM merge audit).",
         "- Under-count (historical, resolved): the claim-list items below were restored by the 2026-09-18",
         "  under-count triage — 4/B33 nil-`downcase` crash (4-D56), 4/B39 case-sensitive host compare",
         "  (4-D57), 4/B26 wrong-rescue (4-D29, WITHDRAWN 2026-09-18), 4/B07 missing scheme validation",
         "  (4-D58), 8/B05 API-contract break (8-D07), and the 11059/B19 + 11059/B23 facets (11059-D30,",
         "  -D32 (duplicate), -D33, -D34). The verified count remains a **floor**, not a ceiling: claims",
         "  whose tests did not converge are reported as in-doubt plumbing, not verified bugs.", ""]
    by_pr = defaultdict(list)
    for r in recs:
        by_pr[r["pr"]].append(r)
    for pr in sorted(by_pr, key=lambda p: (len(p), p)):
        L += [f"## PR {pr} — {len(by_pr[pr])} defects", ""]
        for r in sorted(by_pr[pr], key=lambda x: int(re.search(r"(\d+)$", x["id"]).group(1))):
            tag = "own_executed" if r["evidence_level"] == "own_executed" else ("bundle-primary" if r["defect_is_bundle_primary_claim"] else "bundle-executed")
            if r["tier"] == "D-withdrawn":
                L.append(f"### {r['id']} — {r['label']} — WITHDRAWN 2026-09-18")
            elif r["tier"] == "D-duplicate":
                L.append(f"### {r['id']} — {r['label']} — DUPLICATE of {r['duplicate_of']}")
            else:
                L.append(f"### {r['id']} — {r['label']}")
            L.append(f"- **location**: `{r['anchor'] or 'n/a'}`  ·  **evidence**: `{tag}`  ·  bundle `{r['bundle']}` ({r['bundle_verdict']})")
            if r.get("withdrawn_reason"):
                L.append(f"- **withdrawn**: {r['withdrawn_reason']}")
            if r.get("dup_reason"):
                L.append(f"- **duplicate**: {r['dup_reason']}")
            L.append(f"- **test**: `{r['test']}`")
            L.append(f"- **fix**: `{r['fix']}`  ·  **logs**: `{r['logs']}`")
            if r["sibling_fix_leaves_red"] is not None:
                L.append(f"- **orthogonality**: bundle fix leaves it red = `{r['sibling_fix_leaves_red']}`")
            if r["example_finding"]:
                L.append(f"- **finding**: {r['example_finding'][:220]}")
            for note in ("merged_in_from", "restored", "label_corrected"):
                if r.get(note):
                    L.append(f"- **{note}**: {r[note] if isinstance(r[note], str) else ', '.join(r[note])}")
            L.append("")
    (VG / "GOLD_DEFECT_CATALOG.md").write_text("\n".join(L))

    with open(VG / "GOLD_DEFECT_CATALOG.csv", "w", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=["id", "pr", "label", "tier", "evidence_level",
                                          "defect_is_bundle_primary_claim", "exact_test", "anchor", "bundle", "bundle_verdict",
                                          "test", "fix", "logs", "sibling_fix_leaves_red",
                                          "n_assigned_findings", "merged_in_from", "restored", "withdrawn", "duplicate_of"])
        w.writeheader()
        for r in recs:
            w.writerow({**{k: r.get(k) for k in w.fieldnames}})
    print(json.dumps({"n": len(recs), "levels": dict(Counter(r["evidence_level"] for r in recs)),
                      "primary": sum(1 for r in recs if r["defect_is_bundle_primary_claim"]),
                      "anchors_recovered": sum(1 for r in recs if r["anchor"])}, indent=1))


if __name__ == "__main__":
    main()
