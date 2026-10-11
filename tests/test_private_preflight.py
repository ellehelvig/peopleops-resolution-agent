import json
import tempfile
import unittest
from pathlib import Path
from evals.private_preflight import load_private_cases
from evals.dataset import CASES


class PrivatePreflightTests(unittest.TestCase):
    def check(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_text(json.dumps(rows))
            return load_private_cases(path)

    def row(self, request="Synthetic schema fixture only, never independent validation"):
        return {"id": "fixture", "category": "ambiguous", "request": request, "expected_status": "escalated"}

    def test_valid_schema_is_accepted(self):
        self.assertEqual(len(self.check([self.row()])), 1)

    def test_development_overlap_is_rejected_despite_case_or_whitespace(self):
        with self.assertRaises(ValueError):
            self.check([self.row("  " + CASES[0]["request"].upper() + "  ")])

    def test_placeholder_duplicate_and_empty_set_are_rejected(self):
        for rows in ([], [self.row("Replace with practitioner text")], [self.row(), self.row()]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.check(rows)

    def test_malformed_labels_are_rejected(self):
        for field, value in (("expected_status", "approved"), ("expected_status", []), ("acceptable_flags", ["invented"]), ("expected_intent", "execute"), ("expected_intent", {}), ("employee_id", [])):
            row = self.row(); row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check([row])
