from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommandRecord(Base):
    __tablename__ = "commands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_device: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    command_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    command_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)