"""Scoring gates must not change raw classifications or inflate duplicate credit."""
import copy
import unittest
from tools import advisory_scoring_policy as scoring

POLICY = {'advisory_minimum_confidence': .7, 'penalty_minimum_confidence': .8,
          'bug_label_minimum_confidence': .8}


class PolicyTests(unittest.TestCase):
    def test_credit_and_penalty_boundaries_are_inclusive_and_separate(self):
        for category, confidence, expected in [
            ('important_non_bug', .6999, 'below_scoring_threshold'),
            ('important_non_bug', .7, 'accepted'),
            ('important_non_bug', .8, 'accepted'),
            ('hallucination', .7, 'below_scoring_threshold'),
            ('hallucination', .7999, 'below_scoring_threshold'),
            ('hallucination', .8, 'penalty'),
            ('bug', .7, 'below_scoring_threshold'),
            ('bug', .8, 'excluded_bug')]:
            with self.subTest(category=category, confidence=confidence):
                self.assertEqual(scoring.decision(category, confidence, POLICY), expected)

    def test_invalid_scores_are_rejected_instead_of_silently_counted(self):
        for value in [None, True, float('nan'), float('inf'), -.1, 1.1]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                scoring.decision('important_non_bug', value, POLICY)

    def test_raw_vote_survives_legacy_processed_label(self):
        saved = {'status':'complete', 'instrument':'glm-5.3-background',
                 'result':{'verdict':'unresolved','confidence':.4,
                           'votes':[{'category':'important_non_bug','confidence':.4}]}}
        original = copy.deepcopy(saved)
        self.assertEqual(scoring.raw_vote(saved), ('important_non_bug', .4))
        self.assertEqual(saved, original)

    def test_missing_or_multiple_votes_fail_closed(self):
        for votes in [[], [{'error':'parse'}], [{'category':'bug','confidence':.9}]*2]:
            with self.assertRaises(ValueError):
                scoring.raw_vote({'status':'complete','result':{'votes':votes}})

    def test_newly_eligible_paraphrase_does_not_double_credit_or_get_vetoed(self):
        records = [dict(issue_text=text, verdict_path=f'{i}.json', duplicate_group_id=i,
                        original_record_index=i, instrument='glm-5.3-background')
                   for i,text in enumerate(['high advice','same advice','weak advice','weak penalty','strong penalty'])]
        votes = {f'{i}.json': {'status':'complete','result':{'votes':[{'category':category,'confidence':confidence}]}}
                 for i,(category,confidence) in enumerate([
                     ('important_non_bug',.9),('important_non_bug',.7),('important_non_bug',.6),
                     ('hallucination',.75),('hallucination',.8)])}
        before = copy.deepcopy((records,votes))
        result = scoring.score_records(records, votes, {'0':7,'1':7}, POLICY)
        self.assertEqual((result['accepted_count'],result['penalty_count'],result['below_threshold_count']), (1,1,2))
        accepted = next(r for r in result['records'] if r['decision']=='accepted')
        self.assertEqual(len(accepted['sources']),2)
        weak = next(r for r in result['records'] if r['sources'][0]['issue_text']=='weak penalty')
        self.assertEqual(weak['sources'][0]['raw_verdict'],'hallucination')
        self.assertEqual((records,votes),before)

    def test_unvalidated_advisory_identity_prevents_scoring(self):
        records=[{'issue_text':'advice','verdict_path':'0.json','duplicate_group_id':0,'original_record_index':0}]
        votes={'0.json':{'status':'complete','result':{'votes':[{'category':'important_non_bug','confidence':.7}]}}}
        with self.assertRaisesRegex(ValueError,'dedup'):
            scoring.score_records(records,votes,{},POLICY)

    def test_fixed_verified_bug_bypasses_model_confidence_but_never_gets_bonus(self):
        record={'issue_text':'verified bug','verdict_path':'0.json','duplicate_group_id':0,
                'instrument':'reused_verified_bug','defect_ids':['4-D01'],'original_record_index':0}
        result=scoring.score_records([record],{}, {},POLICY)
        self.assertEqual((result['accepted_count'],result['penalty_count']),(0,0))
        self.assertEqual(result['records'][0]['decision'],'excluded_bug')

if __name__ == '__main__':
    unittest.main()

class PolicyIntegrationTests(unittest.TestCase):
    def make_fixture(self, root):
        import json, hashlib
        canonical=lambda v: hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        base=root/'analysis/verified_gold/advisory_readjudication'
        (root/'runs/run').mkdir(parents=True)
        (base/'runs').mkdir(parents=True)
        (base/'verdicts').mkdir()
        directory=base/'scoring_policies/test'
        (directory/'groups').mkdir(parents=True)
        summary={'adjudication_records':[{'issue_text':'advice','adjudication':{'verdict':'important_non_bug'}}]}
        (root/'runs/run/summary.json').write_text(json.dumps(summary))
        manifest={'model':'glm-5.3-background'}
        sha=canonical(manifest)
        (base/'manifest.json').write_text(json.dumps(manifest))
        (base/'acceptance_policy.json').write_text(json.dumps({'raw_pass_digest':sha,'minimum_confidence':.8,'applies_to':'all_categories','below_threshold':'unresolved'}))
        url='https://github.com/a/b/pull/4'
        policy={**POLICY,'raw_pass_digest':sha,'below_threshold':'classified_but_unscored'}
        psha=canonical(policy)
        (directory/'policy.json').write_text(json.dumps(policy))
        (base/'active_scoring_policy.json').write_text(json.dumps({'directory':'scoring_policies/test','policy_sha256':psha}))
        record={'issue_text':'advice','new_verdict':'important_non_bug','confidence':.7,
                'original_record_index':0,'verdict_path':'verdicts/0.json','duplicate_group_id':4,'cluster':{'id':'4:unresolved'}}
        (base/'runs/run.json').write_text(json.dumps({'status':'complete','pass_digest':sha,
            'expected_records':1,'summary_sha256':canonical(summary),'records':[record]}))
        vp=base/'verdicts/0.json'
        vp.write_text(json.dumps({'status':'complete','pass_digest':sha,'url':url,'judged_text':'advice',
                                 'result':{'votes':[{'category':'important_non_bug','confidence':.7}]}}))
        gp=directory/'groups'/('4-'+canonical(url)[:12]+'.json')
        gp.write_text(json.dumps({'status':'complete','url':url,'raw_pass_digest':sha,'policy_sha256':psha,
                                 'claim_to_group':{'0':0},'eligible_claim_ids':[0],
                                 'classification_sha256':{'0':hashlib.sha256(vp.read_bytes()).hexdigest()}}))
        groups=json.loads(gp.read_text())
        binding={k:groups[k] for k in ('url','raw_pass_digest','policy_sha256','classification_sha256')}
        binding['source_sha256']={'frozen.py':'source-hash'}
        groups['source_sha256']=binding['source_sha256']
        request={'url':url,'pairs':[[0,1]]}
        checkpoints=[]
        for parent,name,value in [
            (directory,'pair_calls/policy.json',{'binding':binding,'url':url,'status':'complete',
                'request':request,'request_sha256':canonical(request)}),
            (base,'pair_calls/reused.json',{'pass_digest':sha,'url':url,'status':'complete',
                'request':request,'request_sha256':canonical(request)})]:
            checkpoint=parent/name;checkpoint.parent.mkdir(parents=True,exist_ok=True)
            checkpoint.write_text(json.dumps(value))
            checkpoints.append({'path':name,'sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest()})
        audit=directory/'audit/pr.json';audit.parent.mkdir()
        audit.write_text(json.dumps({'binding':binding,'validated_groups':[[0]],
                                    'policy_calls':[checkpoints[0]],'reused_pair_checkpoints':[checkpoints[1]]}))
        groups['audit']={'path':'audit/pr.json','sha256':hashlib.sha256(audit.read_bytes()).hexdigest()}
        gp.write_text(json.dumps(groups))
        return {'run_id':'run','url':url},vp,gp

    def test_active_policy_scores_saved_vote_and_waits_for_dedup(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run,vp,gp=self.make_fixture(root)
            result=scoring.advisory_evidence(root,run)
            self.assertEqual(result['accepted_count'],1)
            self.assertTrue(result['measured'])
            gp.unlink()
            result=scoring.advisory_evidence(root,run)
            self.assertFalse(result['measured'])
            self.assertEqual(result['advisory_run_status'],'pending')
            self.assertEqual(result['records'],[])

    def test_changed_raw_vote_cannot_reuse_policy_dedup(self):
        import tempfile,json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run,vp,gp=self.make_fixture(root)
            saved=json.loads(vp.read_text());saved['result']['votes'][0]['confidence']=.9
            vp.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError,'hash'):
                scoring.advisory_evidence(root,run)

    def test_policy_mapping_must_equal_its_verified_audit_partition(self):
        import tempfile,json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run,vp,gp=self.make_fixture(root)
            groups=json.loads(gp.read_text());groups['claim_to_group']['0']=7
            gp.write_text(json.dumps(groups))
            with self.assertRaisesRegex(ValueError,'mapping'):
                scoring.advisory_evidence(root,run)

    def test_audit_and_checkpoint_provenance_fail_closed_after_valid_read(self):
        import tempfile,json,hashlib
        from pathlib import Path
        for scenario in ['audit_hash','audit_escape','binding','source_binding','missing_member',
                         'duplicate_member','boolean_member','boolean_group','policy_hash',
                         'reused_hash','policy_binding','reused_binding','request_hash','checkpoint_escape']:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);run,vp,gp=self.make_fixture(root)
                self.assertEqual(scoring.advisory_evidence(root,run)['accepted_count'],1)
                directory=gp.parent.parent;common=vp.parent.parent
                groups=json.loads(gp.read_text());ap=directory/groups['audit']['path']
                audit=json.loads(ap.read_text());reseal=True
                if scenario=='audit_hash':
                    audit['extra']='changed';reseal=False
                elif scenario=='audit_escape':groups['audit']['path']='../../outside.json'
                elif scenario=='binding':audit['binding']['url']='other-pr'
                elif scenario=='source_binding':audit['binding']['source_sha256']={}
                elif scenario=='missing_member':audit['validated_groups']=[]
                elif scenario=='duplicate_member':audit['validated_groups']=[[0],[0]]
                elif scenario=='boolean_member':audit['validated_groups']=[[False]]
                elif scenario=='boolean_group':groups['claim_to_group']['0']=False
                else:
                    reused=scenario.startswith('reused')
                    key='reused_pair_checkpoints' if reused else 'policy_calls'
                    entry=audit[key][0];cp=(common if reused else directory)/entry['path']
                    value=json.loads(cp.read_text())
                    if scenario.endswith('hash') and scenario!='request_hash':value['extra']='changed'
                    elif scenario=='policy_binding':value['binding']['policy_sha256']='other-policy'
                    elif scenario=='reused_binding':value['pass_digest']='other-pass'
                    elif scenario=='request_hash':value['request']['url']='other-pr'
                    elif scenario=='checkpoint_escape':entry['path']='../../outside.json'
                    cp.write_text(json.dumps(value))
                    if scenario not in ['policy_hash','reused_hash']:
                        entry['sha256']=hashlib.sha256(cp.read_bytes()).hexdigest()
                ap.write_text(json.dumps(audit))
                if reseal:groups['audit']['sha256']=hashlib.sha256(ap.read_bytes()).hexdigest()
                gp.write_text(json.dumps(groups))
                with self.assertRaises(ValueError):scoring.advisory_evidence(root,run)
