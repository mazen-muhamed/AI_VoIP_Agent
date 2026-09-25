from datetime import datetime, timezone
from typing import Optional

from app.modules.calls.models import Call
from app.modules.calls.repository import CallsRepository
from app.modules.calls.schemas import CallEventCreate


class CallsService:
    def __init__(self, repository: CallsRepository):
        self.repository = repository

    async def process_event(self, event: CallEventCreate) -> Call:
        self._validate_event(event)

        wait_seconds = self._calculate_wait_seconds(
            event.started_at,
            event.answered_at,
        )

        talk_seconds = self._calculate_talk_seconds(
            event.answered_at,
            event.ended_at,
        )

        data = event.model_dump()

        data["wait_seconds"] = wait_seconds
        data["talk_seconds"] = talk_seconds

        return await self.repository.upsert(data)

    def _validate_event(self, event: CallEventCreate) -> None:
        self._validate_timestamp(event.started_at)
        self._validate_timestamp(event.answered_at)
        self._validate_timestamp(event.ended_at)

        if event.csat_score is not None and not event.csat_collected:
            raise ValueError("csat_score requires csat_collected=true")

    def _validate_timestamp(self, value: Optional[datetime]) -> None:
        if value is None:
            return

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")

    def _calculate_wait_seconds(
        self,
        started_at: datetime,
        answered_at: Optional[datetime],
    ) -> Optional[int]:
        if answered_at is None:
            return None

        return max(0, int((answered_at - started_at).total_seconds()))

    def _calculate_talk_seconds(
        self,
        answered_at: Optional[datetime],
        ended_at: Optional[datetime],
    ) -> Optional[int]:
        if answered_at is None or ended_at is None:
            return None

        return max(0, int((ended_at - answered_at).total_seconds()))