"""Hash-bound execution extension for deterministic advisory-pass resumption.

The frozen production runner is not edited. Its grouping function is transformed
only to order chunk results and freeze/load the proposal partition before pair
validation. The original comparison, classifier and export code stays intact.
"""
import argparse
import asyncio
import hashlib
import inspect
import json
import textwrap
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict

from tools import readjudicate_report_advisories as runner


def stable_results(rows):
    return sorted(rows, key=lambda row: (row[0], row[1]))


def proposal_binding(plan, members, pass_digest, categories):
    return {'pass_digest': pass_digest, 'url': plan['url'],
            'plan_sha256': runner.digest(plan),
            'membership_sha256': runner.digest(members),
            'categories_sha256': runner.digest(categories or {})}


def validate_partition(groups, count):
    if not isinstance(groups, list) or any(not isinstance(g, list) or not g for g in groups):
        raise ValueError('Invalid proposal groups')
    values = [i for group in groups for i in group]
    if any(type(i) is not int for i in values) or sorted(values) != list(range(count)):
        raise ValueError('Proposal must partition every unit exactly once')


def freeze_proposal(path, binding, groups, count):
    validate_partition(groups, count)
    runner.freeze_manifest(path, {'binding': binding, 'proposed_groups': groups})


def load_proposal(path, binding, count):
    if not path.exists():
        return None
    value = json.loads(path.read_text())
    if value.get('binding') != binding:
        raise ValueError('Stale frozen proposal inputs')
    validate_partition(value.get('proposed_groups'), count)
    return value['proposed_groups']


def reconstruct_original_proposal(plan, bucket_for, checkpoints):
    """Recover original paid merges; later duplicate requests are excluded.

    Selection timestamps are only a provenance aid: the caller must also verify
    that every original first-round pair request hash matches this partition.
    """
    units = plan['units']
    phases = defaultdict(list)
    for path, timestamp, value in checkpoints:
        if value['url'] != plan['url']:
            raise ValueError('Cross-PR grouping checkpoint')
        if value['status'] == 'complete':
            phases[path.name.rsplit('_', 1)[0]].append((timestamp, path, value))
    selected = []; excluded = []
    for values in phases.values():
        values.sort(key=lambda item: (item[0], str(item[1])))
        selected.append(values[0])
        excluded.extend(item[1] for item in values[1:])
    initial = defaultdict(list); merges = {}
    for _, path, value in selected:
        order = value['request']['units']
        groups = runner.constrained_groups(
            [[order[i] for i in group] for group in
             runner.validate_group_mapping(value['parsed_response'], len(order))], units)
        key = path.name.split('_')[0]
        if '_merge_' in path.name:
            merges[key] = groups
        else:
            initial[key].extend(groups)
    buckets = defaultdict(list)
    for index, bucket in bucket_for.items():
        buckets[tuple(bucket)].append(int(index))
    final = [[i] for i, unit in enumerate(units) if unit['defect_ids']]
    for bucket, indices in sorted(buckets.items()):
        key = runner.digest(bucket)[:10]
        groups = initial[key]
        covered = {i for group in groups for i in group}
        missing = set(indices) - covered
        if len(missing) > 1 or covered - set(indices):
            raise ValueError('Incomplete or wrong-bucket original chunks')
        groups = groups + [[i] for i in sorted(missing)]
        if key in merges:
            owner = {i: group for group in groups for i in group}
            final.extend([[i for rep in group for i in owner[rep]] for group in merges[key]])
        elif len(groups) == 1:
            final.extend(groups)
        else:
            raise ValueError('Missing original representative merge')
    validate_partition(final, len(units))
    return final, [item[1] for item in selected], excluded


def build_resume_grouping():
    source = inspect.getsource(runner.reuse_grouping)
    replacements = {
        'results.append((file,await group(order,name)))':
            'results.append((file,name,await group(order,name)))',
        'for file,groups in results:byfile[file].extend(groups)':
            'for file,name,groups in stable_results(results):byfile[file].extend(groups)',
    }
    for before, after in replacements.items():
        if source.count(before) != 1:
            raise ValueError('Frozen grouping source no longer matches extension')
        source = source.replace(before, after)
    start = source.index('    buckets=defaultdict(list)')
    end = source.index('    async def compare_pairs(pairs):')
    block = source[start:end]
    block = block.replace('    from tools import advisory_pair_validation as pv\n', '')
    extension = '''    checkpoint = out/'proposal_checkpoints'/f'{key}.json'
    binding = proposal_binding(plan, members, pass_hash, categories)
    proposed = load_proposal(checkpoint, binding, len(units))
    if proposed is None:
'''
    extension += textwrap.indent(block, '    ')
    extension += "        freeze_proposal(checkpoint, binding, proposed, len(units))\n"
    extension += '    from tools import advisory_pair_validation as pv\n'
    source = source[:start] + extension + source[end:]
    namespace = dict(vars(runner))
    namespace.update(stable_results=stable_results, proposal_binding=proposal_binding,
                     load_proposal=load_proposal, freeze_proposal=freeze_proposal)
    exec(compile(source, '<hash-bound advisory resume extension>', 'exec'), namespace)
    return namespace['reuse_grouping'], source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=runner.OUTPUT/'passes/glm_base_claim_v3')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    extension_path = args.output/'execution_extensions/deterministic_grouping_v1'
    manifest = json.loads((extension_path/'manifest.json').read_text())
    raw = json.loads((args.output/'manifest.json').read_text())
    if runner.digest(raw) != manifest['raw_pass_digest']:
        raise ValueError('Wrong raw pass for execution extension')
    for name, sha in manifest['source_sha256'].items():
        if hashlib.sha256((runner.ROOT/name).read_bytes()).hexdigest() != sha:
            raise ValueError(f'Execution extension source changed: {name}')
    for name, sha in manifest['frozen_recovery_files'].items():
        if hashlib.sha256((args.output/name).read_bytes()).hexdigest() != sha:
            raise ValueError(f'Frozen recovery evidence changed: {name}')
    function, source = build_resume_grouping()
    if hashlib.sha256(source.encode()).hexdigest() != manifest['generated_grouping_sha256']:
        raise ValueError('Generated grouping source changed')
    if args.verify_only:
        print('Execution extension and frozen recovery hashes verified')
        return
    if (args.output/'STOP').exists():
        raise ValueError('STOP drain flag still present')
    runner.reuse_grouping = function
    config = SimpleNamespace(root=runner.ROOT, output=args.output, judge=raw['model'],
                             group_judge=raw['grouping_model'], effort=raw['effort'],
                             concurrency=4, dry_run=False, prepare_only=False)
    asyncio.run(runner.sequential_main(config))


if __name__ == '__main__':
    main()
