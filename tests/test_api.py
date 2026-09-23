"""The HTTP server and the in-browser demo must run the same API code."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import server
from peopleops.api import Api

ROOT = Path(__file__).resolve().parent.parent


class SharedApiTests(unittest.TestCase):
    def test_server_delegates_to_the_shared_api(self) -> None:
        self.assertIsInstance(server.API, Api)
        self.assertIsNotNone(server.API.evaluation_report, "server should load the committed evaluation report")

    def test_browser_loads_every_module_in_the_package(self) -> None:
        script = (ROOT / "web" / "in-browser-api.js").read_text()
        listed = re.search(r"var MODULES = \[([^\]]*)\]", script)
        self.assertIsNotNone(listed, "MODULES list not found in web/in-browser-api.js")
        in_browser = sorted(re.findall(r"'([^']+\.py)'", listed.group(1)))
        in_package = sorted(p.name for p in (ROOT / "peopleops").glob("*.py"))
        self.assertEqual(in_browser, in_package, "web/in-browser-api.js MODULES must match peopleops/*.py")

    def test_json_bridge_matches_direct_calls(self) -> None:
        api = Api()
        bridged = json.loads(api.handle_json("POST", "/api/resolve", json.dumps({"request": "Can I work remotely?", "employee_id": "E-1001"})))
        self.assertEqual(bridged["status"], 200)
        self.assertEqual(bridged["payload"]["intent"], "remote_work")
        self.assertEqual(bridged["payload"]["employee_id"], "E-1001")

    def test_bad_input_is_a_400_not_an_exception(self) -> None:
        api = Api()
        self.assertEqual(api.handle("POST", "/api/resolve", {"request": 42})[0], 400)
        self.assertEqual(api.handle("POST", "/api/resolve", ["not", "an", "object"])[0], 400)
        self.assertEqual(json.loads(api.handle_json("POST", "/api/resolve", "{not json"))["status"], 400)
        self.assertEqual(api.handle("DELETE", "/api/bootstrap")[0], 405)

    def test_missing_report_is_a_404(self) -> None:
        self.assertEqual(Api().handle("GET", "/api/evaluation")[0], 404)


if __name__ == "__main__":
    unittest.main()
