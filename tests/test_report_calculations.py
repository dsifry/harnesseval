"""Regression checks using real report code without its import-time generation."""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def report_tree():
    return ast.parse((ROOT / 'tools/final_report_compute.py').read_text())


def function(name):
    node = next(n for n in ast.walk(report_tree()) if isinstance(n, ast.FunctionDef) and n.name == name)
    scope = {'np': np}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<report helper>', 'exec'), scope)
    return scope[name]


class BootstrapTests(unittest.TestCase):
    def test_metrics_aggregate_sampled_prs_not_metric_columns(self):
        rows = np.array([[2, 4, 1, 1], [1, 2, 0, 1], [0, 2, 2, 0], [3, 4, 0, 0]], dtype=float)
        indices = np.array([[0, 1, 2, 3], [0, 0, 0, 0]])
        # Totals: (6,12,3,2) and (8,16,4,4), respectively.
        for name in ('_mets', '_m'):
            with self.subTest(helper=name):
                recall, f1, f1p = function(name)(rows, indices)
                np.testing.assert_allclose(recall, [.5, .5])
                np.testing.assert_allclose(f1, [4/7, 4/7])
                np.testing.assert_allclose(f1p, [12/23, .5])

    def test_harness_recall_intervals_match_pooled_point_estimate(self):
        from collections import defaultdict
        rows = np.array([[1, 1], [0, 9]], dtype=float)
        vanilla = np.array([[0, 1], [0, 9]], dtype=float)
        def matrix(cell, urls, **kwargs):
            return vanilla if cell[1] == 'vanilla-engineered' else rows
        class Samples:
            def integers(self, *args, **kwargs):
                # Every replicate includes both PRs: micro recall = 1/10,
                # whereas the incorrect average of PR recalls is 1/2.
                return np.array([[0, 1], [0, 1]])
        for name in ('_hv_sem', '_vhv'):
            with self.subTest(comparison=name):
                tree = report_tree()
                body = next(n.body for n in ast.walk(tree) if isinstance(getattr(n, 'body', None), list)
                            and any(isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in x.targets) for x in n.body))
                start = next(i for i, x in enumerate(body) if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in x.targets))
                scope = {'np': np, 'MODELS': ['model'], 'EFFORTS': ['low'], 'TOP6': [0, 1],
                         'sel': defaultdict(lambda: {0: None, 1: None}), 'B': 2,
                         'rng4': Samples(), 'rng5': Samples(), '_sem_rows': matrix,
                         '_verified_rows': lambda cell, urls: [{'tpB': t, 'den': d} for t, d in matrix(cell, urls)]}
                exec(compile(ast.Module(body=body[start:start+2], type_ignores=[]), '<harness comparison>', 'exec'), scope)
                for result in scope[name].values():
                    np.testing.assert_allclose(result['dRecall_sem'], [.1, .1, .1])

    def test_cost_comparison_uses_glm_low_and_opus_medium(self):
        tree = report_tree()
        start = next(i for i, n in enumerate(tree.body) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ratio3' for t in n.targets))
        urls = list(range(6))
        glm = ('glm-5.3-vision-background', 'metareview-realistic', 'low')
        glm_medium = (*glm[:2], 'medium')
        opus = ('claude-opus-5', 'metareview-realistic', 'medium')
        from collections import defaultdict
        selection = defaultdict(dict, {c: dict.fromkeys(urls) for c in (glm, glm_medium, opus)})
        values = {glm: [10, 1], glm_medium: [90, 9], opus: [20, 4]}
        def matrix(cell, urls):
            return np.tile(values[cell], (len(urls), 1))
        scope = {'np': np, 'TOP6': urls, 'sel': selection, 'KEYS': ['tok', 'cost'], 'B': 20,
                 'rng': np.random.default_rng(1), 'cell_matrix': matrix,
                 'blended': lambda cell, urls: dict(zip(('tok', 'cost'), matrix(cell, urls).sum(axis=0)))}
        exec(compile(ast.Module(body=tree.body[start:start+2], type_ignores=[]), '<cost ratios>', 'exec'), scope)
        key = '|'.join(glm) + ' vs ' + '|'.join(opus)
        np.testing.assert_allclose(scope['ratio3'][key]['costtask_ratio'], [.25, .25, .25])


class CatalogueTests(unittest.TestCase):
    def catalogue(self, metadata, registry=None):
        spec = importlib.util.spec_from_file_location('catalog', ROOT / 'tools/gold_defect_catalog.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vg = root / 'analysis/verified_gold'
            dd = vg / '1/B01-claim/defects/1-D01'
            dd.mkdir(parents=True)
            (dd / 'test.diff').write_text('test artifact')
            (dd / 'meta.json').write_text(json.dumps(metadata))
            defect = {'id': '1-D01', 'pr': '1', 'label': 'claim', 'bundle': '1-B01', 'tier': 'D-verified', **(registry or {})}
            (vg / 'DEFECT_REGISTRY.json').write_text(json.dumps({'defects': [defect]}))
            (root / 'analysis/final_report_dataset.json').write_text(json.dumps({'pr_golden': [], 'all_healthy_runs': []}))
            with patch.object(module, 'ROOT', root), patch.object(module, 'VG', vg), contextlib.redirect_stdout(io.StringIO()):
                module.main()
            return json.loads((vg / 'GOLD_DEFECT_CATALOG.json').read_text())['defects'][0]

    def test_container_provenance_does_not_claim_orthogonality(self):
        rec = self.catalogue({'evidence_provenance': 'container 1-B01: single-defect container', 'own_fix_makes_test_pass': True, 'sibling_fix_leaves_test_red': None})
        self.assertIn('container', rec['exact_test'])
        self.assertNotIn('orthogonality proven', rec['exact_test'])

    def test_absent_or_negative_orthogonality_is_not_proof(self):
        for sibling in (None, False):
            with self.subTest(sibling=sibling):
                rec = self.catalogue({'own_fix_makes_test_pass': True, 'sibling_fix_leaves_test_red': sibling})
                self.assertNotIn('orthogonality proven', rec['exact_test'])

    def test_explicit_orthogonality_is_reported(self):
        rec = self.catalogue({'own_fix_makes_test_pass': True, 'sibling_fix_leaves_test_red': True})
        self.assertIn('orthogonality proven', rec['exact_test'])

    def test_withdrawal_overrides_old_label_verification(self):
        rec = self.catalogue({'own_fix_makes_test_pass': True}, {'tier': 'D-withdrawn', 'withdrawn': True, 'withdrawn_reason': 'test manufactures failure', 'label_corrected': 'old correction'})
        self.assertIn('withdrawn', rec['label_review'].lower())
        self.assertIn('test manufactures failure', rec['label_review'])
        self.assertIsNot(rec['head_fail_fixed_pass'], True)

    def test_missing_execution_metadata_is_not_verified(self):
        rec = self.catalogue({})
        self.assertIsNone(rec['head_fail_fixed_pass'])
        self.assertFalse(rec['label_review'].startswith('verified:'))


if __name__ == '__main__':
    unittest.main()
