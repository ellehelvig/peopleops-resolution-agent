"""The evaluation harness records runs separately and never overwrites an archive."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from evals import compare, summarize
from peopleops.screen import ScreenResult

ARCHIVE = Path(compare.__file__).parent / "runs" / "2026-10-01-untuned"


def digest(folder: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}


class CaseSetTests(unittest.TestCase):
    def test_boundary_set_is_included_in_pairs(self):
        sets = compare._cases()
        boundary = sets["boundary_regression"]
        self.assertEqual(len(boundary), 12)
        categories = [case[1] for case in boundary]
        self.assertEqual(categories.count("business_instruction"), 6)
        self.assertEqual(categories.count("system_manipulation"), 6)


class RunDirTests(unittest.TestCase):
    def test_refuses_a_folder_that_already_has_files(self):
        before = digest(ARCHIVE)
        argv = ["compare", "--screen", "claude-code", "--run-dir", str(ARCHIVE)]
        with mock.patch.object(sys, "argv", argv), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            compare.main()
        self.assertEqual(digest(ARCHIVE), before)

    def test_run_dir_requires_a_live_screen(self):
        with tempfile.TemporaryDirectory() as tmp:
            argv = ["compare", "--screen", "recorded", "--run-dir", str(Path(tmp) / "new")]
            with mock.patch.object(sys, "argv", argv), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                compare.main()

    def test_live_run_writes_its_own_folder_with_provenance(self):
        class Fake:
            source = "claude-code:test-model"

            def __init__(self, *args, **kwargs):
                pass

            def screen(self, request):
                return ScreenResult((), False, "unknown", self.source)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            run_dir = tmp / "runs" / "tuned-a"
            argv = ["compare", "--screen", "claude-code", "--run-dir", str(run_dir)]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(compare, "ClaudeCodeScreen", Fake), \
                    mock.patch.object(compare, "REPORT", tmp / "screen_report.json"), \
                    mock.patch.object(compare, "RECORDINGS", tmp / "screen_recordings.json"), \
                    mock.patch("builtins.print"):
                compare.main()
            recordings = json.loads((run_dir / "screen_recordings.json").read_text())
            self.assertEqual(len(recordings["screen_prompt_sha256"]), 64)
            self.assertIn("ClaudeCodeScreen", recordings["harness"])
            report = json.loads((run_dir / "screen_report.json").read_text())
            self.assertIn("boundary_regression", report["sets"])


class SummarizeTests(unittest.TestCase):
    def test_reads_the_archive_without_writing_it(self):
        before = digest(ARCHIVE)
        text = summarize.summarize([ARCHIVE])
        self.assertEqual(digest(ARCHIVE), before)
        # The untuned run had the three false injection refusals.
        self.assertIn("Q1 Previously observed false injection refusals gone: no", text)
        self.assertIn("false_refusal: 3", text)
        self.assertIn("not independent validation", text)


if __name__ == "__main__":
    unittest.main()
