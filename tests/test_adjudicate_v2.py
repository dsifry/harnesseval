"""Unit tests for the v2 adjudication split + parser (harnesseval#8).

Run: uv run python -m pytest tests/test_adjudicate_v2.py -q  (or python -m unittest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harnesseval.adjudicate import _split_adjudication, _parse_adjudication
from harnesseval.judge import JudgeResult


def _jr(cat=None, conf=0.9, match=None, error=None, reasoning="r"):
    if cat is None:
        return JudgeResult(match=bool(match), confidence=conf, reasoning=reasoning, raw="", error=error)
    m = match if match is not None else (cat in ("bug",))
    return JudgeResult(match=m, confidence=conf, reasoning=reasoning, raw="", error=error, category=cat)


def test_split_three_way_buckets():
    scored = {"tp": 3, "fn": 2, "precision": 0.6, "recall": 0.6}
    results = [
        _jr("bug", 0.9),                      # -> bug_ungold
        _jr("important_non_bug", 0.8),        # -> important_non_bug
        _jr("hallucination", 0.95),           # -> true_hallucination
        _jr(conf=0.0, error="parse"),         # -> unresolved (error, NOT hallucination)
        _jr("unresolved", 0.3),               # -> unresolved (low-confidence positive)
    ]
    fps = [{"candidate": c} for c in ["c1", "c2", "c3", "c4", "c5"]]
    out = _split_adjudication(scored, fps, results, real_threshold=0.7)
    assert len(out["bug_ungold"]) == 1
    assert len(out["important_non_bug"]) == 1
    assert len(out["true_hallucination"]) == 1
    assert len(out["unresolved"]) == 2, out["unresolved"]
    # legacy keys mirror the new buckets
    assert out["real_but_ungold"] == out["bug_ungold"]
    assert out["hallucination"] == out["true_hallucination"]
    # waste precision: TP / (TP + true hal) — unresolved excluded from the denominator
    assert abs(out["adjudicated_precision"] - 3 / (3 + 1)) < 1e-9
    # incremental recall: (TP + bug_ungold) / (TP + FN + bug_ungold)
    assert abs(out["incremental_recall"] - (3 + 1) / (3 + 2 + 1)) < 1e-9


def test_split_v1_style_results_compat():
    """v1-style results (no category attr, match bool) still split correctly."""
    scored = {"tp": 1, "fn": 0, "precision": 0.5, "recall": 1.0}
    results = [_jr(match=True, conf=0.9), _jr(match=False, conf=0.8)]
    fps = [{"candidate": "a"}, {"candidate": "b"}]
    out = _split_adjudication(scored, fps, results, real_threshold=0.7)
    assert len(out["bug_ungold"]) == 1 and len(out["true_hallucination"]) == 1


def test_parse_category_responses():
    r = _parse_adjudication({"category": "bug", "confidence": 0.9, "reasoning": "x"})
    assert r.category == "bug" and r.match and r.confidence == 0.9
    r = _parse_adjudication({"category": "important_non_bug", "confidence": 0.8, "reasoning": "x"})
    assert r.category == "important_non_bug" and not r.match
    r = _parse_adjudication({"category": "hallucination", "confidence": 0.95, "reasoning": "x"})
    assert r.category == "hallucination" and not r.match


def test_parse_conf_floor():
    """Low-confidence positives -> unresolved, not hidden gold (readjudicate3 rule)."""
    r = _parse_adjudication({"category": "bug", "confidence": 0.4, "reasoning": "guessy"})
    assert r.category == "unresolved" and not r.match
    r = _parse_adjudication({"category": "important_non_bug", "confidence": 0.49, "reasoning": "guessy"})
    assert r.category == "unresolved"


def test_parse_v1_fallback():
    """v1 is_real responses still parse (backward compat for stored formats)."""
    r = _parse_adjudication({"is_real": True, "confidence": 0.9, "reasoning": "x"})
    assert r.category == "bug" and r.match
    r = _parse_adjudication({"is_real": False, "confidence": 0.9, "reasoning": "x"})
    assert r.category == "hallucination" and not r.match


def test_parse_bad_category_unresolved():
    r = _parse_adjudication({"category": "maybe?", "confidence": 0.9, "reasoning": "x"})
    assert r.category == "unresolved"


def test_empty_fps_returns_all_keys():
    scored = {"tp": 0, "fn": 1, "precision": 0.0, "recall": 0.0}
    out = _split_adjudication(scored, [], [], real_threshold=0.7)
    for k in ("bug_ungold", "important_non_bug", "true_hallucination", "unresolved",
              "real_but_ungold", "hallucination"):
        assert k in out and out[k] == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
