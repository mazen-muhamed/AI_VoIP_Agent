# dependencies for authentication and authorization

from typing import List, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token, verify_token_type
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    #Get AuthService instance
    return AuthService(db)


async def get_repository(db: AsyncSession = Depends(get_db)) -> AuthRepository:
    #Get AuthRepository instance
    return AuthRepository(db)


async def get_current_user(token: str = Depends(oauth2_scheme),auth_service: AuthService = Depends(get_auth_service),) -> User:
    
    #Validate JWT access token and return current user.
    #Use this dependency to protect endpoints that require authentication.
    return await auth_service.get_current_user(token)


async def get_current_active_user(current_user: User = Depends(get_current_user),) -> User:
    #Ensure user is active 
    if not current_user.is_active:
        raise AuthenticationError("Account is disabled")
    return current_user


def require_role(*required_roles: str):
    
    #Dependency factory for role-based access control (RBAC).
    # Usage: Depends(require_role("admin", "supervisor"))
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_roles = {role.name for role in current_user.roles}
        if not any(role in user_roles for role in required_roles):
            raise AuthorizationError(f"Required role(s): {', '.join(required_roles)}")
        return current_user

    return role_checker


def require_permission(*required_permissions: str):
    
   #Dependency factory for permission-based access control (ABAC-ready).
   #Usage: Depends(require_permission("calls:read", "calls:write")) Checks user's permissions from token (fast, no DB hit).
    
    async def permission_checker(token: str = Depends(oauth2_scheme),current_user: User = Depends(get_current_active_user),) -> User:
        try:
            payload = decode_token(token)
            verify_token_type(payload, "access")
            user_permissions = set(payload.permissions)
        except ValueError as e:
            raise AuthenticationError(str(e))

        if not any(perm in user_permissions for perm in required_permissions):
            raise AuthorizationError(f"Required permission(s): {', '.join(required_permissions)}")
        return current_user

    return permission_checker


def require_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    #Require superuser access — checks system:admin permission via roles
    user_permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            user_permissions.add(f"{perm.resource}:{perm.action}")

    if "system:admin" not in user_permissions:
        raise AuthorizationError("Superuser access required")
    return current_user