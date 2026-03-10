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