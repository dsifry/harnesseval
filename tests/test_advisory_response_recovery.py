import json
import unittest

from tools.advisory_response_recovery import repair_invalid_string_escapes


class RecoveryTests(unittest.TestCase):
    def test_regex_escape_preserves_literal_backslash(self):
        raw = r'{"category":"bug","reasoning":"regex ^https?\:\/\// and \A","confidence":0.7}'
        repaired, edits = repair_invalid_string_escapes(raw)
        self.assertEqual(json.loads(repaired), {
            'category': 'bug', 'reasoning': r'regex ^https?\:/// and \A',
            'confidence': 0.7})
        self.assertEqual(len(edits), 2)

    def test_valid_escapes_and_escaped_backslashes_unchanged(self):
        raw = json.dumps({'text': 'quoted " slash \\A newline\n unicode ☃'})
        self.assertEqual(repair_invalid_string_escapes(raw), (raw, []))

    def test_structure_and_unicode_errors_are_not_repaired(self):
        for raw in [r'{"x":"\uZZZZ"}', '{"x":1,}', '{"x":"unterminated', r'{\x:1}']:
            repaired, _ = repair_invalid_string_escapes(raw)
            with self.assertRaises(json.JSONDecodeError):
                json.loads(repaired)

    def test_case_and_fields_are_not_changed(self):
        raw = r'{"category":"hallucination","reasoning":"Foo\Qfoo","confidence":0.55}'
        repaired, edits = repair_invalid_string_escapes(raw)
        value = json.loads(repaired)
        self.assertEqual(value['confidence'], 0.55)
        self.assertEqual(value['category'], 'hallucination')
        self.assertEqual(value['reasoning'], r'Foo\Qfoo')
        self.assertEqual(edits[0]['escape'], r'\Q')


if __name__ == '__main__':
    unittest.main()
