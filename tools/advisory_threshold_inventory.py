"""Matched six-PR raw eligibility inventory, never presented as final F2′."""
from collections import defaultdict
import json
from pathlib import Path
from tools import readjudicate_report_advisories as runner
from tools.advisory_scoring_policy import raw_vote


def main():
    root=runner.ROOT
    base=root/'analysis/verified_gold/advisory_readjudication'
    active=json.loads((base/'active_pass.json').read_text())
    raw=base/active['directory']
    policy_pointer=json.loads((base/'active_scoring_policy.json').read_text())
    target=base/policy_pointer['directory']
    rows,summaries,members=runner.inventory(root)
    dataset=json.loads((root/'analysis/final_report_dataset.json').read_text())
    frameworks=['vanilla-engineered','metareview-realistic','compound-realistic']
    cells=defaultdict(set)
    for r in rows:cells[(r['model'],r['effort'],r['framework'])].add(r['url'])
    shared=set.intersection(*[{(m,e) for (m,e,f),urls in cells.items() if f==fw and len(urls)==6} for fw in frameworks])
    selected={r['run_id']:r for r in rows if (r['model'],r['effort']) in shared}
    counts={rid:{'A80':set(),'A70':set(),'H80':set()} for rid in selected}
    for url,emissions in members.items():
        key=runner.pr_key(url)
        plan=json.loads((raw/'claim_plans'/f'{key}.json').read_text())
        assert plan['membership_sha256']==runner.digest(emissions)
        votes={}
        for cid in plan['representatives']:
            saved=json.loads((raw/'verdicts'/key/f'{cid}.json').read_text())
            if saved['instrument']=='reused_verified_bug':continue
            votes[int(cid)]=raw_vote(saved)
        for member,cid in zip(emissions,plan['cids']):
            rid=member['run_id']
            if rid not in selected or cid not in votes:continue
            category,confidence=votes[cid]
            if category=='important_non_bug':
                if confidence>=.7:counts[rid]['A70'].add(cid)
                if confidence>=.8:counts[rid]['A80'].add(cid)
            if category=='hallucination' and confidence>=.8:counts[rid]['H80'].add(cid)
    result={'status':'raw eligibility only; semantic deduplication pending',
            'definition':'Distinct exact claim IDs per selected review, then summed across matched reviews; not semantic identities, final credited A/H, or F2prime.',
            'raw_pass_digest':active['manifest_sha256'],'scoring_policy_sha256':policy_pointer['policy_sha256'],
            'model_effort_combinations':len(shared),'reviews_per_framework':len(shared)*6,'frameworks':{}}
    for fw in frameworks:
        rids=[rid for rid,r in selected.items() if r['framework']==fw]
        result['frameworks'][fw]={'reviews':len(rids),**{k:sum(len(counts[rid][k]) for rid in rids) for k in ['A80','A70','H80']}}
    (target/'matched_raw_inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
