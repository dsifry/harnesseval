import unittest
from tools import pilot_report_advisories as pilot

class PilotTests(unittest.TestCase):
    def test_partition_comparison_ignores_arbitrary_group_numbers(self):
        self.assertEqual(pilot.partition({'0':2,'1':2,'2':1}),pilot.partition({'0':0,'1':0,'2':2}))
        self.assertNotEqual(pilot.partition({'0':0,'1':0}),pilot.partition({'0':0,'1':1}))
    def test_confidence_gate_applies_to_penalty_and_positive(self):
        for verdict in ['bug','important_non_bug','hallucination']:
            self.assertEqual(pilot.effective({'verdict':verdict,'confidence':.79}),'unresolved')
            self.assertEqual(pilot.effective({'verdict':verdict,'confidence':.8}),verdict)

    def test_model_override_preserves_frozen_requests_and_low_thinking(self):
        import json,tempfile
        from pathlib import Path
        template=pilot.BASE/'pilots/deepseek_flash_low_v1/manifest.json'
        with tempfile.TemporaryDirectory() as tmp:
            manifest,_=pilot.prepare(Path(tmp),'glm-5.3-flash-background',template)
        original=json.loads(template.read_text())
        self.assertEqual(manifest['model'],'glm-5.3-flash-background')
        self.assertEqual(manifest['requests'],original['requests'])
        self.assertEqual(manifest['classifier_prompt'],original['classifier_prompt'])
        self.assertEqual(manifest['effort'],'low')

    def test_explicit_high_effort_preserves_inputs_and_maps_to_wire_high(self):
        import json,tempfile
        from pathlib import Path
        template=pilot.BASE/'pilots/deepseek_flash_low_v1/manifest.json'
        with tempfile.TemporaryDirectory() as tmp:
            manifest,_=pilot.prepare(Path(tmp),'deepseek-4.1-flash-background',template,effort='xhigh')
        prior=json.loads(template.read_text())
        self.assertEqual(manifest['requests'],prior['requests'])
        self.assertEqual(manifest['effort'],'xhigh')
        self.assertEqual(manifest['wire_effort_kwargs'],{'reasoning_effort':'high'})
