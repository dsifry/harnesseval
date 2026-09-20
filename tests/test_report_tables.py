"""Regression checks for the report's generated Markdown evidence tables."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
import markdown
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Rows(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None
    def handle_starttag(self, tag, attrs):
        if tag=='tr': self.row=[]
        if tag in ('td','th'): self.cell=''
    def handle_data(self, data):
        if self.cell is not None: self.cell += data
    def handle_endtag(self, tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(self.cell); self.cell=None
        if tag=='tr': self.rows.append(self.row); self.row=None

class ReportTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT/'tools/final_report_tables.py')], check=True, capture_output=True)
        cls.text=Path('/tmp/final_report_tables.md').read_text()
        cls.metrics=json.loads((ROOT/'analysis/final_report_metrics.json').read_text())
    def section(self, number):
        return self.text.split(f'### T{number} —',1)[1].split('### ',1)[0]
    def test_ratio_columns_contain_numbers(self):
        p=Rows(); p.feed(markdown.markdown(self.section(7),extensions=['tables']))
        for row in p.rows[1:]:
            self.assertRegex(row[1],r'^\d',row)
    def test_true_gold_header_uses_current_universe(self):
        den=self.metrics['true_gold_defects']['verified']['derived']['coverage']['den']
        self.assertIn(f'{den}-bug',self.section(16))
    def test_true_gold_framework_summary_uses_f2_prime(self):
        pairs=self.metrics['true_gold_defects']['verified']['pairs'].values()
        positive=sum(p['dF2p'][0]>0 for p in pairs)
        resolved=sum(p['dF2p'][1]>0 for p in pairs)
        negative=sum(p['dF2p'][2]<0 for p in pairs)
        self.assertIn(f'MRV-vs-CE F2′: {positive}/{len(pairs)} pairs positive',self.section(16))
        self.assertIn(f'{resolved}/{len(pairs)} favor MRV and {negative}/{len(pairs)} favor CE at 95%',self.section(16))
    def test_true_gold_f2_column_is_f2_not_precision(self):
        p=Rows(); p.feed(markdown.markdown('\n'.join(l for l in self.section(16).splitlines() if l.startswith('|')),extensions=['tables']))
        self.assertEqual(len(p.rows),73)
        for row in p.rows[1:]:
            key='|'.join(row[0].removesuffix(' † unranked').split(' · '))
            value=self.metrics['true_gold_defects']['verified']['cells'][key]['F2p']
            self.assertTrue(row[6].startswith(f'{value:.3f} ['),row)

if __name__=='__main__': unittest.main()
