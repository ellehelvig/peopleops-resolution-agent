"""Regression tests for the 60-case evaluation suite and its report."""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from evals.dataset import CASES
from evals.run import evaluate

ROOT = Path(__file__).resolve().parent.parent


class EvaluationSuiteTests(unittest.TestCase):
    def test_suite_has_sixty_cases_across_ten_categories(self) -> None:
        self.assertEqual(len(CASES), 60)
        categories = Counter(case["category"] for case in CASES)
        self.assertEqual(len(categories), 10)
        self.assertTrue(all(count == 6 for count in categories.values()), categories)

    def test_case_ids_are_unique(self) -> None:
        ids = [case["id"] for case in CASES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_deterministic_baseline_passes_every_case(self) -> None:
        report = evaluate()
        self.assertEqual(report["total"], 60)
        self.assertEqual(report["failures"], [], report["failures"])
        self.assertEqual(report["pass_rate"], 100.0)
        for metric, value in report["metrics"].items():
            self.assertEqual(value, 100.0, metric)

    def test_committed_report_matches_the_current_engine(self) -> None:
        """evals/latest_report.json is checked in as evidence. If the engine
        changes and the report is not regenerated, this test fails so the
        evidence can't silently drift from the code."""
        committed = json.loads((ROOT / "evals" / "latest_report.json").read_text())
        fresh = evaluate()
        self.assertEqual(committed["total"], fresh["total"])
        self.assertEqual(committed["passed"], fresh["passed"])
        self.assertEqual(committed["categories"], fresh["categories"])
        self.assertEqual(committed["metrics"], fresh["metrics"])
        self.assertEqual(committed["holdout"], fresh["holdout"])


    def test_holdout_is_reported_and_never_leaks_into_the_baseline(self) -> None:
        from evals.holdout import CASES as HOLDOUT
        baseline_requests = {case["request"] for case in CASES}
        self.assertFalse(baseline_requests & {case[2] for case in HOLDOUT})
        report = evaluate()["holdout"]
        self.assertEqual(report["total"], len(HOLDOUT))
        self.assertEqual(sum(report["miss_types"].values()), report["total"] - report["passed"])


if __name__ == "__main__":
    unittest.main()
