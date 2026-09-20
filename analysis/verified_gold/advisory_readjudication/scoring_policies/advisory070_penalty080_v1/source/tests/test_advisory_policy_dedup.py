import asyncio
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock


class PolicyDedupTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('tools.advisory_policy_dedup'),
                             'The separate policy-specific dedup runner is missing')
        from tools import advisory_policy_dedup
        return advisory_policy_dedup

    def test_eligibility_uses_raw_vote_threshold_and_excludes_fixed_bug(self):
        m=self.module()
        seed={'units':[{'defect_ids':[]} for _ in range(5)]}
        seed['units'][4]['defect_ids']=['D1']
        values={}
        for i,(category,confidence) in enumerate([('important_non_bug',.7),('important_non_bug',.69),('hallucination',.99),('important_non_bug',.8),('important_non_bug',.9)]):
            values[i]={'status':'complete','result':{'verdict':'unresolved','votes':[{'category':category,'confidence':confidence}]}}
        self.assertEqual(m.eligible_claim_ids(seed,values,.7),[0,3])
        del values[0]
        with self.assertRaises(ValueError):m.eligible_claim_ids(seed,values,.7)

    def test_pair_identity_preserves_case_and_pr_scope(self):
        m=self.module()
        self.assertEqual(m.pair_key('url1','A','B'),m.pair_key('url1','B','A'))
        self.assertNotEqual(m.pair_key('url1','Foo','B'),m.pair_key('url1','foo','B'))
        self.assertNotEqual(m.pair_key('url1','A','B'),m.pair_key('url2','A','B'))

    def test_refinement_reuses_negative_and_positive_votes(self):
        m=self.module();texts={0:'A',1:'B',2:'C'}
        cached={m.pair_key('url',texts[0],texts[1]):False,
                m.pair_key('url',texts[0],texts[2]):True}
        request=AsyncMock(side_effect=AssertionError('No paid comparison should be needed'))
        result=asyncio.run(m.refine_with_cache('url',[[0,1,2]],texts,cached,request))
        self.assertEqual(result,[[0,2],[1]])

    def test_refinement_calls_only_missing_pairs(self):
        m=self.module();texts={0:'A',1:'B',2:'C'};seen=[]
        cached={m.pair_key('url','A','B'):True}
        async def request(pairs):
            seen.extend(pairs);return [False for _ in pairs]
        result=asyncio.run(m.refine_with_cache('url',[[0,1,2]],texts,cached,request))
        self.assertEqual(result,[[0,1],[2]])
        self.assertEqual(seen,[(0,2)])

    def test_proposal_checkpoint_rejects_stale_inputs_and_missing_eligible(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'proposal.json'
            m.freeze_proposal(p,{'policy':'a'},[[2,5],[9]],[2,5,9])
            self.assertEqual(m.read_proposal(p,{'policy':'a'},[2,5,9]),[[2,5],[9]])
            with self.assertRaises(ValueError):m.read_proposal(p,{'policy':'b'},[2,5,9])
            with self.assertRaises(ValueError):m.freeze_proposal(Path(tmp)/'bad.json',{},[[2,5]],[2,5,9])

    def test_bucket_constraints_use_validated_base_candidates(self):
        m=self.module()
        base={'url':'url','bucket_for':{'2':['unresolved','a.py'],'5':['important_non_bug','b.py'],'9':['unresolved','unknown']}}
        self.assertEqual(m.policy_buckets('url',[2,5,9],base),{'a.py':[2],'b.py':[5],'unknown':[9]})
        with self.assertRaises(ValueError):m.policy_buckets('other',[2],base)
        with self.assertRaises(ValueError):m.policy_buckets('url',[7],base)

    def test_saved_pair_votes_validate_exact_request_and_keep_false(self):
        m=self.module();self.assertTrue(callable(getattr(m,'load_pair_cache',None)))
        from tools import advisory_pair_validation as pv, readjudicate_report_advisories as r
        import json
        texts={0:'A',1:'B'}
        request={'url':'url','model':'glm-5.3-background','system':pv.SYSTEM,'prompt':pv.make_prompt([('A','B')]),'effort':'low','pairs':[[0,1]]}
        vote={'pair':1,'same':False,'confidence':.9,'material_differences':['different mechanism'],
              'a':{'mechanism':'A','trigger':'x','consequence':'y'},'b':{'mechanism':'B','trigger':'x','consequence':'y'},'reason':'different'}
        value={'url':'url','pass_digest':'raw','status':'complete','request':request,'request_sha256':r.digest(request),'parsed_response':{'pairs':[vote]}}
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);p=base/'pair_calls'/'key'/'one.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(value))
            cache,provenance=m.load_pair_cache(base,'key','url',texts,'raw',[0,1])
            self.assertEqual(cache,{m.pair_key('url','A','B'):False})
            self.assertEqual(len(provenance),1)
            with self.assertRaises(ValueError):m.load_pair_cache(base,'key','url',{0:'Changed',1:'B'},'raw',[0,1])
            with self.assertRaises(ValueError):m.load_pair_cache(base,'key','other',texts,'raw',[0,1])

    def test_base_guard_blocks_pending_or_missing_review(self):
        m=self.module();self.assertTrue(callable(getattr(m,'require_base_complete',None)));import json
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);(base/'runs').mkdir();(base/'validation').mkdir()
            manifest={'runs':[{'run_id':'r','url':'url'}]};digest='raw'
            (base/'progress.json').write_text(json.dumps({'phase':'pair_validation'}))
            with self.assertRaises(ValueError):m.require_base_complete(base,manifest,digest)
            (base/'progress.json').write_text(json.dumps({'phase':'complete','pass_digest':digest}))
            with self.assertRaises(ValueError):m.require_base_complete(base,manifest,digest)
            (base/'runs/r.json').write_text(json.dumps({'status':'complete','pass_digest':digest,'run_id':'r','url':'url'}))
            (base/'validation/p.json').write_text(json.dumps({'status':'complete','pass_digest':digest,'url':'url'}))
            m.require_base_complete(base,manifest,digest)

    def test_deterministic_proposals_respect_files_and_resume_without_calls(self):
        m=self.module();self.assertTrue(callable(getattr(m,'make_proposals',None)))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'proposals.json';calls=[]
            async def group(order,phase):
                calls.append(list(order))
                await asyncio.sleep(.001 if order[0]==0 else 0)
                return [order]
            buckets={'b.py':[2,3],'a.py':[0,1]};texts={i:str(i) for i in range(4)}
            first=asyncio.run(m.make_proposals(path,{},buckets,texts,group))
            self.assertEqual(first,[[0,1],[2,3]])
            second=asyncio.run(m.make_proposals(path,{},dict(reversed(list(buckets.items()))),texts,AsyncMock(side_effect=AssertionError('Resume regrouped'))))
            self.assertEqual(first,second)

    def test_reused_cliques_are_candidate_evidence_not_automatic_merges(self):
        m=self.module();self.assertTrue(callable(getattr(m,'candidate_union',None)))
        proposals=m.candidate_union([[0,1],[2]],[[1,2]],{0:'a.py',1:'a.py',2:'a.py'})
        self.assertEqual(proposals,[[0,1,2]])
        async def compare(wanted):return [False for _ in wanted]
        result=asyncio.run(m.refine_with_cache('url',proposals,{0:'A',1:'B',2:'C'},{},compare))
        self.assertEqual(result,[[0],[1],[2]])
        with self.assertRaises(ValueError):m.candidate_union([[0],[1]],[[0,1]],{0:'a.py',1:'b.py'})

    def test_checked_call_retries_bad_schema_and_freezes_success(self):
        m=self.module();self.assertTrue(hasattr(m,'PolicyCalls'))
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            calls=m.PolicyCalls(Path(tmp),{'raw_pass_digest':'raw','policy_sha256':'policy'},'url',asyncio.Semaphore(4))
            outputs=[({},1,1,{}),({'0':0,'1':0},1,1,{})]
            with patch.object(m.runner.model_router,'call_model_json',AsyncMock(side_effect=outputs)):
                result=asyncio.run(calls.group([2,5],'chunk',{2:'A',5:'B'}))
            self.assertEqual(result,[[2,5]])
            with patch.object(m.runner.model_router,'call_model_json',AsyncMock(side_effect=AssertionError('Paid cache hit'))):
                self.assertEqual(asyncio.run(calls.group([2,5],'chunk',{2:'A',5:'B'})),[[2,5]])
            self.assertEqual(len(list((Path(tmp)/'attempts').rglob('*.json'))),2)

    def test_group_output_rejects_changed_classifications_on_resume(self):
        m=self.module();self.assertTrue(callable(getattr(m,'verify_output',None)))
        good={'status':'complete','raw_pass_digest':'raw','policy_sha256':'policy','url':'url',
              'eligible_claim_ids':[2,5],'claim_to_group':{'2':0,'5':0},'classification_sha256':{'2':'a','5':'b'}}
        m.verify_output(good,'url','raw','policy',[2,5],{'2':'a','5':'b'})
        with self.assertRaises(ValueError):m.verify_output(good,'url','raw','policy',[2,5],{'2':'changed','5':'b'})
        with self.assertRaises(ValueError):m.verify_output(good,'url','raw','policy',[2],{'2':'a','5':'b'})

    def test_policy_pr_exports_exact_membership_and_all_classification_hashes(self):
        m=self.module();self.assertTrue(callable(getattr(m,'process_pr',None)))
        from tools import readjudicate_report_advisories as r
        import json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'base';out=Path(tmp)/'policy';url='https://example.test/repo/pull/1';key=r.pr_key(url)
            seed={'url':url,'units':[{'defect_ids':[],'representative':i,'location':['x.py',i+1,i+1],'old_groups':[]} for i in range(3)]}
            members=[{'record':{'issue_text':f'claim {i}'}} for i in range(3)]
            for i,(cat,conf) in enumerate([('important_non_bug',.8),('important_non_bug',.7),('hallucination',.9)]):
                r.write_json(base/'verdicts'/key/f'{i}.json',{'status':'complete','url':url,'pass_digest':'raw','result':{'votes':[{'category':cat,'confidence':conf}]}})
            r.write_json(base/'candidates'/f'{key}.json',{'url':url,'bucket_for':{str(i):['old','x.py'] for i in range(3)},'interval_edges':[]})
            r.write_json(base/'dedup_audit'/f'{key}.json',{'validated_groups':[[0],[1],[2]]})
            async def group(self,order,phase,texts):return [[i] for i in order]
            policy={'advisory_minimum_confidence':.7};sources={'runner':'sha'}
            with patch.object(m.PolicyCalls,'group',group):
                result=asyncio.run(m.process_pr(base,out,policy,'raw',seed,members,sources))
            self.assertEqual(result['eligible_claim_ids'],[0,1]);self.assertEqual(set(result['classification_sha256']),{'0','1','2'})
            self.assertEqual(result['claim_to_group'],{'0':0,'1':1});self.assertEqual(result['status'],'complete')
            m.verify_output(result,url,'raw',r.digest(policy),[0,1],result['classification_sha256'])

    def test_eligibility_rejects_invalid_raw_category_and_confidence(self):
        m=self.module();seed={'units':[{'defect_ids':[]}]}
        for cat,conf in [('invented',.9),('important_non_bug',1.1),('bug',-.1),('bug',True),('bug',float('nan'))]:
            values={0:{'status':'complete','result':{'votes':[{'category':cat,'confidence':conf}]}}}
            with self.subTest(category=cat,confidence=conf):
                with self.assertRaises(ValueError):m.eligible_claim_ids(seed,values,.7)

    def test_cli_cannot_launch_while_base_is_pending(self):
        m=self.module();self.assertTrue(callable(getattr(m,'main',None)))
        from tools import readjudicate_report_advisories as r
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'base';out=Path(tmp)/'policy';policy=out/'policy.json'
            raw={'runs':[]};r.write_json(base/'manifest.json',raw)
            r.write_json(base/'progress.json',{'phase':'classification','pass_digest':r.digest(raw)})
            r.write_json(policy,{'raw_pass_digest':r.digest(raw),'advisory_minimum_confidence':.7,'penalty_minimum_confidence':.8,'pair_equivalence_minimum_confidence':.8})
            with self.assertRaises(ValueError):m.main(['--base',str(base),'--policy',str(policy),'--run'])
            self.assertFalse((out/'execution_manifest.json').exists())
            with self.assertRaises(SystemExit):m.main(['--base',str(base),'--policy',str(policy),'--pilot'])

    def test_pair_checkpoint_reuses_tuple_requests_after_json_roundtrip(self):
        m=self.module()
        from unittest.mock import patch
        response={'pairs':[{'pair':1,'same':False,'confidence':.9,'material_differences':['x'],
                  'a':{'mechanism':'A','trigger':'x','consequence':'y'},'b':{'mechanism':'B','trigger':'x','consequence':'y'},'reason':'different'}]}
        with tempfile.TemporaryDirectory() as tmp:
            call=m.PolicyCalls(Path(tmp),{},'url',asyncio.Semaphore(4))
            with patch.object(m.runner.model_router,'call_model_json',AsyncMock(return_value=(response,1,1,{}))):
                self.assertEqual(asyncio.run(call.compare([(0,1)],{0:'A',1:'B'})),[False])
            with patch.object(m.runner.model_router,'call_model_json',AsyncMock(side_effect=AssertionError('Paid repeated pair'))):
                self.assertEqual(asyncio.run(call.compare([(0,1)],{0:'A',1:'B'})),[False])

    def test_overlap_priority_is_recomputed_across_old_threshold_categories(self):
        m=self.module();self.assertTrue(callable(getattr(m,'prioritized_buckets',None)))
        seed={'units':[{'location':['a.py',20,22]},{'location':['a.py',50,51]},{'location':['a.py',21,23]}]}
        buckets,edges=m.prioritized_buckets(seed,{'a.py':[0,1,2]},{0:'A',1:'B',2:'C'})
        self.assertEqual(buckets,{'a.py':[0,2,1]})
        self.assertEqual(edges,[{'units':[0,2],'reason':'same-file overlapping intervals'}])
