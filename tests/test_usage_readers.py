"""Writers stamp the usage convention; readers apply the read-time Codex correction (harnesseval#19)."""
import asyncio
import unittest
from unittest.mock import patch

from harnesseval import analysis, run_model_matrix
from harnesseval.adapters import compound_realistic
from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.finding import Finding
from harnesseval.usage import USAGE_CONVENTION, corrected_per_model_usage, from_codex_cli

LEGACY = {"gpt-6-astra": {"input_tokens": 10599, "cache_read_input_tokens": 61568,
                          "cache_creation_input_tokens": 0, "output_tokens": 605,
                          "reasoning_output_tokens": 316, "cost_usd": 0.0, "total_tokens": 73088}}
PRE_FIX = "2026-09-14T06:46:31Z"


class MatrixStampTests(unittest.TestCase):
    def test_new_summaries_are_stamped_and_never_recorrected(self):
        per_model = from_codex_cli({"input_tokens": 100, "output_tokens": 40,
                                    "reasoning_output_tokens": 30}, "gpt-6-astra")

        async def fake_review(pr, model, effort):
            return ReviewRun(framework="compound-realistic", model=model, effort=effort,
                             execution_mode="cli", raw_output="",
                             findings=[Finding(issue_text="x")], per_model_usage=per_model)

        async def fake_judge(judge, pairs, concurrency):
            return []

        async def fake_reclassify(scored, cands, diff, model):
            return {}

        scored = {"tp": 0, "fp": 1, "fn": 1, "precision": 0.0, "recall": 0.0}
        records = {"per_golden_matches": [], "adjudication_records": [], "diff_context_hash": "h",
                   "primary_judge": "j", "adjudicating_judge": "j"}
        pr = PRSample(url="u", pr_title="t", source_repo="o/r", diff="",
                      golden_comments=[{"comment": "g"}])
        with patch.object(compound_realistic, "review_realistic_async", fake_review), \
             patch.object(run_model_matrix, "judge_pairs_router", fake_judge), \
             patch.object(run_model_matrix, "score_from_matches", lambda *a: scored), \
             patch.object(run_model_matrix, "reclassify_async", fake_reclassify), \
             patch.object(run_model_matrix, "_build_finding_records", lambda *a: records):
            summary = asyncio.run(run_model_matrix._run_cell_async(
                pr, "compound-realistic", "gpt-6-astra", "low", "j"))
        self.assertEqual(summary["usage_convention"], USAGE_CONVENTION)
        # even with a pre-fix (or missing) registration date, a stamped summary is left alone
        self.assertEqual(corrected_per_model_usage(summary, PRE_FIX), per_model)
        self.assertEqual(corrected_per_model_usage(summary, None), per_model)


class AnalysisReaderTests(unittest.TestCase):
    def _tag(self, registered_at):
        run = {"phase": "B", "framework": "compound-realistic", "status": "pass",
               "registered_at": registered_at,
               "_summary": {"per_model_usage": LEGACY, "execution_mode": "cli"}}
        return analysis.segment([run])[0]["per_model_usage"]["gpt-6-astra"]

    def test_legacy_codex_usage_is_corrected(self):
        u = self._tag(PRE_FIX)
        self.assertEqual((u["output_tokens"], u["total_tokens"]), (289, 72772))

    def test_post_fix_usage_is_untouched(self):
        self.assertEqual(self._tag("2026-11-01T00:00:00Z"), LEGACY["gpt-6-astra"])


if __name__ == "__main__":
    unittest.main()
