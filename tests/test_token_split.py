"""ReviewRun.tokens_in / tokens_out must partition per_model_usage.

tokens_in  = input + cache_read + cache_creation   (every input-side token)
tokens_out = output + reasoning                    (every output-side token)
tokens_in + tokens_out == grand_total(per_model)["total_tokens"]
"""
import asyncio
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from harnesseval import model_router
from harnesseval.adapters import compound_realistic, metareview_realistic, superpowers_realistic
from harnesseval.adapters.base import PRSample
from harnesseval.usage import from_codex_cli, grand_total, split_in_out

# Real codex-cli 0.160.0 usage: 21,993 input (6,016 cached) + 184 output (134 reasoning) = 22,177
CODEX_RECORD = {"input_tokens": 21993, "cached_input_tokens": 6016,
                "output_tokens": 184, "reasoning_output_tokens": 134, "total_tokens": 22177}
EXPECTED_IN, EXPECTED_OUT = 21993, 184


def codex_usage():
    return from_codex_cli(CODEX_RECORD, "gpt-6-astra")


class RouterSplitTests(unittest.TestCase):
    def test_cli_split_partitions_usage(self):
        async def fake_cli(model, system, user, effort):
            return "ok", codex_usage()

        with patch.object(model_router, "_call_cli", fake_cli):
            _, tin, tout, per_model = asyncio.run(
                model_router.call_model("gpt-6-astra", "sys", "user", execution_mode="cli"))
        self.assertEqual((tin, tout), (EXPECTED_IN, EXPECTED_OUT))
        self.assertEqual(tin + tout, grand_total(per_model)["total_tokens"])

    def test_openai_api_split_counts_reasoning_as_output(self):
        usage = NS(prompt_tokens=1000, completion_tokens=300, model_extra={},
                   completion_tokens_details=NS(reasoning_tokens=120),
                   prompt_tokens_details=NS(cached_tokens=400))
        resp = NS(usage=usage, choices=[NS(message=NS(content="ok"))])
        client = NS(chat=NS(completions=NS(create=lambda **kw: resp)))
        with patch.object(model_router.keys, "openai_client", lambda: client):
            text, tin, tout, per_model = asyncio.run(
                model_router.call_model("gpt-6-astra", "sys", "user"))
        self.assertEqual((text, tin, tout), ("ok", 1000, 300))
        self.assertEqual(tin + tout, grand_total(per_model)["total_tokens"])

    def test_anthropic_api_split_includes_cache_tokens(self):
        usage = NS(input_tokens=10, cache_read_input_tokens=200,
                   cache_creation_input_tokens=3000, output_tokens=40)
        resp = NS(usage=usage, content=[NS(type="text", text="ok")])
        client = NS(messages=NS(create=lambda **kw: resp))
        with patch.object(model_router.keys, "anthropic_client", lambda: client):
            text, tin, tout, _ = asyncio.run(
                model_router.call_model("claude-opus-5", "sys", "user"))
        self.assertEqual((text, tin, tout), ("ok", 3210, 40))

    def test_unknown_provider_raises(self):
        with self.assertRaisesRegex(ValueError, "^unknown model provider for: mystery-1$"):
            asyncio.run(model_router.call_model("mystery-1", "sys", "user"))


class SplitInOutTests(unittest.TestCase):
    def test_missing_fields_default_to_zero(self):
        self.assertEqual(split_in_out({"a": {}, "b": {"input_tokens": 1, "output_tokens": 2}}), (1, 2))

    def test_sums_every_field_across_models(self):
        per_model = {"a": {"input_tokens": 1, "cache_read_input_tokens": 20,
                           "cache_creation_input_tokens": 300, "output_tokens": 4000,
                           "reasoning_output_tokens": 50000},
                     "b": {"input_tokens": 600000, "output_tokens": 7000000}}
        self.assertEqual(split_in_out(per_model), (600321, 7054000))


class RealisticAdapterSplitTests(unittest.TestCase):
    PR = PRSample(url="https://github.com/o/r/pull/1", pr_title="t", source_repo="o/r", diff="")

    def _run(self, module, resolved):
        async def fake_session(repo_dir, slug, effort, prompt, timeout=None):
            return "no findings", codex_usage(), resolved

        clock = iter([100.0])
        fake_time = NS(time=lambda: next(clock, 102.5))  # t0 = 100.0, every later call 102.5
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "init", "-q", repo], check=True)
            with patch.object(module, "materialize", lambda url: Path(repo)), \
                 patch.object(module, "_run_codex_session", fake_session), \
                 patch.object(module, "time", fake_time):
                return module.review_realistic(self.PR, "gpt-6-astra", "low")

    def _check(self, module):
        run = self._run(module, resolved="gpt-6-astra-resolved")
        self.assertIsNone(run.error)
        self.assertEqual((run.tokens_in, run.tokens_out), (EXPECTED_IN, EXPECTED_OUT))
        self.assertEqual(run.tokens_in + run.tokens_out,
                         grand_total(run.per_model_usage)["total_tokens"])
        self.assertEqual(run.framework, module.__name__.rsplit(".", 1)[1].replace("_", "-"))
        self.assertEqual((run.model, run.effort, run.execution_mode),
                         ("gpt-6-astra-resolved", "low", "cli"))
        self.assertEqual((run.raw_output, run.findings), ("no findings", []))
        self.assertEqual(run.wall_ms, 2500.0)
        self.assertEqual(run.total_cost_usd, 0.0)
        # unresolved model id falls back to the requested one
        self.assertEqual(self._run(module, resolved="").model, "gpt-6-astra")

    def test_compound_realistic(self):
        self._check(compound_realistic)

    def test_metareview_realistic(self):
        self._check(metareview_realistic)

    def test_superpowers_realistic(self):
        self._check(superpowers_realistic)


if __name__ == "__main__":
    unittest.main()
