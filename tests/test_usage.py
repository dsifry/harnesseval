"""Per-model usage normalization (harnesseval#19)."""
import json
import unittest

from harnesseval.usage import from_codex_cli, from_openai_api, grand_total, merge
from tools.backfill_codex_reasoning import normalize


# Real codex-cli 0.160.0 last_token_usage record: total_tokens == input + output,
# so reasoning is already inside output_tokens and cached inside input_tokens.
CODEX_RECORD = {"input_tokens": 21993, "cached_input_tokens": 6016,
                "cache_write_input_tokens": 0, "output_tokens": 184,
                "reasoning_output_tokens": 134, "total_tokens": 22177}


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class CodexUsageTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
