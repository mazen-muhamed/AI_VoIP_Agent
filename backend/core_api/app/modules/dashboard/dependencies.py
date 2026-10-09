from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.service import DashboardService


def get_dashboard_service(db: AsyncSession = Depends(get_db),) -> DashboardService:
    repository = DashboardRepository(db)
    return DashboardService(repository)