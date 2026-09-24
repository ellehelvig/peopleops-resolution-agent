"""Guards on what the optional MCP facade exposes to a model.

These read mcp_server.py as source instead of importing it, so they run
without the optional `mcp` dependency, the same as CI.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parent.parent / "mcp_server.py").read_text()


def _tools() -> dict[str, ast.FunctionDef]:
    tools = {}
    for node in ast.parse(SOURCE).body:
        if isinstance(node, ast.FunctionDef) and any(
            isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "tool" for d in node.decorator_list
        ):
            tools[node.name] = node
    return tools


class McpSurfaceTests(unittest.TestCase):
    def test_exposes_exactly_three_tools(self) -> None:
        self.assertEqual(set(_tools()), {"retrieve_policy", "get_employee_eligibility_fields", "create_case"})

    def test_no_tool_can_record_a_human_decision(self) -> None:
        # A model connected over MCP must not be able to approve its own recommendation.
        for name, node in _tools().items():
            body = ast.unparse(node)
            self.assertNotIn("decide(", body, name)
            self.assertNotIn("reviewer", [a.arg for a in node.args.args], name)

    def test_create_case_takes_request_text_not_decision_fields(self) -> None:
        # Status, risk, and approval_required come from the engine, never from the caller.
        args = [a.arg for a in _tools()["create_case"].args.args]
        self.assertEqual(args, ["request", "employee_id"])
        self.assertIn("engine.resolve(", ast.unparse(_tools()["create_case"]))


if __name__ == "__main__":
    unittest.main()
