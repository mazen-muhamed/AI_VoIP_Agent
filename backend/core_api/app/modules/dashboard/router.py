from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.core.exceptions import ForbiddenError
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.calls.schemas import CallDirection, CallStatus
from app.modules.dashboard.dependencies import get_dashboard_service
from app.modules.dashboard.schemas import DashboardCallsResponse, DashboardOverviewResponse, ServiceLevelResponse
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.utils import get_period_utc_range

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_user_tenant_id(current_user: User):
    """Return the authenticated user's tenant, never a client-supplied tenant."""
    if current_user.tenant_id is None:
        raise ForbiddenError("User is not assigned to a tenant")

    return current_user.tenant_id


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(
    period: str = Query(default="today", pattern="^(today|7d|30d)$"),
    current_user: User = Depends(require_permission("calls:read")),
    service: DashboardService = Depends(get_dashboard_service),
):
    tenant_id = get_user_tenant_id(current_user)
    start_at, end_at = get_period_utc_range(period)

    return await service.get_overview(
        tenant_id,
        start_at,
        end_at,
        period,
    )


@router.get("/calls", response_model=DashboardCallsResponse)
async def get_calls(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: CallStatus | None = None,
    direction: CallDirection | None = None,
    transferred: bool | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_permission("calls:read")),
    service: DashboardService = Depends(get_dashboard_service),
):
    tenant_id = get_user_tenant_id(current_user)

    return await service.get_calls(
        tenant_id=tenant_id,
        start_at=date_from,
        end_at=date_to,
        status=status,
        direction=direction,
        transferred=transferred,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/service-level", response_model=ServiceLevelResponse)
async def get_service_level(
    period: str = Query(default="today", pattern="^(today|7d|30d)$"),
    current_user: User = Depends(require_permission("calls:read")),
    service: DashboardService = Depends(get_dashboard_service),
):
    tenant_id = get_user_tenant_id(current_user)
    start_at, end_at = get_period_utc_range(period)

    return await service.get_service_level(
        tenant_id,
        start_at,
        end_at,
        period,
    )