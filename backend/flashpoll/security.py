import hashlib
import hmac
import secrets

from fastapi import Request

POLL_ID_BYTES = 6  # 8 URL-safe chars, 48 bits
ADMIN_TOKEN_BYTES = 24  # 32 URL-safe chars, 192 bits


def new_poll_id() -> str:
    return secrets.token_urlsafe(POLL_ID_BYTES)


def new_admin_token() -> str:
    return secrets.token_urlsafe(ADMIN_TOKEN_BYTES)


def hash_admin_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def voter_key(kind: str, poll_id: str, value: str) -> str:
    """Per-poll hashed voter identifier, so raw IPs and voter tokens are never stored."""
    digest = hashlib.sha256(f"{poll_id}:{value}".encode()).hexdigest()
    return f"{kind}#{digest}"


def client_ip(request: Request, client_ip_header: str | None) -> str:
    """The caller's IP (docs/spec.md, 4.2).

    Behind CloudFront, `client_ip_header` is `CloudFront-Viewer-Address` ("ip:port"), which
    CloudFront sets itself, so viewers can't spoof it. Locally there is no proxy and the
    socket peer is the client.
    """
    if client_ip_header:
        value = request.headers.get(client_ip_header, "").strip()
        if value:
            # "203.0.113.7:4567" or "2001:db8::1:4567" -> drop the trailing port.
            return value.rsplit(":", 1)[0] if ":" in value else value
    return request.client.host if request.client else "unknown"


def origin_verified(provided: str | None, expected: str | None) -> bool:
    """True when no origin secret is configured, or the request carries the right one."""
    if not expected:
        return True
    return provided is not None and hmac.compare_digest(provided, expected)
