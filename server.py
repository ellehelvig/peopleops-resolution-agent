#!/usr/bin/env python3
"""Zero-dependency local API and static server."""

from __future__ import annotations

import json
import mimetypes
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from collections import defaultdict, deque
from threading import Lock
from urllib.parse import urlparse

from peopleops.data import EMPLOYEES, POLICIES
from peopleops.engine import ResolutionEngine
from peopleops.store import CaseStore

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
ENGINE = ResolutionEngine()
STORE = CaseStore()
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_REQUESTS = 60
RATE_LIMITS: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT_LOCK = Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "PeopleOpsDemo/1.0"

    def log_message(self, format: str, *args) -> None:
        return

    def _client_key(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "")
        return forwarded.split(",", 1)[0].strip() or self.client_address[0]

    def _rate_limited(self) -> bool:
        now = time.monotonic()
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        key = self._client_key()
        with RATE_LIMIT_LOCK:
            requests = RATE_LIMITS[key]
            while requests and requests[0] < cutoff:
                requests.popleft()
            if len(requests) >= RATE_LIMIT_REQUESTS:
                return True
            requests.append(now)
            return False

    def _json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Synthetic-Data", "true")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 <= length <= 16_384:
            raise ValueError("Request body length must be between 0 and 16 KB.")
        payload = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    @staticmethod
    def _text(payload: dict, field: str, default: str = "") -> str:
        value = payload.get(field, default)
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string.")
        return value.strip()

    def do_GET(self) -> None:
        if self._rate_limited():
            self._json({"error": "Too many requests. Please try again shortly."}, 429)
            return
        path = urlparse(self.path).path
        if path == "/api/bootstrap":
            self._json({
                "employees": [{"id": e["id"], "name": e["name"], "region": e["region"], "role_category": e["role_category"]} for e in EMPLOYEES.values()],
                "metrics": STORE.metrics(), "cases": STORE.list_cases(), "audit": STORE.audit[-20:],
                "policies": [{k: p[k] for k in ("id", "title", "topic", "version", "effective_date", "status", "owner")} for p in POLICIES],
            })
            return
        if path == "/api/health":
            self._json({"status": "ok", "mode": "deterministic", "synthetic_data": True})
            return
        if path == "/api/evaluation":
            report = ROOT / "evals" / "latest_report.json"
            if not report.is_file():
                self._json({"error": "No evaluation report. Run: python3 -m evals.run"}, 404)
                return
            self._json(json.loads(report.read_text()))
            return
        target = WEB / ("index.html" if path == "/" else path.lstrip("/"))
        if not target.is_file() or WEB not in target.resolve().parents:
            self.send_error(404)
            return
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self._rate_limited():
            self._json({"error": "Too many requests. Please try again shortly."}, 429)
            return
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            self._json({"error": "Content-Type must be application/json."}, 415)
            return
        path = urlparse(self.path).path
        try:
            payload = self._body()
            if path == "/api/resolve":
                request = self._text(payload, "request")
                if not request or len(request) > 4000:
                    self._json({"error": "Request must be between 1 and 4,000 characters."}, 400)
                    return
                result = ENGINE.resolve(request, self._text(payload, "employee_id"), self._text(payload, "actor_role", "employee"))
                self._json(STORE.save(result))
                return
            if path.startswith("/api/cases/") and path.endswith("/decision"):
                case_id = path.split("/")[3]
                decision = self._text(payload, "decision")
                if decision not in {"approve", "reject"}:
                    self._json({"error": "Decision must be approve or reject."}, 400)
                    return
                row = STORE.decide(case_id, decision, self._text(payload, "reviewer"), self._text(payload, "note"))
                self._json(row or {"error": "Case not found."}, 200 if row else 404)
                return
            self._json({"error": "Not found."}, 404)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": f"Invalid request: {exc}"}, 400)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    address = (host, port)
    print(f"PeopleOps Resolution Agent running at http://{address[0]}:{address[1]}")
    ThreadingHTTPServer(address, Handler).serve_forever()
