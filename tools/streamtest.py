"""Streaming-path validation: one real lens call through call_model_json (streaming ON)."""
import asyncio, time, os, sys
os.environ.setdefault('HARNESS_LUNAROUTE_TIMEOUT_S', '600')
from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.adapters.metareview import LENS_SYSTEM, LENS_PROMPTS
from harnesseval.model_router import call_model_json, _STREAM_LUNAROUTE

async def main():
    print('streaming enabled:', _STREAM_LUNAROUTE, flush=True)
    diff = fetch_diff('https://github.com/calcom/cal.com/pull/10967').get('diff') or ''
    prompt = f"{LENS_PROMPTS['security']}\n\n# Diff\n{diff}"
    t0 = time.time()
    parsed, tin, tout, pmu = await call_model_json(
        'glm-5.3-vision-background', system=LENS_SYSTEM, user=prompt, effort='high')
    n = len(parsed.get('findings') or [])
    print(f'RESULT OK {time.time()-t0:.0f}s findings={n} in={tin} out={tout}', flush=True)

asyncio.run(main())
