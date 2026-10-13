# Security Utilities: Password Hashing, UUID, JWT Tokens, REfresh Token Hashing

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # user_id as string
    username: str
    email[Optional]: str
    roles: list[str] = []
    permissions: list[str] = []
    exp: int  # Unix timestamp 'RFC 7519'
    iat: int  # Unix timestamp 'RFC 7519'
    type: str = "access"  # "access" or "refresh"
    family_id: Optional[str] = None  # Token family for reuse detection


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_refresh_token(token: str) -> str:
    #Hash refresh token with HMAC-SHA256 + server pepper
    
    return hmac.new(
        settings.JWT_SECRET.encode(), token.encode(), hashlib.sha256).hexdigest()

def create_access_token(
    user_id: UUID,
    username: str,
    email: Optional[str],
    roles: list[str],
    permissions: list[str],
    expires_delta: Optional[timedelta] = None,) -> str:

    #Create a short-lived JWT access token.
    # NOTE HS256 symmetric — fine while monolith. When auth splits
    # into telephony/ML services, migrate to RS256/ES256 asymmetric so
    # services verify tokens without holding the signing secret.

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = TokenPayload(
        sub=str(user_id),
        username=username,
        email=email,
        roles=roles,
        permissions=permissions,
        exp=int(expire.timestamp()),
        iat=int(now.timestamp()),
        type="access",
    )
    return jwt.encode(payload.model_dump(), settings.JWT_SECRET, algorithm=settings.JWT_AlGORITHM)


def create_refresh_token(family_id: str) -> tuple[str, str, datetime]:
    #Create refresh token ,Returns: (raw_token, token_hash, expires_at)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, token_hash, expires_at


def decode_token(token: str) -> TokenPayload:
    # Decode and validate JWT token
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_AlGORITHM])
        return TokenPayload(**payload) # 'Unpack'
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")


def verify_token_type(payload: TokenPayload, expected_type: str) -> None:
    #Verify token 
    if payload.type != expected_type:
        raise ValueError(f"Expected {expected_type} token, got {payload.type}")