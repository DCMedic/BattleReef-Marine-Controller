from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.db.models.device_state import DeviceStateRecord


class DeviceStateService:
    def __init__(self, db: Session):
        self.db = db
        self.model = DeviceStateRecord

    def get_by_device_key(self, device_key: str) -> DeviceStateRecord | None:
        return (
            self.db.query(self.model)
            .filter(self.model.device_key == device_key)
            .first()
        )

    def get_mode(self, device_key: str) -> str:
        record = self.get_by_device_key(device_key)
        if record is None or not record.state_payload:
            return "auto"
        mode = str(record.state_payload.get("mode", "auto")).strip().lower()
        return mode if mode in {"auto", "manual"} else "auto"

    def _commit(self, record: DeviceStateRecord) -> DeviceStateRecord:
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def set_mode(self, device_key: str, mode: str) -> DeviceStateRecord:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in {"auto", "manual"}:
            raise ValueError("mode must be 'auto' or 'manual'")

        record = self.get_by_device_key(device_key)

        if record is None:
            record = self.model(
                device_key=device_key,
                state_payload={"mode": normalized_mode},
                state_source="ui",
            )
        else:
            payload = dict(record.state_payload or {})
            payload["mode"] = normalized_mode
            record.state_payload = payload
            record.state_source = "ui"

        return self._commit(record)

    def set_state(
        self,
        *,
        device_key: str,
        state_payload: dict,
        source: str,
    ) -> DeviceStateRecord:
        record = self.get_by_device_key(device_key)

        if record is None:
            record = self.model(
                device_key=device_key,
                state_payload=state_payload,
                state_source=source,
            )
        else:
            merged_payload = dict(record.state_payload or {})
            merged_payload.update(state_payload)
            record.state_payload = merged_payload
            record.state_source = source

        return self._commit(record)

    def list_recent(self, limit: int = 20) -> List[DeviceStateRecord]:
        return (
            self.db.query(self.model)
            .order_by(self.model.updated_at.desc())
            .limit(limit)
            .all()
        )
