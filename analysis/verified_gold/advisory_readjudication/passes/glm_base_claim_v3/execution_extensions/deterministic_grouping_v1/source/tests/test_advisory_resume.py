import asyncio
import inspect
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tools import readjudicate_report_advisories as runner
from tools.advisory_resume import (
    build_resume_grouping, freeze_proposal, load_proposal, proposal_binding,
    reconstruct_original_proposal, stable_results,
)


class ResumeTests(unittest.TestCase):
    def test_original_paid_partition_wins_and_cross_pr_reuse_is_rejected(self):
        url = 'https://example.test/repo/pull/1'
        plan = {'url': url, 'units': [
            {'defect_ids': [], 'location': ['x.py', 1, 2]} for _ in range(2)]}
        bucket = ['unresolved', 'x.py']; key = runner.digest(tuple(bucket))[:10]
        def call(name, stamp, mapping):
            return (Path(name), stamp, {'url': url, 'status': 'complete',
                    'request': {'units': [0, 1]}, 'parsed_response': mapping})
        calls = [call(f'{key}_000_initial.json', 1, {'0': 0, '1': 1}),
                 call(f'{key}_merge_original.json', 2, {'0': 0, '1': 0}),
                 call(f'{key}_merge_extra.json', 3, {'0': 0, '1': 1})]
        groups, used, excluded = reconstruct_original_proposal(plan, {0: bucket, 1: bucket}, calls)
        self.assertEqual(groups, [[0, 1]])
        self.assertEqual([p.name for p in excluded], [f'{key}_merge_extra.json'])
        self.assertEqual(len(used), 2)
        calls[0][2]['url'] = 'https://different.test/repo/pull/1'
        with self.assertRaises(ValueError):
            reconstruct_original_proposal(plan, {0: bucket, 1: bucket}, calls)

    def test_completion_order_cannot_change_merge_order(self):
        rows = [(('bug', 'x.py'), '002', [[2]]),
                (('bug', 'x.py'), '000', [[0]]),
                (('bug', 'x.py'), '001', [[1]])]
        self.assertEqual(stable_results(rows), stable_results(list(reversed(rows))))
        self.assertEqual([r[2] for r in stable_results(rows)], [[[0]], [[1]], [[2]]])

    def test_proposal_rejects_stale_inputs_or_incomplete_partition(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'proposal.json'
            binding = {'pass_digest': 'pass', 'membership_sha256': 'one'}
            freeze_proposal(path, binding, [[0], [1]], 2)
            self.assertEqual(load_proposal(path, binding, 2), [[0], [1]])
            with self.assertRaises(ValueError):
                load_proposal(path, {**binding, 'membership_sha256': 'changed'}, 2)
            for groups in [[[0]], [[0], [0]], [[False], [1]], [[0], [2]]]:
                with self.assertRaises(ValueError):
                    freeze_proposal(Path(tmp) / 'invalid.json', binding, groups, 2)

    def test_saved_proposal_resumes_without_any_grouping_call(self):
        url = 'https://example.test/repo/pull/1'
        members = [{'record': {'issue_text': 'claim A'}}, {'record': {'issue_text': 'claim B'}}]
        plan = {'url': url, 'units': [
            {'representative': i, 'members': [i], 'defect_ids': []} for i in range(2)]}
        args = SimpleNamespace(group_judge='glm-5.3-background', effort='low', concurrency=4)
        categories = {0: 'unresolved', 1: 'unresolved'}
        function, source = build_resume_grouping()
        # The original comparison and output code is retained exactly.
        tail = inspect.getsource(runner.reuse_grouping).split('    async def compare_pairs(pairs):', 1)[1]
        self.assertEqual(source.split('    async def compare_pairs(pairs):', 1)[1], tail)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            freeze_proposal(out / 'proposal_checkpoints' / f'{runner.pr_key(url)}.json',
                            proposal_binding(plan, members, 'pass', categories), [[0], [1]], 2)
            forbidden = AsyncMock(side_effect=AssertionError('No model request allowed'))
            with patch.object(runner.model_router, 'call_model_json', forbidden):
                result = asyncio.run(function(plan, members, args, asyncio.Semaphore(4), out, 'pass', categories))
            forbidden.assert_not_called()
            self.assertEqual(result['duplicate_cids'], [0, 1])

    def test_pair_failure_keeps_proposal_and_resume_only_requests_pairs(self):
        url = 'https://example.test/repo/pull/2'
        members = [{'record': {'issue_text': text}} for text in ['claim A', 'claim B']]
        plan = {'url': url, 'units': [
            {'representative': i, 'members': [i], 'defect_ids': [],
             'location': ['x.py', 1, 2], 'old_groups': []} for i in range(2)]}
        args = SimpleNamespace(group_judge='glm-5.3-background', effort='low', concurrency=4)
        categories = {0: 'unresolved', 1: 'unresolved'}
        function, _ = build_resume_grouping()
        async def fail_pairs(model, system, prompt, **kwargs):
            if system == runner.GROUP_SYSTEM:
                return {'0': 0, '1': 0}, 1, 1, {}
            raise RuntimeError('injected pair failure')
        fields = {'mechanism': 'same', 'trigger': 'same', 'consequence': 'same'}
        vote = {'pairs': [{'pair': 1, 'a': fields, 'b': fields,
                          'material_differences': [], 'same': True,
                          'confidence': .9, 'reason': 'equivalent'}]}
        async def resume_pairs(model, system, prompt, **kwargs):
            self.assertNotEqual(system, runner.GROUP_SYSTEM)
            return vote, 1, 1, {}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch.object(runner.model_router, 'call_model_json', fail_pairs):
                with self.assertRaises(RuntimeError):
                    asyncio.run(function(plan, members, args, asyncio.Semaphore(4), out, 'pass', categories))
            checkpoint = out/'proposal_checkpoints'/f'{runner.pr_key(url)}.json'
            self.assertEqual(load_proposal(checkpoint, proposal_binding(plan, members, 'pass', categories), 2), [[0, 1]])
            before = checkpoint.read_bytes()
            with patch.object(runner.model_router, 'call_model_json', resume_pairs):
                result = asyncio.run(function(plan, members, args, asyncio.Semaphore(4), out, 'pass', categories))
            self.assertEqual(checkpoint.read_bytes(), before)
            self.assertEqual(result['duplicate_cids'], [0, 0])


if __name__ == '__main__':
    unittest.main()
