"""Hash-bound concurrency-only experiment for the frozen advisory base pass."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import statistics
from types import SimpleNamespace

from tools import advisory_resume as resume
from tools import readjudicate_report_advisories as runner


def configuration(base,raw,concurrency):
    if concurrency not in (6,8):raise ValueError('Only explicitly reviewed six/eight-worker experiments supported')
    return SimpleNamespace(root=runner.ROOT,output=base,judge=raw['model'],group_judge=raw['grouping_model'],
                           effort=raw['effort'],concurrency=concurrency,dry_run=False,prepare_only=False)


def summarize_window(rows,start,end):
    if end<=start:raise ValueError('Empty measurement window')
    selected=[r for r in rows if r['phase']=='final' and start<=r['completed']<end]
    successes=[r for r in selected if r['status']=='complete']
    return {'start':start,'end':end,'seconds':end-start,'completed_batches':len(successes),
            'completed_pairs':sum(r['pairs'] for r in successes),
            'pairs_per_minute':sum(r['pairs'] for r in successes)*60/(end-start),
            'failed_attempts':sum(r['status']=='error' for r in selected),
            'median_success_elapsed_s':statistics.median(r['elapsed_s'] for r in successes) if successes else None,
            'p90_success_elapsed_s':sorted(r['elapsed_s'] for r in successes)[int(.9*(len(successes)-1))] if successes else None,
            'measurement':'Completion throughput over a homogeneous final-pair phase; elapsed includes request/parse work, retries reported separately'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(base,manifest):
    raw=json.loads((base/'manifest.json').read_text())
    if runner.digest(raw)!=manifest['raw_pass_digest']:raise ValueError('Wrong raw pass')
    configuration(base,raw,manifest['concurrency'])
    extension=base/'execution_extensions/deterministic_grouping_v1/manifest.json'
    if sha(extension)!=manifest['deterministic_extension_manifest_sha256']:raise ValueError('Wrong deterministic execution extension')
    prior=json.loads(extension.read_text())
    for name,digest in {**prior['source_sha256'],**manifest['source_sha256']}.items():
        if sha(runner.ROOT/name)!=digest:raise ValueError(f'Execution source changed: {name}')
    for name,digest in {**prior['frozen_recovery_files'],**manifest['frozen_files']}.items():
        if sha(base/name)!=digest:raise ValueError(f'Frozen execution evidence changed: {name}')
    function,source=resume.build_resume_grouping()
    if hashlib.sha256(source.encode()).hexdigest()!=prior['generated_grouping_sha256']:
        raise ValueError('Generated deterministic grouping changed')
    return raw,function


def run(base,raw,concurrency,function):
    if (base/'STOP').exists():raise ValueError('STOP flag still present; drain must finish before restart')
    runner.reuse_grouping=function
    asyncio.run(runner.sequential_main(configuration(base,raw,concurrency)))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=runner.OUTPUT/'passes/glm_base_claim_v3')
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args(argv)
    manifest=json.loads(args.manifest.read_text());raw,function=verify(args.base,manifest)
    print(f'Concurrency extension verified: workers={manifest["concurrency"]}; manifest={runner.digest(manifest)}',flush=True)
    if not args.verify_only:run(args.base,raw,manifest['concurrency'],function)


if __name__=='__main__':main()
