"""In-memory case and audit store for the local portfolio demo."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock

from .data import SEED_CASES

MAX_CASES = 250
MAX_AUDIT_ENTRIES = 500


class CaseStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.cases = {case["id"]: deepcopy(case) for case in SEED_CASES}
        self.audit: list[dict] = []

    def save(self, result: dict, actor: str = "employee", request: str = "", employee_id: str = "") -> dict:
        with self._lock:
            row = deepcopy(result)
            # The ledger shows who asked and what they asked, as the seeded cases do.
            # The engine result carries neither, so a live case listed as "employee n/a".
            if request:
                row["request"] = request
            if employee_id:
                row["employee_id"] = employee_id
            row["created_at"] = datetime.now(timezone.utc).isoformat()
            self.cases[row["case_id"]] = row
            while len(self.cases) > MAX_CASES:
                oldest_id = next(iter(self.cases))
                del self.cases[oldest_id]
            self._log(row["case_id"], actor, "resolution_created", {"status": row["status"], "sources": [c["policy_id"] for c in row["citations"]]})
            return deepcopy(row)

    def decide(self, case_id: str, decision: str, reviewer: str, note: str = "") -> dict | None:
        if not isinstance(decision, str) or decision not in {"approve", "reject"}:
            raise ValueError("Decision must be approve or reject.")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("A named reviewer is required.")
        if not isinstance(note, str):
            raise ValueError("Reviewer note must be a string.")
        with self._lock:
            case = self.cases.get(case_id)
            if not case:
                return None
            if case.get("status") != "waiting_approval":
                raise ValueError("Only cases waiting for approval can be decided.")
            case["status"] = "approved" if decision == "approve" else "rejected"
            case["reviewer"] = reviewer.strip()
            case["review_note"] = note
            case["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            self._log(case_id, reviewer, f"human_{case['status']}", {"note": note})
            return deepcopy(case)

    def metrics(self) -> dict:
        rows = self.list_cases()
        resolved = [r for r in rows if r.get("status") in {"resolved", "approved"}]
        approvals = [r for r in rows if r.get("approval_required") or r.get("status") in {"waiting_approval", "approved", "rejected"}]
        return {
            "total_cases": len(rows),
            "completion_rate": round(100 * len(resolved) / len(rows), 1) if rows else 0,
            "escalation_rate": round(100 * sum(r.get("status") == "escalated" for r in rows) / len(rows), 1) if rows else 0,
            "estimated_hours_saved": round(len(rows) * 14 / 60, 1),
            "human_override_rate": round(100 * sum(bool(r.get("human_override")) for r in rows) / len(rows), 1) if rows else 0,
            "pending_approvals": sum(r.get("status") == "waiting_approval" for r in rows),
            "approval_cases": len(approvals),
        }

    def list_cases(self) -> list[dict]:
        with self._lock:
            return [deepcopy(row) for row in reversed(list(self.cases.values()))]

    def _log(self, case_id: str, actor: str, event: str, details: dict) -> None:
        self.audit.append({"timestamp": datetime.now(timezone.utc).isoformat(), "case_id": case_id, "actor": actor, "event": event, "details": details})
        if len(self.audit) > MAX_AUDIT_ENTRIES:
            del self.audit[:-MAX_AUDIT_ENTRIES]
