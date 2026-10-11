"""Private evaluation must not leak request text into shareable recordings."""
import json
import unittest
from unittest.mock import patch

from evals.compare import RecordingScreen, compare
from peopleops.screen import ScreenResult


class StubScreen:
    source = "synthetic-test"

    def screen(self, request):
        return ScreenResult((), True, "unknown", self.source)


class EvaluationPrivacyTests(unittest.TestCase):
    def test_private_requests_bypass_recordings_and_cache(self):
        secret = "SYNTHETIC_PRIVATE_CANARY do not persist this request"
        cases = {"private": [("PRIVATE-ID", "ambiguous", secret, "escalated", None, None, "E-1001")]}
        recorder = RecordingScreen(StubScreen())
        with patch("evals.compare._cases", return_value=cases):
            report = compare(recorder)
        self.assertEqual(recorder.recordings, {})
        self.assertEqual(recorder._cache, {})
        self.assertNotIn(secret, json.dumps(report))
        self.assertNotIn("PRIVATE-ID", json.dumps(report))
        self.assertEqual(report["sets"]["private"]["rules_plus_screen"]["total"], 1)

    def test_public_synthetic_requests_still_record(self):
        recorder = RecordingScreen(StubScreen())
        recorder.screen("public synthetic fixture")
        self.assertIn("public synthetic fixture", recorder.recordings)
