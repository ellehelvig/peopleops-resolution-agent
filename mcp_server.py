#!/usr/bin/env python3
"""Optional MCP facade over three narrow PeopleOps tools.

Install requirements-optional.txt, then run `python mcp_server.py`.
The UI does not require this dependency; both surfaces call the same domain layer.

There is deliberately no approval tool. Anything exposed here can be called by
the model on the other end of the connection, so a tool that records a human
decision would let the model approve its own recommendation. Approvals are
recorded only through the reviewer UI and HTTP API.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from peopleops.api import MAX_REQUEST_CHARS
from peopleops.data import active_policies, public_employee
from peopleops.engine import ResolutionEngine
from peopleops.store import CaseStore

mcp = FastMCP("peopleops-resolution-tools")
store = CaseStore()
engine = ResolutionEngine()


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
def create_case(request: str, employee_id: str) -> dict:
    """Run the deterministic workflow on an employee request and record the resulting case.

    The model supplies only the request text and employee ID. Status, risk,
    citations, and whether approval is required are all set by the engine, so a
    model cannot create a case that is already approved or skips the approval gate.
    Does not execute an HR action.
    """
    if not isinstance(request, str) or not request.strip() or len(request) > MAX_REQUEST_CHARS:
        return {"error": f"request must be 1 to {MAX_REQUEST_CHARS} characters"}
    result = engine.resolve(request, employee_id)
    return store.save(result, "mcp_client", request=request, employee_id=employee_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
