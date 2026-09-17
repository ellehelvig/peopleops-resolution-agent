#!/usr/bin/env python3
"""Optional standards-based MCP facade over four narrow PeopleOps tools.

Install requirements-optional.txt, then run `python mcp_server.py`.
The UI does not require this dependency; both surfaces call the same domain layer.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from peopleops.data import active_policies, public_employee
from peopleops.store import CaseStore

mcp = FastMCP("peopleops-resolution-tools")
store = CaseStore()


@mcp.tool()
def retrieve_policy(topic: str, region: str) -> list[dict]:
    """Return active policy records for one approved HR topic and employee region. Read-only."""
    if topic not in {"parental_leave", "remote_work", "relocation", "manager_change"}:
        return []
    return active_policies(topic, region)


@mcp.tool()
def get_employee_eligibility_fields(employee_id: str) -> dict:
    """Return an allowlisted, minimum-data HRIS view; never returns pay, medical, or demographic data. Read-only."""
    return public_employee(employee_id) or {"error": "employee_not_found"}


@mcp.tool()
def create_case(draft: dict, actor: str = "agent") -> dict:
    """Create a draft case record and audit event. Does not execute an HR action."""
    required = {"case_id", "status", "intent", "risk", "answer", "recommended_action", "approval_required", "citations", "decision_trace", "data_accessed", "safety_flags"}
    missing = required - draft.keys()
    if missing:
        return {"error": "missing_fields", "fields": sorted(missing)}
    return store.save(draft, actor)


@mcp.tool()
def record_approval(case_id: str, decision: str, reviewer: str, note: str = "") -> dict:
    """Record a named human decision. Call only after approval is received outside the agent."""
    if decision not in {"approve", "reject"}:
        return {"error": "invalid_decision"}
    try:
        return store.decide(case_id, decision, reviewer, note) or {"error": "case_not_found"}
    except ValueError as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
