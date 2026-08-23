"""Phase A.1 cross-check: re-judge the genuine-disagreement pairs via the Martian proxy.

Tests the hypothesis that the nonzero aggregate Δ on (propel, mra-ultra, mra-a,
entelligence, mra-openai) comes from the proxy-path difference (Martian judged via
api.withmartian.com; we used native Anthropic — same Opus 4.5 model). If re-judging
these pairs through the exact Martian proxy brings Δ→0, the hypothesis is confirmed
and the lab achieves bit-exact parity with Martian's published judge path.

Usage:
  uv run python -m harnesseval.crosscheck
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from harnesseval import keys
from harnesseval.dataset import martian
from harnesseval.judge import martian_judge_pairs, score_from_matches

# The 5 (url,tool) pairs with nonzero Δ in the native-Anthropic 50-pair pilot.
# All were on keycloak/pull/37038 (the getGroupIdsWithViewPermission / canManage PR).
DIDID = "anthropic/claude-opus-4-5-20251101"  # Martian's exact judge model id (creator-prefixed)
TARGET_PAIRS = [
    ("https://github.com/keycloak/keycloak/pull/37038", "propel"),
    ("https://github.com/keycloak/keycloak/pull/37038", "mra-ultra"),
    ("https://github.com/keycloak/keycloak/pull/37038", "mra-a"),
    ("https://github.com/keycloak/keycloak/pull/37038", "entelligence"),
    ("https://github.com/keycloak/keycloak/pull/37038", "mra-openai"),
]


def _find_pairs(_tool_names: list[str]) -> list[tuple[str, str]]:
    return TARGET_PAIRS


def main():
    target_tools = [t for _, t in TARGET_PAIRS]
    pairs = _find_pairs(target_tools)
    print(f"[crosscheck] target pairs ({len(pairs)}): {pairs}")

    goldens = martian.golden_comments_by_url()
    cands_all = martian.candidates_by_url("opus")
    dedup_all = martian.dedup_groups_by_url("opus")
    shipped = martian.shipped_evaluations("opus")
    client = keys.martian_client()

    all_pairs, pair_meta, per_url_tool = [], [], []
    for url, tool in pairs:
        golden = goldens.get(url, [])
        cands = cands_all.get(url, {}).get(tool, [])
        cand_texts = [c["text"] for c in cands if c.get("text")]
        if not golden or not cand_texts:
            continue
        for g in golden:
            for c in cand_texts:
                all_pairs.append((g["comment"], c))
                pair_meta.append((url, tool, g["comment"], c))
        per_url_tool.append((url, tool, golden, cand_texts))

    print(f"[crosscheck] Martian-proxy judge={DIDID}  pairs={len(per_url_tool)}  calls={len(all_pairs)}")
    t0 = time.time()
    results = asyncio.run(martian_judge_pairs(client, DIDID, all_pairs, concurrency=2))
    dt = time.time() - t0
    n_err = sum(1 for r in results if r.error)
    print(f"[crosscheck] judged {len(results)} pairs in {dt:.1f}s  errors={n_err}")

    pair_results_by_ut: dict[tuple[str, str], list] = {}
    for (url, tool, g, c), r in zip(pair_meta, results):
        pair_results_by_ut.setdefault((url, tool), []).append(r)

    print(f"[crosscheck] per-(url,tool) TP/FP/FN  Martian-proxy(ours) vs their shipped Opus:")
    max_delta = 0
    for url, tool, golden, cand_texts in per_url_tool:
        ut_results = []
        idx = 0
        for g in golden:
            for c in cand_texts:
                ut_results.append(pair_results_by_ut[(url, tool)][idx]); idx += 1
        groups = dedup_all.get(url, {}).get(tool)
        ours = score_from_matches(golden, cand_texts, ut_results, groups)
        theirs = shipped[url][tool]
        dtp = ours["tp"] - theirs["tp"]; dfp = ours["fp"] - theirs["fp"]; dfn = ours["fn"] - theirs["fn"]
        max_delta = max(max_delta, abs(dtp), abs(dfp), abs(dfn))
        print(f"   {tool:14s}  ours(tp={ours['tp']},fp={ours['fp']},fn={ours['fn']})  "
              f"theirs(tp={theirs['tp']},fp={theirs['fp']},fn={theirs['fn']})  Δ=({dtp:+d},{dfp:+d},{dfn:+d})")
    print(f"[crosscheck] max |Δ| via Martian proxy: {max_delta}")
    print(f"[crosscheck] HYPOTHESIS: {'CONFIRMED ✅ (proxy path was the cause)' if max_delta == 0 else 'PARTIAL — residual Δ from genuine model ambiguity'}")

    out = Path("results/phase_a1_crosscheck.json"); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"judge": DIDID, "pairs": len(per_url_tool), "calls": len(all_pairs),
                               "max_delta": max_delta, "errors": n_err, "wall_s": dt}, indent=2))
    print(f"[crosscheck] written to {out}")


if __name__ == "__main__":
    main()
