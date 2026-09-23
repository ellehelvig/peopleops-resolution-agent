"""Transport-independent request handling for the demo.

Every route the UI calls lives here, once. `server.py` wraps it in HTTP for
local use; the static demo calls the same object in the visitor's browser
through Pyodide. Neither transport adds behavior of its own beyond what only it
can do (HTTP headers and rate limits on one side, nothing on the other), so the
code the tests exercise is the code visitors run.
"""

from __future__ import annotations

import json
from typing import Any

from .data import EMPLOYEES, POLICIES
from .engine import ResolutionEngine
from .store import CaseStore

MAX_REQUEST_CHARS = 4000


class Api:
    def __init__(self, evaluation_report: dict | None = None) -> None:
        self.engine = ResolutionEngine()
        self.store = CaseStore()
        self.evaluation_report = evaluation_report

    def handle(self, method: str, path: str, body: Any = None) -> tuple[int, dict]:
        """Return (status, payload) for one API call. Never raises for bad input."""
        try:
            if method == "GET":
                return self._get(path)
            if method == "POST":
                if body is None:
                    body = {}
                if not isinstance(body, dict):
                    raise ValueError("Request body must be a JSON object.")
                return self._post(path, body)
            return 405, {"error": "Method not allowed."}
        except ValueError as exc:
            return 400, {"error": f"Invalid request: {exc}"}

    def handle_json(self, method: str, path: str, body_json: str = "") -> str:
        """JSON in, JSON out, for callers across a language boundary."""
        try:
            body = json.loads(body_json) if body_json else None
        except json.JSONDecodeError as exc:
            return json.dumps({"status": 400, "payload": {"error": f"Invalid request: {exc}"}})
        status, payload = self.handle(method, path, body)
        return json.dumps({"status": status, "payload": payload})

    def _get(self, path: str) -> tuple[int, dict]:
        if path == "/api/bootstrap":
            return 200, {
                "employees": [{"id": e["id"], "name": e["name"], "region": e["region"], "role_category": e["role_category"]} for e in EMPLOYEES.values()],
                "metrics": self.store.metrics(),
                "cases": self.store.list_cases(),
                "audit": self.store.audit[-20:],
                "policies": [{k: p[k] for k in ("id", "title", "topic", "version", "effective_date", "status", "owner")} for p in POLICIES],
            }
        if path == "/api/health":
            return 200, {"status": "ok", "mode": "deterministic", "synthetic_data": True}
        if path == "/api/evaluation":
            if self.evaluation_report is None:
                return 404, {"error": "No evaluation report. Run: python3 -m evals.run"}
            return 200, self.evaluation_report
        return 404, {"error": "Not found."}

    def _post(self, path: str, body: dict) -> tuple[int, dict]:
        if path == "/api/resolve":
            request = _text(body, "request")
            if not request or len(request) > MAX_REQUEST_CHARS:
                return 400, {"error": "Request must be between 1 and 4,000 characters."}
            employee_id = _text(body, "employee_id")
            result = self.engine.resolve(request, employee_id, _text(body, "actor_role", "employee"))
            return 200, self.store.save(result, request=request, employee_id=employee_id)
        if path.startswith("/api/cases/") and path.endswith("/decision"):
            case_id = path.split("/")[3]
            decision = _text(body, "decision")
            if decision not in {"approve", "reject"}:
                return 400, {"error": "Decision must be approve or reject."}
            row = self.store.decide(case_id, decision, _text(body, "reviewer"), _text(body, "note"))
            return (200, row) if row else (404, {"error": "Case not found."})
        return 404, {"error": "Not found."}


def _text(payload: dict, field: str, default: str = "") -> str:
    value = payload.get(field, default)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string.")
    return value.strip()
