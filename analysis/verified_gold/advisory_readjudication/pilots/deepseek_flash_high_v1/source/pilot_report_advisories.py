#!/usr/bin/env python3
"""Bounded DeepSeek pilot, isolated from every production adjudication pass."""
from __future__ import annotations
import argparse
import asyncio
from collections import Counter, defaultdict
import contextvars
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import readjudicate_report_advisories as runner
from tools.report_advisories import accepted_common_verdict
from harnesseval import model_router
from harnesseval.effort import openai_effort_kwargs
import readjudicate3 as rj

MODEL='deepseek-4.1-flash-background'
BASE=ROOT/'analysis/verified_gold/advisory_readjudication'
OUT=BASE/'pilots/deepseek_flash_low_v1'
CALLS=contextvars.ContextVar('pilot_calls',default=None)


def partition(mapping):
    groups=defaultdict(list)
    for index,group in mapping.items():groups[group].append(int(index))
    return sorted(sorted(g) for g in groups.values())


def effective(result):
    return accepted_common_verdict({'new_verdict':result.get('verdict'),'confidence':result.get('confidence')},{'minimum_confidence':.8})


def prepare(out, model=MODEL, template=None, effort='low'):
    url='https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10'
    diff=json.loads((BASE/'diffs/10.json').read_text())['diff']
    controls=[]
    for path in sorted((BASE/'classification_pilot').glob('*.json')):
        old=json.loads(path.read_text())
        assert old['url']==url
        controls.append({'id':path.stem,'kind':'classification','candidate':old['judged_text'],
                         'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'historical_glm_result':old['result'],'historical_glm_elapsed_s':old['elapsed_s']})
    assert len(controls)==7
    seed=json.loads((BASE/'passes/reuse_v2/seed_inventory.json').read_text())[url]
    rows,summaries,byurl=runner.inventory(ROOT); members=byurl[url]
    buckets=defaultdict(list)
    for unit in seed['units']:
        if not unit['defect_ids'] and unit['location'][0]:buckets[unit['location'][0]].append(unit)
    file,units=max(buckets.items(),key=lambda kv:len(kv[1]))
    indices=[u['representative'] for u in units[:28]]
    texts=[runner.classifier_candidate(members[i]['record']) for i in indices]
    texts+=texts[:2]  # two known identical-text controls, same full prompt in both stages
    body='\n'.join(f'{i}. {text}' for i,text in enumerate(texts))
    grouping={'id':'grouping_file_30','kind':'grouping','file':file,'texts':texts,'source_indices':indices,
              'identical_pairs':[[0,28],[1,29]],'prompt':runner.GROUP_PROMPT.format(reps=body)}
    requests=controls+[grouping]
    prompt=runner.common_classifier_prompt()
    source_paths=[Path(__file__),Path(runner.__file__),Path(rj.__file__),ROOT/'tools/report_advisories.py',ROOT/'tools/enum_advisory_ceiling.py']
    manifest={'schema_version':1,'purpose':'bounded model suitability trial, never promoted automatically',
              'url':url,'model':model,'concurrency_stages':[4,6],'calls_per_stage':8,'total_calls':16,
              'effort':effort,'wire_effort_kwargs':openai_effort_kwargs(effort,model=model),'wire_temperature':1,'k':1,'minimum_confidence':.8,'diff_sha256':runner.digest(diff),
              'requests':requests,'classifier_system':rj.V2_SYSTEM,'classifier_prompt':prompt,
              'grouping_system':runner.GROUP_SYSTEM,'grouping_prompt':runner.GROUP_PROMPT,
              'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
              'interpretation':'Stage6 follows stage4: cache warmup/order confounds causal speed comparisons. Historical GLM rubric differed; descriptive timing only.'}
    if template is not None:
        prior=json.loads(Path(template).read_text())
        if prior['url']!=url or prior['diff_sha256']!=manifest['diff_sha256'] or prior['classifier_prompt']!=prompt or prior['grouping_prompt']!=runner.GROUP_PROMPT:
            raise ValueError('Comparison template inputs or prompt changed')
        manifest['requests']=prior['requests']
        manifest['comparison_template_sha256']=runner.digest(prior)
    runner.freeze_manifest(out/'manifest.json',manifest)
    runner.freeze_manifest(out/'diff.json',{'url':url,'diff':diff,'sha256':runner.digest(diff)})
    for path in source_paths:
        target=out/'source'/path.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    return manifest,diff


async def run(out,prepare_only=False,model=MODEL,template=None,effort='low'):
    manifest,diff=prepare(out,model,template,effort);sha=runner.digest(manifest)
    print(f'PREPARED {out} pass={sha};16 calls=7 controls+1 grouping repeated at4 and6',flush=True)
    if prepare_only:return
    original=model_router.call_model_json
    async def logged(*args,**kwargs):
        result=await original(*args,**kwargs)
        calls=CALLS.get()
        if calls is not None:calls.append({'model':args[0],'response':result[0],'input_tokens':result[1],'output_tokens':result[2],'usage':result[3]})
        return result
    rj.call_model_json=logged
    rj.V2_PROMPT=manifest['classifier_prompt']
    for concurrency in (4,6):
        gate=asyncio.Semaphore(concurrency);stage_start=time.time();stage_records=[]
        async def job(order,request):
            path=out/f'concurrency_{concurrency}'/f'{request["id"]}.json'
            if path.exists():
                saved=json.loads(path.read_text())
                if saved['manifest_sha256']!=sha:raise ValueError('Stale pilot checkpoint')
                if saved['status']=='complete':stage_records.append(saved);return
            enqueued=time.time()
            async with gate:
                started=time.time();calls=[];token=CALLS.set(calls);error=None;result=None
                try:
                    model_router.set_session(f'advisory-{model}-pilot-{concurrency}')
                    if request['kind']=='classification':
                        result=await rj.adjudicate(request['candidate'],diff,model,asyncio.Semaphore(1),k=1,vote_effort=effort)
                        if result.get('votes') and all('error' in v for v in result['votes']):error='classifier_transport_or_parse'
                    else:
                        result,tin,tout,usage=await logged(model,runner.GROUP_SYSTEM,request['prompt'],effort=effort,max_tokens=8192)
                        runner.validate_group_mapping(result,len(request['texts']))
                except Exception as exc:error=type(exc).__name__
                finally:CALLS.reset(token)
                ended=time.time()
                saved={'manifest_sha256':sha,'id':request['id'],'kind':request['kind'],'concurrency':concurrency,
                       'order':order,'enqueued_epoch_s':enqueued,'started_epoch_s':started,'ended_epoch_s':ended,
                       'queue_s':started-enqueued,'service_s':ended-started,'status':'error' if error else 'complete',
                       'error_type':error,'result':result,'effective_verdict':effective(result) if result and request['kind']=='classification' else None,
                       'calls':calls,'request_sha256':runner.digest(request)}
                runner.write_json(path,saved);stage_records.append(saved)
                print(f'concurrency{concurrency} {request["kind"]} {request["id"][:12]}: {saved["status"]} service={saved["service_s"]:.1f}s queue={saved["queue_s"]:.1f}s effective={saved["effective_verdict"]}',flush=True)
        await asyncio.gather(*(job(i,r) for i,r in enumerate(manifest['requests'])))
        runner.write_json(out/f'stage_{concurrency}.json',{'manifest_sha256':sha,'concurrency':concurrency,
            'wall_s':time.time()-stage_start,'completed':sum(r['status']=='complete' for r in stage_records),
            'errors':sum(r['status']=='error' for r in stage_records),'requests_per_minute':len(stage_records)*60/(time.time()-stage_start)})
        if any(r['status']=='error' for r in stage_records):
            print('Pilot stage had errors; stopping before raising concurrency',flush=True);return
    pairs=[]
    for request in manifest['requests']:
        a=json.loads((out/'concurrency_4'/f'{request["id"]}.json').read_text());b=json.loads((out/'concurrency_6'/f'{request["id"]}.json').read_text())
        same=(a['effective_verdict']==b['effective_verdict']) if request['kind']=='classification' else partition(a['result'])==partition(b['result'])
        pairs.append({'id':request['id'],'kind':request['kind'],'consistent':same,
                      'raw_verdict_same':a['result'].get('verdict')==b['result'].get('verdict') if request['kind']=='classification' else None,
                      'service_s':[a['service_s'],b['service_s']],'effective_verdicts':[a['effective_verdict'],b['effective_verdict']],
                      'identical_pairs_merged':all(x['result'][str(i)]==x['result'][str(j)] for x in (a,b) for i,j in request.get('identical_pairs',[])) if request['kind']=='grouping' else None})
    runner.write_json(out/'comparison.json',{'manifest_sha256':sha,'pairs':pairs,'consistent':sum(p['consistent'] for p in pairs),'total':len(pairs),'caveats':manifest['interpretation']})
    print(f'COMPLETE: {sum(p["consistent"] for p in pairs)}/{len(pairs)} repeated requests agree after gating/partition normalization',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--model',default=MODEL);parser.add_argument('--template',type=Path);parser.add_argument('--effort',choices=['low','medium','xhigh'],default='low');args=parser.parse_args()
    asyncio.run(run(args.output,args.prepare_only,args.model,args.template,args.effort))
