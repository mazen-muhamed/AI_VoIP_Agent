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

        started_at = self._to_utc(event.started_at)
        answered_at = self._to_utc(event.answered_at)
        ended_at = self._to_utc(event.ended_at)

        wait_seconds = self._calculate_wait_seconds(
            started_at,
            answered_at,
        )

        talk_seconds = self._calculate_talk_seconds(
            answered_at,
            ended_at,
        )

        data = event.model_dump()

        data["started_at"] = started_at
        data["answered_at"] = answered_at
        data["ended_at"] = ended_at
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

    def _to_utc(self, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None

        return value.astimezone(timezone.utc)

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