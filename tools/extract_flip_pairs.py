#!/usr/bin/env python3
"""Derive the adjudication flip regression set (handoff 2026-09-08 §3C.5).

Joins analysis/all_matches.json (CE-bug -> mrv-finding match records over the 81 matched
pairs in analysis/pairs.json) with each mrv run's readjudication3.json verdicts to extract
the flip set: the CE-confirmed bugs mrv also reported where mrv's own v2 adjudicator
disagreed with CE's confirmation — 98 verdicts of `important_non_bug` and 18 of
`true_hallucination` (116 of 1,340 matched, 8.6%).

Each member is labeled `expected: "bug"` (CE's independent confirmation is the label). The
openssl case from the handoff is the canonical member: identical wording judged `bug` in one
run and `true_hallucination` in another — under the v3 cross-run dedup both phrasings are
structurally ONE cluster with ONE verdict, which is the property the regression suite pins.

Also emits the near-verbatim groups (same CE bug, multiple mrv phrasings) so the suite can
check cluster-level stability: members of one group must all inherit one v3 verdict.

Output: tests/fixtures/flip_pairs.json (FROZEN once derived; prompt changes are scored
against the frozen set, never a re-derivation that could move the goalposts).

Read-only over analysis/ and runs/.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readjudicate3 import strip_provenance  # noqa: E402

PAIRS = Path("analysis/pairs.json")
MATCHES = Path("analysis/all_matches.json")
OUT = Path("tests/fixtures/flip_pairs.json")


def mrv_verdict(mrv_dir: str, m_idx: int, summary: dict) -> str | None:
    """The v2 (readjudication3) verdict of mrv finding #m_idx in one run, or None."""
    rj = Path(mrv_dir) / "readjudication3.json"
    if m_idx >= len(summary.get("findings", [])):
        return None
    text = summary["findings"][m_idx].get("issue_text", "")
    if rj.exists():
        for r in json.load(open(rj)).get("records", []):
            if r.get("issue_text") == text:
                return r.get("new_verdict")
    # not re-judged by v2 -> the primary verdict stands
    for a in summary.get("adjudication_records", []):
        if a.get("issue_text") == text:
            v = a.get("primary_judge_verdict")
            return "bug" if v in ("real_but_ungold", "match") else v
    return None


def main() -> None:
    pairs = json.load(open(PAIRS))
    matches = json.load(open(MATCHES))

    members = []          # the flip set: matched, CE-confirmed, mrv v2 verdict != bug
    groups: dict[str, list] = {}   # same CE bug -> all mrv phrasings + verdicts (stability view)
    for key, m in matches.items():
        if m.get("match") is None:
            continue
        pid, ce_id = key.split("|", 1)
        p = pairs[int(pid)]
        m_idx = int(m["match"][1:])  # "M19" -> 19
        s = json.load(open(Path(p["mrv_dir"]) / "summary.json"))
        verdict = mrv_verdict(p["mrv_dir"], m_idx, s)
        if verdict is None:
            continue
        entry = {
            "pair_id": int(pid), "ce_id": ce_id, "url": p["url"],
            "ce_key": f'{p["url"]}#{ce_id}',  # score_flips.py keys its report on this
            "mrv_dir": p["mrv_dir"], "m_idx": m_idx,
            "model": p["model"], "effort": p["eff"],
            "issue_text": s["findings"][m_idx].get("issue_text", ""),
            "stripped_text": strip_provenance(s["findings"][m_idx].get("issue_text", "")),
            "v2_verdict": verdict,
        }
        groups.setdefault(f'{p["url"]}#{ce_id}', []).append(entry)
        if verdict in ("important_non_bug", "hallucination"):
            entry = dict(entry, expected="bug")   # CE independently confirmed the bug
            members.append(entry)

    stability_groups = [
        {"ce_key": k, "url": v[0]["url"], "ce_id": v[0]["ce_id"],
         "n_members": len(v),
         "verdicts": sorted({mm["v2_verdict"] for mm in v}),
         "members": v}
        for k, v in sorted(groups.items()) if len({mm["v2_verdict"] for mm in v}) > 1
    ]

    out = {
        "derived_from": {"pairs": str(PAIRS), "matches": str(MATCHES)},
        "label": "expected=bug: CE independently confirmed these bugs; mrv's v2 adjudicator "
                 "disagreed (important_non_bug or hallucination)",
        "n_flips": len(members),
        "by_v2_verdict": dict(Counter(m["v2_verdict"] for m in members)),
        "flips": members,
        "stability_groups": stability_groups,
        "n_stability_groups": len(stability_groups),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}: {len(members)} flip members "
          f"({out['by_v2_verdict']}), {len(stability_groups)} cross-phrasing stability groups")


if __name__ == "__main__":
    main()
