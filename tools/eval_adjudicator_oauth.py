#!/usr/bin/env python3
"""OAuth-CLI judge variant: premium models (astra via codex, opus via claude) at $0 API cost."""
import asyncio, collections, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import readjudicate3 as rj
from harnesseval.cli_backends import _codex_cli, _claude_cli
from eval_adjudicator import sample_findings

def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

async def run(judge_spec, cli_kind, slug, n=90, conc=3):
    sample = sample_findings(n)
    sem = asyncio.Semaphore(conc)
    t0 = time.time()
    async def one(s):
        diff, text, ref, prov = s
        prompt = rj.V2_PROMPT.format(diff=diff[:rj.DIFF_LIMIT], candidate=rj.strip_provenance(text))
        try:
            if cli_kind == "codex":
                out, _, _ = await _codex_cli(slug, "low", prompt, rj.V2_SYSTEM)
            else:
                out, _, _ = await _claude_cli(slug, "low", prompt, rj.V2_SYSTEM)
            d = extract_json(out) or {}
            cat = str(d.get("category", "")).strip().lower()
            return cat if cat in ("bug", "important_non_bug", "hallucination") else "unresolved", ref
        except Exception as e:
            return f"error:{type(e).__name__}", ref
    res = await asyncio.gather(*[one(s) for s in sample])
    verdicts = [{"verdict": g, "ref": r, "text": s[1][:160]} for (g, r), s in zip(res, sample)]
    outdir = Path("analysis/adjudicator_verdicts"); outdir.mkdir(exist_ok=True)
    safe = judge_spec.replace(":", "_")
    (outdir / f"{safe}.json").write_text(json.dumps(verdicts, indent=1))
    dist = collections.Counter(v["verdict"] for v in verdicts)
    agrees = sum(1 for v in verdicts if v["verdict"] == v["ref"])
    print(f"{judge_spec:35s} agreement={agrees/len(sample):.3f} dist={dict(dist)} wall={time.time()-t0:.0f}s", flush=True)

async def main():
    await run("gpt-6-astra:oauth", "codex", "gpt-6-astra")
    await run("claude-opus-4-5:oauth", "claude", "opus")
asyncio.run(main())
