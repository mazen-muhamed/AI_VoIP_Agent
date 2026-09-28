from datetime import datetime
from uuid import UUID

from app.modules.dashboard.repository import DashboardRepository


class DashboardService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository

    # Get dashboard overview statistics
    async def get_overview(
        self,
        tenant_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        data = await self.repository.get_overview(
            tenant_id,
            start_at,
            end_at,
        )

        answered = data.answered or 0
        ai_resolved = data.ai_resolved or 0
        csat_responses = data.csat_response_count or 0
        positive_csat = data.positive_csat_count or 0

        # Calculate containment rate
        containment_rate = (
            (ai_resolved / answered) * 100
            if answered > 0
            else 0.0
        )

        # Calculate positive CSAT rate
        csat_rate = (
            (positive_csat / csat_responses) * 100
            if csat_responses > 0
            else 0.0
        )

        return {
            "total_calls": data.total_calls or 0,
            "answered": answered,
            "agents_avail": 0,
            "active_calls": data.active_calls or 0,
            "containment_rate": containment_rate,
            "transfer_count": data.transfer_count or 0,
            "avg_csat": (
                float(data.avg_csat)
                if data.avg_csat is not None
                else None
            ),
            "csat_response_count": csat_responses,
            "csat_rate": csat_rate,
        }

    # Get paginated calls with filters
    async def get_calls(
        self,
        tenant_id: UUID,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        status: str | None = None,
        transferred: bool | None = None,
        csat_given: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        page_size = min(page_size, 100)

        calls, total = await self.repository.get_calls(
            tenant_id=tenant_id,
            start_at=start_at,
            end_at=end_at,
            status=status,
            transferred=transferred,
            csat_given=csat_given,
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
            "ratio": ratio,
            "numerator": numerator,
            "denominator": denominator,
        }