from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Call(Base):
    __tablename__ = "calls"

    __table_args__ = (
        UniqueConstraint("call_uuid", name="uq_call_uuid"),
        Index("ix_call_tenant_id", "tenant_id"),
        Index("ix_call_started_at", "started_at"),
        Index("ix_call_status", "status"),
        Index("ix_call_transferred_to_human", "transferred_to_human"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4,)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False,)
    call_uuid: Mapped[str] = mapped_column(String(255), nullable=False, index=True,)
    direction: Mapped[str] = mapped_column(String(20), nullable=False,)
    from_number: Mapped[str] = mapped_column(String(50), nullable=False,)
    to_number: Mapped[str] = mapped_column(String(50), nullable=False,)
    status: Mapped[str] = mapped_column(String(30), nullable=False,)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,)
    wait_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True,)
    talk_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True,)
    hangup_cause: Mapped[Optional[str]] = mapped_column(String(100), nullable=True,)
    transferred_to_human: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,)
    transfer_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True,)
    ai_resolved: Mapped[bool] = mapped_column(Boolean, default=False,nullable=False,)
    csat_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True,)
    csat_collected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False,)