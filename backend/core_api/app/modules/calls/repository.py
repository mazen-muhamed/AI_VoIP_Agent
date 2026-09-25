from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calls.models import Call


class CallsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_call_uuid(self, call_uuid: str) -> Optional[Call]:
        stmt = select(Call).where(Call.call_uuid == call_uuid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, call_id: UUID) -> Optional[Call]:
        stmt = select(Call).where(Call.id == call_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, call: Call) -> Call:
        self.db.add(call)
        await self.db.flush()
        return call

    async def update(self, call: Call, data: dict) -> Call:
        for field, value in data.items():
            setattr(call, field, value)

        await self.db.flush()
        return call

    async def upsert(self, data: dict) -> Call:
        call_uuid = data["call_uuid"]

        existing_call = await self.get_by_call_uuid(call_uuid)

        if existing_call:
            return await self.update(existing_call, data)

        call = Call(**data)
        return await self.create(call)

    async def delete(self, call: Call) -> None:
        await self.db.delete(call)
        await self.db.flush()