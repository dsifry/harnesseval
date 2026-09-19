"""Exercise the real dashboard generator and Node exporter in a temporary tree."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DashboardExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'tools/final_report_html.py'
        source = path.read_text().split('path = f"{ROOT}/analysis/figures/interactive_dashboard.html"')[0]
        namespace = {'__file__': str(path)}
        exec(compile(source, str(path), 'exec'), namespace)
        cls.data = namespace['DATA']
        cls.metrics = namespace['M']
        cls.html = namespace['out']
        cls.means = namespace['means']
        cls.matched = namespace['matched']
        with tempfile.TemporaryDirectory() as temp:
            tree = Path(temp)
            (tree / 'tools').mkdir()
            figures = tree / 'analysis/figures'
            figures.mkdir(parents=True)
            (figures / 'interactive_dashboard.html').write_text(namespace['out'])
            exporter = tree / 'tools/export_dashboard_panels.js'
            shutil.copyfile(ROOT / 'tools/export_dashboard_panels.js', exporter)
            subprocess.run(['node', str(exporter), '--ci'], check=True, capture_output=True, text=True)
            cls.panels = {p.stem: json.loads(p.read_text()) for p in (figures / 'interactive').glob('dash_*.json')}
            exporter.write_text(exporter.read_text().replace("selmet: 'recall'", "selmet: 'F1'"))
            subprocess.run(['node', str(exporter)], check=True, capture_output=True, text=True)
            cls.f1 = json.loads((figures / 'interactive/dash_chart4.json').read_text())

    def test_quality_points_match_current_verified_metrics(self):
        for c in self.data['cells']:
            key = f"{c['model']}|{c['fw']}|{c['eff']}"
            expected = self.metrics['true_gold_defects']['verified']['cells'][key]
            self.assertTrue(c['advisory_measured'])
            self.assertAlmostEqual(c['F2p_sem'], expected['F2p'], delta=0.00001)
            self.assertEqual(c['advisory_count'], expected['advisory_count'])

    def test_matched_summary_and_policy_are_current(self):
        comparison = json.loads((ROOT / 'analysis/verified_gold/advisory_readjudication/scoring_policies/advisory070_penalty080_v1/framework_comparison.json').read_text())
        self.assertEqual(len(self.matched), comparison['matched_model_effort_combinations'])
        for fw, mean in self.means.items():
            self.assertAlmostEqual(mean, comparison['frameworks'][fw]['mean_F2p_A70'])
        self.assertIn('≥0.70', self.html)
        self.assertIn('≥0.80', self.html)
        self.assertIn('MRV in 8, CE in 3, and include zero in 10', self.html)
        self.assertNotIn('__FRAMEWORK_SUMMARY__', self.html)

    def test_selection_gap_uses_original_gold_metrics(self):
        for metric, panel in [('recall', self.panels['dash_chart4']), ('F1', self.f1)]:
            plotted = {}
            for trace in panel['traces']:
                for x, row in zip(trace['x'], trace['customdata']):
                    plotted[row['cell']] = x
            self.assertEqual(set(plotted), set(self.metrics['selection_effect']))
            for key, x in plotted.items():
                row = self.metrics['selection_effect'][key]
                self.assertAlmostEqual(x, row[metric+'_t6'] - row[metric+'_full'], delta=0.00002)

    def test_per_pr_selection_uses_original_gold_recall(self):
        selected = self.data['percell'][sorted(self.data['percell'])[0]]['prs']
        expected = {row['pr']: row['rec'] for row in selected}
        plotted = {}
        for trace in self.panels['dash_chart5']['traces'][:2]:
            plotted.update((row['pr'], value) for row, value in zip(trace['customdata'], trace['y']))
        self.assertEqual(plotted, expected)

    def test_token_export_carries_filter_metadata(self):
        for trace in self.panels['dash_chart3']['traces']:
            self.assertEqual(len(trace['x']), len(trace['customdata']))
            for row in trace['customdata']:
                self.assertIn(row['model'], {c['model'] for c in self.data['cells']})
                self.assertIn(row['fw'], {c['fw'] for c in self.data['cells']})
                self.assertEqual(row['eff'], 'low')


if __name__ == '__main__':
    unittest.main()
