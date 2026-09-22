# argon2 + JWT (access + Refresh tokens) 'crypto utilities'

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta

import argon2
import jwt

from app.core.config import settings

_password_hasher = argon2.PasswordHasher()

# func. to hash/verify passwords by using argon2 
def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, password)
    except argon2.exceptions.VerificationError:
        return False


def hash_refresh_token(raw: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


def new_refresh_token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex

# HS256, JWT, 15MIN, carries: "sub ,user ,roles, premissions"
def create_access_token(user_id: uuid.UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

# Validate Helpers
def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])