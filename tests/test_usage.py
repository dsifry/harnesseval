"""Per-model usage normalization and the read-time Codex correction (harnesseval#19)."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from harnesseval.usage import (
    USAGE_CONVENTION,
    ModelUsage,
    corrected_per_model_usage,
    from_codex_cli,
    from_openai_api,
    grand_total,
    merge,
    needs_codex_correction,
)
from tools.codex_reasoning_correction import main as report_main

# Real codex-cli 0.160.0 last_token_usage record: total_tokens == input + output,
# so reasoning is already inside output_tokens and cached inside input_tokens.
CODEX_RECORD = {"input_tokens": 21993, "cached_input_tokens": 6016,
                "cache_write_input_tokens": 0, "output_tokens": 184,
                "reasoning_output_tokens": 134, "total_tokens": 22177}


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class ModelUsageTests(unittest.TestCase):
    def test_total_sums_every_field_once(self):
        u = ModelUsage(input_tokens=1, cache_read_input_tokens=20, cache_creation_input_tokens=300,
                       output_tokens=4000, reasoning_output_tokens=50000)
        self.assertEqual(u.total_tokens, 54321)


class CodexUsageTests(unittest.TestCase):
    def test_missing_fields_default_to_zero(self):
        u = from_codex_cli({}, "m")["m"]
        for k in ("input_tokens", "cache_read_input_tokens", "output_tokens",
                  "reasoning_output_tokens", "total_tokens"):
            self.assertEqual(u[k], 0, k)

    def test_total_matches_codex_reported_total(self):
        usage = from_codex_cli(CODEX_RECORD, "m")
        self.assertEqual(grand_total(usage)["total_tokens"], CODEX_RECORD["total_tokens"])

    def test_issue_reproducer(self):
        rec = {"input_tokens": 23696, "cached_input_tokens": 9984,
               "output_tokens": 415, "reasoning_output_tokens": 32, "total_tokens": 24111}
        self.assertEqual(grand_total(from_codex_cli(rec, "m"))["total_tokens"], 24111)

    def test_output_excludes_reasoning_like_openai_path(self):
        u = from_codex_cli(CODEX_RECORD, "m")["m"]
        self.assertEqual(u["output_tokens"], 50)
        self.assertEqual(u["reasoning_output_tokens"], 134)
        self.assertEqual(u["input_tokens"], 21993 - 6016)
        self.assertEqual(u["cache_read_input_tokens"], 6016)

    def test_output_clamped_when_reasoning_exceeds_output(self):
        u = from_codex_cli({"input_tokens": 10, "output_tokens": 5,
                            "reasoning_output_tokens": 9}, "m")["m"]
        self.assertEqual(u["output_tokens"], 0)

    def test_merge_preserves_codex_total(self):
        merged = merge({}, from_codex_cli(CODEX_RECORD, "m"))
        merge(merged, from_codex_cli(CODEX_RECORD, "m"))
        self.assertEqual(merged["m"]["total_tokens"], 2 * CODEX_RECORD["total_tokens"])


class OpenAIUsageTests(unittest.TestCase):
    def test_total_is_prompt_plus_completion(self):
        resp = _Obj(usage=_Obj(prompt_tokens=1000, completion_tokens=300,
                               completion_tokens_details=_Obj(reasoning_tokens=120),
                               prompt_tokens_details=_Obj(cached_tokens=400)))
        self.assertEqual(grand_total(from_openai_api(resp, "m"))["total_tokens"], 1300)


class CorrectedUsageTests(unittest.TestCase):
    PRE = "2026-09-14T06:46:31Z"   # last stored Codex run
    POST = "2026-10-27T00:45:27Z"  # #21 merge instant: already fixed

    def _summary(self):
        # Stored shape from runs/000face57524/summary.json (pre-fix)
        return {"per_model_usage": {
            "gpt-6-astra": {"input_tokens": 10599, "cache_read_input_tokens": 61568,
                            "cache_creation_input_tokens": 0, "output_tokens": 605,
                            "reasoning_output_tokens": 316, "cost_usd": 0.0, "total_tokens": 73088},
            "glm-5.3-background": {"input_tokens": 100, "cache_read_input_tokens": 0,
                                   "cache_creation_input_tokens": 0, "output_tokens": 10,
                                   "reasoning_output_tokens": 5, "cost_usd": 0.0, "total_tokens": 115}}}

    def test_legacy_matches_fixed_parser(self):
        fixed = from_codex_cli({"input_tokens": 72167, "cached_input_tokens": 61568,
                                "output_tokens": 605, "reasoning_output_tokens": 316}, "gpt-6-astra")
        pm = corrected_per_model_usage(self._summary(), self.PRE)
        self.assertEqual(pm["gpt-6-astra"], fixed["gpt-6-astra"])
        self.assertEqual(pm["glm-5.3-background"], self._summary()["per_model_usage"]["glm-5.3-background"])

    def test_does_not_mutate_summary(self):
        s = self._summary()
        corrected_per_model_usage(s, self.PRE)
        self.assertEqual(s, self._summary())

    def test_registered_at_or_after_fix_is_left_alone(self):
        for ts in (self.POST, "2026-10-27T00:45:28Z", "2026-10-26T20:45:27-04:00"):
            self.assertEqual(corrected_per_model_usage(self._summary(), ts),
                             self._summary()["per_model_usage"], ts)
        self.assertIs(needs_codex_correction({}, self.POST), False)

    def test_registered_before_fix_is_corrected(self):
        for ts in (self.PRE, "2026-10-27T00:45:26Z", "2026-10-26T20:45:26-04:00", None, ""):
            self.assertIs(needs_codex_correction({}, ts), True, ts)

    def test_convention_stamp_overrides_date(self):
        s = dict(self._summary(), usage_convention=USAGE_CONVENTION)
        self.assertIs(needs_codex_correction(s, self.PRE), False)
        self.assertEqual(corrected_per_model_usage(s, self.PRE), s["per_model_usage"])
        self.assertTrue(needs_codex_correction({"usage_convention": USAGE_CONVENTION - 1}, self.PRE))

    def test_edge_entries(self):
        s = {"per_model_usage": {
            "gpt-paid": {"input_tokens": 1, "cache_read_input_tokens": 0,
                         "cache_creation_input_tokens": 0, "output_tokens": 10,
                         "reasoning_output_tokens": 4, "cost_usd": 0.5, "total_tokens": 15},
            "gpt-nocost": {"input_tokens": 1, "cache_read_input_tokens": 2,
                           "cache_creation_input_tokens": 3, "output_tokens": 10,
                           "reasoning_output_tokens": 4, "cost_usd": None, "total_tokens": 20},
            "gpt-clamp": {"input_tokens": 1, "cache_read_input_tokens": 0,
                          "cache_creation_input_tokens": 0, "output_tokens": 3,
                          "reasoning_output_tokens": 5, "total_tokens": 9},
            "gpt-sparse": {"reasoning_output_tokens": None},
            "gpt-noreason": {"input_tokens": 1, "cache_read_input_tokens": 0,
                             "cache_creation_input_tokens": 0, "output_tokens": 7, "total_tokens": 8},
            "gpt-bad": "not-a-dict"}}
        pm = corrected_per_model_usage(s, self.PRE)
        self.assertEqual(pm["gpt-paid"], s["per_model_usage"]["gpt-paid"])  # paid API: already correct
        self.assertEqual((pm["gpt-nocost"]["output_tokens"], pm["gpt-nocost"]["total_tokens"]), (6, 16))
        self.assertEqual((pm["gpt-clamp"]["output_tokens"], pm["gpt-clamp"]["total_tokens"]), (0, 6))
        self.assertEqual((pm["gpt-sparse"]["output_tokens"], pm["gpt-sparse"]["total_tokens"]), (0, 0))
        self.assertEqual((pm["gpt-noreason"]["output_tokens"], pm["gpt-noreason"]["total_tokens"]), (7, 8))
        self.assertEqual(pm["gpt-bad"], "not-a-dict")

    def test_missing_usage(self):
        self.assertEqual(corrected_per_model_usage({"per_model_usage": None}, self.PRE), {})
        self.assertEqual(corrected_per_model_usage({}, self.POST), {})


class CorrectionReportTests(unittest.TestCase):
    CODEX: ClassVar[dict] = {"per_model_usage": {"gpt-6-astra": {
        "input_tokens": 10, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
        "output_tokens": 8, "reasoning_output_tokens": 3, "cost_usd": 0.0, "total_tokens": 21}}}

    def _tree(self, root):
        runs = Path(root) / "runs"
        cells = {  # name: (summary, registered_at or None for no manifest)
            "codex": (self.CODEX, "2026-09-01T00:00:00Z"),
            "codex_nomanifest": (self.CODEX, None),
            "codex_noreason": ({"per_model_usage": {"gpt-5.6-sol": {
                "input_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                "output_tokens": 2, "reasoning_output_tokens": 0, "cost_usd": 0.0,
                "total_tokens": 3}}}, "2026-09-01T00:00:00Z"),
            "codex_new": (self.CODEX, "2026-11-01T00:00:00Z"),
            "codex_stamped": (dict(self.CODEX, usage_convention=USAGE_CONVENTION), "2026-09-01T00:00:00Z"),
            "glm": ({"per_model_usage": {"glm-5.3": dict(self.CODEX["per_model_usage"]["gpt-6-astra"])}},
                    "2026-09-01T00:00:00Z"),
            "baduse": ({"per_model_usage": {"gpt-5.6-sol": "not-a-dict"}}, "2026-09-01T00:00:00Z"),
            "mixed": ({"per_model_usage": {
                "gpt-none": {"output_tokens": None, "reasoning_output_tokens": 2, "cost_usd": 0},
                "gpt-nototal": {"input_tokens": 1, "output_tokens": 5, "reasoning_output_tokens": 2},
                "glm-nototal": {"output_tokens": 5, "reasoning_output_tokens": 2},
                "gpt-bad": "not-a-dict"}}, "2026-09-01T00:00:00Z"),
            "nousage": ({"tp": 1}, "2026-09-01T00:00:00Z"),
            "list": ([1], "2026-09-01T00:00:00Z"),
        }
        for name, (summary, ts) in cells.items():
            (runs / name).mkdir(parents=True)
            (runs / name / "summary.json").write_text(json.dumps(summary, indent=2))
            if ts:
                (runs / name / "manifest.json").write_text(json.dumps({"registered_at": ts}))
        (runs / "broken").mkdir()
        (runs / "broken" / "summary.json").write_text("{not json")
        (runs / "badmanifest").mkdir()
        (runs / "badmanifest" / "summary.json").write_text(json.dumps(self.CODEX))
        (runs / "badmanifest" / "manifest.json").write_text("{not json")
        return runs

    def _run(self, root, *argv):
        out = io.StringIO()
        cwd = os.getcwd()
        try:
            os.chdir(root)
            with patch("sys.argv", ["report", *argv]), contextlib.redirect_stdout(out):
                report_main()
        finally:
            os.chdir(cwd)
        return out.getvalue()

    def test_counts_only_legacy_codex_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            runs = self._tree(root)
            before = {p: p.read_bytes() for p in runs.rglob("*.json")}
            out = self._run(root)
            # codex, codex_nomanifest, badmanifest (3 each), mixed (2), codex_noreason (0)
            self.assertEqual(out, "5 legacy Codex summaries corrected at read time (4 with reasoning); "
                                  "11 double-counted tokens removed from total_tokens\n")
            self.assertEqual(self._run(root, "--runs", str(runs)), out)
            self.assertEqual(before, {p: p.read_bytes() for p in runs.rglob("*.json")})


if __name__ == "__main__":
    unittest.main()
