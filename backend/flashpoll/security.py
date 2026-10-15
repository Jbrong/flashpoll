import hashlib
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


def client_ip(request: Request, trusted_proxy_count: int) -> str:
    """The caller's IP, trusting `trusted_proxy_count` proxy hops (docs/spec.md, 4.2)."""
    if trusted_proxy_count > 0:
        forwarded = [
            hop.strip()
            for hop in request.headers.get("x-forwarded-for", "").split(",")
            if hop.strip()
        ]
        if len(forwarded) >= trusted_proxy_count:
            return forwarded[-trusted_proxy_count]
    return request.client.host if request.client else "unknown"
