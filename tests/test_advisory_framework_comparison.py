import unittest
from tools import advisory_framework_comparison as comparison

class ComparisonTests(unittest.TestCase):
    def test_same_identities_and_matched_cells_isolate_threshold_effect(self):
        # Two equivalent texts are ONE advisory. Its strongest source is >=.80.
        groups=[{'decision':'accepted','sources':[{'confidence':.7},{'confidence':.9}]},
                {'decision':'accepted','sources':[{'confidence':.7}]},
                {'decision':'penalty','sources':[{'confidence':.9}]}]
        self.assertEqual(comparison.advisory_counts(groups),(1,2))
        fw=['vanilla-engineered','metareview-realistic','compound-realistic']
        cells={f'm|{f}|low':{'n_pr':6,'advisory_measured':True,
                 'per_pr':[{'url':f'u{i}','counts':[1,2,0,0,2,1]} for i in range(6)]} for f in fw}
        evidence={f'{f}{i}':{'records':groups} for f in fw for i in range(6)}
        selected=[{'run_id':f'{f}{i}','model':'m','framework':f,'effort':'low','url':f'u{i}'} for f in fw for i in range(6)]
        cells['extra|vanilla-engineered|low']={'n_pr':6,'advisory_measured':True,'per_pr':[]}
        result=comparison.summarize(cells,evidence,selected)
        self.assertEqual(result['matched_model_effort_combinations'],1)
        for row in result['frameworks'].values():
            self.assertEqual((row['reviews'],row['A80'],row['A70'],row['H80']),(6,6,12,6))
            self.assertAlmostEqual(row['mean_F2p_A80'],6/11)
            self.assertAlmostEqual(row['mean_F2p_A70'],7/12)
            self.assertEqual(row['TP'],6)

    def test_below_threshold_source_does_not_earn_baseline_credit(self):
        self.assertEqual(comparison.advisory_counts([
            {'decision':'accepted','sources':[{'confidence':.79}]},
            {'decision':'excluded_verified_bug','sources':[{'confidence':.9}]}]),(0,1))
