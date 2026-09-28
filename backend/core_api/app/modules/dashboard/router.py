from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import DashboardCallsResponse, DashboardOverviewResponse, ServiceLevelResponse
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.utils import get_today_utc_range


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(
    db: AsyncSession = Depends(get_db), ) -> DashboardService:
    return DashboardService(DashboardRepository(db))


# Get today's dashboard overview
@router.get("/overview", response_model=DashboardOverviewResponse,)
async def get_overview(
    tenant_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
):
    start_at, end_at = get_today_utc_range()

    return await service.get_overview(tenant_id, start_at, end_at,)


# Get paginated calls with optional filters
@router.get("/calls", response_model=DashboardCallsResponse,)
async def get_calls(
    tenant_id: UUID,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: str | None = None,
    transferred: bool | None = None,
    csat_given: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_calls(
        tenant_id=tenant_id,
        start_at=start_at,
        end_at=end_at,
        status=status,
        transferred=transferred,
        csat_given=csat_given,
        page=page,
        page_size=page_size,
    )


# Get service-level statistics
@router.get("/service-level", response_model=ServiceLevelResponse,)
async def get_service_level(
    tenant_id: UUID,
    start_at: datetime,
    end_at: datetime,
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_service_level(tenant_id, start_at, end_at,)