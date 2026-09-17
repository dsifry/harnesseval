"""mitmproxy addon: dump every lunaroute request/response to a searchable log.
Usage: mitmdump -s tools/lunaroute_spy.py --mode reverse:https://gw.lunaroute.com -p 8080
Log: logs/lunaroute_spy.jsonl — one JSON line per HTTP exchange:
  {ts, method, path, status, req_body_chars, resp_body_chars, req_head, resp_head, duration}
  req_head/resp_head are the first 2000 chars of each body (truncated for the long streaming ones).
"""
import json, time, os

LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "lunaroute_spy.jsonl")
HEAD = 2000

def request(flow):
    flow.metadata["spy_ts"] = time.time()
    try:
        body = flow.request.get_text() or ""
    except Exception:
        body = ""
    import re
    mt = re.search(r'"max_completion_tokens"\s*:\s*(\d+)', body) or re.search(r'"max_tokens"\s*:\s*(\d+)', body)
    eff = re.search(r'"reasoning_effort"\s*:\s*"(\w+)"', body)
    with open(LOG, "a") as f:
        f.write(json.dumps({
            "ts": time.strftime("%H:%M:%S"), "dir": "req",
            "method": flow.request.method, "path": flow.request.path,
            "chars": len(body), "cap": int(mt.group(1)) if mt else None,
            "effort": eff.group(1) if eff else None, "head": body[:HEAD],
        }) + "\n")

def response(flow):
    try:
        body = flow.response.get_text() or ""
    except Exception:
        body = ""
    dur = round(time.time() - flow.metadata.get("spy_ts", time.time()), 1)
    import re
    fr = re.search(r'"finish_reason"\s*:\s*"(\w+)"', body)
    ut = re.search(r'"total_tokens"\s*:\s*(\d+)', body)
    rt = re.search(r'"reasoning_output_tokens"\s*:\s*(\d+)', body) or re.search(r'"reasoning_tokens"\s*:\s*(\d+)', body)
    ct = re.search(r'"completion_tokens"\s*:\s*(\d+)', body)
    with open(LOG, "a") as f:
        f.write(json.dumps({
            "ts": time.strftime("%H:%M:%S"), "dir": "resp",
            "status": flow.response.status_code, "path": flow.request.path,
            "chars": len(body), "dur_s": dur,
            "finish": fr.group(1) if fr else None,
            "total_tok": int(ut.group(1)) if ut else None,
            "completion_tok": int(ct.group(1)) if ct else None,
            "reasoning_tok": int(rt.group(1)) if rt else None,
            "head": body[:HEAD],
        }) + "\n")
