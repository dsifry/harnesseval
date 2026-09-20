"""Thin full-channel runner tests; reuse the established rj3 classifier."""
import json
import tempfile
import unittest
from pathlib import Path
from tools import readjudicate_report_advisories as runner


class RunnerTests(unittest.TestCase):
    def test_representative_matcher_indices_are_reused(self):
        from unittest.mock import patch
        import difflib
        import readjudicate3 as rj
        matcher = difflib.SequenceMatcher
        texts = ['aaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbb', 'ccccccccccccccc', 'ddddddddddddddd']
        with patch.object(difflib, 'SequenceMatcher', wraps=matcher) as constructors:
            self.assertEqual(rj.cluster_texts(texts), [0, 1, 2, 3])
            self.assertLessEqual(constructors.call_count, len(texts))

    def test_impossible_similarity_skips_expensive_ratio(self):
        from unittest.mock import patch
        import difflib
        import readjudicate3 as rj
        with patch.object(difflib.SequenceMatcher, 'ratio', side_effect=AssertionError('unneeded full ratio')):
            self.assertEqual(rj.cluster_texts(['short', 'very long unrelated string with many tokens']), [0, 1])

    def test_optimized_clustering_preserves_original_partition(self):
        import difflib
        import readjudicate3 as rj
        import random
        # Frozen original algorithm: reference used only for equivalence.
        def original(texts, threshold):
            reps, out = [], []
            for text in texts:
                norm = rj.normalize_for_cluster(text)
                ratios = [1.0 if norm == rep else difflib.SequenceMatcher(None, norm, rep).ratio() for rep in reps]
                best = max(range(len(ratios)), key=ratios.__getitem__) if ratios else -1
                if best >= 0 and ratios[best] >= threshold:
                    out.append(best)
                else:
                    reps.append(norm); out.append(len(reps)-1)
            return out
        rng = random.Random(91)
        seeds = ['array[1] overflows buffer in handler', 'array[2] overflows buffer in handler',
                 'a' * 240 + 'b', 'b' + 'a' * 240, 'missing tests for deploy switch', '', '[confidence:90] missing timeout']
        texts = seeds + [' '.join(rng.choices(['handler', 'timeout', 'query', 'migration', 'nil', 'fails'], k=rng.randrange(3, 12))) for _ in range(70)]
        for threshold in [.3, .75, 1.0]:
            self.assertEqual(rj.cluster_texts(texts, threshold), original(texts, threshold))

    def test_selection_includes_all_unmatched_channels(self):
        records = [{'issue_text': label, 'primary_judge_verdict': label,
                    'adjudication': {'verdict': label}} for label in
                   ['important_non_bug', 'real_but_ungold', 'hallucination', 'unresolved', 'unjudged', 'matched']]
        selected = runner.unmatched_records({'adjudication_records': records})
        self.assertEqual(len(selected), 5)
        self.assertNotIn('matched', [r['issue_text'] for _, r in selected])

    def test_matching_normalized_golden_candidate_is_excluded(self):
        s = {'adjudication_records': [{'issue_text': '[ADVISORY] same', 'adjudication': {'verdict': 'important_non_bug'}}],
             'per_golden_matches': [{'matched_candidate': '[BUG] same'}]}
        self.assertEqual(runner.unmatched_records(s), [])

    def test_frozen_manifest_compares_json_semantics(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'manifest.json'
            runner.freeze_manifest(path, {'patterns': [('regex', 2)]})
            runner.freeze_manifest(path, {'patterns': [('regex', 2)]})

    def test_resume_rejects_changed_frozen_input(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'manifest.json'
            runner.freeze_manifest(path, {'digest': 'first'})
            runner.freeze_manifest(path, {'digest': 'first'})
            with self.assertRaisesRegex(ValueError, 'changed'):
                runner.freeze_manifest(path, {'digest': 'second'})

    def test_progress_counts_only_current_and_explicitly_reused_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            runner.write_json(out / 'manifest.json', {'runs': [{}, {}]})
            runner.write_json(out / 'grouping_calls/1/current.json', {'pass_digest': 'current', 'status': 'complete'})
            runner.write_json(out / 'grouping_calls/1/reused.json', {'pass_digest': 'prior', 'status': 'complete'})
            runner.write_json(out / 'grouping_calls/1/stale.json', {'pass_digest': 'stale', 'status': 'complete'})
            runner.write_json(out / 'verdicts/1/0.json', {'pass_digest': 'current', 'status': 'complete'})
            runner.write_progress(out, 'current', 'classification', ['prior'])
            progress = json.loads((out / 'progress.json').read_text())
            self.assertEqual(progress['grouping_calls_complete'], 2)
            self.assertEqual(progress['classification_clusters_complete'], 1)
            self.assertEqual(progress['expected_runs'], 2)

    def test_classifier_candidate_removes_reviewer_labels(self):
        self.assertEqual(runner.classifier_candidate({'issue_text': '[ADVISORY] [P1] [confidence:90] Foo[1] fails'}), 'Foo[1] fails')

    def test_reused_grouping_requires_matching_stage_inputs_and_model(self):
        prior = {'model': 'glm', 'grouping_mode': 'chunked_semantic_v1', 'grouping_prompt_sha256': 'p',
                 'grouping_chunk': 60, 'grouping_text_limit': 500, 'grouping_context_limit': 350000,
                 'membership_sha256': 'members', 'diff_hashes': {'pr': 'd'}}
        current = {**prior, 'grouping_model': 'glm', 'classifier_cleaning': 'new cleaning'}
        self.assertTrue(runner.compatible_grouping_stage(prior, current))
        self.assertFalse(runner.compatible_grouping_stage(prior, {**current, 'membership_sha256': 'changed'}))
        self.assertFalse(runner.compatible_grouping_stage(prior, {**current, 'grouping_model': 'different'}))

    def test_group_mapping_requires_every_index_and_valid_group_ids(self):
        self.assertEqual(runner.validate_group_mapping({'0': 0, '1': 0, '2': 2}, 3), [[0, 1], [2]])
        for result in [{'0': 0}, {'0': 0, '1': 1, '2': 2}, {'0': 0, '1': True}, {'0': 0, '1': -1}, {'0': 0, '1': 'missing'}]:
            with self.subTest(result=result), self.assertRaises(ValueError):
                runner.validate_group_mapping(result, 2)

    def test_scope_uses_verified_grid_not_only_model_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'analysis').mkdir()
            rows = [{'run_id': 'a', 'model': 'm', 'framework': 'f', 'effort': e, 'url': 'pr'} for e in ['low', 'extra']]
            (root / 'analysis/final_report_dataset.json').write_text(json.dumps({'top6': ['pr'], 'selected_runs': rows}))
            (root / 'analysis/final_report_metrics.json').write_text(json.dumps({'true_gold_defects': {'verified': {'cells': {'m|f|low': {}}}}}))
            self.assertEqual([r['effort'] for r in runner.selected_runs(root)], ['low'])


class GroupingCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def test_cross_chunk_membership_is_complete_and_resume_reuses_requests(self):
        import asyncio
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, patch
        args = SimpleNamespace(judge='classifier', group_judge='grouping', reused_grouping_passes=[], group_pilot=0)
        provider = AsyncMock(return_value=({'0': 0, '1': 0}, 10, 4, {}))
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            with patch.object(runner, 'GROUP_CHUNK', 2), patch.object(runner.model_router, 'call_model_json', provider):
                cids = await runner.chunked_groups(['A', 'B', 'C', 'D'], 'https://example/pull/1', args, asyncio.Semaphore(2), 'pass', out)
                self.assertEqual(cids, [0, 0, 0, 0])
                self.assertEqual(provider.await_count, 3)
                provider.reset_mock()
                provider.side_effect = AssertionError('Completed grouping calls must be reused')
                self.assertEqual(await runner.chunked_groups(['A', 'B', 'C', 'D'], 'https://example/pull/1', args, asyncio.Semaphore(2), 'pass', out), cids)
                provider.assert_not_awaited()
            self.assertEqual(len(list((out / 'grouping_calls/1').glob('*.json'))), 3)


if __name__ == '__main__': unittest.main()

class ReusePlanTests(unittest.TestCase):
    def test_validated_locations_and_overlap_are_pr_local(self):
        paths = {'src/a.py', 'src/b.py'}
        self.assertEqual(runner.validated_location('a.py:10-20 concern', paths), ('src/a.py', 10, 20))
        self.assertEqual(runner.validated_location('obj.run is wrong', paths), (None, None, None))
        self.assertTrue(runner.intervals_overlap(('src/a.py', 10, 20), ('src/a.py', 18, 24)))
        self.assertFalse(runner.intervals_overlap(('src/a.py', 10, 20), ('src/b.py', 18, 24)))
        self.assertNotEqual(runner.pr_key('https://github.com/a/b/pull/1'), runner.pr_key('https://github.com/c/d/pull/1'))

    def test_reuse_splits_conflicting_defects_and_files(self):
        units = [{'members':[0], 'defect_ids':['D1'], 'location':('a.py',1,3)},
                 {'members':[1], 'defect_ids':['D2'], 'location':('a.py',2,3)},
                 {'members':[2], 'defect_ids':[], 'location':('b.py',1,3)}]
        out = runner.constrained_groups([[0,1,2]], units)
        self.assertEqual(out, [[0],[1],[2]])

    def test_unknown_location_is_not_a_match(self):
        self.assertFalse(runner.intervals_overlap((None,None,None),(None,None,None)))

    def test_active_pass_requires_bound_manifest(self):
        from tools.report_advisories import common_pass_directory
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); base=root/'analysis/verified_gold/advisory_readjudication'; base.mkdir(parents=True)
            (base/'active_pass.json').write_text(json.dumps({'directory':'passes/v2','manifest_sha256':'bad'}))
            with self.assertRaises(ValueError): common_pass_directory(root)

class CommonStaffBarTests(unittest.TestCase):
    def test_common_prompt_reuses_staff_bar_preserves_historical_contract(self):
        from tools import enum_advisory_ceiling, score_flips
        from unittest.mock import patch
        original=runner.rj.V2_PROMPT
        prompt=runner.common_classifier_prompt()
        for line in enum_advisory_ceiling.BAR.splitlines():
            if line.startswith('- '):self.assertIn(line,prompt)
        self.assertIn('concrete benefit',prompt)
        with patch.object(runner.rj,'V2_PROMPT',prompt):self.assertEqual(score_flips.prompt_contract_holds(),[])
        self.assertEqual(runner.rj.V2_PROMPT,original)

    def test_group_prompt_prohibits_false_consequence_propagation(self):
        self.assertIn('materially equivalent factual claims and consequences',runner.GROUP_PROMPT)
        self.assertIn('invented active execution path',runner.GROUP_PROMPT)

    def test_raw_anchor_metadata_is_recovered(self):
        self.assertEqual(runner.validated_location('[anchor src/a.py:10-20] missing test',{'src/a.py'}),('src/a.py',10,20))

class PaidPropagationTests(unittest.TestCase):
    def test_paid_same_location_vote_cannot_make_false_active_claim_a_fixed_bug(self):
        import hashlib
        from unittest.mock import patch
        url='https://github.com/a/b/pull/10'
        texts=['src/a.py:10 saveChanges is an inert API', 'src/a.py:10 active saveChanges fails users']
        members=[{'run_id':'r','record_index':i,'record':{'issue_text':t}} for i,t in enumerate(texts)]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); prior=root/'prior';(prior/'grouping_calls/10').mkdir(parents=True)
            vg=root/'analysis/verified_gold';vg.mkdir(parents=True)
            key=hashlib.sha1(runner.rj.normalize_for_cluster(texts[0]).encode()).hexdigest()[:16]
            (vg/'DEFECT_ASSIGN.json').write_text(json.dumps({'10':{key:'10-D01'}}))
            (vg/'DEFECT_REGISTRY.json').write_text(json.dumps({'defects':[{'id':'10-D01','tier':'D-verified'}]}))
            (root/'analysis/final_report_dataset.json').write_text(json.dumps({'all_healthy_runs':[]}))
            (root/'analysis/exp_union_semantic_pilot_10.json').write_text(json.dumps({'finding_to_cluster':{}}))
            (root/'analysis/semantic_true_golden_verify_10.json').write_text(json.dumps({'clusters':[]}))
            (prior/'manifest.json').write_text(json.dumps({'membership_sha256':runner.digest({url:members})}))
            (prior/'grouping_calls/10/chunk0.json').write_text(json.dumps({'status':'complete','request':{'indices':[0,1]},'parsed_response':{'0':0,'1':0}}))
            with patch.object(runner,'inventory',return_value=([],{}, {url:members})):
                seed=runner.reuse_inventory(root,url,members,'+++ b/src/a.py\n',prior)
            self.assertEqual(len(seed['units']),2)
            self.assertEqual(seed['units'][0]['members'],[0])
            self.assertEqual(seed['units'][1]['defect_ids'],[])
            self.assertTrue(seed['units'][1]['paid_sources'])

class FullClaimGroupingTests(unittest.IsolatedAsyncioTestCase):
    async def test_grouping_sees_claims_after_old_500_character_limit(self):
        import asyncio
        from types import SimpleNamespace
        from unittest.mock import patch
        prefix='a.py:10 '+('shared context '*50)
        texts=[prefix+' inert API concern',prefix+' unsupported active-path claim']
        members=[{'record':{'issue_text':t}} for t in texts]
        units=[{'members':[i],'representative':i,'location':('a.py',10,10),'old_groups':[],'defect_ids':[]} for i in range(2)]
        calls=[]
        async def fake(*args,**kwargs):
            calls.append(args[2]);return {'0':0,'1':1},0,0,{}
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner.model_router,'call_model_json',side_effect=fake):
            plan=await runner.reuse_grouping({'url':'https://github.com/a/b/pull/1','units':units},members,SimpleNamespace(group_judge='test',concurrency=1,effort='low'),asyncio.Semaphore(1),Path(tmp),'pass')
        self.assertEqual(plan['cids'],[0,1])
        self.assertTrue(all('unsupported active-path claim' in p and 'inert API concern' in p for p in calls))

class SequentialCliTests(unittest.IsolatedAsyncioTestCase):
    async def test_legacy_bounded_flags_rejected_before_inventory_or_calls(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        for option in ['pilot','group_pilot','cluster_only','cluster_pr','reuse_grouping_manifest']:
            args=SimpleNamespace(**{option:1})
            with patch.object(runner,'inventory',side_effect=AssertionError('must not inventory')):
                with self.assertRaisesRegex(ValueError,'unsupported'):
                    await runner.sequential_main(args)
