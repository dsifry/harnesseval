"""Full-channel advisory accounting from saved evidence, without model calls."""
import json
import tempfile
import unittest
from pathlib import Path

from tools import report_advisories


class AdvisoryEvidenceTests(unittest.TestCase):
    def evidence(self, original, rj3=None, *, v2=True, counts=None, matched=()):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'runs' / 'run'
            folder.mkdir(parents=True)
            summary = {'adjudication_records': original, 'per_golden_matches': [
                {'matched_candidate': text} for text in matched]}
            if v2:
                summary['n_true_hallucination'] = sum(r['adjudication']['verdict'] == 'hallucination' for r in original)
                summary['n_important_non_bug'] = sum(r['adjudication']['verdict'] == 'important_non_bug' for r in original)
            summary.update(counts or {})
            (folder / 'summary.json').write_text(json.dumps(summary))
            if rj3 is not None:
                (folder / 'readjudication3.json').write_text(json.dumps({'records': rj3}))
            return report_advisories.advisory_evidence(root, {'run_id': 'run'})

    @staticmethod
    def original(text, verdict):
        return {'issue_text': text, 'adjudication': {'verdict': verdict}}

    @staticmethod
    def revised(text, verdict, cluster=None):
        return {'issue_text': text, 'new_verdict': verdict, 'cluster': {'id': cluster} if cluster is not None else None}

    def test_full_channel_union_preserves_uncovered_advisories_and_penalties(self):
        result = self.evidence([self.original('coverage gap', 'important_non_bug'),
                                self.original('specific concern', 'real_but_ungold'),
                                self.original('format nit', 'hallucination'),
                                self.original('vague suggestion', 'hallucination')],
                               [self.revised('specific concern', 'important_non_bug')])
        self.assertEqual((result['accepted_count'], result['penalty_count']), (2, 2))
        self.assertTrue(result['measured'])
        self.assertEqual(len(result['records']), 4)

    def test_revised_verdict_overrides_original_and_preserves_provenance(self):
        result = self.evidence([self.original('[ADVISORY] [P1 confidence 90] coverage gap', 'important_non_bug'),
                                self.original('uncertain', 'important_non_bug')],
                               [self.revised('coverage  gap', 'bug'), self.revised('uncertain', 'unresolved')])
        self.assertEqual((result['accepted_count'], result['unresolved_count']), (0, 1))
        self.assertEqual(sum(len(r['sources']) for r in result['records']), 4)

    def test_deduplicates_exact_text_and_recorded_clusters_only(self):
        result = self.evidence([self.original('[ADVISORY] A', 'important_non_bug'), self.original('A', 'important_non_bug'),
                                self.original('A distinct concern', 'important_non_bug')],
                               [self.revised('B', 'important_non_bug', 0), self.revised('C', 'important_non_bug', 0)])
        self.assertEqual(result['accepted_count'], 3)

    def test_matched_or_effective_bug_group_cannot_receive_advisory_credit(self):
        result = self.evidence([self.original('gold', 'important_non_bug')],
                               [self.revised('bug', 'bug', 7), self.revised('advice', 'important_non_bug', 7)], matched=['[BUG] gold'])
        self.assertEqual(result['accepted_count'], 0)

    def test_v1_unmeasured_differs_from_measured_zero(self):
        self.assertFalse(self.evidence([], v2=False)['measured'])
        self.assertTrue(self.evidence([])['measured'])
        self.assertTrue(self.evidence([], [], v2=False)['measured'])

    def test_rj3_hallucination_replaces_original_advisory(self):
        result = self.evidence([self.original('style preference', 'important_non_bug')],
                               [self.revised('[ADVISORY] style preference', 'hallucination')])
        self.assertEqual((result['accepted_count'], result['penalty_count']), (0, 1))

    def test_code_case_and_meaningful_brackets_are_not_semantically_merged(self):
        result = self.evidence([self.original('array[1] fails', 'important_non_bug'),
                                self.original('array[2] fails', 'important_non_bug'),
                                self.original('Array[1] fails', 'important_non_bug')])
        self.assertEqual(result['accepted_count'], 3)

    def test_absent_record_collection_is_not_observed_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'runs' / 'run'
            folder.mkdir(parents=True)
            (folder / 'summary.json').write_text(json.dumps({'n_true_hallucination': 0}))
            with self.assertRaisesRegex(ValueError, 'adjudication_records'):
                report_advisories.advisory_evidence(Path(temp), {'run_id': 'run'})

    def test_active_common_pass_never_falls_back_to_old_judges(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); folder = root / 'runs/run'; folder.mkdir(parents=True)
            (folder / 'summary.json').write_text(json.dumps({'adjudication_records': [self.original('advice', 'important_non_bug')], 'n_true_hallucination': 0}))
            target = root / 'analysis/verified_gold/advisory_readjudication'; target.mkdir(parents=True)
            (target / 'manifest.json').write_text('{}')
            result = report_advisories.advisory_evidence(root, {'run_id': 'run'})
            self.assertFalse(result['measured'])
            self.assertEqual(result['records'], [])
            self.assertEqual(result['accepted_count'], 0)
            self.assertEqual(result['advisory_run_status'], 'pending')

    def test_complete_common_pass_overrides_older_channels_and_measures_v1(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); folder = root / 'runs/run'; folder.mkdir(parents=True)
            original = [self.original('concern', 'hallucination')]
            summary = {'adjudication_records': original}
            (folder / 'summary.json').write_text(json.dumps(summary))
            target = root / 'analysis/verified_gold/advisory_readjudication/runs'
            target.mkdir(parents=True)
            sha = hashlib.sha256(json.dumps(summary, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            manifest = {'model': 'glm-5.3-vision-background'}
            (target.parent / 'manifest.json').write_text(json.dumps(manifest))
            pass_digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            (target / 'run.json').write_text(json.dumps({'status': 'complete', 'expected_records': 1,
                'summary_sha256': sha, 'pass_digest': pass_digest, 'records': [{**self.revised('concern', 'important_non_bug'), 'original_record_index': 0, 'confidence': .8}]}))
            (target.parent / 'acceptance_policy.json').write_text(json.dumps({'raw_pass_digest': pass_digest, 'minimum_confidence': .8, 'applies_to': 'all_categories', 'below_threshold': 'unresolved'}))
            result = report_advisories.advisory_evidence(root, {'run_id': 'run'})
            self.assertEqual((result['accepted_count'], result['penalty_count']), (1, 0))
            self.assertTrue(result['measured'])
            self.assertEqual(result['classification_source'], 'common_readjudication')
            self.assertEqual(result['acceptance_policy']['minimum_confidence'], .8)
            saved = json.loads((target / 'run.json').read_text())
            saved['records'][0]['confidence'] = .55
            (target / 'run.json').write_text(json.dumps(saved))
            gated = report_advisories.advisory_evidence(root, {'run_id': 'run'})
            self.assertEqual((gated['accepted_count'], gated['penalty_count'], gated['unresolved_count']), (0, 0, 1))
            source = gated['records'][0]['sources'][-1]
            self.assertEqual(source['raw_verdict'], 'important_non_bug')
            self.assertEqual(source['verdict'], 'unresolved')
            self.assertEqual(source['evidence']['confidence'], .55)

    def test_common_acceptance_floor_is_inclusive_and_applies_to_every_category(self):
        policy = {'minimum_confidence': .8}
        for category in ['bug', 'important_non_bug', 'hallucination']:
            for confidence in [.55, .79, None, float('nan')]:
                record = {'new_verdict': category, 'confidence': confidence}
                self.assertEqual(report_advisories.accepted_common_verdict(record, policy), 'unresolved')
                self.assertEqual(record['new_verdict'], category)
            self.assertEqual(report_advisories.accepted_common_verdict({'new_verdict': category, 'confidence': .8}, policy), category)

    def test_common_policy_is_required_and_bound_to_raw_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, 'acceptance policy'):
                report_advisories.load_acceptance_policy(root, 'raw')
            policy = {'raw_pass_digest': 'other', 'minimum_confidence': .8,
                      'applies_to': 'all_categories', 'below_threshold': 'unresolved'}
            (root / 'acceptance_policy.json').write_text(json.dumps(policy))
            with self.assertRaisesRegex(ValueError, 'raw pass'):
                report_advisories.load_acceptance_policy(root, 'raw')
            policy['raw_pass_digest'] = 'raw'
            (root / 'acceptance_policy.json').write_text(json.dumps(policy))
            saved, sha = report_advisories.load_acceptance_policy(root, 'raw')
            self.assertEqual(saved, policy)
            self.assertEqual(len(sha), 64)

    def test_orphan_common_file_requires_frozen_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); folder = root / 'runs/run'; folder.mkdir(parents=True)
            (folder / 'summary.json').write_text(json.dumps({'adjudication_records': []}))
            target = root / 'analysis/verified_gold/advisory_readjudication/runs'; target.mkdir(parents=True)
            (target / 'run.json').write_text(json.dumps({'status': 'complete'}))
            with self.assertRaisesRegex(ValueError, 'missing.*manifest'):
                report_advisories.advisory_evidence(root, {'run_id': 'run'})

    def test_missing_record_evidence_is_reported(self):
        with self.assertWarnsRegex(UserWarning, 'n_important_non_bug'):
            result = self.evidence([], counts={'n_important_non_bug': 3})
        self.assertTrue(result['warnings'])


if __name__ == '__main__':
    unittest.main()

class VerifiedReuseTests(unittest.TestCase):
    def test_verified_reuse_requires_own_assignment_and_registry(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); vg=root/'analysis/verified_gold';vg.mkdir(parents=True)
            text='specific defect'; norm=__import__('readjudicate3').normalize_for_cluster(text)
            amap={'10':{hashlib.sha1(norm.encode()).hexdigest()[:16]:'10-D01'}}
            ap=vg/'DEFECT_ASSIGN.json';ap.write_text(json.dumps(amap))
            (vg/'DEFECT_REGISTRY.json').write_text(json.dumps({'defects':[{'id':'10-D01','tier':'D-verified'}]}))
            record={'issue_text':text,'new_verdict':'bug','confidence':None,'instrument':'reused_verified_bug','defect_ids':['10-D01'],'assignment_sha256':hashlib.sha256(ap.read_bytes()).hexdigest()}
            self.assertEqual(report_advisories.reused_verified_verdict(root,record,{'url':'https://github.com/a/b/pull/10'}),'bug')
            record['issue_text']='unsupported additional claim'
            with self.assertRaisesRegex(ValueError,'own audited assignment'):
                report_advisories.reused_verified_verdict(root,record,{'url':'https://github.com/a/b/pull/10'})
