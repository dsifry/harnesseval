"""Is 6-wide real, or are 2 requests merely queued? Measure per-request TTFT (streaming)."""
import time, threading, os, json
from openai import OpenAI
from harnesseval.dataset.pr_diff import fetch_diff
from harnesseval.adapters.metareview import LENS_SYSTEM, LENS_PROMPTS

diff = fetch_diff("https://github.com/calcom/cal.com/pull/10967").get("diff") or ""
k = {}
for line in open(os.path.expanduser("~/.config/harnesseval/keys.env.bench")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k[line.split("=", 1)[0]] = line.split("=", 1)[1]

def go(i, lens, res):
    prompt = f"{LENS_PROMPTS[lens]}\n\n# Diff\n{diff}"
    c = OpenAI(api_key=k["HARNESS_LUNAROUTE_API_KEY"], base_url=k["LUNAROUTE_BASE_URL"], timeout=1200, max_retries=0)
    t0 = time.time()
    ttft = None
    try:
        stream = c.chat.completions.create(
            model="glm-5.3-vision-background",
            messages=[{"role": "system", "content": LENS_SYSTEM}, {"role": "user", "content": prompt}],
            max_completion_tokens=65536, reasoning_effort="high",
            stream=True, stream_options={"include_usage": True})
        for chunk in stream:
            if ttft is None:
                ch = chunk.choices[0] if getattr(chunk, "choices", None) else None
                d = getattr(ch, "delta", None) if ch else None
                if d and (getattr(d, "content", None) or getattr(d, "reasoning_content", None)):
                    ttft = time.time() - t0
        res[i] = (lens, ttft, time.time() - t0)
    except Exception as e:
        res[i] = (lens, ttft, f"ERR {type(e).__name__} after {time.time()-t0:.0f}s")

lenses = list(LENS_PROMPTS)[:6]
res = {}
ts = [threading.Thread(target=go, args=(i, l, res)) for i, l in enumerate(lenses)]
wall0 = time.time()
[t.start() for t in ts]; [t.join() for t in ts]
print(f"wall clock for all 6: {time.time()-wall0:.0f}s")
print(f"{'lens':14s} {'TTFT':>8s} {'total':>8s}")
for i in range(6):
    lens, ttft, tot = res[i]
    tt = f"{ttft:.0f}s" if isinstance(ttft, float) else "never"
    tt2 = f"{tot:.0f}s" if isinstance(tot, float) else tot
    print(f"{lens[:14]:14s} {tt:>8s} {tt2:>8s}")
