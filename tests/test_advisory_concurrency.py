import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,AsyncMock
import importlib.util


class ConcurrencyTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('tools.advisory_concurrency'))
        from tools import advisory_concurrency
        return advisory_concurrency

    def test_only_concurrency_changes_from_frozen_settings(self):
        m=self.module()
        raw={'model':'glm-5.3-background','grouping_model':'glm-5.3-background','effort':'low'}
        config=m.configuration(Path('/base'),raw,6)
        self.assertEqual(config.concurrency,6)
        self.assertEqual((config.judge,config.group_judge,config.effort),('glm-5.3-background','glm-5.3-background','low'))
        self.assertFalse(config.dry_run)
        with self.assertRaises(ValueError):m.configuration(Path('/base'),raw,16)

    def test_baseline_uses_only_selected_phase_and_exposes_retries(self):
        m=self.module()
        rows=[{'phase':'final','completed':100+i,'elapsed_s':10,'pairs':20,'status':'complete'} for i in range(30)]
        rows.append({'phase':'splitting','completed':125,'elapsed_s':2,'pairs':3,'status':'complete'})
        rows.append({'phase':'final','completed':120,'elapsed_s':7,'pairs':20,'status':'error'})
        result=m.summarize_window(rows,100,130)
        self.assertEqual(result['completed_batches'],30)
        self.assertEqual(result['completed_pairs'],600)
        self.assertEqual(result['failed_attempts'],1)
        self.assertEqual(result['median_success_elapsed_s'],10)
        self.assertEqual(result['pairs_per_minute'],1200)

    def test_runtime_respects_stop_and_does_not_regroup(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);(base/'STOP').write_text('drain')
            with self.assertRaises(ValueError):m.run(base,{'model':'glm','grouping_model':'glm','effort':'low'},6,lambda:None)

    def test_verify_rejects_changed_frozen_proposal(self):
        m=self.module();import json,hashlib
        from tools import readjudicate_report_advisories as r
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);raw={'model':'glm-5.3-background','grouping_model':'glm-5.3-background','effort':'low'}
            r.write_json(base/'manifest.json',raw);proposal=base/'proposal.json';proposal.write_text('original')
            source='generated source';prior={'source_sha256':{},'frozen_recovery_files':{},'generated_grouping_sha256':hashlib.sha256(source.encode()).hexdigest()}
            path=base/'execution_extensions/deterministic_grouping_v1/manifest.json';r.write_json(path,prior)
            manifest={'raw_pass_digest':r.digest(raw),'concurrency':6,'deterministic_extension_manifest_sha256':m.sha(path),'source_sha256':{},'frozen_files':{'proposal.json':m.sha(proposal)}}
            with patch.object(m.resume,'build_resume_grouping',return_value=(lambda:None,source)):
                m.verify(base,manifest)
                proposal.write_text('changed')
                with self.assertRaises(ValueError):m.verify(base,manifest)

    def test_execution_passes_six_without_changing_model_or_group_function(self):
        m=self.module();seen=[]
        async def sequential(config):seen.append(config)
        function=lambda:None
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.runner,'sequential_main',sequential),patch.object(m.runner,'reuse_grouping'):
            m.run(Path(tmp),{'model':'glm-5.3-background','grouping_model':'glm-5.3-background','effort':'low'},6,function)
            self.assertIs(m.runner.reuse_grouping,function)
        self.assertEqual(seen[0].concurrency,6);self.assertEqual(seen[0].effort,'low')
