"""Approval invariants. Only the reviewer UI and HTTP API can record a decision."""

import unittest
from concurrent.futures import ThreadPoolExecutor

from peopleops.engine import ResolutionEngine
from peopleops.store import CaseStore


class StoreTests(unittest.TestCase):
    def test_invalid_decisions_do_not_mutate_the_case(self):
        store = CaseStore()
        before = store.list_cases()
        for decision, reviewer in (("maybe", "Reviewer"), ([], "Reviewer"), ("approve", " ")):
            with self.assertRaises(ValueError):
                store.decide("CASE-2402", decision, reviewer)
        self.assertEqual(store.list_cases(), before)
        self.assertEqual(store.audit, [])

    def test_specialist_escalations_cannot_be_approved(self):
        store = CaseStore()
        with self.assertRaises(ValueError):
            store.decide("CASE-2404", "approve", "Reviewer")
        self.assertEqual(store.cases["CASE-2404"]["status"], "escalated")
        self.assertEqual(store.audit, [])

    def test_concurrent_decisions_record_only_one_outcome(self):
        store = CaseStore()

        def decide(decision):
            try:
                return store.decide("CASE-2402", decision, "Reviewer")
            except ValueError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(decide, ["approve", "reject"]))
        self.assertEqual(sum(row is not None for row in outcomes), 1)
        self.assertEqual(len(store.audit), 1)

    def test_rejection_counts_as_a_human_override(self):
        store = CaseStore()
        result = ResolutionEngine().resolve("Can I work remotely?", "E-1001")
        store.save(result)
        before = store.metrics()["human_override_rate"]
        store.decide(result["case_id"], "reject", "Demo People Partner")
        self.assertTrue(store.cases[result["case_id"]]["human_override"])
        self.assertGreater(store.metrics()["human_override_rate"], before)

    def test_returned_cases_cannot_mutate_the_store(self):
        store = CaseStore()
        rows = store.list_cases()
        rows[0]["status"] = "approved"
        self.assertEqual(store.cases[rows[0]["id"]]["status"], "escalated")
