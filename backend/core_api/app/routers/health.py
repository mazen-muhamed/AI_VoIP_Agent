#Health check router

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.database import check_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    #Basic health check - returns OK if service is running
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/db", summary="Database health check")
async def db_health_check(db: AsyncSession = Depends(get_db)) -> dict:
#Database health check — forces a real server round-trip.

    try:
        await check_db(db)
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
