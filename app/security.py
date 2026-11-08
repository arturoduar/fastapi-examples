"""Password hashing (stdlib PBKDF2) and JWT access tokens (PyJWT)."""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from jwt import PyJWTError

ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    pass


def hash_password(password: str, iterations: int = 200_000) -> str:
    """Return ``pbkdf2_sha256$<iterations>$<salt>$<hash>`` (salt and hash base64)."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt, digest = stored.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(candidate, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def create_access_token(username: str, secret_key: str, minutes: int = 30,
                        now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    claims = {"sub": username, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(claims, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> str:
    """Return the username in a valid, unexpired token or raise InvalidTokenError."""
    try:
        claims = jwt.decode(token, secret_key, algorithms=[ALGORITHM],
                            options={"require": ["sub", "exp"]})
    except PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    return claims["sub"]
