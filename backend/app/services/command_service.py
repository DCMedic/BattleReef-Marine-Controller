from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, List

from sqlalchemy.orm import Session

from app.db.models.command import CommandRecord
from app.schemas.command import CommandCreateRequest


DELIVERY_POLICY_DEFAULTS: dict[str, tuple[int, int]] = {
    "safety_critical": (4, 5),
    "state_setting": (3, 10),
    "one_shot": (1, 15),
    "best_effort": (2, 15),
}


class CommandService:
    """Handles creation, retrieval, deduplication, delivery, and verification of device commands."""

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

    @staticmethod
    def delivery_policy_for(payload: CommandCreateRequest) -> str:
        if payload.requested_by == "safety_watchdog" and payload.command_type in {"set_power", "power"}:
            return "safety_critical"
        if payload.command_type in {"set_power", "power", "set_intensity"}:
            return "state_setting"
        if payload.command_type in {"trigger_feed", "trigger"}:
            return "one_shot"
        return "best_effort"

    @staticmethod
    def retry_safe(policy: str) -> bool:
        return policy in {"safety_critical", "state_setting", "best_effort"}

    @staticmethod
    def timeout_seconds_for(policy: str) -> int:
        return DELIVERY_POLICY_DEFAULTS.get(policy, DELIVERY_POLICY_DEFAULTS["best_effort"])[1]

    def create_command(self, payload: CommandCreateRequest) -> CommandRecord:
        policy = self.delivery_policy_for(payload)
        max_attempts, _ = DELIVERY_POLICY_DEFAULTS[policy]
        record = self.model(
            requested_by=payload.requested_by,
            target_device=payload.target_device,
            command_type=payload.command_type,
            command_payload=payload.command_payload,
            delivery_policy=policy,
            status="queued",
            max_attempts=max_attempts,
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
            .filter(self.model.status.notin_(["failed", "timeout"]))
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
        return self.db.query(self.model).order_by(self.model.requested_at.desc()).limit(limit).all()

    def list_dispatchable(self, limit: int = 20) -> List[CommandRecord]:
        return (
            self.db.query(self.model)
            .filter(self.model.status.in_(["queued", "retry_pending"]))
            .order_by(self.model.requested_at.asc())
            .limit(limit)
            .all()
        )

    def list_queued(self, limit: int = 20) -> List[CommandRecord]:
        return self.list_dispatchable(limit=limit)

    def list_expired_dispatched(self, now: datetime | None = None, limit: int = 100) -> List[CommandRecord]:
        now = now or datetime.now(timezone.utc)
        return (
            self.db.query(self.model)
            .filter(self.model.status.in_(["dispatched", "acknowledged"]))
            .filter(self.model.ack_deadline.is_not(None))
            .filter(self.model.ack_deadline <= now)
            .order_by(self.model.ack_deadline.asc())
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
        if record.status not in {"dispatched", "acknowledged"}:
            raise ValueError(f"command_not_acknowledgeable_from_{record.status}")
        record.status = "acknowledged"
        record.acknowledged_at = datetime.now(timezone.utc)
        return self._commit(record)

    def mark_dispatched(self, record: CommandRecord) -> CommandRecord:
        if record.status not in {"queued", "retry_pending"}:
            raise ValueError(f"command_not_dispatchable_from_{record.status}")
        now = datetime.now(timezone.utc)
        record.status = "dispatched"
        record.dispatch_attempts = int(record.dispatch_attempts or 0) + 1
        record.last_dispatched_at = now
        record.ack_deadline = now + timedelta(seconds=self.timeout_seconds_for(record.delivery_policy))
        record.error_message = None
        return self._commit(record)

    def mark_retry_pending(self, record: CommandRecord, reason: str) -> CommandRecord:
        record.status = "retry_pending"
        record.ack_deadline = None
        record.error_message = reason
        return self._commit(record)

    def mark_verified(self, record: CommandRecord) -> CommandRecord:
        record.status = "verified"
        record.verified_at = datetime.now(timezone.utc)
        record.ack_deadline = None
        return self._commit(record)

    def mark_completed(self, record: CommandRecord) -> CommandRecord:
        now = datetime.now(timezone.utc)
        if record.acknowledged_at is None:
            record.acknowledged_at = now
        if record.verified_at is None:
            record.verified_at = now
        record.status = "completed"
        record.completed_at = now
        record.ack_deadline = None
        record.error_message = None
        return self._commit(record)

    def mark_timeout(self, record: CommandRecord, error_message: str) -> CommandRecord:
        record.status = "timeout"
        record.completed_at = datetime.now(timezone.utc)
        record.ack_deadline = None
        record.error_message = error_message
        return self._commit(record)

    def mark_failed(self, record: CommandRecord, error_message: str) -> CommandRecord:
        record.status = "failed"
        record.completed_at = datetime.now(timezone.utc)
        record.ack_deadline = None
        record.error_message = error_message
        return self._commit(record)

    @staticmethod
    def verify_ack_state(record: CommandRecord, state_payload: dict[str, Any]) -> tuple[bool, str]:
        command_type = record.command_type
        expected = record.command_payload or {}

        if command_type in {"set_power", "power"}:
            expected_power = expected.get("power", expected.get("state"))
            actual_power = state_payload.get("power", state_payload.get("state"))
            if isinstance(expected_power, str):
                expected_power = expected_power.strip().lower() in {"1", "true", "on", "yes"}
            if isinstance(actual_power, str):
                actual_power = actual_power.strip().lower() in {"1", "true", "on", "yes"}
            if actual_power is None:
                return False, "ack_missing_power_state"
            if bool(actual_power) != bool(expected_power):
                return False, "ack_power_state_mismatch"
            return True, "power_state_verified"

        if command_type == "set_intensity":
            if "intensity" not in state_payload:
                return False, "ack_missing_intensity"
            if state_payload.get("intensity") != expected.get("intensity"):
                return False, "ack_intensity_mismatch"
            return True, "intensity_verified"

        if command_type in {"trigger_feed", "trigger"}:
            if state_payload.get("success") is False:
                return False, "one_shot_device_reported_failure"
            return True, "one_shot_acknowledged"

        if state_payload.get("success") is False:
            return False, "device_reported_failure"
        return True, "acknowledged"

    def acknowledge_command(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        return None if record is None else self.mark_acknowledged(record)

    def complete_command(self, command_id: int) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        return None if record is None else self.mark_completed(record)

    def fail_command(self, command_id: int, error_message: str) -> CommandRecord | None:
        record = self.get_by_id(command_id)
        return None if record is None else self.mark_failed(record, error_message)
