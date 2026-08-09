from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DeviceHealthRecord(Base):
    __tablename__ = "device_health"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown", index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    ack_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
