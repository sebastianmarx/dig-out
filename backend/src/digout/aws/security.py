"""Platform password hashing and the signed gate cookie (checked by the CloudFront function)."""

import base64
import hashlib
import hmac
import secrets
import time

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
GATE_COOKIE = "__Host-gate"
GATE_MAX_AGE = 30 * 24 * 3600


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt, digest = encoded.split("$")
        if scheme != "scrypt":
            return False
        candidate = hashlib.scrypt(password.encode(), salt=_unb64(salt), n=int(n), r=int(r), p=int(p), dklen=32)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, _unb64(digest))


def sign_gate_cookie(key: str, now: float | None = None) -> str:
    """Cookie value '<expiry>.<hex hmac-sha256(key, expiry)>' – same format the CloudFront function verifies."""
    expiry = str(int(now if now is not None else time.time()) + GATE_MAX_AGE)
    signature = hmac.new(key.encode(), expiry.encode(), hashlib.sha256).hexdigest()
    return f"{expiry}.{signature}"


def verify_gate_cookie(key: str, value: str, now: float | None = None) -> bool:
    expiry, _, signature = value.partition(".")
    if not expiry.isdigit() or int(expiry) <= (now if now is not None else time.time()):
        return False
    expected = hmac.new(key.encode(), expiry.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def gate_set_cookie(value: str) -> str:
    return f"{GATE_COOKIE}={value}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age={GATE_MAX_AGE}"
