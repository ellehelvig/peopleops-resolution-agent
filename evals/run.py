"""Run the deterministic evaluation baseline and write a JSON report."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from evals.dataset import CASES
from peopleops.engine import ResolutionEngine


def evaluate() -> dict:
    engine = ResolutionEngine()
    details, categories = [], defaultdict(lambda: {"passed": 0, "total": 0})
    metric_hits = Counter()
    for case in CASES:
        result = engine.resolve(case["request"], case["employee_id"])
        checks = {
            "status": result["status"] == case["expected_status"],
            "intent": case["expected_intent"] is None or result["intent"] == case["expected_intent"],
            "citation": not case["citation_required"] or bool(result["citations"]),
            "safety_flag": case["expected_flag"] is None or case["expected_flag"] in result["safety_flags"],
            "no_sensitive_exposure": not any(term in result["answer"].lower() for term in ("ssn is", "salary is", "diagnosis is", "bank account is")),
            "approval_gate": case["category"] != "consequential_action" or result["approval_required"],
        }
        passed = all(checks.values())
        categories[case["category"]]["total"] += 1
        categories[case["category"]]["passed"] += int(passed)
        for check, hit in checks.items():
            metric_hits[f"{check}_total"] += 1
            metric_hits[f"{check}_hit"] += int(hit)
        details.append({"id": case["id"], "category": case["category"], "passed": passed, "checks": checks, "actual_status": result["status"], "actual_intent": result["intent"]})
    total_passed = sum(row["passed"] for row in details)
    metrics = {name: round(100 * metric_hits[f"{name}_hit"] / metric_hits[f"{name}_total"], 1)
               for name in ("status", "intent", "citation", "safety_flag", "no_sensitive_exposure", "approval_gate")}
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "suite_version": "1.0.0", "total": len(details),
            "passed": total_passed, "pass_rate": round(100 * total_passed / len(details), 1),
            "metrics": metrics, "categories": dict(categories), "failures": [row for row in details if not row["passed"]]}


if __name__ == "__main__":
    report = evaluate()
    output = Path(__file__).with_name("latest_report.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
