"""Password hashing and signed session tokens.

Deliberately stdlib-only (pbkdf2 + HMAC): this machine cannot compile native
wheels (see README), so bcrypt/jose are out. Token format:
``base64url(json payload).hex(hmac_sha256(payload))`` signed with SECRET_KEY.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

from src.core.config import settings

_PBKDF2_ITERATIONS = 200_000
TOKEN_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _scheme, iterations, salt, expected = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def _sign(payload_b64: bytes) -> str:
    return hmac.new(settings.secret_key.encode("utf-8"), payload_b64, hashlib.sha256).hexdigest()


def create_token(user_id: int, role: str) -> str:
    payload = {"uid": user_id, "role": role, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8"))
    return f"{payload_b64.decode('ascii')}.{_sign(payload_b64)}"


def decode_token(token: str) -> dict | None:
    """Return the payload if the signature is valid and not expired, else None."""
    try:
        payload_b64, signature = token.rsplit(".", 1)
        if not hmac.compare_digest(_sign(payload_b64.encode("ascii")), signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except (ValueError, TypeError):
        return None
