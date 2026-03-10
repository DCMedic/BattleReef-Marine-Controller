from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.device_state import DeviceStateRecord
from app.schemas.device_state import DeviceStateUpsertRequest


class DeviceStateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_device_key(self, device_key: str) -> DeviceStateRecord | None:
        stmt = select(DeviceStateRecord).where(DeviceStateRecord.device_key == device_key).limit(1)
        return self.db.scalar(stmt)

    def list_all(self, limit: int = 100) -> list[DeviceStateRecord]:
        stmt = (
            select(DeviceStateRecord)
            .order_by(DeviceStateRecord.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def upsert(self, payload: DeviceStateUpsertRequest) -> DeviceStateRecord:
        record = self.get_by_device_key(payload.device_key)

        if record is None:
            record = DeviceStateRecord(
                device_key=payload.device_key,
                state_payload=payload.state_payload,
                state_source=payload.state_source,
            )
            self.db.add(record)
        else:
            record.state_payload = payload.state_payload
            record.state_source = payload.state_source
            record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(record)
        return record