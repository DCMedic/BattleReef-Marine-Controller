from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, List

from sqlalchemy.orm import Session

from app.db.models.command import CommandRecord
from app.schemas.command import CommandCreateRequest


class CommandService:
    """Handles creation, retrieval, deduplication, and lifecycle management of device commands."""

    def __init__(self, db: Session):
        self.db = db
        self.model = CommandRecord

    def _commit(self, record: CommandRecord) -> CommandRecord:
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _intent(command_type: str, payload: dict[str, Any]) -> tuple[Any, ...]:
        if command_type in {"set_power", "power"}:
            power = payload.get("power", payload.get("state"))
            if isinstance(power, str):
                power = power.strip().lower() in {"1", "true", "on", "yes"}
            return ("set_power", bool(power))

        if command_type == "set_intensity":
            return ("set_intensity", payload.get("intensity"))

        if command_type in {"trigger_feed", "trigger"}:
            return (
                "trigger_feed",
                payload.get("duration_seconds"),
                payload.get("schedule_name"),
            )

        return (command_type, tuple(sorted(payload.items())))

    def create_command(self, payload: CommandCreateRequest) -> CommandRecord:
        record = self.model(
            requested_by=payload.requested_by,
            target_device=payload.target_device,
            command_type=payload.command_type,
            command_payload=payload.command_payload,
            status="queued",
        )
        return self._commit(record)

    def create_if_not_duplicate(
        self,
        payload: CommandCreateRequest,
        duplicate_window_seconds: int = 60,
    ) -> tuple[CommandRecord, bool]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=duplicate_window_seconds)
        recent = (
            self.db.query(self.model)
            .filter(self.model.target_device == payload.target_device)
            .filter(self.model.requested_at >= cutoff)
            .filter(self.model.status != "failed")
            .order_by(self.model.requested_at.desc())
            .limit(20)
            .all()
        )

        requested_intent = self._intent(payload.command_type, payload.command_payload)
        for record in recent:
            if self._intent(record.command_type, record.command_payload or {}) == requested_intent:
                return record, False

        return self.create_command(payload), True

    def list_recent(self, limit: int = 50) -> List[CommandRecord]:
        return (
            self.db.query(self.model)
            .order_by(self.model.requested_at.desc())
            .limit(limit)
            .all()
        )

    def list_queued(self, limit: int = 20) -> List[CommandRecord]:
        return (
            self.db.query(self.model)
            .filter(self.model.status == "queued")
            .order_by(self.model.requested_at.asc())
            .limit(limit)
            .all()
        )

    def get_last_command_for_device(self, device_key: str) -> CommandRecord | None:
        return (
            self.db.query(self.model)
            .filter(self.model.target_device == device_key)
            .order_by(self.model.requested_at.desc())
            .first()
        )

    def get_by_id(self, command_id: int) -> CommandRecord | None:
        return self.db.query(self.model).filter(self.model.id == command_id).first()

    def mark_acknowledged(self, record: CommandRecord) -> CommandRecord:
        record.status = "acknowledged"
        record.acknowledged_at = datetime.now(timezone.utc)
        return self._commit(record)

    def mark_dispatched(self, record: CommandRecord) -> CommandRecord:
        record.status = "dispatched"
        return self._commit(record)

    def mark_completed(self, record: CommandRecord) -> CommandRecord:
        now = datetime.now(timezone.utc)
        if record.acknowledged_at is None:
            record.acknowledged_at = now
        record.status = "completed"
        record.completed_at = now
        record.error_message = None
        return self._commit(record)

    def mark_failed(self, record: CommandRecord, error_message: str) -> CommandRecord:
        now = datetime.now(timezone.utc)
        record.status = "failed"
        record.completed_at = now
        record.error_message = error_message
        return self._commit(record)

    def acknowledge_command(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        return None if record is None else self.mark_acknowledged(record)

    def complete_command(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        return None if record is None else self.mark_completed(record)

    def fail_command(self, command_id: int, error_message: str) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        return None if record is None else self.mark_failed(record, error_message)
