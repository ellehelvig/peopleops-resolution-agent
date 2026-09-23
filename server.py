#!/usr/bin/env python3
"""Zero-dependency local HTTP server: static files plus the API in peopleops/api.py."""

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

from peopleops.api import Api

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
REPORT = ROOT / "evals" / "latest_report.json"
API = Api(json.loads(REPORT.read_text()) if REPORT.is_file() else None)
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

    def do_GET(self) -> None:
        if self._rate_limited():
            self._json({"error": "Too many requests. Please try again shortly."}, 429)
            return
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            status, payload = API.handle("GET", path)
            self._json(payload, status)
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
        try:
            declared_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json({"error": "Invalid Content-Length."}, 400)
            return
        if declared_length < 0 or declared_length > 16_384:
            self._json({"error": "Request body length must be between 0 and 16 KB."}, 400)
            return
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            self._json({"error": "Content-Type must be application/json."}, 415)
            return
        path = urlparse(self.path).path
        try:
            payload = self._body()
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": f"Invalid request: {exc}"}, 400)
            return
        status, body = API.handle("POST", path, payload)
        self._json(body, status)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    address = (host, port)
    print(f"PeopleOps Resolution Agent running at http://{address[0]}:{address[1]}")
    ThreadingHTTPServer(address, Handler).serve_forever()
