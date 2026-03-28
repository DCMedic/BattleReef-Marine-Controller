from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    reading_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    sensor_key: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source_node: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    value_double: Mapped[float] = mapped_column(Float, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    unit: Mapped[str] = mapped_column(Text, nullable=False)
    quality: Mapped[str] = mapped_column(Text, nullable=False, default="good")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


TelemetryRecord = TelemetryReading