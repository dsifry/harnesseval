"""Read-only source analysis; writes only this separate evaluation directory.

Fixed-seed hash sampling: three advisory claims and one penalty claim per
representative-framework/confidence-band stratum. No classifier calls.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PASS = OUT.parent / 'passes/glm_base_claim_v3'
SEED = 'threshold-audit-20260919-v1'
runs = {r['run_id']: r for r in json.loads((ROOT / 'analysis/final_report_dataset.json').read_text())['selected_runs']}
rows = []
for path in sorted((PASS / 'verdicts').glob('*/*.json')):
    d = json.loads(path.read_text())
    if d.get('instrument') == 'reused_verified_bug':
        continue
    assert d['status'] == 'complete'
    votes = [v for v in d['result']['votes'] if 'category' in v]
    assert len(votes) == 1
    v = votes[0]
    rows.append({'source': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'url': d['url'], 'category': v['category'], 'confidence': v['confidence'],
                 'representative_framework': runs[d['representative']['run_id']]['framework'],
                 'claim': d['judged_text']})
assert len(rows) == 10057
counts = {}
for threshold in (.5, .6, .7, .8):
    counts[str(threshold)] = dict(Counter(r['category'] for r in rows if r['confidence'] >= threshold))
strata = defaultdict(list)
for r in rows:
    c = r['confidence']
    if c < .5 or r['category'] not in ('important_non_bug', 'hallucination'):
        continue
    band = '0.8–1.0' if c >= .8 else '0.7–<0.8' if c >= .7 else '0.6–<0.7' if c >= .6 else '0.5–<0.6'
    strata[(r['category'], band, r['representative_framework'])].append(r)
selected = []
for (category, band, framework), candidates in sorted(strata.items()):
    ordered = sorted(candidates, key=lambda r: hashlib.sha256((SEED + r['source']).encode()).hexdigest())
    n = 3 if category == 'important_non_bug' else 1
    assert len(ordered) >= n
    for r in ordered[:n]:
        selected.append({**r, 'band': band, 'stratum_population': len(candidates)})
selected.sort(key=lambda r: hashlib.sha256((SEED + '-shuffle-' + r['source']).encode()).hexdigest())
for i, r in enumerate(selected, 1):
    r['audit_id'] = f'S{i:02d}'
(OUT / 'population.json').write_text(json.dumps({'pass_digest': json.loads((PASS/'progress.json').read_text())['pass_digest'], 'n':len(rows), 'threshold_counts':counts, 'rows':rows}, indent=2))
(OUT / 'sample_key.json').write_text(json.dumps({'seed':SEED, 'design':'3 advisory + 1 penalty claim per confidence-band/representative-framework stratum; exact claims, not semantic identities; equal stratum allocation, not population prevalence', 'samples':selected}, indent=2))
(OUT / 'sample_claims.json').write_text(json.dumps([{'audit_id':r['audit_id'], 'url':r['url'], 'claim':r['claim']} for r in selected], indent=2))
print(json.dumps({'n':len(rows),'threshold_counts':counts,'audit_claims':len(selected)}))
