from datetime import datetime
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.calls.models import Call


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Get overview statistics for a tenant
    async def get_overview(
        self,
        tenant_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        stmt = select(
            func.count(Call.id).label("total_calls"),
            func.count(Call.id)
            .filter(Call.answered_at.is_not(None))
            .label("answered"),
            func.count(Call.id)
            .filter(Call.status == "in_progress")
            .label("active_calls"),
            func.count(Call.id)
            .filter(Call.transferred_to_human.is_(True))
            .label("transfer_count"),
            func.count(Call.id)
            .filter(
                Call.ai_resolved.is_(True),
                Call.answered_at.is_not(None),
            )
            .label("ai_resolved"),
            func.avg(Call.csat_score)
            .filter(Call.csat_collected.is_(True))
            .label("avg_csat"),
            func.count(Call.id)
            .filter(Call.csat_collected.is_(True))
            .label("csat_response_count"),
            func.count(Call.id)
            .filter(
                Call.csat_collected.is_(True),
                Call.csat_score >= 4,
            )
            .label("positive_csat_count"),
        ).where(
            Call.tenant_id == tenant_id,
            Call.started_at >= start_at,
            Call.started_at < end_at,
        )

        result = await self.db.execute(stmt)
        return result.one()

    # Get service-level numerator and denominator
    async def get_service_level(
        self,
        tenant_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ):
        numerator = func.count(Call.id).filter(
            Call.wait_seconds.is_not(None),
            Call.wait_seconds <= 30,
        )

        denominator = (
            func.count(Call.id).filter(
                Call.answered_at.is_not(None)
            )
            + func.count(Call.id).filter(
                Call.status == "abandoned"
            )
        )

        stmt = (select(numerator.label("numerator"), denominator.label("denominator"),)
        .where(
            Call.tenant_id == tenant_id,
            Call.started_at >= start_at,
            Call.started_at < end_at,
        ))

        result = await self.db.execute(stmt)
        return result.one()

    # Get paginated calls with optional filters
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
        conditions = [Call.tenant_id == tenant_id]

        if start_at is not None:
            conditions.append(Call.started_at >= start_at)

        if end_at is not None:
            conditions.append(Call.started_at < end_at)

        if status is not None:
            conditions.append(Call.status == status)

        if transferred is not None:
            conditions.append(Call.transferred_to_human == transferred)

        if csat_given is not None:
            conditions.append(Call.csat_collected == csat_given)

        # Count total matching calls
        total_stmt = select(func.count(Call.id)).where(*conditions)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

        # Get calls ordered by newest first
        stmt = (
            select(Call)
            .where(*conditions)
            .order_by(Call.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(stmt)
        calls = result.scalars().all()

        return calls, total