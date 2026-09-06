"""batch_083 collision audit: find runs corrupted by the shared-materialize-repo bug.

Bug (fixed on branch mrv-0101-comparison): materialize() caches one repo dir per PR and the
realistic adapters mutate it in place. Two CONCURRENT runs on the same PR clobber each other:
reset_clean wipes in-flight work, git state interleaves, and both runs extract the SAME
findings file (last writer wins). Signature: two runs on the same PR with overlapping
[start,end] windows whose extracted findings are identical or near-identical.

Corruption vs legit similarity: re-runs of the SAME (fw,model,effort) cell on the same PR are
expected to be similar (same model + prompt). Findings identical/near-identical across
DIFFERENT cells is only possible via the shared findings file.

Run: uv run python audit_batch_083.py
"""
import json
from pathlib import Path
from collections import defaultdict

BATCH = "20260825-batch-083-fullmatrix"
MIN_OVERLAP_S = 30.0


def load_runs():
    runs = []
    for line in open("runs/registry.jsonl"):
        if BATCH not in line:
            continue
        d = json.loads(line)
        sp = Path(d.get("summary_path", ""))
        if not sp.exists():
            continue
        try:
            s = json.load(open(sp))
        except Exception:
            continue
        url = s.get("url", "")
        if not url:
            continue
        mp = sp.parent / "manifest.json"
        end = mp.stat().st_mtime if mp.exists() else sp.stat().st_mtime
        wall = float(d.get("wall_s") or 0) or float(s.get("wall_ms", 0) or 0) / 1000.0 or 300.0
        findings = [f.get("issue_text", "")[:80] for f in s.get("findings", [])]
        runs.append({
            "rid": d["run_id"], "fw": d.get("framework", "?"), "model": d.get("model", "?"),
            "effort": d.get("effort"), "url": url, "wall": wall,
            "start": end - wall, "end": end, "status": d.get("status"),
            "n": len(findings), "fset": frozenset(findings),
            "cell": (d.get("framework"), d.get("model"), d.get("effort"), url),
        })
    return runs


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main():
    runs = load_runs()
    print(f"batch_083 runs with url + timing: {len(runs)}")

    by_url = defaultdict(list)
    for r in runs:
        by_url[r["url"]].append(r)

    # 1. same-PR overlap windows
    pairs = []
    for url, rs in by_url.items():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                ov = min(a["end"], b["end"]) - max(a["start"], b["start"])
                if ov >= MIN_OVERLAP_S:
                    pairs.append((url, a, b, ov))
    print(f"same-PR overlapping pairs (>={MIN_OVERLAP_S:.0f}s exposure): {len(pairs)}")

    # 2. classify pairs
    confirmed = []   # jac >= 0.5 across DIFFERENT cells
    suspect = []     # 0.2 <= jac < 0.5 across DIFFERENT cells
    same_cell_overlaps = 0
    for url, a, b, ov in pairs:
        if a["cell"][:3] == b["cell"][:3]:
            same_cell_overlaps += 1
            continue
        j = jaccard(a["fset"], b["fset"])
        rec = {"url": url.rsplit("/", 1)[-1], "ov": int(ov), "j": round(j, 2),
               "a": f"{a['fw'][:12]}/{a['model'][:10]}/{a['effort']}/{a['rid'][:8]} (n={a['n']})",
               "b": f"{b['fw'][:12]}/{b['model'][:10]}/{b['effort']}/{b['rid'][:8]} (n={b['n']})",
               "a_rid": a["rid"], "b_rid": b["rid"]}
        if j >= 0.5:
            confirmed.append(rec)
        elif j >= 0.2:
            suspect.append(rec)
    confirmed.sort(key=lambda r: -r["j"])
    suspect.sort(key=lambda r: -r["j"])

    print(f"  same-cell rerun overlaps (expected-similar, excluded): {same_cell_overlaps}")
    print(f"  CONFIRMED corruption (jac>=0.5 across different cells): {len(confirmed)}")
    print(f"  SUSPECT (0.2<=jac<0.5 across different cells):          {len(suspect)}")

    implicated = set()
    for r in confirmed + suspect:
        implicated.add(r["a_rid"]); implicated.add(r["b_rid"])
    print(f"  unique runs implicated: {len(implicated)}")
    impl_fw = defaultdict(int)
    rid2run = {r["rid"]: r for r in runs}
    for rid in implicated:
        impl_fw[rid2run[rid]["fw"]] += 1
    for fw, n in sorted(impl_fw.items()):
        print(f"    by framework: {fw}: {n}")

    # 3. show the worst confirmed pairs
    print("\n=== top CONFIRMED pairs (by jaccard) ===")
    for r in confirmed[:15]:
        print(f"  PR {r['url']:>6} ov={r['ov']:>4}s jac={r['j']:.2f}  {r['a']}  <->  {r['b']}")

    # 4. zero-finding (degenerate) runs: were they exposed to an overlap?
    degenerate = [r for r in runs if r["n"] == 0 and r["status"] == "pass"]
    exposed_degen = 0
    for r in degenerate:
        for url, a, b, ov in pairs:
            if a["rid"] == r["rid"] or b["rid"] == r["rid"]:
                exposed_degen += 1
                break
    print(f"\n=== degenerate (0-finding, pass) runs: {len(degenerate)}; overlapping same-PR run: {exposed_degen} ===")
    degen_by_cell = defaultdict(int)
    for r in degenerate:
        fw, m, e, url = r["cell"]
        degen_by_cell[(fw, m, e, url.rsplit("/", 1)[-1])] += 1
    for (fw, m, e, pr), n in sorted(degen_by_cell.items()):
        print(f"  {fw[:14]}/{m[:10]}/{e} PR{pr}: {n}")

    # 5. cell-level impact on the designed 56-cell matrix
    cells = defaultdict(lambda: {"runs": 0, "implicated": 0, "zero": 0})
    for r in runs:
        c = cells[r["cell"]]
        c["runs"] += 1
        if r["rid"] in implicated:
            c["implicated"] += 1
        if r["n"] == 0 and r["status"] == "pass":
            c["zero"] += 1
    tainted = {k: v for k, v in cells.items() if v["implicated"] or v["zero"]}
    print(f"\n=== designed cells with tainted data: {len(tainted)} of {len(cells)} ===")
    for (fw, m, e, url), v in sorted(tainted.items()):
        pr = url.rsplit("/", 1)[-1]
        print(f"  {fw[:14]}/{m[:10]}/{e} PR{pr}: runs={v['runs']} implicated={v['implicated']} zero-finding={v['zero']}")


if __name__ == "__main__":
    main()
