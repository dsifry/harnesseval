import unittest
import numpy as np
from tools.report_quality import advisory_f2

class AdvisoryQualityTests(unittest.TestCase):
    def test_alternative_bug_universe_cannot_double_credit_an_advisory(self):
        import ast
        from pathlib import Path
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'tools/verified_gold_defect_metrics.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'scored_advisory_counts')
        scope = {'sha': lambda text: text, 'normalize_for_cluster': lambda text: text}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<advisory accounting>', 'exec'), scope)
        evidence = {'records': [{'decision': 'accepted', 'sources': [{'issue_text': 'candidate'}]}]}
        count = scope['scored_advisory_counts']
        self.assertEqual(count(evidence, {'candidate': 'tentative'}, {'verified'})['advisories'], 1)
        self.assertEqual(count(evidence, {'candidate': 'tentative'}, {'verified', 'tentative'})['advisories'], 0)
        below = {'records': [{'decision': 'below_scoring_threshold', 'sources': [{'issue_text': 'candidate'}]}]}
        self.assertEqual(count(below, {}, {'verified'})['below_threshold'], 1)
        self.assertEqual(count(below, {'candidate': 'verified'}, {'verified'})['below_threshold'], 0)

    def test_reduces_to_bug_f2(self):
        self.assertAlmostEqual(advisory_f2(72,147,0,17),360/677)
    def test_reward_and_penalty_have_opposite_effects(self):
        base=advisory_f2(72,147,0,17)
        self.assertGreater(advisory_f2(72,147,89,17),base)
        self.assertLess(advisory_f2(72,147,0,106),base)
    def test_weight_and_bound(self):
        self.assertAlmostEqual(advisory_f2(72,147,89,17),449/766)
        self.assertLess(advisory_f2(72,147,89,17,.5),advisory_f2(72,147,89,17,2))
        self.assertLessEqual(advisory_f2(147,147,100000,0),1)
        self.assertEqual(advisory_f2(0,0,0,0),0)
    def test_bootstrap_uses_pooled_counts(self):
        t=np.array([20,50]);d=np.array([40,107]);a=np.array([2,10]);h=np.array([1,8])
        self.assertAlmostEqual(advisory_f2(t.sum(),d.sum(),a.sum(),h.sum()),362/679)
        np.testing.assert_allclose(advisory_f2(t,d,a,h),[102/183,260/496])

    def test_framework_means_use_the_same_model_effort_mix(self):
        import ast
        from pathlib import Path
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'tools/final_report_true_gold.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'matched_framework_means')
        scope = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<framework means>', 'exec'), scope)
        cells = {f'm|{fw}|low': {'F2p': value} for fw, value in
                 [('vanilla-engineered', .2), ('compound-realistic', .3), ('metareview-realistic', .4)]}
        cells['extra|vanilla-engineered|low'] = {'F2p': .9}
        result = scope['matched_framework_means'](cells)
        self.assertEqual(result['vanilla-engineered'], {'n': 1, 'mean_F2p': .2})
        self.assertEqual(result['compound-realistic']['n'], 1)
        self.assertEqual(result['metareview-realistic']['n'], 1)
