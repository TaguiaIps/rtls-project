from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from rtls_api.config import Settings
from rtls_api.models import User

PASSWORD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class TokenError(ValueError):
    pass


def hash_password(password: str) -> str:
    return PASSWORD_CONTEXT.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return PASSWORD_CONTEXT.verify(password, password_hash)


def issue_access_token(settings: Settings, user: User) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def issue_refresh_token(settings: Settings, user: User, session_id: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=settings.refresh_token_ttl_days)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "sid": session_id,
        "jti": str(uuid4()),
        "typ": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str, settings: Settings, *, expected_type: str) -> dict[str, object]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as error:
        raise TokenError("Invalid token") from error

    token_type = payload.get("typ")
    if token_type != expected_type:
        raise TokenError("Unexpected token type")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
