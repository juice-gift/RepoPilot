"""Webhook delivery behavior for the Golden Repository."""

import hashlib
import hmac


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Authenticate a webhook using a SHA-256 HMAC signature."""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def create_delivery_key(event_id: str, destination: str) -> str:
    """Create a stable idempotency key that prevents duplicate event delivery."""
    value = f"{event_id}:{destination}".encode()
    return hashlib.sha256(value).hexdigest()
