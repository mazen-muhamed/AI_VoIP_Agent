from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from app.modules.calls.schemas import CallResponse

class SLA(BaseModel):
    pct: float
    target: int
    answered_in_threshold: int
    offered: int


class Containment(BaseModel):
    pct: float
    ai_resolved: int
    answered: int

class DashboardOverviewResponse(BaseModel):
    period: str
    total_calls: int
    answered: int
    active_calls: int
    previous_period_total: int
    avg_wait_seconds: float
    p95_wait_seconds: float
    sla: SLA
    containment: Containment




class DashboardCallsResponse(BaseModel):
    items: list[CallResponse]
    page: int
    page_size: int = Field(le=100)
    total: int


class ServiceLevelResponse(BaseModel):
    period: str
    sla: SLA
    buckets: list