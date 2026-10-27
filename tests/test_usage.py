"""Per-model usage normalization (harnesseval#19)."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from harnesseval.usage import ModelUsage, from_codex_cli, from_openai_api, grand_total, merge
from tools.backfill_codex_reasoning import main as backfill_main, normalize


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


class BackfillTests(unittest.TestCase):
    def _summary(self):
        # Stored shape from runs/000face57524/summary.json (pre-fix)
        return {"per_model_usage": {
            "gpt-6-astra": {"input_tokens": 10599, "cache_read_input_tokens": 61568,
                            "cache_creation_input_tokens": 0, "output_tokens": 605,
                            "reasoning_output_tokens": 316, "cost_usd": 0.0, "total_tokens": 73088},
            "glm-5.3-background": {"input_tokens": 100, "cache_read_input_tokens": 0,
                                   "cache_creation_input_tokens": 0, "output_tokens": 10,
                                   "reasoning_output_tokens": 5, "cost_usd": 0.0, "total_tokens": 115}}}

    def test_backfill_matches_fixed_parser(self):
        d = self._summary()
        self.assertEqual(normalize(d), 316)
        fixed = from_codex_cli({"input_tokens": 72167, "cached_input_tokens": 61568,
                                "output_tokens": 605, "reasoning_output_tokens": 316}, "gpt-6-astra")
        self.assertEqual(d["per_model_usage"]["gpt-6-astra"], fixed["gpt-6-astra"])

    def test_backfill_skips_non_codex_and_is_idempotent(self):
        d = self._summary()
        normalize(d)
        self.assertEqual(d["per_model_usage"]["glm-5.3-background"]["total_tokens"], 115)
        before = json.dumps(d, sort_keys=True)
        self.assertEqual(normalize(d), 0)
        self.assertEqual(json.dumps(d, sort_keys=True), before)

    def test_edge_entries(self):
        d = {"per_model_usage": {
            "gpt-paid": {"input_tokens": 1, "cache_read_input_tokens": 0,
                         "cache_creation_input_tokens": 0, "output_tokens": 10,
                         "reasoning_output_tokens": 4, "cost_usd": 0.5, "total_tokens": 15},
            "gpt-nocost": {"input_tokens": 1, "cache_read_input_tokens": 2,
                           "cache_creation_input_tokens": 3, "output_tokens": 10,
                           "reasoning_output_tokens": 4, "cost_usd": None, "total_tokens": 20},
            "gpt-clamp": {"input_tokens": 1, "cache_read_input_tokens": 0,
                          "cache_creation_input_tokens": 0, "output_tokens": 3,
                          "reasoning_output_tokens": 5, "total_tokens": 9},
            "gpt-sparse": {"input_tokens": 1, "cache_read_input_tokens": 0,
                           "cache_creation_input_tokens": 0, "reasoning_output_tokens": None},
            "gpt-noreason": {"input_tokens": 1, "cache_read_input_tokens": 0,
                             "cache_creation_input_tokens": 0, "output_tokens": 7, "total_tokens": 8},
            "gpt-bad": "not-a-dict"}}
        removed = normalize(d)
        pm = d["per_model_usage"]
        self.assertEqual(pm["gpt-paid"]["output_tokens"], 10)  # paid API entry untouched
        self.assertEqual(pm["gpt-nocost"]["output_tokens"], 6)
        self.assertEqual(pm["gpt-nocost"]["total_tokens"], 16)
        self.assertEqual(pm["gpt-clamp"]["output_tokens"], 0)
        self.assertEqual(pm["gpt-clamp"]["total_tokens"], 6)
        self.assertEqual(pm["gpt-sparse"]["output_tokens"], 0)
        self.assertEqual(pm["gpt-sparse"]["total_tokens"], 1)
        self.assertEqual(pm["gpt-noreason"]["output_tokens"], 7)
        self.assertEqual(pm["gpt-noreason"]["total_tokens"], 8)
        self.assertEqual(pm["gpt-bad"], "not-a-dict")
        self.assertEqual(removed, 4 + 3 - 1 + 0)

    def test_summary_without_usage_is_marked(self):
        d = {"per_model_usage": None}
        self.assertEqual(normalize(d), 0)
        self.assertTrue(d["codex_reasoning_normalized"])


class BackfillMainTests(unittest.TestCase):
    CODEX = {"per_model_usage": {"gpt-6-astra": {
        "input_tokens": 10, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
        "output_tokens": 8, "reasoning_output_tokens": 3, "cost_usd": 0.0, "total_tokens": 21}}}

    def _tree(self, root):
        runs = Path(root) / "runs"
        files = {
            "codex": self.CODEX,
            "codex_noreason": {"per_model_usage": {"gpt-5.6-sol": {
                "input_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                "output_tokens": 2, "reasoning_output_tokens": 0, "cost_usd": 0.0, "total_tokens": 3}}},
            "glm": {"per_model_usage": {"glm-5.3": dict(self.CODEX["per_model_usage"]["gpt-6-astra"])}},
            "done": dict(self.CODEX, codex_reasoning_normalized=True),
            "nousage": {"tp": 1},
            "baduse": {"per_model_usage": {"gpt-5.6-sol": "not-a-dict"}},
            "list": [1],
        }
        for name, d in files.items():
            (runs / name).mkdir(parents=True)
            (runs / name / "summary.json").write_text(json.dumps(d, indent=2))
        (runs / "broken").mkdir()
        (runs / "broken" / "summary.json").write_text("{not json")
        (runs / "codex" / "other.json").write_text(json.dumps(self.CODEX))
        return runs

    def _run(self, root, *argv):
        out = io.StringIO()
        cwd = os.getcwd()
        try:
            os.chdir(root)
            with patch("sys.argv", ["backfill", *argv]), contextlib.redirect_stdout(out):
                backfill_main()
        finally:
            os.chdir(cwd)
        return out.getvalue()

    def test_dry_run_reports_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            runs = self._tree(root)
            before = {p: p.read_bytes() for p in runs.rglob("*.json")}
            out = self._run(root)
            self.assertEqual(out, "would rewrite 2 Codex summaries (1 with reasoning); "
                                  "3 double-counted tokens removed from total_tokens\n")
            self.assertEqual(before, {p: p.read_bytes() for p in runs.rglob("*.json")})

    def test_write_rewrites_only_codex_summaries(self):
        with tempfile.TemporaryDirectory() as root:
            runs = self._tree(root)
            glm_before = (runs / "glm" / "summary.json").read_bytes()
            done_before = (runs / "done" / "summary.json").read_bytes()
            other_before = (runs / "codex" / "other.json").read_bytes()
            out = self._run(root, "--write", "--runs", str(runs))
            self.assertTrue(out.startswith("rewrote 2 Codex summaries (1 with reasoning); 3 "))
            expected = json.loads(json.dumps(self.CODEX))
            normalize(expected)
            self.assertEqual((runs / "codex" / "summary.json").read_text(),
                             json.dumps(expected, indent=2))
            self.assertIn('"codex_reasoning_normalized": true',
                          (runs / "codex_noreason" / "summary.json").read_text())
            self.assertEqual((runs / "glm" / "summary.json").read_bytes(), glm_before)
            self.assertEqual((runs / "done" / "summary.json").read_bytes(), done_before)
            self.assertEqual((runs / "codex" / "other.json").read_bytes(), other_before)
            self.assertEqual(self._run(root, "--write", "--runs", str(runs)),
                             "rewrote 0 Codex summaries (0 with reasoning); "
                             "0 double-counted tokens removed from total_tokens\n")


if __name__ == "__main__":
    unittest.main()
