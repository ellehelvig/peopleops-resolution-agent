"""Validate a private set locally without logging its text or sending model calls.

Passing this check does not establish practitioner authorship or independence.
"""
import argparse
import hashlib
import json
from pathlib import Path

from evals import boundary_regression, challenge_v2, dataset, holdout
from peopleops.screen import SIGNALS, INTENTS


def normalized(text):
    return " ".join(text.casefold().split())


def load_private_cases(path):
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list) or not rows:
        raise ValueError("Private set must be a nonempty array")
    development = {normalized(r["request"]) for r in dataset.CASES}
    development.update(normalized(r[2]) for cases in (holdout.CASES, challenge_v2.CASES, boundary_regression.CASES) for r in cases)
    ids, requests = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each private case must be an object")
        for field in ("id", "category", "request"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError("Private case has a missing or invalid text field")
        request = normalized(row["request"])
        if row["id"] in ids or request in requests or request in development:
            raise ValueError("Duplicate or development-contaminated private case")
        if "replace with" in request or len(row["request"]) > 4000:
            raise ValueError("Placeholder or oversized private request")
        if not isinstance(row.get("expected_status"), str) or row["expected_status"] not in {"escalated", "refused", "waiting_approval", "needs_clarification"}:
            raise ValueError("Invalid expected status")
        if row.get("expected_intent") is not None and (not isinstance(row["expected_intent"], str) or row["expected_intent"] not in INTENTS):
            raise ValueError("Invalid expected intent")
        flags = row.get("acceptable_flags")
        if flags is not None and (not isinstance(flags, list) or not flags or any(not isinstance(f, str) or f not in SIGNALS for f in flags)):
            raise ValueError("Invalid expected routing flags")
        if not isinstance(row.get("employee_id", "E-1001"), str) or row.get("employee_id", "E-1001") not in {"E-1001", "E-1002", "E-1003", "E-1004", "E-1005", "E-9999"}:
            raise ValueError("Use synthetic employee identifiers only")
        ids.add(row["id"])
        requests.add(request)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        rows = load_private_cases(args.path)
    except (ValueError, OSError):
        parser.exit(1, "Private set rejected; inspect schema, duplicates and development overlap locally.\n")
    print(json.dumps({"cases": len(rows), "sha256": hashlib.sha256(args.path.read_bytes()).hexdigest(),
                      "schema_preflight": "passed", "independent_validation": "NOT ESTABLISHED"}))


if __name__ == "__main__":
    main()
