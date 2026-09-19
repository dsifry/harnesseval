import copy
import unittest

from tools.advisory_pair_recovery import schema_recovery_request


class PairRecoveryTests(unittest.TestCase):
    def test_request_preserves_all_original_inputs_and_settings(self):
        original = {'url': 'https://example.test/repo/pull/1', 'model': 'glm-5.3-background',
                    'system': 'system', 'prompt': 'FULL MATERIAL CLAIMS A and B',
                    'effort': 'low', 'pairs': [[1, 7]]}
        before = copy.deepcopy(original)
        recovered = schema_recovery_request(original)
        self.assertEqual(original, before)
        self.assertTrue(recovered['prompt'].startswith(original['prompt']))
        self.assertEqual({k: v for k, v in recovered.items() if k != 'prompt'},
                         {k: v for k, v in original.items() if k != 'prompt'})

    def test_missing_claim_details_are_explicitly_not_invented(self):
        prompt = schema_recovery_request({'prompt': 'original'})['prompt']
        self.assertIn('not stated', prompt)
        self.assertIn('Do not infer or invent', prompt)
        self.assertIn('equivalence rules above remain unchanged', prompt)
        self.assertIn('non-empty strings', prompt)


if __name__ == '__main__':
    unittest.main()
