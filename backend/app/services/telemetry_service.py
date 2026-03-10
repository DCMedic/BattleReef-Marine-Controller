from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.telemetry import TelemetryReading
from app.schemas.telemetry import TelemetryHistoryPoint, TelemetryHistorySeries, TelemetryIngestRequest


class TelemetryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest(self, payload: TelemetryIngestRequest) -> TelemetryReading:
        record = TelemetryReading(
            reading_time=payload.timestamp,
            sensor_key=payload.sensor_key,
            source_node=payload.source_node,
            value_double=payload.value,
            unit=payload.unit,
            quality=payload.quality,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def latest(self, limit: int = 100) -> list[TelemetryReading]:
        stmt = (
            select(TelemetryReading)
            .order_by(TelemetryReading.reading_time.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def latest_by_sensor(self, sensor_key: str, limit: int = 100) -> list[TelemetryReading]:
        stmt = (
            select(TelemetryReading)
            .where(TelemetryReading.sensor_key == sensor_key)
            .order_by(TelemetryReading.reading_time.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def history_for_sensor(self, sensor_key: str, limit: int = 120) -> TelemetryHistorySeries:
        rows = self.latest_by_sensor(sensor_key=sensor_key, limit=limit)
        rows = list(reversed(rows))

        unit = rows[-1].unit if rows else ""

        return TelemetryHistorySeries(
            sensor_key=sensor_key,
            unit=unit,
            points=[
                TelemetryHistoryPoint(
                    timestamp=row.reading_time,
                    value=row.value_double,
                )
                for row in rows
            ],
        )

    def history_for_sensors(self, sensor_keys: list[str], limit: int = 120) -> list[TelemetryHistorySeries]:
        return [self.history_for_sensor(sensor_key=sensor_key, limit=limit) for sensor_key in sensor_keys]