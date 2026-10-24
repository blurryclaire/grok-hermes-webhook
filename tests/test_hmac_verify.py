import hashlib
import hmac

import pytest

from grok_hermes_webhook.hmac_verify import SignatureError, verify_signature

SECRET = "test-secret-not-for-production"
BODY = b'{"task":"ping"}'


def _sig(body: bytes = BODY, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_ok_x_webhook_signature():
    verify_signature(BODY, {"X-Webhook-Signature": _sig()}, secret=SECRET)


def test_ok_sha256_prefix():
    verify_signature(BODY, {"X-Hub-Signature-256": f"sha256={_sig()}"}, secret=SECRET)


def test_missing_header():
    with pytest.raises(SignatureError, match="missing"):
        verify_signature(BODY, {}, secret=SECRET)


def test_bad_signature():
    with pytest.raises(SignatureError, match="invalid"):
        verify_signature(BODY, {"X-Webhook-Signature": "deadbeef"}, secret=SECRET)


def test_missing_secret():
    with pytest.raises(SignatureError, match="WEBHOOK_SECRET"):
        verify_signature(BODY, {"X-Webhook-Signature": _sig()}, secret="")
