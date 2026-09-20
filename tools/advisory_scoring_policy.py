"""Versioned report scoring over immutable common-pass classifier evidence.

This module is separate from the frozen runner and its original 0.80 export.
Changing scoring never changes a classifier's category/confidence. A-only
policy-specific duplicate identities are mandatory before publishing scores.
"""
from collections import defaultdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

from tools import report_advisories as legacy


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def decision(category, confidence, policy):
    if category not in ('important_non_bug', 'hallucination', 'bug'):
        raise ValueError('Unknown raw classifier category')
    if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence) or not 0 <= confidence <= 1):
        raise ValueError('Invalid classifier confidence')
    threshold, accepted = {
        'important_non_bug': (policy['advisory_minimum_confidence'], 'accepted'),
        'hallucination': (policy['penalty_minimum_confidence'], 'penalty'),
        'bug': (policy['bug_label_minimum_confidence'], 'excluded_bug'),
    }[category]
    return accepted if confidence >= threshold else 'below_scoring_threshold'


def raw_vote(saved):
    if saved.get('status') != 'complete':
        raise ValueError('Classification is not complete')
    votes = saved.get('result', {}).get('votes', [])
    if len(votes) != 1 or 'category' not in votes[0]:
        raise ValueError('Expected one independent raw classification vote')
    vote = votes[0]
    return vote['category'], vote.get('confidence')


def score_records(records, classifications, advisory_groups, policy):
    groups = defaultdict(list)
    for record in records:
        fixed = record.get('instrument') == 'reused_verified_bug'
        if fixed:
            category, confidence, outcome = 'bug', None, 'excluded_bug'
            identity = ('fixed', tuple(record['defect_ids']))
        else:
            category, confidence = raw_vote(classifications[record['verdict_path']])
            outcome = decision(category, confidence, policy)
            if outcome == 'accepted':
                claim_id = Path(record['verdict_path']).stem
                if claim_id not in advisory_groups:
                    raise ValueError('Missing policy-specific advisory dedup identity')
                identity = ('advisory', advisory_groups[claim_id])
            else:
                # H and high-confidence bug labels retain original identities.
                # Unscored raw categories remain distinct in audit counts.
                identity = (outcome, category, record['duplicate_group_id'])
        groups[identity].append({'source': 'common_readjudication',
                                'record_index': record['original_record_index'],
                                'issue_text': record['issue_text'],
                                'normalized_text': legacy._normalize(record['issue_text']),
                                'raw_verdict': category, 'confidence': confidence,
                                'verdict': category, 'scoring_decision': outcome,
                                'evidence': record, 'superseded': False})
    output = []
    for identity, sources in groups.items():
        outcome = sources[0]['scoring_decision']
        output.append({'decision': outcome, 'effective_verdict': sources[0]['raw_verdict'],
                       'normalized_texts': sorted({s['normalized_text'] for s in sources}),
                       'cluster_ids': [repr(identity)], 'sources': sources})
    return {'accepted_count': sum(g['decision'] == 'accepted' for g in output),
            'penalty_count': sum(g['decision'] == 'penalty' for g in output),
            'below_threshold_count': sum(g['decision'] == 'below_scoring_threshold' for g in output),
            'records': output}


@lru_cache(maxsize=20000)
def _read_json(path, mtime_ns, size):
    return json.loads(Path(path).read_text())


def read_json(path):
    path = Path(path)
    stat = path.stat()
    return _read_json(str(path), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=4096)
def _hashed_json(path, expected_sha, fingerprint):
    """Cache verified bytes, invalidated by replacement or any normal file edit."""
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError('Policy audit or checkpoint hash changed')
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError('Policy evidence must be a JSON object')
    return value


def bound_json(directory, reference):
    if (not isinstance(reference, dict) or not isinstance(reference.get('path'), str)
            or not isinstance(reference.get('sha256'), str)):
        raise ValueError('Missing policy evidence path or hash')
    path = (Path(directory)/reference['path']).resolve()
    if not path.is_relative_to(Path(directory).resolve()):
        raise ValueError('Policy evidence path escapes its evidence root')
    try:
        stat = path.stat()
        fingerprint = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        return _hashed_json(str(path), reference['sha256'], fingerprint)
    except OSError as exc:
        raise ValueError('Missing policy evidence file') from exc


def validate_group_audit(directory, common, groups):
    """Bind scored identities to the immutable partition and paid checkpoints.

    This consumes saved judgments; it never changes or reruns the frozen judge.
    File fingerprints keep repeated per-review reads cheap without hiding edits.
    """
    audit = bound_json(directory, groups.get('audit'))
    binding = audit.get('binding')
    fields = ('url', 'raw_pass_digest', 'policy_sha256', 'classification_sha256', 'source_sha256')
    if (not isinstance(binding, dict)
            or any(field not in groups or binding.get(field) != groups[field] for field in fields)):
        raise ValueError('Policy audit binding does not match scored evidence')
    eligible = groups.get('eligible_claim_ids')
    partition = audit.get('validated_groups')
    if (not isinstance(eligible, list) or any(type(i) is not int or i < 0 for i in eligible)
            or len(set(eligible)) != len(eligible)
            or not isinstance(partition, list)
            or any(not isinstance(group, list) or not group for group in partition)):
        raise ValueError('Invalid policy audit partition')
    members = [i for group in partition for i in group]
    if any(type(i) is not int for i in members) or sorted(members) != sorted(eligible):
        raise ValueError('Policy audit partition must cover eligible claims exactly once')
    expected_mapping = {str(i):gid for gid, group in enumerate(partition) for i in group}
    mapping = groups.get('claim_to_group')
    if (not isinstance(mapping, dict) or any(type(gid) is not int for gid in mapping.values())
            or mapping != expected_mapping):
        raise ValueError('Policy mapping does not match its verified audit partition')
    for field, root in (('policy_calls', directory), ('reused_pair_checkpoints', common)):
        references = audit.get(field)
        if not isinstance(references, list):
            raise ValueError('Missing policy audit checkpoints')
        for reference in references:
            checkpoint = bound_json(root, reference)
            if checkpoint.get('status') != 'complete' or checkpoint.get('url') != groups['url']:
                raise ValueError('Incomplete or cross-PR policy checkpoint')
            if field == 'policy_calls':
                if checkpoint.get('binding') != binding:
                    raise ValueError('Policy checkpoint binding changed')
            elif checkpoint.get('pass_digest') != groups['raw_pass_digest']:
                raise ValueError('Reused pair checkpoint belongs to a different raw pass')
            request = checkpoint.get('request')
            if (not isinstance(request, dict) or request.get('url') != groups['url']
                    or digest(request) != checkpoint.get('request_sha256')):
                raise ValueError('Policy checkpoint request hash or PR changed')


def active_policy(root, common):
    base = Path(root)/'analysis/verified_gold/advisory_readjudication'
    pointer = base/'active_scoring_policy.json'
    if not pointer.exists():
        return None
    active = read_json(pointer)
    directory = (base/active['directory']).resolve()
    if not directory.is_relative_to(base.resolve()):
        raise ValueError('Scoring policy directory escapes evidence root')
    policy = read_json(directory/'policy.json')
    if digest(policy) != active['policy_sha256']:
        raise ValueError('Active scoring policy hash changed')
    if policy['raw_pass_digest'] != digest(read_json(common/'manifest.json')):
        raise ValueError('Scoring policy points to a different raw pass')
    for field in ('advisory_minimum_confidence', 'penalty_minimum_confidence', 'bug_label_minimum_confidence'):
        value = policy[field]
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not 0 <= value <= 1:
            raise ValueError('Invalid scoring policy cutoff')
    if policy.get('below_threshold') != 'classified_but_unscored':
        raise ValueError('Policy must preserve classified but unscored findings')
    return directory, policy, active['policy_sha256']


def advisory_evidence(root, run):
    # Reuse original full coverage, member text, summary, pass and verified-source
    # guards without modifying the runner's frozen module or acceptance policy.
    baseline = legacy.advisory_evidence(root, run)
    common = legacy.common_pass_directory(root)
    active = active_policy(root, common)
    if active is None:
        return baseline
    directory, policy, policy_sha = active
    if baseline.get('advisory_run_status') != 'complete':
        return {**baseline, 'acceptance_policy': policy, 'acceptance_policy_sha256': policy_sha}
    key = run['url'].rsplit('/', 1)[-1]+'-'+digest(run['url'])[:12]
    group_path = directory/'groups'/f'{key}.json'
    if not group_path.exists():
        return {**baseline, 'accepted_count':0, 'penalty_count':0, 'below_threshold_count':0,
                'unresolved_count':0, 'records':[], 'measured':False,
                'advisory_run_status':'pending', 'acceptance_policy':policy,
                'acceptance_policy_sha256':policy_sha,
                'warnings':baseline['warnings']+['Policy-specific advisory deduplication pending; no provisional counts published']}
    groups = read_json(group_path)
    if (groups.get('status') != 'complete' or groups.get('url') != run['url']
            or groups.get('raw_pass_digest') != policy['raw_pass_digest']
            or groups.get('policy_sha256') != policy_sha):
        raise ValueError('Incomplete or stale policy-specific deduplication')
    mapping = groups['claim_to_group']
    if set(mapping) != {str(i) for i in groups['eligible_claim_ids']}:
        raise ValueError('Incomplete advisory identity mapping')
    validate_group_audit(directory, common, groups)
    saved_run = read_json(common/'runs'/f"{run['run_id']}.json")
    classifications = {}
    for record in saved_run['records']:
        if record.get('instrument') == 'reused_verified_bug':
            continue  # legacy already checked each record's own frozen assignment
        path = (common/record['verdict_path']).resolve()
        if not path.is_relative_to(common.resolve()):
            raise ValueError('Classifier path escapes raw pass')
        if hashlib.sha256(path.read_bytes()).hexdigest() != groups.get('classification_sha256', {}).get(path.stem):
            raise ValueError('Classifier source hash changed since policy deduplication')
        saved = read_json(path)
        if (saved.get('url') != run['url'] or saved.get('pass_digest') != policy['raw_pass_digest']
                or saved.get('judged_text') != legacy._normalize(record['issue_text'])):
            raise ValueError('Classifier claim provenance changed')
        classifications[record['verdict_path']] = saved
    result = score_records(saved_run['records'], classifications, mapping, policy)
    return {**baseline, **result,
            # Compatibility alias only for old downstream schemas. The decision
            # and raw category remain explicit; this is NOT processing failure.
            'unresolved_count':result['below_threshold_count'],
            'acceptance_policy':policy, 'acceptance_policy_sha256':policy_sha,
            'dedup_method':'Policy-specific A-only material-equivalence cliques; original H identities; no verdict sharing',
            'policy_dedup_path':str(group_path.relative_to(Path(root).resolve())),
            'policy_dedup_sha256':hashlib.sha256(group_path.read_bytes()).hexdigest()}
