from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import DashboardCallsResponse, DashboardOverviewResponse, ServiceLevelResponse
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.utils import get_period_utc_range
from app.modules.calls.schemas import CallDirection, CallStatus
from app.modules.dashboard.dependencies import get_dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Get dashboard overview for the selected period
@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(
    tenant_id: UUID,
    period: str = Query(default="today", pattern="^(today|7d|30d)$"),
    service: DashboardService = Depends(get_dashboard_service),
):
    start_at, end_at = get_period_utc_range(period)
    return await service.get_overview(
        tenant_id,
        start_at,
        end_at,
        period,
    )


# Get paginated calls with optional filters
@router.get("/calls", response_model=DashboardCallsResponse,)
async def get_calls(
    tenant_id: UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: CallStatus | None = None,
    direction: CallDirection | None = None,
    transferred: bool | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_calls(
        direction=direction,
        search=search,
        tenant_id=tenant_id,
        start_at=date_from,
        end_at=date_to,
        status=status,
        transferred=transferred,
        page=page,
        page_size=page_size,
    )


# Get service-level statistics
@router.get("/service-level", response_model=ServiceLevelResponse)
async def get_service_level(
    tenant_id: UUID,
    period: str = Query(
        default="today",
        pattern="^(today|7d|30d)$",
    ),
    service: DashboardService = Depends(get_dashboard_service),
):
    start_at, end_at = get_period_utc_range(period)

    return await service.get_service_level(
        tenant_id,
        start_at,
        end_at,
        period,
    )