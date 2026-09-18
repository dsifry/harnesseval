#!/usr/bin/env python3
"""Build the canonical DEFECT registry (individual bugs) out of the verified bundles.

Why: a bundle is a cluster, not a bug. Some bundles are over-merged (the merge audit found 2-4 distinct
defects inside 28 of them) and some duplicate each other, so per-run credit computed per bundle is wrong
in both directions. This emits one record per DEFECT with a stable id, its label, its anchor, the bundle
that carries its evidence, and whether that defect is *individually* evidence-backed or only audited.

Tiers:
  D-verified  the defect is the one an executed test+fix demonstrates (fails pre-fix, passes post-fix)
  D-labelled  the merge audit split it out of a multi-concern cluster (judge labels over the findings);
              it has findings but no dedicated test yet

Writes analysis/verified_gold/DEFECT_REGISTRY.{json,md}.
Usage: .venv/bin/python tools/verified_gold_defect_registry.py
"""
from __future__ import annotations
import glob, json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VG = ROOT / "analysis/verified_gold"
INCLUDE = {"confirmed_regression", "behavior_change_not_regression", "duplicate_of"}
ANY = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]{1,4}):(\d+)(?:-(\d+))?")


def toks(s):
    return {w for w in re.findall(r"[a-z0-9]{4,}", (s or "").lower())}


def jac(a, b):
    ta, tb = toks(a), toks(b or "")
    return len(ta & tb) / max(1, len(ta | tb))


def bundle_anchor(m):
    pr = m["bug_id"].split("-")[0]
    idx = int(m["bug_id"].split("B")[1])
    try:
        v = json.load(open(VG.parent / f"analysis/semantic_true_golden_verify_{pr}.json"))
        pil = json.load(open(VG.parent / f"analysis/exp_union_semantic_pilot_{pr}.json"))
        D = json.load(open(VG.parent / "analysis/final_report_dataset.json"))
        f2c = {int(a): b for a, b in pil["finding_to_cluster"].items()}
        runs = [r for r in D["all_healthy_runs"] if r["url"] == pil["pr"]]
        flat = [t for r in runs for t in (r.get("bugtexts") or [])]
        mem = defaultdict(list)
        for i, t in enumerate(flat):
            mem[f2c[i]].append(t)
        texts = [t for g in v["clusters"][idx]["merge_group"] for t in mem[g]]
    except Exception:
        texts = []
    sp = defaultdict(Counter := __import__("collections").Counter)
    for t in texts:
        for m2 in ANY.finditer(t):
            sp[m2.group(1)][(int(m2.group(2)), int(m2.group(3) or m2.group(2)))] += 1
    if sp:
        f = max(sp, key=lambda k: sum(sp[k].values()))
        rng = sorted(sp[f], key=lambda se: -sp[f][se])[:3]
        return f, ", ".join(f"{s}-{e}" if s != e else str(s) for s, e in rng)
    c = m.get("candidate") or {}
    return (c.get("file_resolved") or c.get("file") or "?"), ""


def main():
    audit = {r["bug_id"]: r for r in json.load(open(VG / "MERGE_AUDIT.json"))["results"]}
    rows = []
    for f in sorted(glob.glob(str(VG / "*/*/meta.json"))):
        m = json.load(open(f))
        if m.get("verdict") not in INCLUDE:
            continue
        bid, pr = m["bug_id"], m["bug_id"].split("-")[0]
        c = m.get("candidate") or {}
        a = audit.get(bid) or {}
        n = a.get("n_distinct") or 1
        labels = [l for l in (a.get("distinct_defects") or []) if l] if n > 1 else [str(c.get("title"))[:140]]
        anchor_file, anchor_lines = bundle_anchor(m)
        d = Path(f).parent
        rows.append({"bundle": bid, "pr": pr, "verdict": m.get("verdict"),
                     "duplicate_of": (m.get("duplicate_of") or {}).get("bug_id"),
                     "labels": labels, "n_distinct": len(labels),
                     "anchor_file": anchor_file, "anchor_lines": anchor_lines,
                     "test": (d / "test.diff").exists() or (d / "test.patch").exists(),
                     "fix": (d / "fix.patch").exists(),
                     "evidence_dir": str(d.relative_to(ROOT)),
                     "title": str(c.get("title"))[:140]})

    # canonicalise: fold duplicate bundles' labels into their keeper where the labels match
    by_bundle = {r["bundle"]: r for r in rows}
    defects = []
    nid = defaultdict(int)
    def new_id(pr):
        nid[pr] += 1
        return f"{pr}-D{nid[pr]:02d}"
    for r in sorted(rows, key=lambda r: (len(r["pr"]), r["pr"], r["bundle"])):
        if r["duplicate_of"]:
            continue                                  # folded when its keeper is processed
        # the bundle's executed test demonstrates exactly ONE of its labels: the one matching its title
        title = r["title"]
        own = max(r["labels"], key=lambda l: jac(l, title)) if r["labels"] else title
        take = [{"label": l, "from": r["bundle"], "own": (l == own)} for l in r["labels"]]
        for dup_bid, dup in by_bundle.items():        # pull unique labels from its duplicates
            if dup["duplicate_of"] != r["bundle"]:
                continue
            for l in dup["labels"]:
                # the duplicate verdict already asserts "same defect as the keeper", so its own claim
                # folds into the keeper's (never a second D-verified); only genuinely unique facets are
                # kept, and those carry no dedicated test => D-labelled
                if not any(jac(l, t["label"]) >= 0.45 for t in take):
                    take.append({"label": l, "from": dup_bid, "own": False,
                                 "note": "unique facet of a duplicate bundle (no dedicated test)"})
        for i, t in enumerate(take):
            defects.append({"id": new_id(r["pr"]), "pr": r["pr"], "label": t["label"],
                            "tier": "D-verified" if (by_bundle[t["from"]]["test"] and by_bundle[t["from"]]["fix"] and t.get("own")) else "D-labelled",
                            "bundle": t["from"], "anchor_file": r["anchor_file"], "anchor_lines": r["anchor_lines"],
                            "evidence_dir": r["evidence_dir"], "duplicate_of": None if t["from"] == r["bundle"] else r["bundle"],
                            "bundle_verdict": r["verdict"]})

    per_pr = defaultdict(lambda: {"D-verified": 0, "D-labelled": 0})
    for d in defects:
        per_pr[d["pr"]][d["tier"]] += 1
    out = {"n_defects": len(defects),
           "n_verified": sum(1 for d in defects if d["tier"] == "D-verified"),
           "n_labelled": sum(1 for d in defects if d["tier"] == "D-labelled"),
           "per_pr": {k: dict(v) for k, v in per_pr.items()}, "defects": defects}
    (VG / "DEFECT_REGISTRY.json").write_text(json.dumps(out, indent=1))

    L = ["# Defect registry — individual bugs (bundle -> defect renumbering)", "",
         f"**{out['n_defects']} individual defects** from {len(rows)} verified bundles "
         f"(includes duplicate bundles' unique labels): **{out['n_verified']} D-verified** "
         f"(own executed test+fix) and **{out['n_labelled']} D-labelled** (split out by the merge audit, "
         "findings only, no dedicated test yet).", "",
         "| PR | D-verified | D-labelled | total |", "|---|---|---|---|"]
    for pr in sorted(per_pr, key=lambda x: (len(x), x)):
        v = per_pr[pr]
        L.append(f"| {pr} | {v['D-verified']} | {v['D-labelled']} | {v['D-verified'] + v['D-labelled']} |")
    L += [f"| **total** | **{out['n_verified']}** | **{out['n_labelled']}** | **{out['n_defects']}** |", "",
          "## First 25 defects", "", "| id | tier | anchor | label |", "|---|---|---|---|"]
    for d in defects[:25]:
        L.append(f"| {d['id']} | {d['tier']} | `{d['anchor_file']}:{d['anchor_lines']}` | {d['label'][:90]} |")
    (VG / "DEFECT_REGISTRY.md").write_text("\n".join(L) + "\n")
    print(json.dumps({k: out[k] for k in ("n_defects", "n_verified", "n_labelled", "per_pr")}, indent=1))


if __name__ == "__main__":
    main()
