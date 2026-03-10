from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeviceStateRecord(Base):
    __tablename__ = "device_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    state_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state_source: Mapped[str] = mapped_column(String(100), nullable=False, default="system", index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
    )