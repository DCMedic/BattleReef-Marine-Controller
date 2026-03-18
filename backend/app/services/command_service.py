from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.db.models.command import CommandRecord
from app.schemas.command import CommandCreateRequest


class CommandService:
    """
    Handles creation, retrieval, and lifecycle management of device commands.
    """

    def __init__(self, db: Session):
        self.db = db
        self.model = CommandRecord

    # -----------------------------
    # CREATE COMMAND
    # -----------------------------
    def create_command(self, payload: CommandCreateRequest) -> CommandRecord:
        record = self.model(
            requested_by=payload.requested_by,
            target_device=payload.target_device,
            command_type=payload.command_type,
            command_payload=payload.command_payload,
            status="queued",
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # LIST RECENT COMMANDS
    # -----------------------------
    def list_recent(self, limit: int = 50) -> List[CommandRecord]:
        return (
            self.db.query(self.model)
            .order_by(self.model.requested_at.desc())
            .limit(limit)
            .all()
        )

    # -----------------------------
    # LIST QUEUED COMMANDS
    # -----------------------------
    def list_queued(self, limit: int = 20) -> List[CommandRecord]:
        return (
            self.db.query(self.model)
            .filter(self.model.status == "queued")
            .order_by(self.model.requested_at.asc())
            .limit(limit)
            .all()
        )

    # -----------------------------
    # GET LAST COMMAND FOR DEVICE
    # -----------------------------
    def get_last_command_for_device(self, device_key: str) -> CommandRecord | None:
        return (
            self.db.query(self.model)
            .filter(self.model.target_device == device_key)
            .order_by(self.model.requested_at.desc())
            .first()
        )

    # -----------------------------
    # LOOKUP BY ID
    # -----------------------------
    def get_by_id(self, command_id: int) -> CommandRecord | None:
        return (
            self.db.query(self.model)
            .filter(self.model.id == command_id)
            .first()
        )

    # -----------------------------
    # MARK ACKNOWLEDGED
    # -----------------------------
    def mark_acknowledged(self, record: CommandRecord) -> CommandRecord:
        record.status = "acknowledged"
        record.acknowledged_at = datetime.now(timezone.utc)

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # MARK DISPATCHED
    # -----------------------------
    def mark_dispatched(self, record: CommandRecord) -> CommandRecord:
        now = datetime.now(timezone.utc)

        record.status = "dispatched"
        if record.acknowledged_at is None:
            record.acknowledged_at = now

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # MARK COMPLETED
    # -----------------------------
    def mark_completed(self, record: CommandRecord) -> CommandRecord:
        now = datetime.now(timezone.utc)

        if record.acknowledged_at is None:
            record.acknowledged_at = now

        record.status = "completed"
        record.completed_at = now

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # MARK FAILED
    # -----------------------------
    def mark_failed(self, record: CommandRecord, error_message: str) -> CommandRecord:
        now = datetime.now(timezone.utc)

        if record.acknowledged_at is None:
            record.acknowledged_at = now

        record.status = "failed"
        record.completed_at = now
        record.error_message = error_message

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # LEGACY ID-BASED HELPERS
    # -----------------------------
    def acknowledge_command(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        if record is None:
            return None
        return self.mark_acknowledged(record)

    def complete_command(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        if record is None:
            return None
        return self.mark_completed(record)

    def fail_command(self, command_id: int, error_message: str) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        if record is None:
            return None
        return self.mark_failed(record, error_message)