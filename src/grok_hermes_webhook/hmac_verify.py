"""HMAC-SHA256 verification over the raw request body (fail closed)."""

from __future__ import annotations

import hashlib
import hmac
import os


class SignatureError(ValueError):
    """Missing or invalid webhook signature."""


SIGNATURE_HEADERS = (
    "X-Webhook-Signature",
    "X-Hub-Signature-256",
)


def _normalize_signature(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("sha256="):
        value = value.split("=", 1)[1].strip()
    return value.lower()


def verify_signature(
    raw_body: bytes,
    headers: dict[str, str],
    *,
    secret: str | None = None,
) -> None:
    """Verify HMAC-SHA256(raw_body) against a signature header.

    Looks up WEBHOOK_SECRET from the environment when ``secret`` is omitted.
    Raises SignatureError on any failure (fail closed).
    """
    secret = secret if secret is not None else os.environ.get("WEBHOOK_SECRET", "")
    if not secret:
        raise SignatureError("WEBHOOK_SECRET is not set")

    provided = None
    # Header lookup is case-insensitive
    lower_map = {k.lower(): v for k, v in headers.items()}
    for name in SIGNATURE_HEADERS:
        hit = lower_map.get(name.lower())
        if hit:
            provided = hit
            break

    if not provided:
        raise SignatureError("missing signature header")

    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    got = _normalize_signature(provided)
    if not hmac.compare_digest(expected, got):
        raise SignatureError("invalid signature")
