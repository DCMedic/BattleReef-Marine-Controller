from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelemetryRecord(Base):
    __tablename__ = "telemetry_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    reading_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    sensor_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_node: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    value_double: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quality: Mapped[str] = mapped_column(String(20), nullable=False, default="good")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )