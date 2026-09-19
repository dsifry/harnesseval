import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


class TimeoutTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('tools.advisory_timeout'))
        from tools import advisory_timeout
        return advisory_timeout

    def test_success_preserves_payload_and_result(self):
        m = self.module()
        command = [sys.executable, '-c', 'import sys,json; print(json.dumps(json.load(sys.stdin)))']
        self.assertEqual(asyncio.run(m.child_call(command, {'effort': 'low'}, 2)), {'effort': 'low'})

    def test_timeout_kills_child_before_late_side_effect(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'late'
            command = [sys.executable, '-c',
                       'import time,pathlib; time.sleep(.3); pathlib.Path(' + repr(str(target)) + ').touch()']
            async def check():
                with self.assertRaises(TimeoutError):
                    await m.child_call(command, {}, .05)
                await asyncio.sleep(.4)
                self.assertFalse(target.exists())
            asyncio.run(check())

    def test_nonzero_exit_is_failure_not_empty_verdict(self):
        m = self.module()
        with self.assertRaises(RuntimeError):
            asyncio.run(m.child_call([sys.executable, '-c', 'raise SystemExit(7)'], {}, 2))

    def test_cancel_kills_child_before_late_side_effect(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'late'
            command = [sys.executable, '-c',
                       'import time,pathlib; time.sleep(.3); pathlib.Path(' + repr(str(target)) + ').touch()']
            async def check():
                task = asyncio.create_task(m.child_call(command, {}, 2))
                await asyncio.sleep(.05)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                await asyncio.sleep(.4)
                self.assertFalse(target.exists())
            asyncio.run(check())

    def test_three_timeouts_are_checkpointed_and_stop_without_a_verdict(self):
        m = self.module()
        from tools import advisory_policy_dedup as policy
        real_child = m.child_call
        async def hanging_child(command, payload, seconds):
            return await real_child([sys.executable, '-c', 'import time; time.sleep(10)'], payload, seconds)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            original = policy.runner.model_router.call_model_json
            try:
                m.install(out / 'extension', .03)
                async def check():
                    calls = policy.PolicyCalls(out, {}, 'https://example.test/pull/1', asyncio.Semaphore(1))
                    with self.assertRaises(RuntimeError):
                        await calls.checked('pair', '0', {'model': 'glm-5.3-background', 'system': 's',
                            'prompt': 'p', 'effort': 'low', 'max_tokens': 8192}, lambda x: x)
                    self.assertTrue(calls.failed)
                    self.assertEqual(calls.audit, [])
                with patch.object(m, 'child_call', hanging_child):
                    asyncio.run(check())
                attempts = [json.loads(p.read_text()) for p in (out / 'attempts').rglob('*.json')]
                self.assertEqual(len(attempts), 3)
                self.assertTrue(all(x['status'] == 'error' and x['error_type'] == 'TimeoutError'
                                    and x['parsed_response'] is None for x in attempts))
            finally:
                policy.runner.model_router.call_model_json = original
