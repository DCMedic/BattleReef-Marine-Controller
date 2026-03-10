from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.telemetry import TelemetryReading
from app.schemas.telemetry import TelemetryIngestRequest


class TelemetryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest(self, payload: TelemetryIngestRequest) -> TelemetryReading:
        record = TelemetryReading(
            sensor_key=payload.sensor_key,
            source_node=payload.source_node,
            reading_time=payload.timestamp,
            value_double=payload.value,
            unit=payload.unit,
            quality=payload.quality,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def latest(self, limit: int = 20) -> list[TelemetryReading]:
        stmt = (
            select(TelemetryReading)
            .order_by(TelemetryReading.reading_time.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())