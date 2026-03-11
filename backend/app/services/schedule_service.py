from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.schedule import ScheduleRecord
from app.schemas.schedule import ScheduleCreateRequest, ScheduleUpdateRequest


class ScheduleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_schedules(self, limit: int = 100) -> list[ScheduleRecord]:
        stmt = (
            select(ScheduleRecord)
            .order_by(ScheduleRecord.device_key.asc(), ScheduleRecord.id.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_schedule(self, schedule_id: int) -> ScheduleRecord | None:
        stmt = (
            select(ScheduleRecord)
            .where(ScheduleRecord.id == schedule_id)
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_enabled_by_type(self, schedule_type: str) -> list[ScheduleRecord]:
        stmt = (
            select(ScheduleRecord)
            .where(ScheduleRecord.schedule_type == schedule_type)
            .where(ScheduleRecord.enabled.is_(True))
            .order_by(ScheduleRecord.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def create_schedule(self, payload: ScheduleCreateRequest) -> ScheduleRecord:
        record = ScheduleRecord(
            device_key=payload.device_key,
            schedule_type=payload.schedule_type,
            name=payload.name,
            enabled=payload.enabled,
            config_payload=payload.config_payload,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update_schedule(self, schedule_id: int, payload: ScheduleUpdateRequest) -> ScheduleRecord | None:
        record = self.get_schedule(schedule_id)
        if record is None:
            return None

        if payload.name is not None:
            record.name = payload.name
        if payload.enabled is not None:
            record.enabled = payload.enabled
        if payload.config_payload is not None:
            record.config_payload = payload.config_payload

        record.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(record)
        return record

    def seed_defaults_if_empty(self) -> list[ScheduleRecord]:
        existing = self.list_schedules(limit=1)
        if existing:
            return self.list_schedules(limit=100)

        defaults = [
            ScheduleCreateRequest(
                device_key="lights_main",
                schedule_type="lighting",
                name="Primary Lighting Window",
                enabled=True,
                config_payload={
                    "start_hour_utc": 14,
                    "end_hour_utc": 23,
                    "power_on": True,
                },
            ),
            ScheduleCreateRequest(
                device_key="feeder_main",
                schedule_type="feeding",
                name="Afternoon Feeding",
                enabled=True,
                config_payload={
                    "hour_utc": 14,
                    "duration_seconds": 5,
                },
            ),
            ScheduleCreateRequest(
                device_key="feeder_main",
                schedule_type="feeding",
                name="Evening Feeding",
                enabled=True,
                config_payload={
                    "hour_utc": 20,
                    "duration_seconds": 5,
                },
            ),
            ScheduleCreateRequest(
                device_key="wavemaker_left",
                schedule_type="flow",
                name="Left Wavemaker Day Profile",
                enabled=True,
                config_payload={
                    "day_start_hour_utc": 12,
                    "day_end_hour_utc": 23,
                    "day_intensity": "high",
                    "night_intensity": "low",
                },
            ),
            ScheduleCreateRequest(
                device_key="wavemaker_right",
                schedule_type="flow",
                name="Right Wavemaker Day Profile",
                enabled=True,
                config_payload={
                    "day_start_hour_utc": 12,
                    "day_end_hour_utc": 23,
                    "day_intensity": "high",
                    "night_intensity": "low",
                },
            ),
        ]

        created: list[ScheduleRecord] = []
        for item in defaults:
            created.append(self.create_schedule(item))

        return created