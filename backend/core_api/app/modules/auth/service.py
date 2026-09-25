# Business Logic. Security Guard. ## Important Fileeeeee ##
# Verify Passwords, iussues
# Login Flow, Rotation, Reuse Detection

import secrets 
import time 
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.event import attr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.base import ATTR_EMPTY

from app.core.config import settings
from app.core import exceptions
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_token_type,
)
from app.modules.auth import models
from app.modules.auth import models_audit
from backend.core_api.app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse



        ### Business Logic for Auth & Authoirze ###
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)
        self._login_attempts: dict[str, List[float]] = defaultdict[str, list[float]](list)
        #DEV ONLY -- Replace it with Redis in FUTURE
        self._rate_limit_window_seconds: int = settings.RATE_LIMIT_WINDOW_SECONDS
        self._max_login_attempts: int = settings.RATE_LIMIT_LOGIN_ATTEMPTS

    async def _check_rate_limit(self, ip: Optional[str]) -> None:
        # Check if IP_Address exceeded login attempts
        if not ip:
            return
        now = time.time()
        attempts = self._login_attempts.get(ip, [])
        cutoff = now - self._rate_limit_window_seconds
        self._login_attempts[ip] = [t for t in attempts if t > cutoff]

        if len(self._login_attempts[ip]) >= self._max_login_attempts:
            raise exceptions.AuthenticationError(f"Too many login attempts. Try again in {self._rate_limit_window_seconds // 60} minutes.")

    async def _record_login_attempts(self, ip: Optional[str], success: bool) -> None:
        if not ip:
            return
        now = time.time()
        if success:
            self._login_attempts[ip] = []
        else:
            self._login_attempts[ip].append(now)

    async def _log_auth_event(
        self,
        event_type: str,
        user_id: Optional[UUID],
        username: Optional[str] = None,
        email: Optional[str] = None,
        ip: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        log = models_audit.AuditLog(
            event_type = event_type,
            user_id = user_id,
            username = username,
            email = email,
            ip_address = ip,
            details = details,
        )
        self.db.add(log)
        # Flush deferred to session commit / rollback — does not block auth logic
    
    async def authenticate(self, username: str, password: str, ip: Optional[str] = None) -> models.User:
            # No tenant context at login (username-only): repo resolves a single
        # match; ambiguous username across tenants -> None -> invalid creds

        user = await self.repo.get_user_by_username(username)
        if not user:
            await self._record_login_attempt(ip, success=False)
            await self._log_auth_event(
                "login_failed", None, username=username, ip=ip, details="User not found"
            )
            await self.db.commit()
            raise exceptions.AuthenticationError("Invalid credentials")

        if not user.is_active:
            await self._log_auth_event(
                "login_failed", user.id, username=username, ip=ip, details="Account disabled"
            )
            await self.db.commit()
            raise exceptions.AccountDisabledError()

        if not verify_password(password, user.hashed_password):
            await self._record_login_attempt(ip, success=False)
            await self._log_auth_event(
                "login_failed", user.id, username=username, ip=ip, details="Invalid password"
            )
            await self.db.commit()
            raise exceptions.AuthenticationError("Invalid credentials")

        await self._record_login_attempt(ip, success=True)
        return user

    async def login(self, request: LoginRequest, ip: Optional[str] = None) -> TokenResponse:
        user = await self.authenticate(request.username, request.password, ip)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        # Create token family (Fix 2)
        family_id = secrets.token_hex(16)

        # Get roles and permissions
        roles, permissions = await self.repo.get_user_roles_and_permissions(user.id)
        role_names = [r.name for r in roles]
        permission_names = [f"{p.resource}:{p.action}" for p in permissions]

        # Create tokens
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=role_names,
            permissions=permission_names,
        )
        raw_refresh, refresh_hash, refresh_expires = create_refresh_token(family_id)
        await self.repo.create_refresh_token(
            user.id, refresh_hash, refresh_expires, family_id
        )
        await self._log_auth_event(
            "login_success", user.id, username=user.username, email=user.email, ip=ip, details=f"Family: {family_id}"
        )
        await self.db.commit()

        return TokenResponse(access_token = access_token,refresh_token = raw_refresh,expires_in= 30 * 60,)

    async def refresh_tokens(self, refresh_token: str, ip: Optional[str] = None ) -> TokenResponse:
        #Rotate refresh token and issue new access token\


        refresh_hash = hash_refresh_token(refresh_token)
        stored_token = await self.repo.get_valid_refresh_token(refresh_hash)

        if not stored_token:
            await self._log_auth_event(
                "token_refresh_failed", None, username=None, email=None, ip=ip, details="Invalid or expired token"
            )
            await self.db.commit()
            raise exceptions.AuthenticationError("Invalid or expired refresh token")

# Check if token family has been reused (theft detection)
        family_tokens = await self.repo.get_refresh_token_family(stored_token.family_id)
        revoked_in_family = [t for t in family_tokens if t.revoked_at is not None]
        if len(revoked_in_family) > 0:
            # A previous token in this family was already used — reuse detected!
            await self.repo.revoke_token_family(stored_token.family_id)
            await self._log_auth_event(
                "token_reuse_detected",
                stored_token.user_id,
                username=None,
                email=None,
                ip=ip,
                details=f"Family {stored_token.family_id} reuse detected — all tokens revoked",
            )
            await self.db.commit()
            raise exceptions.AuthenticationError(
                "Suspicious activity detected. Please log in again."
            )

        user = await self.repo.get_user_by_id(stored_token.user_id)
        if not user or not user.is_active:
            await self._log_auth_event(
                "token_refresh_failed",
                stored_token.user_id,
                username=None,
                email=None,
                ip=ip,
                details="User disabled",
            )
            await self.db.commit()
            raise exceptions.AccountDisabledError()

        # Rotate: revoke old, create new
        new_raw_refresh, new_refresh_hash, new_refresh_expires = create_refresh_token(
            stored_token.family_id
        )
        await self.repo.revoke_refresh_token(refresh_hash, replaced_by_hash=new_refresh_hash)
        await self.repo.create_refresh_token(
            user.id, new_refresh_hash, new_refresh_expires, stored_token.family_id
        )

        # Create new access token
        roles, permissions = await self.repo.get_user_roles_and_permissions(user.id)
        role_names = [r.name for r in roles]
        permission_names = [f"{p.resource}:{p.action}" for p in permissions]

        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=role_names,
            permissions=permission_names,
        )
        # Audit must be added before commit — after commit it would never be persisted
        await self._log_auth_event(
            "token_refreshed", user.id, username=user.username, email=user.email, ip=ip, details=f"Family: {stored_token.family_id}"
        )
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            expires_in=30 * 60,
        )

    async def logout(self, refresh_token: str, ip: Optional[str] = None) -> bool:
        # Revoke refresh token (logout)
        from app.core.security import hash_refresh_token

        refresh_hash = hash_refresh_token(refresh_token)
        stored_token = await self.repo.get_valid_refresh_token(refresh_hash)

        if not stored_token:
            return False

        user_id = stored_token.user_id
        family_id = stored_token.family_id

        await self.repo.revoke_refresh_token(refresh_hash)
        # Audit must be added before commit — after commit it would never be persisted
        await self._log_auth_event("logout", user_id, username=None, email=None, ip=ip, details=f"Family: {family_id}")
        await self.db.commit()
        return True

    async def get_current_user(self, token: str) -> models.User:
        """Validate access token and return user."""
        try:
            payload = decode_token(token)
            verify_token_type(payload, "access")
        except ValueError as e:
            error_msg = str(e)
            if "expired" in error_msg.lower():
                raise exceptions.TokenExpiredError()
            raise exceptions.TokenInvalidError()

        user = await self.repo.get_user_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise exceptions.AccountDisabledError()

        return user

    async def get_user_profile(self, user_id: UUID) -> models.User:
        # Fetch a user by ID (admin user lookup — not token validation)
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise exceptions.NotFoundError("User not found")
        return user

    async def create_user(self, request: UserCreate, created_by: Optional[UUID] = None) -> models.User:
        # Create a new user (admin only)
        existing = await self.repo.get_user_by_username(request.username, request.tenant_id)
        if existing:
            raise exceptions.ConflictError("Username already registered")

        if request.email:
            existing_email = await self.repo.get_user_by_email(request.email, request.tenant_id)
            if existing_email:
                raise exceptions.ConflictError("Email already registered")

        user = models.User(
            username=request.username,
            email=request.email,
            hashed_password= hash_password(request.password),
            full_name=request.full_name,
            tenant_id=request.tenant_id,
            is_active=request.is_active,
        )
        self.db.add(user)
        await self.db.flush()

        for role_id in request.role_ids:
            await self.repo.assign_role_to_user(user.id, role_id, created_by)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(
        self,
        user_id: UUID,
        request: UserCreate,
        updated_by: Optional[UUID] = None,
    ) -> models.User:
        # Update user details and roles
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise exceptions.NotFoundError("User not found")

        if request.username and request.username != user.username:
            existing = await self.repo.get_user_by_username(request.username, user.tenant_id)
            if existing:
                raise exceptions.ConflictError("Username already in use")
            user.username = request.username

        if request.email and request.email != user.email:
            existing = await self.repo.get_user_by_email(request.email, user.tenant_id)
            if existing:
                raise exceptions.ConflictError("Email already in use")
            user.email = request.email

        if request.full_name:
            user.full_name = request.full_name

        if request.tenant_id is not None:
            user.tenant_id = request.tenant_id

        if request.is_active is not None:
            user.is_active = request.is_active

        if request.role_ids is not None:
            current_roles = {r.id for r in user.roles}
            new_roles = set(request.role_ids)
            for role_id in current_roles - new_roles:
                await self.repo.remove_role_from_user(user.id, role_id)
            for role_id in new_roles - current_roles:
                await self.repo.assign_role_to_user(user.id, role_id, updated_by)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        # Change user password
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise exceptions.NotFoundError("User not found")

        if not verify_password(current_password, user.hashed_password):
            raise exceptions.AuthenticationError("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        await self.db.commit()
        return True
