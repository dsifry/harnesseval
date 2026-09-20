"""Separate advisory-only duplicate identities for a versioned scoring policy.

Uses saved raw classifier votes. Never reclassifies or edits the frozen base pass.
Run only after the base pass has completed all selected PRs and reviews.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import time

from tools import readjudicate_report_advisories as runner
from tools import advisory_pair_validation as pairs


def eligible_claim_ids(seed, verdicts, minimum):
    eligible=[]
    for i,unit in enumerate(seed['units']):
        if unit['defect_ids']:
            continue
        value=verdicts.get(i)
        if not value or value.get('status')!='complete':
            raise ValueError(f'Missing complete classification for unit {i}')
        votes=value['result'].get('votes',[])
        if len(votes)!=1 or 'error' in votes[0]:
            raise ValueError('Policy requires one valid preserved raw classifier vote')
        vote=votes[0]; confidence=vote.get('confidence')
        if isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not math.isfinite(confidence) or not 0<=confidence<=1:
            raise ValueError('Invalid raw vote confidence')
        if vote.get('category') not in {'bug','important_non_bug','hallucination'}:
            raise ValueError('Unknown raw classifier category')
        if vote.get('category')=='important_non_bug' and confidence>=minimum:
            eligible.append(i)
    return eligible


def pair_key(url,a,b):
    return runner.digest([url,sorted([pairs.claim_key(a),pairs.claim_key(b)])])


async def refine_with_cache(url,proposals,texts,cache,request):
    async def compare(wanted):
        missing=[pair for pair in wanted if pair_key(url,texts[pair[0]],texts[pair[1]]) not in cache]
        if missing:
            votes=await request(missing)
            if len(votes)!=len(missing) or any(type(v) is not bool for v in votes):
                raise ValueError('Missing validated pair decisions')
            for (a,b),vote in zip(missing,votes):cache[pair_key(url,texts[a],texts[b])]=vote
        return [cache[pair_key(url,texts[a],texts[b])] for a,b in wanted]
    return await pairs.refine_groups(proposals,compare)


def validate_partition(groups,eligible):
    if not isinstance(groups,list) or any(not isinstance(g,list) or not g for g in groups):
        raise ValueError('Invalid policy proposal groups')
    values=[i for g in groups for i in g]
    if any(type(i) is not int for i in values) or sorted(values)!=sorted(eligible):
        raise ValueError('Policy proposals must partition exactly the eligible units')


def freeze_proposal(path,binding,groups,eligible):
    validate_partition(groups,eligible)
    runner.freeze_manifest(path,{'binding':binding,'groups':groups,'eligible_claim_ids':sorted(eligible)})


def read_proposal(path,binding,eligible):
    if not path.exists():return None
    value=json.loads(path.read_text())
    if value.get('binding')!=binding or value.get('eligible_claim_ids')!=sorted(eligible):
        raise ValueError('Stale policy proposal checkpoint')
    validate_partition(value.get('groups'),eligible)
    return value['groups']


def policy_buckets(url,eligible,base_candidates):
    if base_candidates.get('url')!=url:raise ValueError('Cross-PR candidate reuse')
    buckets=defaultdict(list)
    for i in eligible:
        row=base_candidates['bucket_for'].get(str(i))
        if not row or len(row)!=2:raise ValueError('Missing validated file candidate bucket')
        buckets[row[1]].append(i)
    return dict(buckets)


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_base_complete(base,manifest,raw_digest):
    progress_path=base/'progress.json'
    if not progress_path.exists():raise ValueError('Base pass is not complete')
    progress=json.loads(progress_path.read_text())
    if progress.get('phase')!='complete' or progress.get('pass_digest')!=raw_digest:
        raise ValueError('Base pass is still active or incomplete')
    expected={r['run_id']:r['url'] for r in manifest['runs']}
    paths={p.stem:p for p in (base/'runs').glob('*.json')}
    if set(paths)!=set(expected):raise ValueError('Base review coverage incomplete')
    for rid,path in paths.items():
        value=json.loads(path.read_text())
        if value.get('status')!='complete' or value.get('pass_digest')!=raw_digest or value.get('url')!=expected[rid]:
            raise ValueError('Base review validation mismatch')
    validated=set()
    for path in (base/'validation').glob('*.json'):
        value=json.loads(path.read_text())
        if value.get('status')!='complete' or value.get('pass_digest')!=raw_digest:
            raise ValueError('Base PR validation incomplete')
        validated.add(value['url'])
    if validated!=set(expected.values()):raise ValueError('Base PR coverage incomplete')


def load_pair_cache(base,key,url,texts,raw_digest,eligible):
    cache={};provenance=[];eligible=set(eligible)
    for path in sorted((base/'pair_calls'/key).glob('*.json')):
        value=json.loads(path.read_text())
        if value.get('status')!='complete':raise ValueError('Base pair checkpoint incomplete')
        if value.get('url')!=url or value.get('pass_digest')!=raw_digest:
            raise ValueError('Stale or cross-PR pair checkpoint')
        request=value['request']
        if runner.digest(request)!=value['request_sha256']:raise ValueError('Pair request hash mismatch')
        original=value.get('original_request',request)
        if original is not request:
            recovery=value.get('schema_recovery',{})
            rp=(base/recovery.get('manifest','')).resolve()
            if not rp.is_relative_to(base.resolve()) or not rp.is_file() or file_sha(rp)!=recovery.get('manifest_sha256'):
                raise ValueError('Missing schema recovery provenance')
            audit=json.loads(rp.read_text())
            if audit['request']!=request or audit['original_request']!=original or audit['raw_pass_digest']!=raw_digest:
                raise ValueError('Schema recovery request mismatch')
        indices=original['pairs']
        expected_prompt=pairs.make_prompt([(texts[a],texts[b]) for a,b in indices])
        if (original.get('url')!=url or original.get('model')!='glm-5.3-background' or original.get('effort')!='low'
                or original.get('system')!=pairs.SYSTEM or original.get('prompt')!=expected_prompt):
            raise ValueError('Saved pair does not match the exact full claims and judge settings')
        votes=pairs.parse_votes(value['parsed_response'],len(indices));used=0
        for (a,b),vote in zip(indices,votes):
            if a not in eligible or b not in eligible:continue
            k=pair_key(url,texts[a],texts[b])
            if k in cache and cache[k]!=vote:raise ValueError('Conflicting saved pair decisions')
            cache[k]=vote;used+=1
        if used:provenance.append({'path':str(path.relative_to(base)),'sha256':file_sha(path),'eligible_pairs':used})
    return cache,provenance


async def make_proposals(path,binding,buckets,texts,group):
    eligible=sorted(i for ids in buckets.values() for i in ids)
    saved=read_proposal(path,binding,eligible)
    if saved is not None:return saved
    jobs=[]
    for bucket,indices in sorted(buckets.items()):
        for start in range(0,len(indices),runner.GROUP_CHUNK):
            jobs.append((bucket,indices[start:start+runner.GROUP_CHUNK],f'{runner.digest(bucket)[:10]}_{start//runner.GROUP_CHUNK:03}'))
    # gather returns input order, independent of paid-call completion order.
    results=await asyncio.gather(*(group(order,name) for _,order,name in jobs),return_exceptions=True)
    for result in results:
        if isinstance(result,BaseException):raise result
    by_bucket=defaultdict(list)
    for (bucket,_,_),groups in zip(jobs,results):by_bucket[bucket].extend(groups)
    proposals=[]
    for bucket,groups in sorted(by_bucket.items()):
        representatives=[min(g,key=lambda i:(len(texts[i]),texts[i],i)) for g in groups]
        owner={rep:g for rep,g in zip(representatives,groups)}
        merged=await group(representatives,f'{runner.digest(bucket)[:10]}_merge') if len(groups)>1 else [representatives]
        proposals.extend([[i for rep in g for i in owner[rep]] for g in merged])
    freeze_proposal(path,binding,proposals,eligible)
    return proposals


def candidate_union(proposals,reused_cliques,bucket_for):
    """Union candidate evidence only; final identity still requires pair cliques."""
    parent={i:i for i in bucket_for}
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for group in proposals+reused_cliques:
        if not group:continue
        if len({bucket_for[i] for i in group})!=1:raise ValueError('Cross-file candidate union')
        for i in group[1:]:parent[root(i)]=root(group[0])
    grouped=defaultdict(list)
    for i in sorted(parent):grouped[root(i)].append(i)
    return sorted(grouped.values(),key=lambda group:group[0])


def verify_output(value,url,raw_digest,policy_digest,eligible,classification_hashes):
    expected={'status':'complete','url':url,'raw_pass_digest':raw_digest,'policy_sha256':policy_digest,
              'eligible_claim_ids':sorted(eligible),'classification_sha256':classification_hashes}
    if any(value.get(k)!=v for k,v in expected.items()):raise ValueError('Stale policy-specific group output')
    mapping=value.get('claim_to_group',{})
    if set(mapping)!={str(i) for i in eligible} or any(type(x) is not int or x<0 for x in mapping.values()):
        raise ValueError('Incomplete policy group mapping')


class PolicyCalls:
    def __init__(self,out,binding,url,sem):
        self.out=out;self.binding=binding;self.url=url;self.sem=sem
        self.failed=False;self.audit=[]

    async def checked(self,kind,phase,request,validate):
        request=json.loads(json.dumps(request))  # canonical JSON lists for safe resume equality
        sha=runner.digest(request);key=runner.pr_key(self.url)
        path=self.out/f'{kind}_calls'/key/f'{phase}_{sha}.json'
        if path.exists():
            saved=json.loads(path.read_text())
            if saved.get('binding')!=self.binding or saved.get('request')!=request or saved.get('request_sha256')!=sha:
                raise ValueError('Stale policy call checkpoint')
            if saved['status']=='complete':
                result=validate(saved['parsed_response'])
                self.audit.append({'path':str(path.relative_to(self.out)),'sha256':file_sha(path),'reused':True})
                return result
        for attempt in range(3):
            parsed=usage=None;error=None;started=time.time()
            try:
                async with self.sem:
                    if self.failed or (self.out/'STOP').exists():raise runner.DrainRequested()
                    parsed,tin,tout,usage=await runner.model_router.call_model_json(
                        request['model'],request['system'],request['prompt'],effort=request['effort'],max_tokens=request['max_tokens'])
                result=validate(parsed)
            except runner.DrainRequested:raise
            except Exception as exc:error=type(exc).__name__
            saved={'binding':self.binding,'url':self.url,'request':request,'request_sha256':sha,
                   'status':'error' if error else 'complete','error_type':error,'parsed_response':parsed,
                   'usage':usage,'started_at':started,'elapsed_s':time.time()-started}
            runner.write_json(self.out/'attempts'/key/f'{sha}_{time.time_ns()}.json',saved)
            runner.write_json(path,saved)
            if not error:
                self.audit.append({'path':str(path.relative_to(self.out)),'sha256':file_sha(path),'reused':False})
                runner.write_json(self.out/'progress.json',{'phase':kind,'url':self.url,**self.binding,
                    'updated_at':time.time(),'completed_calls_this_pr':len(self.audit),'last_request':sha})
                print(f'{self.url} {kind} {phase}: complete',flush=True)
                return result
        self.failed=True
        raise RuntimeError(f'{kind} schema/transport failure after three attempts')

    async def group(self,order,phase,texts):
        if len(order)<2:return [order] if order else []
        prompt=runner.GROUP_PROMPT.format(reps='\n'.join(f'{j}. {texts[i]}' for j,i in enumerate(order)))
        if len(prompt)>runner.GROUP_CONTEXT_LIMIT:raise ValueError('Grouping context limit exceeded; no truncation allowed')
        req={'url':self.url,'model':'glm-5.3-background','system':runner.GROUP_SYSTEM,'prompt':prompt,
             'effort':'low','max_tokens':8192,'units':order}
        def validate(parsed):
            return [[order[i] for i in g] for g in runner.validate_group_mapping(parsed,len(order))]
        return await self.checked('group',phase,req,validate)

    async def compare(self,wanted,texts):
        async def batch(start,chunk):
            prompt=pairs.make_prompt([(texts[a],texts[b]) for a,b in chunk])
            req={'url':self.url,'model':'glm-5.3-background','system':pairs.SYSTEM,'prompt':prompt,
                 'effort':'low','max_tokens':8192,'pairs':chunk}
            return await self.checked('pair',str(start),req,lambda value:pairs.parse_votes(value,len(chunk)))
        results=await asyncio.gather(*(batch(start,wanted[start:start+20]) for start in range(0,len(wanted),20)),return_exceptions=True)
        for result in results:
            if isinstance(result,BaseException):raise result
        return [vote for result in results for vote in result]


def prioritized_buckets(seed,buckets,texts):
    # Recompute overlap candidates across the former .80 category boundary.
    edges=[];parent={i:i for ids in buckets.values() for i in ids}
    def root(i):
        while parent[i]!=i:i=parent[i]
        return i
    for bucket,ids in sorted(buckets.items()):
        for n,a in enumerate(ids):
            for b in ids[n+1:]:
                if runner.intervals_overlap(seed['units'][a]['location'],seed['units'][b]['location']):
                    edges.append({'units':[a,b],'reason':'same-file overlapping intervals'})
                    x,y=root(a),root(b);parent[max(x,y)]=min(x,y)
    ordered={bucket:sorted(ids,key=lambda i:(root(i),seed['units'][i]['location'][1] or 10**9,texts[i],i))
             for bucket,ids in buckets.items()}
    return ordered,edges


async def process_pr(base,out,policy,raw_digest,seed,members,sources):
    url=seed['url'];key=runner.pr_key(url);policy_digest=runner.digest(policy)
    verdicts={int(p.stem):json.loads(p.read_text()) for p in (base/'verdicts'/key).glob('*.json')}
    for value in verdicts.values():
        if value.get('url')!=url or value.get('pass_digest')!=raw_digest:raise ValueError('Classification provenance mismatch')
    eligible=eligible_claim_ids(seed,verdicts,policy['advisory_minimum_confidence'])
    texts={i:runner.classifier_candidate(members[u['representative']]['record']) for i,u in enumerate(seed['units'])}
    hashes={str(i):file_sha(base/'verdicts'/key/f'{i}.json') for i,u in enumerate(seed['units']) if not u['defect_ids']}
    target=out/'groups'/f'{key}.json'
    if target.exists():
        value=json.loads(target.read_text());verify_output(value,url,raw_digest,policy_digest,eligible,hashes)
        if value.get('source_sha256')!=sources:raise ValueError('Policy runner sources changed')
        return value
    candidate_path=base/'candidates'/f'{key}.json'
    candidates=json.loads(candidate_path.read_text());buckets=policy_buckets(url,eligible,candidates)
    buckets,interval_edges=prioritized_buckets(seed,buckets,texts)
    bucket_for={i:bucket for bucket,ids in buckets.items() for i in ids}
    cache,reused_pairs=load_pair_cache(base,key,url,texts,raw_digest,eligible)
    dedup_path=base/'dedup_audit'/f'{key}.json';old=json.loads(dedup_path.read_text())
    reused_cliques=[[i for i in group if i in bucket_for] for group in old['validated_groups']]
    reused_cliques=[g for g in reused_cliques if g]
    validate_partition(reused_cliques,eligible)
    import itertools
    for group in reused_cliques:
        for a,b in itertools.combinations(group,2):
            if cache.get(pair_key(url,texts[a],texts[b])) is not True:
                raise ValueError('Base clique lacks accepted full-text pair evidence')
    binding={'raw_pass_digest':raw_digest,'policy_sha256':policy_digest,'url':url,
             'classification_sha256':hashes,'texts_sha256':runner.digest(texts),'seed_sha256':runner.digest(seed),
             'candidates_sha256':file_sha(candidate_path),'base_dedup_sha256':file_sha(dedup_path),
             'source_sha256':sources}
    calls=PolicyCalls(out,binding,url,asyncio.Semaphore(4))
    proposal_path=out/'proposals'/f'{key}.json'
    proposed=read_proposal(proposal_path,binding,eligible)
    if proposed is None:
        initial=await make_proposals(out/'group_proposals'/f'{key}.json',binding,buckets,texts,
                                     lambda order,phase:calls.group(order,phase,texts))
        proposed=candidate_union(initial,reused_cliques,bucket_for)
        freeze_proposal(proposal_path,binding,proposed,eligible)
    validated=await refine_with_cache(url,proposed,texts,cache,lambda wanted:calls.compare(wanted,texts))
    validate_partition(validated,eligible)
    for group in validated:
        for a,b in itertools.combinations(group,2):
            if cache.get(pair_key(url,texts[a],texts[b])) is not True:raise ValueError('Unverified policy clique')
    audit={'binding':binding,'proposed_groups':proposed,'validated_groups':validated,
           'reused_clique_candidates':reused_cliques,'reused_pair_checkpoints':reused_pairs,
           'interval_candidate_edges':interval_edges,
           'policy_calls':[{'path':str(p.relative_to(out)),'sha256':file_sha(p)}
                           for kind in ('group','pair') for p in sorted((out/f'{kind}_calls'/key).glob('*.json'))]}
    audit_path=out/'audit'/f'{key}.json';runner.freeze_manifest(audit_path,audit)
    value={'status':'complete','raw_pass_digest':raw_digest,'policy_sha256':policy_digest,'url':url,
           'claim_to_group':{str(i):gid for gid,g in enumerate(validated) for i in g},
           'eligible_claim_ids':sorted(eligible),'classification_sha256':hashes,'source_sha256':sources,
           'audit':{'path':str(audit_path.relative_to(out)),'sha256':file_sha(audit_path)},
           'pair_equivalence_minimum_confidence':.8,'model':'glm-5.3-background','effort':'low',
           'base_penalty_groups':'unchanged; this file only defines advisory identities'}
    verify_output(value,url,raw_digest,policy_digest,eligible,hashes)
    runner.freeze_manifest(target,value)
    print(f'COMPLETE POLICY PR {url}: {len(eligible)} advisory claims -> {len(validated)} identities',flush=True)
    return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=runner.OUTPUT/'passes/glm_base_claim_v3')
    parser.add_argument('--policy',type=Path,default=runner.OUTPUT/'scoring_policies/advisory070_penalty080_v1/policy.json')
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--run',action='store_true',help='Execute only after the base pass has fully completed')
    mode.add_argument('--prepare-only',action='store_true',help='Freeze inputs and execution provenance without model calls (default)')
    args=parser.parse_args(argv);base=args.base.resolve();out=args.policy.resolve().parent
    raw=json.loads((base/'manifest.json').read_text());raw_digest=runner.digest(raw)
    policy=json.loads(args.policy.read_text());policy_digest=runner.digest(policy)
    if (policy.get('raw_pass_digest')!=raw_digest or policy.get('advisory_minimum_confidence')!=.7
            or policy.get('penalty_minimum_confidence')!=.8 or policy.get('pair_equivalence_minimum_confidence')!=.8):
        raise ValueError('Wrong raw pass or unsupported policy settings')
    require_base_complete(base,raw,raw_digest)
    if raw.get('model')!='glm-5.3-background' or raw.get('effort')!='low':raise ValueError('Unexpected base judge settings')
    for name,sha in raw['source_hashes'].items():
        if file_sha(runner.ROOT/name)!=sha:raise ValueError(f'Frozen base dependency changed: {name}')
    rows,summaries,members=runner.inventory(runner.ROOT)
    if runner.digest(members)!=raw['membership_sha256']:raise ValueError('Base review membership changed')
    for row in raw['runs']:
        if runner.digest(summaries[row['run_id']])!=row['summary_sha256']:raise ValueError('Original review summary changed')
    seeds=json.loads((base/'seed_inventory.json').read_text())
    if runner.digest(seeds)!=raw['seed_sha256'] or set(seeds)!=set(members):raise ValueError('Base seed inventory changed')
    sources=dict(raw['source_hashes'])
    for name in ['tools/advisory_policy_dedup.py','tests/test_advisory_policy_dedup.py']:
        sources[name]=file_sha(runner.ROOT/name)
    inputs={str(p.relative_to(base)):file_sha(p) for folder in ['verdicts','pair_calls','candidates','dedup_audit','validation','runs']
            for p in sorted((base/folder).rglob('*.json'))}
    inputs['manifest.json']=file_sha(base/'manifest.json');inputs['seed_inventory.json']=file_sha(base/'seed_inventory.json')
    execution={'raw_pass_digest':raw_digest,'policy_sha256':policy_digest,'source_sha256':sources,
               'base_input_sha256':inputs,'model':'glm-5.3-background','effort':'low','concurrency':4,
               'wire_settings':raw['wire_settings'],'group_prompt_sha256':runner.digest([runner.GROUP_SYSTEM,runner.GROUP_PROMPT]),
               'pair_prompt_sha256':runner.digest([pairs.SYSTEM,pairs.PROMPT]),
               'scope':list(seeds),'grouping_chunk':runner.GROUP_CHUNK,'grouping_text_limit':None,
               'pair_cache_identity':'full PR URL and exact case-preserving full normalized claim pair; true and false reused',
               'method':'A-only same-file candidate grouping plus existing clique candidate union, followed by full pairwise equivalence; no classification'}
    runner.freeze_manifest(out/'execution_manifest.json',execution)
    for name in sources:
        if not name.endswith('.py'):continue
        target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        data=(runner.ROOT/name).read_bytes()
        if target.exists() and target.read_bytes()!=data:raise ValueError('Archived policy source changed')
        target.write_bytes(data)
    runner.freeze_manifest(out/'prompts.json',{'group_system':runner.GROUP_SYSTEM,'group_prompt':runner.GROUP_PROMPT,
                                             'pair_system':pairs.SYSTEM,'pair_prompt':pairs.PROMPT})
    print(f'Policy preflight complete: {len(seeds)} PRs; execution manifest {runner.digest(execution)}',flush=True)
    if not args.run:return
    if (out/'STOP').exists():raise ValueError('Policy STOP drain flag present')
    import fcntl
    lock=(out/'RUN.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise ValueError('Another policy dedup process is active')
    async def run_all():
        completed=[]
        for url,seed in seeds.items():
            await process_pr(base,out,policy,raw_digest,seed,members[url],sources)
            completed.append(url)
            runner.write_json(out/'progress.json',{'phase':'pr_complete','raw_pass_digest':raw_digest,'policy_sha256':policy_digest,
                                                  'completed_prs':completed,'updated_at':time.time()})
        runner.write_json(out/'progress.json',{'phase':'complete','raw_pass_digest':raw_digest,'policy_sha256':policy_digest,
                                              'completed_prs':completed,'updated_at':time.time()})
    try:asyncio.run(run_all())
    finally:lock.close()


if __name__=='__main__':
    main()
