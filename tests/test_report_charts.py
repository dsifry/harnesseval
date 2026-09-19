"""Regression checks for plot limits using the report's actual plotted CI endpoints."""
import importlib.util
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ReportChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('charts', ROOT / 'tools/report_interactive_charts.py')
        cls.charts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.charts)

    def figure(self, method):
        figures = []
        with patch.object(self.charts, 'save', side_effect=lambda fig, *args: figures.append(fig)):
            getattr(self.charts, method)()
        return figures[0]

    def test_f2_reference_is_horizontal(self):
        fig = self.figure('chart_true_gold_pareto')
        ref = fig.layout.shapes[0]
        self.assertEqual(ref.y0, ref.y1)
        self.assertEqual(ref.y0, self.charts.HEAD['vanilla']['best_f2p']['F2p'])

    def test_scored_chart_hover_preserves_processed_finding_status(self):
        fig = self.figure('chart_true_gold_pareto')
        statuses = [row[4] for trace in fig.data if trace.customdata is not None
                    for row in trace.customdata if len(row) == 5]
        self.assertTrue(statuses)
        for status in statuses:
            self.assertNotIn('unresolved classifications', status)
            self.assertIn('classified findings below scoring threshold:', status)

    def test_interactive_limits_include_all_ci_endpoints(self):
        for method in ('chart_true_gold_pareto', 'chart_pareto_frontier'):
            fig = self.figure(method)
            for trace in fig.data:
                axis = fig.layout['yaxis' + (trace.yaxis or 'y')[1:]]
                errors = trace.error_y.array or [0] * len(trace.y)
                self.assertGreater(axis.range[1], max(y + e for y, e in zip(trace.y, errors)))

    def test_static_quality_limits_include_ci_endpoints(self):
        from matplotlib.figure import Figure
        checked = []
        def inspect(fig, path, *args, **kwargs):
            if Path(path).stem not in ('fig_pareto_frontier', 'fig_effort_ladder', 'fig_efficiency_2x2', 'fig_true_gold_pareto', 'fig_true_gold_efficiency'):
                return
            for ax in fig.axes:
                if ax.get_ylabel().startswith(('F2', 'recall')):
                    checked.append(ax)
                    self.assertGreater(ax.get_ylim()[1], ax.dataLim.ymax, str(path))
        with patch.object(Figure, 'savefig', inspect):
            runpy.run_path(str(ROOT / 'tools/final_report_figures.py'))
            path = ROOT / 'tools/final_report_figures_true_gold.py'
            source = path.read_text().split('# ---- markdown headline block')[0]
            exec(compile(source, str(path), 'exec'), {'__file__': str(path)})
        self.assertTrue(checked)


if __name__ == '__main__':
    unittest.main()
