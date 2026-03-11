from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.device_state import DeviceStateRecord
from app.schemas.device_state import DeviceStateUpsertRequest


class DeviceStateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_device_key(self, device_key: str) -> DeviceStateRecord | None:
        stmt = (
            select(DeviceStateRecord)
            .where(DeviceStateRecord.device_key == device_key)
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_or_create(self, device_key: str) -> DeviceStateRecord:
        existing = self.get_by_device_key(device_key)
        if existing is not None:
            return existing

        record = DeviceStateRecord(
            device_key=device_key,
            state_payload={"mode": "auto"},
            state_source="system",
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def upsert(self, payload: DeviceStateUpsertRequest) -> DeviceStateRecord:
        record = self.get_by_device_key(payload.device_key)

        if record is None:
            record = DeviceStateRecord(
                device_key=payload.device_key,
                state_payload=payload.state_payload,
                state_source=payload.state_source,
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(record)
        else:
            merged_state = dict(record.state_payload or {})
            merged_state.update(payload.state_payload or {})
            record.state_payload = merged_state
            record.state_source = payload.state_source
            record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(record)
        return record

    def set_mode(self, device_key: str, mode: str, source: str = "dashboard.mode_control") -> DeviceStateRecord:
        record = self.get_or_create(device_key)

        merged_state = dict(record.state_payload or {})
        merged_state["mode"] = mode

        record.state_payload = merged_state
        record.state_source = source
        record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_mode(self, device_key: str) -> str:
        record = self.get_by_device_key(device_key)
        if record is None:
            return "auto"

        state_payload = record.state_payload or {}
        mode = state_payload.get("mode")

        if mode in {"auto", "manual"}:
            return str(mode)

        return "auto"

    def list_recent(self, limit: int = 100) -> list[DeviceStateRecord]:
        stmt = (
            select(DeviceStateRecord)
            .order_by(DeviceStateRecord.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())