from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.command import CommandRecord
from app.schemas.command import CommandCreateRequest


class CommandService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_command(self, payload: CommandCreateRequest) -> CommandRecord:
        record = CommandRecord(
            requested_at=datetime.now(timezone.utc),
            requested_by=payload.requested_by,
            target_device=payload.target_device,
            command_type=payload.command_type,
            command_payload=payload.command_payload,
            status="queued",
            acknowledged_at=None,
            completed_at=None,
            error_message=None,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def create_if_not_duplicate(self, payload: CommandCreateRequest) -> tuple[CommandRecord, bool]:
        stmt = (
            select(CommandRecord)
            .where(CommandRecord.target_device == payload.target_device)
            .where(CommandRecord.command_type == payload.command_type)
            .where(CommandRecord.status.in_(["queued", "dispatched"]))
            .order_by(CommandRecord.requested_at.desc())
            .limit(1)
        )

        latest = self.db.scalar(stmt)

        if latest is not None and latest.command_payload == payload.command_payload:
            return latest, False

        created = self.create_command(payload)
        return created, True

    def list_recent(self, limit: int = 50) -> list[CommandRecord]:
        stmt = (
            select(CommandRecord)
            .order_by(CommandRecord.requested_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, command_id: int) -> CommandRecord | None:
        stmt = (
            select(CommandRecord)
            .where(CommandRecord.id == command_id)
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_next_queued(self) -> CommandRecord | None:
        stmt = (
            select(CommandRecord)
            .where(CommandRecord.status == "queued")
            .order_by(CommandRecord.requested_at.asc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def mark_dispatched(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        if record is None:
            return None

        record.status = "dispatched"
        self.db.commit()
        self.db.refresh(record)
        return record

    def mark_completed(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        if record is None:
            return None

        now = datetime.now(timezone.utc)
        record.status = "completed"
        record.acknowledged_at = now
        record.completed_at = now
        self.db.commit()
        self.db.refresh(record)
        return record

    def mark_failed(self, command_id: int, error_message: str) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        if record is None:
            return None

        record.status = "failed"
        record.error_message = error_message
        self.db.commit()
        self.db.refresh(record)
        return record