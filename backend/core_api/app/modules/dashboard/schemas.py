from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class DashboardOverviewResponse(BaseModel):
    total_calls: int
    answered: int
    agents_avail: int
    active_calls: int
    containment_rate: float
    transfer_count: int
    avg_csat: Optional[float]
    csat_response_count: int
    csat_rate: float


class DashboardCallResponse(BaseModel):
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


class DashboardCallsResponse(BaseModel):
    items: list[DashboardCallResponse]
    page: int
    page_size: int = Field(le=100)
    total: int


class ServiceLevelResponse(BaseModel):
    ratio: float
    numerator: int
    denominator: int