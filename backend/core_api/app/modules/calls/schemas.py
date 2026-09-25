from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CallEventCreate(BaseModel):
    tenant_id: UUID
    call_uuid: str = Field(min_length=1, max_length=255)
    direction: str
    from_number: str
    to_number: str
    status: str
    started_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    hangup_cause: Optional[str] = None
    transferred_to_human: bool = False
    transfer_reason: Optional[str] = None
    ai_resolved: bool = False
    csat_score: Optional[int] = Field(default=None, ge=1, le=5)
    csat_collected: bool = False


class CallResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    call_uuid: str
    direction: str
    from_number: str
    to_number: str
    status: str
    started_at: datetime
    answered_at: Optional[datetime]
    ended_at: Optional[datetime]
    wait_seconds: Optional[int]
    talk_seconds: Optional[int]
    hangup_cause: Optional[str]
    transferred_to_human: bool
    transfer_reason: Optional[str]
    ai_resolved: bool
    csat_score: Optional[int]
    csat_collected: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CallListResponse(BaseModel):
    items: list[CallResponse]
    page: int
    page_size: int
    total: int