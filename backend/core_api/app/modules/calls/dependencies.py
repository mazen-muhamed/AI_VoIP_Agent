import secrets
from uuid import UUID
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.modules.calls.repository import CallsRepository
from app.modules.calls.service import CallsService


async def verify_ingest_key(x_ingest_key: str | None = Header(default=None),) -> UUID:
    expected_key = settings.CALLS_INGEST_API_KEY

    if (
        x_ingest_key is None
        or not secrets.compare_digest(x_ingest_key, expected_key)
    ):
        raise UnauthorizedError("Invalid ingest key")

    try:
        return UUID(settings.CALLS_INGEST_TENANT_ID)
    except ValueError:   
        raise UnauthorizedError("Invalid CALLS_INGEST_TENANT_ID configuration")


def get_calls_service(db: AsyncSession = Depends(get_db),) -> CallsService:
    repository = CallsRepository(db)
    return CallsService(repository, db)