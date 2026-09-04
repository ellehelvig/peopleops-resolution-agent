"""HTTP contract tests for the zero-dependency API and static server."""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import server as server_module


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _get(self, path: str):
        with urllib.request.urlopen(self.base + path, timeout=5) as resp:
            return resp.status, dict(resp.headers), resp.read()

    def _post(self, path: str, payload: dict):
        data = json.dumps(payload).encode()
        req = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_health(self) -> None:
        status, headers, body = self._get("/api/health")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["synthetic_data"])
        self.assertEqual(headers.get("X-Synthetic-Data"), "true")

    def test_bootstrap_exposes_only_minimum_employee_fields(self) -> None:
        status, _, body = self._get("/api/bootstrap")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(set(payload["employees"][0].keys()), {"id", "name", "region", "role_category"})
        self.assertIn("metrics", payload)
        self.assertIn("policies", payload)

    def test_static_index_is_served_with_csp(self) -> None:
        status, headers, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Content-Security-Policy", headers)
        self.assertIn(b"<html", body.lower())

    def test_path_traversal_is_blocked(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/../server.py")
        self.assertEqual(ctx.exception.code, 404)

    def test_resolve_then_approve_round_trip(self) -> None:
        status, case = self._post("/api/resolve", {"request": "What parental leave am I eligible for?", "employee_id": "E-1001"})
        self.assertEqual(status, 200)
        self.assertEqual(case["status"], "waiting_approval")
        self.assertIn("created_at", case)

        status, decided = self._post(f"/api/cases/{case['case_id']}/decision", {"decision": "approve", "reviewer": "Test Partner", "note": "ok"})
        self.assertEqual(status, 200)
        self.assertEqual(decided["status"], "approved")
        self.assertEqual(decided["reviewer"], "Test Partner")

    def test_resolve_validates_input(self) -> None:
        status, payload = self._post("/api/resolve", {"request": "", "employee_id": "E-1001"})
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

        status, payload = self._post("/api/resolve", {"request": "x" * 4001, "employee_id": "E-1001"})
        self.assertEqual(status, 400)

    def test_decision_validates_value_and_case(self) -> None:
        status, payload = self._post("/api/cases/CASE-2402/decision", {"decision": "maybe"})
        self.assertEqual(status, 400)
        status, payload = self._post("/api/cases/CASE-NOPE/decision", {"decision": "approve"})
        self.assertEqual(status, 404)

    def test_unknown_post_route_is_404(self) -> None:
        status, _ = self._post("/api/nothing", {})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
