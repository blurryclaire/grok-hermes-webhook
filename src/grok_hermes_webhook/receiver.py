"""Minimal local webhook receiver stub (stdlib only).

Order: read raw body → verify HMAC → parse JSON → validate non-empty task → 202.
Defaults: LISTEN_HOST=127.0.0.1 LISTEN_PORT=8650
"""

from __future__ import annotations

import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from grok_hermes_webhook.hmac_verify import SignatureError, verify_signature
from grok_hermes_webhook.validate import MAX_BODY_BYTES, ValidationError, extract_task


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    data = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "grok-hermes-webhook/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep stub quiet by default; uncomment to debug locally.
        # super().log_message(fmt, *args)
        return

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.rstrip("/") != "/webhook":
            _json_response(self, 404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            _json_response(self, 400, {"error": "invalid_json", "detail": "empty body"})
            return
        if length > MAX_BODY_BYTES:
            _json_response(self, 413, {"error": "payload_too_large"})
            return

        raw = self.rfile.read(length)

        try:
            verify_signature(raw, dict(self.headers))
        except SignatureError as exc:
            _json_response(self, 401, {"error": "invalid_signature", "detail": str(exc)})
            return

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _json_response(self, 400, {"error": "invalid_json"})
            return

        try:
            task = extract_task(payload)
        except ValidationError as exc:
            _json_response(self, 400, {"error": "empty_task", "detail": str(exc)})
            return

        delivery_id = payload.get("delivery_id") if isinstance(payload, dict) else None
        if not isinstance(delivery_id, str) or not delivery_id.strip():
            delivery_id = str(uuid.uuid4())

        # ENQUEUE placeholder — v0.1 only acknowledges acceptance.
        _ = task
        _json_response(
            self,
            202,
            {
                "status": "accepted",
                "route": "grok-bot-task",
                "delivery_id": delivery_id,
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        _json_response(self, 404, {"error": "not_found"})


def main() -> None:
    host = os.environ.get("LISTEN_HOST", "127.0.0.1")
    port = int(os.environ.get("LISTEN_PORT", "8650"))
    if not os.environ.get("WEBHOOK_SECRET"):
        raise SystemExit("Set WEBHOOK_SECRET before starting the receiver stub.")
    httpd = ThreadingHTTPServer((host, port), WebhookHandler)
    print(f"listening on http://{host}:{port}/webhook")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
