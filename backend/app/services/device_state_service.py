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

    def set_mode(self, device_key: str, mode: str) -> DeviceStateRecord:
        record = self.get_by_device_key(device_key)

        if record is None:
            record = self.model(
                device_key=device_key,
                state_payload={"mode": mode},
                state_source="ui",
            )
            self.db.add(record)
        else:
            payload = dict(record.state_payload or {})
            payload["mode"] = mode
            record.state_payload = payload
            record.state_source = "ui"

        self.db.commit()
        self.db.refresh(record)
        return record

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
            self.db.add(record)
        else:
            merged_payload = dict(record.state_payload or {})
            merged_payload.update(state_payload)
            record.state_payload = merged_payload
            record.state_source = source

        self.db.commit()
        self.db.refresh(record)
        return record

    def list_recent(self, limit: int = 20) -> List[DeviceStateRecord]:
        return (
            self.db.query(self.model)
            .order_by(self.model.updated_at.desc())
            .limit(limit)
            .all()
        )