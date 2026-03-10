from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.command import CommandRecord
from app.schemas.command import CommandCreateRequest


class CommandService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: CommandCreateRequest, status: str = "queued") -> CommandRecord:
        record = CommandRecord(
            requested_by=payload.requested_by,
            target_device=payload.target_device,
            command_type=payload.command_type,
            command_payload=payload.command_payload,
            status=status,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_recent(self, limit: int = 50) -> list[CommandRecord]:
        stmt = (
            select(CommandRecord)
            .order_by(CommandRecord.requested_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_for_target(
        self,
        target_device: str,
        command_type: str | None = None,
    ) -> CommandRecord | None:
        stmt = select(CommandRecord).where(CommandRecord.target_device == target_device)

        if command_type is not None:
            stmt = stmt.where(CommandRecord.command_type == command_type)

        stmt = stmt.order_by(CommandRecord.requested_at.desc()).limit(1)
        return self.db.scalar(stmt)

    def create_if_not_duplicate(
        self,
        payload: CommandCreateRequest,
        status: str = "queued",
    ) -> tuple[CommandRecord, bool]:
        latest = self.get_latest_for_target(
            target_device=payload.target_device,
            command_type=payload.command_type,
        )

        if latest is not None and latest.command_payload == payload.command_payload:
            return latest, False

        record = self.create(payload=payload, status=status)
        return record, True