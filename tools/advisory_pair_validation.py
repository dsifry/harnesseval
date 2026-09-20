"""Common-pass duplicate scoring validation, adapted from readjudicate3 pairs.

This assesses equivalence of complete claims, not factual truth. Each distinct
claim still receives its own independent classifier judgment.
"""
import hashlib
import math
import readjudicate3 as rj
from tools.report_advisories import _normalize

SYSTEM = rj.MERGE_SYSTEM
PROMPT = rj.MERGE_PROMPT.split('Respond with ONLY')[0] + '''
For THIS scoring pass, duplicate equivalence is stricter than sharing a root cause.
You must compare the COMPLETE MATERIAL CLAIMS, including mechanism, triggering
conditions, execution path, and consequence. The same line or broad concern does
not establish equivalence. A report of wrong-category selection, a case/rename
mismatch, a crash, and a silent fallback are different claims even at one lookup.
An inactive/unbound API concern and an alleged active user-facing failure differ.
A compound report with an additional material claim does NOT equal its subset.
Differences only in wording, severity, or hedging do not create separate claims.
If the claimed mechanisms, triggers or consequences conflict, or one report adds
an unsupported/different material factual claim, return same=false. You are NOT
verifying which claim is true; do not repair or reinterpret either report to make
them match. If unsure whether their full claims are equivalent, return false.

For every numbered pair, extract what A and B actually CLAIM into mechanism,
trigger and consequence. Then list material_differences and give your equivalence
verdict, confidence and reason. same=true requires no material differences.
Return ONLY this JSON object, with EVERY pair index exactly once:
{"pairs":[{"pair":1,"a":{"mechanism":"...","trigger":"...","consequence":"..."},"b":{"mechanism":"...","trigger":"...","consequence":"..."},"material_differences":[],"same":true,"confidence":0.9,"reason":"..."}]}

PAIRS:
{pairs}
'''


def claim_key(text):
    return hashlib.sha256(_normalize(text).encode()).hexdigest()


def make_prompt(pairs):
    return PROMPT.replace('{pairs}', '\n\n'.join(f'PAIR {i}:\nA: {_normalize(a)}\nB: {_normalize(b)}' for i,(a,b) in enumerate(pairs,1)))


def parse_votes(parsed, n):
    votes=parsed.get('pairs') if isinstance(parsed,dict) else None
    if not isinstance(votes,list) or len(votes)!=n:raise ValueError('Incomplete pair verdicts')
    by={}
    for vote in votes:
        if not isinstance(vote,dict) or type(vote.get('pair')) is not int:raise ValueError('Invalid pair index')
        index=vote['pair']
        if index in by or not 1<=index<=n:raise ValueError('Duplicate or out-of-range pair index')
        if type(vote.get('same')) is not bool:raise ValueError('Pair same must be boolean')
        confidence=vote.get('confidence')
        if isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not math.isfinite(confidence) or not 0<=confidence<=1:raise ValueError('Invalid pair confidence')
        differences=vote.get('material_differences')
        if not isinstance(differences,list) or any(not isinstance(x,str) for x in differences):raise ValueError('Missing material-difference evidence')
        for side in ['a','b']:
            claims=vote.get(side)
            if not isinstance(claims,dict) or any(not isinstance(claims.get(k),str) or not claims[k].strip() for k in ['mechanism','trigger','consequence']):raise ValueError('Missing extracted claim fields')
        if not isinstance(vote.get('reason'),str) or not vote['reason'].strip():raise ValueError('Missing pair reasoning')
        by[index]=vote['same'] and confidence>=.8 and not differences
    return [by[i] for i in range(1,n+1)]


def scoring_identity(duplicate_id, result):
    from tools.report_advisories import accepted_common_verdict
    category=accepted_common_verdict({'new_verdict':result['verdict'],'confidence':result.get('confidence')},{'minimum_confidence':.8})
    return f'{duplicate_id}:{category}'


async def refine_groups(proposed, compare):
    """Split candidate groups, then enforce pairwise cliques, never connectivity.

    Rejects are reconsidered against a new representative; different root claims
    can therefore form separate paraphrase groups. Every surviving pair must pass.
    """
    import itertools
    cache={}
    async def judged(requests):
        keys=[tuple(sorted(pair)) for pair in requests]
        missing=list(dict.fromkeys(k for k in keys if k not in cache))
        if missing:
            votes=await compare(missing)
            if len(votes)!=len(missing):raise ValueError('Incomplete equivalence decisions')
            cache.update(zip(missing,votes))
        return [cache[k] for k in keys]
    pending=[sorted(g) for g in proposed if g];stars=[]
    while pending:
        requests=[(g[0],i) for g in pending for i in g[1:]]
        decisions=iter(await judged(requests));next_pending=[]
        for group in pending:
            accepted=[group[0]];rejected=[]
            for i in group[1:]:
                (accepted if next(decisions) else rejected).append(i)
            stars.append(accepted)
            if rejected:next_pending.append(rejected)
        pending=next_pending
    await judged([pair for g in stars for pair in itertools.combinations(g,2)])
    result=[]
    for group in stars:
        cliques=[]
        for i in group:
            for clique in cliques:
                if all(cache[tuple(sorted((i,j)))] for j in clique):clique.append(i);break
            else:cliques.append([i])
        result.extend(cliques)
    return result
