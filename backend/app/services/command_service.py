from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.schemas.command import CommandCreateRequest
from app.db.models.command import Command


class CommandService:
    """
    Handles creation, retrieval, and tracking of device commands.
    """

    def __init__(self, db: Session):
        self.db = db
        self.model = Command

    # -----------------------------
    # CREATE COMMAND
    # -----------------------------
    def create_command(self, payload: CommandCreateRequest) -> Command:
        record = self.model(
            requested_by=payload.requested_by,
            target_device=payload.target_device,
            command_type=payload.command_type,
            command_payload=payload.command_payload,
            status="pending",
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # LIST RECENT COMMANDS
    # -----------------------------
    def list_recent(self, limit: int = 50) -> List[Command]:
        return (
            self.db.query(self.model)
            .order_by(self.model.requested_at.desc())
            .limit(limit)
            .all()
        )

    # -----------------------------
    # GET LAST COMMAND FOR DEVICE
    # -----------------------------
    def get_last_command_for_device(self, device_key: str) -> Command | None:
        return (
            self.db.query(self.model)
            .filter(self.model.target_device == device_key)
            .order_by(self.model.requested_at.desc())
            .first()
        )

    # -----------------------------
    # MARK COMMAND ACKNOWLEDGED
    # -----------------------------
    def acknowledge_command(self, command_id: int) -> Command | None:
        record = self.db.query(self.model).get(command_id)

        if not record:
            return None

        record.status = "acknowledged"

        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # MARK COMMAND COMPLETED
    # -----------------------------
    def complete_command(self, command_id: int) -> Command | None:
        record = self.db.query(self.model).get(command_id)

        if not record:
            return None

        record.status = "completed"

        self.db.commit()
        self.db.refresh(record)

        return record

    # -----------------------------
    # MARK COMMAND FAILED
    # -----------------------------
    def fail_command(self, command_id: int, error_message: str) -> Command | None:
        record = self.db.query(self.model).get(command_id)

        if not record:
            return None

        record.status = "failed"
        record.error_message = error_message

        self.db.commit()
        self.db.refresh(record)

        return record