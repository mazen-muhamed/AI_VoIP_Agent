from datetime import datetime
from uuid import UUID
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.utils import get_previous_period_utc_range

class DashboardService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository

    # Get dashboard overview statistics
    async def get_overview(
            self,
            tenant_id: UUID,
            start_at: datetime,
            end_at: datetime,
            period: str,
    ):
        data = await self.repository.get_overview(
            tenant_id,
            start_at,
            end_at,
        )

        active_calls = await self.repository.get_active_calls(
            tenant_id,
        )

        previous_start, previous_end = get_previous_period_utc_range(period)

        previous_data = await self.repository.get_overview(
            tenant_id,
            previous_start,
            previous_end,
        )
        sla_data = await self.repository.get_service_level(
            tenant_id,
            start_at,
            end_at,
        )

        sla_numerator = sla_data.numerator or 0
        sla_denominator = sla_data.denominator or 0

        sla_pct = (
            (sla_numerator / sla_denominator) * 100
            if sla_denominator > 0
            else 0.0
        )
        answered = data.answered or 0
        ai_resolved = data.ai_resolved or 0

        containment_rate = (
            (ai_resolved / answered) * 100
            if answered > 0
            else 0.0
        )

        return {
            "period": period,
            "total_calls": data.total_calls or 0,
            "answered": answered,
            "active_calls": active_calls,
            "previous_period_total": previous_data.total_calls or 0,
            "avg_wait_seconds": (float(data.avg_wait_seconds)
                if data.avg_wait_seconds is not None
                else 0.0
            ),
            "p95_wait_seconds": (float(data.p95_wait_seconds)
                if data.p95_wait_seconds is not None
                else 0.0
            ),
            "sla": {
                "pct": sla_pct,
                "target": 30,
                "answered_in_threshold": sla_numerator,
                "offered": sla_denominator,
            },
            "containment": {
                "pct": containment_rate,
                "ai_resolved": ai_resolved,
                "answered": answered,
            },
        }

    # Get paginated calls with filters
    async def get_calls(
            self,
            tenant_id: UUID,
            start_at: datetime | None = None,
            end_at: datetime | None = None,
            status: str | None = None,
            direction: str | None = None,
            transferred: bool | None = None,
            search: str | None = None,
            page: int = 1,
            page_size: int = 20,
    ):
        page_size = min(page_size, 100)

        calls, total = await self.repository.get_calls(
            tenant_id=tenant_id,
            start_at=start_at,
            end_at=end_at,
            status=status,
            direction=direction,
            transferred=transferred,
            search=search,
            page=page,
            page_size=page_size,
        )

        return {
            "items": calls,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    # Calculate service-level ratio
    async def get_service_level(
            self,
            tenant_id: UUID,
            start_at: datetime,
            end_at: datetime,
            period: str,
    ):
        data = await self.repository.get_service_level(
            tenant_id,
            start_at,
            end_at,
        )

        numerator = data.numerator or 0
        denominator = data.denominator or 0

        ratio = (
            (numerator / denominator) * 100
            if denominator > 0
            else 0.0
        )

        return {
            "period": period,
            "sla": {
                "pct": ratio,
                "target": 30,
                "answered_in_threshold": numerator,
                "offered": denominator,
            },
            "buckets": [],
        }