"""Report module — turn run-registry data into the eval's decision outputs.

Reads runs/registry.jsonl (and per-run summaries) and produces:
  1. Leaderboard table: per (framework, model, effort) — TP/FP/FN, raw + adjudicated precision,
     raw + incremental recall, tokens, cost, wall-time.
  2. Recall-vs-cost Pareto frontier (the money plot): each cell plotted by (cost, recall);
     the Pareto-optimal cells highlighted. This is the primary decision output.
  3. Per-model cost breakdown: for realistic runs, the orchestrator-vs-subagent split (e.g.
     opus orchestrator $3.2 / haiku lenses $0.001 — the §6.3.1 learning made visible).
  4. Failure-mode analysis: per framework, what golden issues it missed (the insight, not the
     headline score).

See docs/SPEC.md §10 (cost), §11 (stats), §6.3 (decomposition).
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"
REGISTRY = RUNS_DIR / "registry.jsonl"


def load_runs(**filters) -> list[dict]:
    """Load registry entries matching filters; merge in per-run summary fields."""
    if not REGISTRY.exists():
        return []
    out = []
    for line in REGISTRY.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if all(e.get(k) == v for k, v in filters.items()):
            # merge summary fields (per_model_usage, resolved_model, etc.)
            if e.get("summary_path") and Path(e["summary_path"]).exists():
                s = json.loads(Path(e["summary_path"]).read_text())
                e["_summary"] = s
            out.append(e)
    return out


def _summary(runs: list[dict]) -> list[dict]:
    """Pull the per-cell summary dict from each run's summary_path."""
    out = []
    for r in runs:
        s = r.get("_summary") or {}
        if s:
            s = {**s, "run_id": r["run_id"], "registered_at": r["registered_at"]}
            out.append(s)
    return out


def leaderboard(runs: list[dict], group_by: tuple = ("framework", "model", "effort"),
               min_findings: int = 1) -> list[dict]:
    """Aggregate runs by (framework, model, effort): sum TP/FP/FN/tokens/cost, derive rates.
    min_findings: skip cells whose runs produced no findings (degenerate/failed runs)."""
    cells = _summary(runs)
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for c in cells:
        if (c.get("n_findings", 0) or 0) < min_findings and (c.get("tp", 0) or 0) == 0 and (c.get("fn", 0) or 0) == 0:
            continue  # skip degenerate (failed) cells with no findings and no goldens judged
        key = tuple(c.get(k) for k in group_by)
        buckets[key].append(c)
    rows = []
    for key, cs in buckets.items():
        tp = sum(c.get("tp", 0) for c in cs); fp = sum(c.get("fp", 0) for c in cs); fn = sum(c.get("fn", 0) for c in cs)
        ru = sum(c.get("n_real_ungold", 0) for c in cs); hal = sum(c.get("n_hallucination", 0) for c in cs)
        tok = sum(c.get("tokens_in", 0) + c.get("tokens_out", 0) for c in cs)
        cost = sum(c.get("total_cost_usd", 0) or 0 for c in cs)
        wall = sum(c.get("wall_s", 0) for c in cs)
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        adj_prec = tp / (tp + hal) if (tp + hal) else 0
        incr_rec = (tp + ru) / (tp + fn + ru) if (tp + fn + ru) else 0
        row = dict(zip(group_by, key))
        row.update({"n_prs": len(cs), "tp": tp, "fp": fp, "fn": fn,
                    "precision": prec, "recall": rec,
                    "adjudicated_precision": adj_prec, "incremental_recall": incr_rec,
                    "n_real_ungold": ru, "n_hallucination": hal,
                    "total_tokens": tok, "total_cost_usd": cost, "wall_s": wall})
        rows.append(row)
    rows.sort(key=lambda r: (-r["recall"], r["total_cost_usd"]))
    return rows


def print_leaderboard(rows: list[dict]):
    print(f"\n{'framework':22s} {'model':28s} {'eff':5s} {'nPR':>3} {'TP':>3} {'FP':>4} {'FN':>3} "
          f"{'prec':>5} {'rec':>5} {'adjP':>5} {'incR':>5} {'real':>4} {'hal':>4} {'tok':>9} {'$':>7} {'wall':>5}")
    for r in rows:
        print(f"{str(r.get('framework',''))[:22]:22s} {str(r.get('model',''))[:28]:28s} "
              f"{str(r.get('effort',''))[:5]:5s} {r['n_prs']:>3} {r['tp']:>3} {r['fp']:>4} {r['fn']:>3} "
              f"{r['precision']:>5.2f} {r['recall']:>5.2f} {r['adjudicated_precision']:>5.2f} "
              f"{r['incremental_recall']:>5.2f} {r['n_real_ungold']:>4} {r['n_hallucination']:>4} "
              f"{r['total_tokens']:>9,} {r['total_cost_usd']:>7.3f} {r['wall_s']:>5.0f}s")


def pareto_frontier(rows: list[dict], cost_field: str = "total_cost_usd",
                    quality_field: str = "incremental_recall") -> list[dict]:
    """Return the Pareto-optimal rows: no other row has >= quality at <= cost."""
    pts = sorted(rows, key=lambda r: (r.get(cost_field, 0), -r.get(quality_field, 0)))
    front = []
    best_q = -1
    for r in pts:
        q = r.get(quality_field, 0)
        if q > best_q:
            front.append(r); best_q = q
    return front


def per_model_cost_breakdown(runs: list[dict]) -> dict[str, dict]:
    """Aggregate per-model usage across realistic runs (the orchestrator-vs-subagent split)."""
    agg: dict[str, dict] = defaultdict(lambda: {"input_tokens": 0, "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0,
        "cost_usd": 0.0, "total_tokens": 0, "n_runs": 0})
    for r in runs:
        s = r.get("_summary") or {}
        pmu = s.get("per_model_usage") or {}
        for mid, u in pmu.items():
            for k in agg[mid]:
                if k == "n_runs": continue
                agg[mid][k] += u.get(k, 0)
            agg[mid]["n_runs"] += 1
    return dict(agg)


def plot_pareto(rows: list[dict], out: str = "results/pareto.png",
                cost_field: str = "total_cost_usd", quality_field: str = "incremental_recall"):
    """Plot recall-vs-cost Pareto frontier. Each (framework, model, effort) a point; frontier highlighted."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 6))
    fronts = pareto_frontier(rows, cost_field, quality_field)
    front_ids = {(r.get("framework"), r.get("model"), r.get("effort")) for r in fronts}
    colors = {"vanilla-engineered": "tab:blue", "vanilla-naive": "tab:cyan",
              "metareview": "tab:orange", "metareview-realistic": "tab:red"}
    for r in rows:
        c = colors.get(r.get("framework"), "gray")
        is_front = (r.get("framework"), r.get("model"), r.get("effort")) in front_ids
        ax.scatter(r.get(cost_field, 0), r.get(quality_field, 0), c=c,
                   edgecolors=("black" if is_front else "none"), s=(120 if is_front else 50),
                   zorder=3, label=None)
    # frontier line
    if len(fronts) > 1:
        fx = [r.get(cost_field, 0) for r in fronts]; fy = [r.get(quality_field, 0) for r in fronts]
        ax.plot(fx, fy, "k--", alpha=0.4, zorder=2)
    ax.set_xlabel(f"Cost ({cost_field}, $)"); ax.set_ylabel(f"Quality ({quality_field})")
    ax.set_title("Recall-vs-Cost Pareto Frontier (per framework × model × effort)")
    # legend by framework
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=9, label=fw)
               for fw, c in colors.items() if any(r.get("framework") == fw for r in rows)]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(out, dpi=120); plt.close(fig)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default=None, help="filter by phase (e.g. B)")
    ap.add_argument("--pareto", default="results/pareto.png")
    ap.add_argument("--out", default="results/leaderboard.json")
    args = ap.parse_args()

    runs = load_runs(phase=args.phase) if args.phase else load_runs()
    print(f"[report] {len(runs)} runs loaded")
    rows = leaderboard(runs)
    print_leaderboard(rows)
    # pareto
    front = pareto_frontier(rows)
    print(f"\n[report] Pareto-optimal cells ({len(front)}):")
    for r in front:
        print(f"  {r.get('framework'):22s} {r.get('model'):28s} {r.get('effort'):5s}  "
              f"{r['incremental_recall']:.2f} recall @ ${r['total_cost_usd']:.3f}")
    try:
        # use $ cost if any run has it; else fall back to token cost (1Mt ~ $15 nominal for axis)
        has_cost = any((r.get("_summary") or {}).get("total_cost_usd", 0) for r in runs)
        cost_field = "total_cost_usd" if has_cost else "total_tokens"
        p = plot_pareto(rows, out=args.pareto, cost_field=cost_field)
        print(f"[report] Pareto plot -> {p} (cost axis: {cost_field})")
    except Exception as e:
        print(f"[report] plot failed: {e}")
    # per-model cost breakdown (realistic runs)
    pmc = per_model_cost_breakdown(runs)
    if pmc:
        print(f"\n[report] Per-model cost breakdown (realistic runs):")
        for mid, u in sorted(pmc.items(), key=lambda kv: -kv[1]["cost_usd"]):
            print(f"  {mid}: in={u['input_tokens']:,} cache_read={u['cache_read_input_tokens']:,} "
                  f"cache_create={u['cache_creation_input_tokens']:,} out={u['output_tokens']:,} "
                  f"reasoning={u['reasoning_output_tokens']:,} cost=${u['cost_usd']:.4f} "
                  f"total={u['total_tokens']:,} (across {u['n_runs']} runs)")
    Path(args.out).write_text(json.dumps(rows, indent=2))
    print(f"[report] leaderboard -> {args.out}")


if __name__ == "__main__":
    main()
