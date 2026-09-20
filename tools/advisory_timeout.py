"""Versioned hard-deadline execution extension; frozen policy sources stay intact."""
import argparse
import asyncio
import contextlib
import json
from pathlib import Path
import sys
import time


async def child_call(command, payload, seconds):
    process = await asyncio.create_subprocess_exec(
        *command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(json.dumps(payload).encode()), timeout=seconds)
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.wait()
        raise
    if process.returncode:
        # Do not copy provider stderr, which could contain credentials or request content.
        raise RuntimeError(f'Isolated model call exited {process.returncode}')
    return json.loads(stdout)


def worker():
    from harnesseval import model_router
    payload = json.load(sys.stdin)
    with contextlib.redirect_stdout(sys.stderr):
        result = asyncio.run(model_router.call_model_json(*payload['args'], **payload['kwargs']))
    print(json.dumps(result), flush=True)


def install(extension, seconds):
    from tools import advisory_policy_dedup as policy
    async def bounded(*args, **kwargs):
        payload = {'args': args, 'kwargs': kwargs}
        started = time.time()
        event = {'started_at': started, 'request_sha256': policy.runner.digest(payload),
                 'deadline_seconds': seconds, 'status': 'running'}
        event_path = extension / 'requests' / f'{time.time_ns()}.json'
        policy.runner.write_json(event_path, event)
        try:
            result = await child_call([sys.executable, '-m', 'tools.advisory_timeout', '--worker'], payload, seconds)
            event['status'] = 'complete'
            return result
        except BaseException as exc:
            event['status'] = 'error'
            event['error_type'] = type(exc).__name__
            raise
        finally:
            event['elapsed_s'] = time.time() - started
            policy.runner.write_json(event_path, event)
    policy.runner.model_router.call_model_json = bounded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    from tools import advisory_policy_dedup as policy
    out = policy.runner.OUTPUT / 'scoring_policies/advisory070_penalty080_v1'
    extension = out / 'execution_extensions/request_timeout_v1'
    original = json.loads((out / 'execution_manifest.json').read_text())
    for name, sha in original['source_sha256'].items():
        if policy.file_sha(policy.runner.ROOT / name) != sha:
            raise ValueError(f'Frozen policy dependency changed: {name}')
    sources = {name: policy.file_sha(policy.runner.ROOT / name) for name in
               ('tools/advisory_timeout.py', 'tests/test_advisory_timeout.py')}
    manifest = {'policy_execution_sha256': policy.file_sha(out / 'execution_manifest.json'),
                'source_sha256': sources, 'deadline_seconds': 120, 'concurrency': 4,
                'outer_attempts': 3, 'method': 'Isolate entire original router call, kill and reap child before retry',
                'preserved': 'model, effort, prompts, token limits, thresholds, existing checkpoints, original validation',
                'scheduling': 'Each child uses original key configuration; in-memory key load/affinity is per child',
                'limitation': 'Connection termination cannot guarantee provider-side computation cancellation; timed-out usage may be unavailable'}
    policy.runner.freeze_manifest(extension / 'manifest.json', manifest)
    for name in sources:
        target = extension / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = (policy.runner.ROOT / name).read_bytes()
        if target.exists() and target.read_bytes() != data:
            raise ValueError('Archived timeout source changed')
        target.write_bytes(data)
    print('Verified timeout extension: 120 seconds per attempt, original three-attempt limit, four workers', flush=True)
    if args.prepare_only:
        return
    install(extension, 120)
    policy.main(['--run'])


if __name__ == '__main__':
    main()
