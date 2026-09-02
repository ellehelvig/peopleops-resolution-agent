"""In-memory case and audit store for the local portfolio demo."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock

from .data import SEED_CASES


class CaseStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.cases = {case["id"]: deepcopy(case) for case in SEED_CASES}
        self.audit: list[dict] = []

    def save(self, result: dict, actor: str = "employee") -> dict:
        with self._lock:
            row = deepcopy(result)
            row["created_at"] = datetime.now(timezone.utc).isoformat()
            self.cases[row["case_id"]] = row
            self._log(row["case_id"], actor, "resolution_created", {"status": row["status"], "sources": [c["policy_id"] for c in row["citations"]]})
            return deepcopy(row)

    def decide(self, case_id: str, decision: str, reviewer: str, note: str = "") -> dict | None:
        with self._lock:
            case = self.cases.get(case_id)
            if not case:
                return None
            case["status"] = "approved" if decision == "approve" else "rejected"
            case["reviewer"] = reviewer
            case["review_note"] = note
            case["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            self._log(case_id, reviewer, f"human_{case['status']}", {"note": note})
            return deepcopy(case)

    def metrics(self) -> dict:
        rows = list(self.cases.values())
        resolved = [r for r in rows if r.get("status") in {"resolved", "approved"}]
        approvals = [r for r in rows if r.get("approval_required") or r.get("status") in {"waiting_approval", "approved", "rejected"}]
        return {
            "total_cases": len(rows),
            "completion_rate": round(100 * len(resolved) / len(rows), 1) if rows else 0,
            "escalation_rate": round(100 * sum(r.get("status") == "escalated" for r in rows) / len(rows), 1) if rows else 0,
            "median_minutes": 7.0,
            "estimated_hours_saved": round(len(rows) * 14 / 60, 1),
            "human_override_rate": round(100 * sum(bool(r.get("human_override")) for r in rows) / len(rows), 1) if rows else 0,
            "pending_approvals": sum(r.get("status") == "waiting_approval" for r in rows),
            "approval_cases": len(approvals),
        }

    def list_cases(self) -> list[dict]:
        return [deepcopy(row) for row in reversed(list(self.cases.values()))]

    def _log(self, case_id: str, actor: str, event: str, details: dict) -> None:
        self.audit.append({"timestamp": datetime.now(timezone.utc).isoformat(), "case_id": case_id, "actor": actor, "event": event, "details": details})
