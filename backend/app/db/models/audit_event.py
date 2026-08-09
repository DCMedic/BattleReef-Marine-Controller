from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info", index=True)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False, default="success", index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(40), nullable=False, default="system", index=True)
    actor_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
