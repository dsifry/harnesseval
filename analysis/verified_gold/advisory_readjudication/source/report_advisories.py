"""Read saved full-channel advisory evidence; never invoke a judge.

An accepted ``important_non_bug`` verdict is an existing-adjudication proxy for
quality, not a fresh independent staff review or advisory-ceiling recall score.
Normalization removes bookkeeping only. Semantic deduplication is limited to
cluster identities already recorded by readjudication3, scoped to this run.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
import hashlib
from pathlib import Path
import re
import warnings


_METADATA = re.compile(
    r'\[\s*(?:confidence|conf|severity|sev|anchor|effort|model|lens|persona|'
    r'deterministic|metareview-deterministic|metareview-session|compound-persona)'
    r'[^\]]*\]|\[\s*P[0-3](?:\s+[^\]]*)?\]|\[\s*(?:BUG|ADVISORY)\s*\]',
    re.IGNORECASE,
)
_PAREN = re.compile(
    r'\(\s*confidence\s*[:=]?\s*\d+\s*(?:[,;]\s*(?:severity\s*[:=]?\s*)?P[0-3]\s*)?\)',
    re.IGNORECASE,
)
DEDUP_METHOD = 'exact text after provenance/tag/whitespace normalization; saved rj3 cluster ID within run; no new semantic matching'


def _normalize(text: str) -> str:
    return ' '.join(_PAREN.sub('', _METADATA.sub('', text or '')).split())


def advisory_evidence(root: Path, run: dict) -> dict:
    """Return distinct accepted/penalized/unresolved evidence and its provenance.

    ``measured=False`` distinguishes v1's unavailable advisory channel from an
    observed zero. Summary/record discrepancies emit a warning and are included
    in ``warnings``; counts always derive from records, never invented evidence.
    """
    run_id = run['run_id']
    folder = Path(root) / 'runs' / run_id
    summary = json.loads((folder / 'summary.json').read_text())
    if not isinstance(summary.get('adjudication_records'), list):
        raise ValueError(f'{run_id}: missing or invalid adjudication_records evidence')
    original = summary['adjudication_records']
    rj_path = folder / 'readjudication3.json'
    revised = json.loads(rj_path.read_text()) if rj_path.exists() else None
    if revised is not None and not isinstance(revised.get('records'), list):
        raise ValueError(f'{run_id}: missing or invalid readjudication3 records evidence')
    common_dir = Path(root) / 'analysis/verified_gold/advisory_readjudication'
    common_path = common_dir / 'runs' / f'{run_id}.json'
    common_required = (common_dir / 'manifest.json').exists()
    if common_path.exists() and not common_required:
        raise ValueError(f'{run_id}: missing frozen common readjudication manifest')
    common = json.loads(common_path.read_text()) if common_path.exists() else None
    common_complete = common is not None and common.get('status') == 'complete'
    revision_source = 'readjudication3'
    if common_required and not common_complete:
        return {'accepted_count': 0, 'penalty_count': 0, 'unresolved_count': 0,
                'measured': False, 'records': [], 'dedup_method': DEDUP_METHOD,
                'warnings': [f'{run_id}: common readjudication pending; legacy judges not used'],
                'classification_source': 'common_readjudication',
                'advisory_instrument': 'common_pending', 'advisory_run_status': 'pending'}
    if common_complete:
        summary_hash = hashlib.sha256(json.dumps(summary, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if common.get('summary_sha256') != summary_hash:
            raise ValueError(f'{run_id}: common readjudication summary hash changed')
        if common_required:
            manifest = json.loads((common_dir / 'manifest.json').read_text())
            pass_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if common.get('pass_digest') != pass_hash:
                raise ValueError(f'{run_id}: common readjudication pass hash changed')
        recs = common.get('records')
        matched_texts = {_normalize(g['matched_candidate']) for g in summary.get('per_golden_matches', []) if g.get('matched_candidate')}
        expected = {i for i, r in enumerate(original) if not (r.get('matched_golden_ids') or
                    r.get('primary_judge_verdict') == 'matched' or
                    (r.get('adjudication') or {}).get('verdict') == 'matched' or _normalize(r['issue_text']) in matched_texts)}
        if not isinstance(recs, list) or len(recs) != len(expected) or common.get('expected_records') != len(expected) or {r.get('original_record_index') for r in recs} != expected:
            raise ValueError(f'{run_id}: incomplete common readjudication record coverage')
        for r in recs:
            if r.get('issue_text') != original[r['original_record_index']]['issue_text']:
                raise ValueError(f'{run_id}: common readjudication membership changed')
        revised = common
        revision_source = 'common_readjudication'
    revisions = revised['records'] if revised is not None else []
    notices = []

    def warn(message):
        message = f'{run_id}: {message}'
        notices.append(message)
        warnings.warn(message, UserWarning, stacklevel=2)

    def reconcile(records, field, expected, mapping, source):
        actual = Counter(field(record) for record in records)
        for key, verdict in mapping.items():
            if key in expected and expected[key] is not None and expected[key] != actual[verdict]:
                warn(f'{source} {key}={expected[key]} but records contain {actual[verdict]} {verdict}; record counts used')

    verdict = lambda r: (r.get('adjudication') or {}).get('verdict')
    reconcile(original, verdict, summary, {
        'n_important_non_bug': 'important_non_bug', 'n_true_hallucination': 'hallucination',
        'n_unresolved': 'unresolved',
        **({'n_hallucination': 'hallucination'} if 'n_true_hallucination' not in summary else {}),
    }, 'summary')
    if revised is not None:
        reconcile(revisions, lambda r: r.get('new_verdict'), revised.get('corrected') or {}, {
            'n_important': 'important_non_bug', 'n_true_hallucination': 'hallucination',
            'n_unresolved': 'unresolved', 'n_bug_ungold': 'bug',
        }, 'readjudication3')

    matched = {_normalize(g['matched_candidate']) for g in summary.get('per_golden_matches', [])
               if g.get('matched_candidate')}
    entries = []
    for source, records in [('summary', original), (revision_source, revisions)]:
        for index, record in enumerate(records):
            text = _normalize(record.get('issue_text', ''))
            if not text:
                raise ValueError(f'{run_id}: {source} record {index} has no issue_text')
            cluster = record.get('cluster') if source == revision_source else None
            cluster = cluster.get('id') if isinstance(cluster, dict) else cluster
            entries.append({'source': source, 'record_index': index, 'issue_text': record['issue_text'],
                            'normalized_text': text, 'verdict': record.get('new_verdict') if source == revision_source else verdict(record),
                            'cluster_id': cluster, 'matched': bool(record.get('matched_golden_ids')) or
                            record.get('primary_judge_verdict') == 'matched' or text in matched or verdict(record) == 'matched',
                            'evidence': record})

    # Union identical text with saved cluster identity, including bridges across
    # multiple original/revised records. A missing cluster is never a shared key.
    parents = list(range(len(entries)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    for i, entry in enumerate(entries):
        keys = [('text', entry['normalized_text'])]
        if entry['cluster_id'] is not None:
            keys.append(('cluster', entry['cluster_id']))
        for key in keys:
            if key in seen:
                parents[find(i)] = find(seen[key])
            else:
                seen[key] = i
    groups = defaultdict(list)
    for i, entry in enumerate(entries):
        groups[find(i)].append(entry)

    output = []
    for members in groups.values():
        override_texts = {e['normalized_text'] for e in members if e['source'] == revision_source}
        effective = [e for e in members if e['source'] == revision_source or e['normalized_text'] not in override_texts]
        labels = {e['verdict'] for e in effective}
        if any(e['matched'] for e in members):
            decision, label = 'excluded_matched', 'matched'
        elif 'hallucination' in labels:
            decision, label = 'penalty', 'hallucination'
        elif labels & {'bug', 'real_but_ungold'}:
            decision, label = 'excluded_bug', 'bug'
        elif 'unresolved' in labels:
            decision, label = 'unresolved', 'unresolved'
        elif 'important_non_bug' in labels:
            decision, label = 'accepted', 'important_non_bug'
        else:
            decision, label = 'excluded_unjudged', 'unjudged'
        output.append({'decision': decision, 'effective_verdict': label,
                       'normalized_texts': sorted({e['normalized_text'] for e in members}),
                       'cluster_ids': sorted({e['cluster_id'] for e in members if e['cluster_id'] is not None}, key=str),
                       'sources': [{**e, 'superseded': e not in effective} for e in members]})
    return {'accepted_count': sum(r['decision'] == 'accepted' for r in output),
            'penalty_count': sum(r['decision'] == 'penalty' for r in output),
            'unresolved_count': sum(r['decision'] == 'unresolved' for r in output),
            'measured': common_complete if common_required else ('n_true_hallucination' in summary or revised is not None),
            'classification_source': revision_source if revised is not None else 'summary',
            'advisory_instrument': (common.get('model', 'common') if common_complete else 'common_pending') if common_required else (revision_source if revised is not None else 'inrun'),
            'advisory_run_status': 'complete' if common_complete else ('pending' if common_required else 'legacy'),
            'records': output, 'dedup_method': DEDUP_METHOD, 'warnings': notices}
