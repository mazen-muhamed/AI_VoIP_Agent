#Data access layer, all async SQLAlchemy, DB Queries with ORM

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import Permission, RefreshToken, Role, User, UserRole


class AuthRepository:
    # Data access layer for authentication
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str, tenant_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.tenant_id == tenant_id)
        stmt = stmt.options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_by_username(self, username: str, tenant_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.username == username, User.tenant_id == tenant_id)
        stmt = stmt.options(
            selectinload(User.roles).selectinload(Role.permissions),
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        #Get user by ID with roles and permissions loaded
        stmt = (
            select(User).where(User.id == user_id).options(
                selectinload(User.roles).selectinload(Role.permissions),
            ) 
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_roles_and_permissions(self, user_id: UUID) -> tuple[List[Role], List[Permission]]:
        user = await self.get_user_by_id(user_id)
        if not user:
            return [], []

        roles = list(user.roles)
        permissions = []
        for role in roles:
            permissions.extend(role.permissions)
        return roles, permissions

    async def create_refresh_token(
        self,user_id: UUID,token_hash: str,expires_at: datetime,family_id: str,) -> RefreshToken:

        #Store a new refresh toke
        refresh_token = RefreshToken(token_hash=token_hash,user_id=user_id,family_id=family_id,expires_at=expires_at,)
        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token

    async def get_valid_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        #Get a valid (non-revoked, non-expired) refresh token
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_refresh_token_family(self, family_id: str) -> List[RefreshToken]:
        #Get all tokens in a family (for reuse detection)
        stmt = select(RefreshToken).where(RefreshToken.family_id == family_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def revoke_refresh_token(self, token_hash: str, replaced_by_hash: Optional[str] = None) -> bool:
        #Revoke a refresh token (mark as used)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        token = result.scalar_one_or_none()

        if not token or token.revoked_at is not None:
            return False

        token.revoked_at = datetime.now(timezone.utc)
        if replaced_by_hash:
            token.replaced_by_token_hash = replaced_by_hash
        await self.db.flush()
        return True

    async def revoke_token_family(self, family_id: str) -> int:
        #Revoke all tokens in a family (reuse detected - stolen token)
        stmt = select(RefreshToken).where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        count = 0
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)
            count += 1

        await self.db.flush()
        return count

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        #Revoke all refresh tokens for a user (logout everywhere)
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        count = 0
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)
            count += 1

        await self.db.flush()
        return count

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        #Get role by name with Permissions.
        stmt = (select(Role).where(Role.name == name).options(selectinload(Role.permissions)))
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_user_role(self, user_id: UUID, role_id: UUID) -> Optional[UserRole]:
        stmt = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_roles_by_names(self, names: List[str]) -> List[Role]:
        #Get multiple roles by names with permissions
        stmt = (select(Role).where(Role.name.in_(names)).options(selectinload(Role.permissions)))
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())

    async def assign_role_to_user(self, user_id: UUID, role_id: UUID, assigned_by: Optional[UUID] = None) -> UserRole:
        #Assign a role to user — checks duplicate to avoid IntegrityError
        existing = await self.get_user_role(user_id, role_id)
        if existing:
            return existing
        user_role = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.db.add(user_role)
        await self.db.flush()
        return user_role

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> bool:
        #Remove a role from a user
        stmt = select(UserRole).where(UserRole.user_id == user_id,UserRole.role_id == role_id)
        result = await self.db.execute(stmt)
        user_role = result.scalar_one_or_none()

        if not user_role:
            return False

        await self.db.delete(user_role)
        await self.db.flush()
        return True
