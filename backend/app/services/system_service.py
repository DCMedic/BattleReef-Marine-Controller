from datetime import datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.models.command import CommandRecord
from app.db.models.device_state import DeviceStateRecord
from app.db.models.telemetry import TelemetryReading
from app.schemas.system import (
    DeviceStateSummary,
    SensorLatestReading,
    SystemCounts,
    SystemSummaryResponse,
    TimescaleStatus,
)


class SystemService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _count_telemetry(self) -> int:
        stmt = select(func.count()).select_from(TelemetryReading)
        return int(self.db.scalar(stmt) or 0)

    def _count_commands_total(self) -> int:
        stmt = select(func.count()).select_from(CommandRecord)
        return int(self.db.scalar(stmt) or 0)

    def _count_commands_by_status(self, status: str) -> int:
        stmt = select(func.count()).select_from(CommandRecord).where(CommandRecord.status == status)
        return int(self.db.scalar(stmt) or 0)

    def _count_device_states(self) -> int:
        stmt = select(func.count()).select_from(DeviceStateRecord)
        return int(self.db.scalar(stmt) or 0)

    def get_counts(self) -> SystemCounts:
        return SystemCounts(
            telemetry_readings=self._count_telemetry(),
            commands_total=self._count_commands_total(),
            commands_queued=self._count_commands_by_status("queued"),
            commands_dispatched=self._count_commands_by_status("dispatched"),
            commands_completed=self._count_commands_by_status("completed"),
            commands_failed=self._count_commands_by_status("failed"),
            device_states=self._count_device_states(),
        )

    def get_latest_readings(self) -> list[SensorLatestReading]:
        sensor_keys_stmt = select(TelemetryReading.sensor_key).distinct()
        sensor_keys = [row for row in self.db.scalars(sensor_keys_stmt).all()]

        items: list[SensorLatestReading] = []

        for sensor_key in sensor_keys:
            stmt = (
                select(TelemetryReading)
                .where(TelemetryReading.sensor_key == sensor_key)
                .order_by(TelemetryReading.reading_time.desc())
                .limit(1)
            )
            record = self.db.scalar(stmt)
            if record is not None:
                items.append(
                    SensorLatestReading(
                        sensor_key=record.sensor_key,
                        source_node=record.source_node,
                        reading_time=record.reading_time,
                        value=record.value_double,
                        unit=record.unit,
                        quality=record.quality,
                    )
                )

        items.sort(key=lambda x: x.sensor_key)
        return items

    def get_device_states(self) -> list[DeviceStateSummary]:
        stmt = (
            select(DeviceStateRecord)
            .order_by(DeviceStateRecord.updated_at.desc())
            .limit(100)
        )
        records = list(self.db.scalars(stmt).all())

        return [
            DeviceStateSummary(
                device_key=record.device_key,
                state_payload=record.state_payload,
                state_source=record.state_source,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    def get_timescale_status(self) -> TimescaleStatus:
        extension_stmt = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_extension
                WHERE extname = 'timescaledb'
            )
            """
        )
        hypertable_stmt = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'telemetry_readings'
            )
            """
        )

        extension_installed = bool(self.db.execute(extension_stmt).scalar())
        telemetry_is_hypertable = bool(self.db.execute(hypertable_stmt).scalar())

        return TimescaleStatus(
            extension_installed=extension_installed,
            telemetry_is_hypertable=telemetry_is_hypertable,
        )

    def ensure_timescale(self) -> dict:
        before = self.get_timescale_status()

        if not before.extension_installed:
            return {
                "ok": False,
                "message": "TimescaleDB extension is not installed.",
                "before": before.model_dump(),
                "after": before.model_dump(),
            }

        if before.telemetry_is_hypertable:
            return {
                "ok": True,
                "message": "telemetry_readings is already a hypertable.",
                "before": before.model_dump(),
                "after": before.model_dump(),
            }

        try:
            self.db.execute(text("ALTER TABLE telemetry_readings DROP CONSTRAINT IF EXISTS telemetry_readings_pkey"))
            self.db.execute(
                text(
                    """
                    ALTER TABLE telemetry_readings
                    ADD CONSTRAINT telemetry_readings_pkey
                    PRIMARY KEY (reading_time, id)
                    """
                )
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            after = self.get_timescale_status()
            return {
                "ok": False,
                "message": f"primary key adjustment failed: {exc}",
                "before": before.model_dump(),
                "after": after.model_dump(),
            }

        try:
            self.db.execute(
                text(
                    """
                    SELECT create_hypertable(
                        'telemetry_readings',
                        'reading_time',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    )
                    """
                )
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            after = self.get_timescale_status()
            return {
                "ok": False,
                "message": f"create_hypertable failed: {exc}",
                "before": before.model_dump(),
                "after": after.model_dump(),
            }

        try:
            self.db.execute(
                text(
                    """
                    ALTER TABLE telemetry_readings
                    SET (
                        timescaledb.compress,
                        timescaledb.compress_segmentby = 'sensor_key',
                        timescaledb.compress_orderby = 'reading_time DESC'
                    )
                    """
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

        try:
            self.db.execute(
                text(
                    """
                    SELECT add_compression_policy(
                        'telemetry_readings',
                        INTERVAL '7 days',
                        if_not_exists => TRUE
                    )
                    """
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

        try:
            self.db.execute(
                text(
                    """
                    SELECT add_retention_policy(
                        'telemetry_readings',
                        INTERVAL '30 days',
                        if_not_exists => TRUE
                    )
                    """
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()

        after = self.get_timescale_status()

        return {
            "ok": after.telemetry_is_hypertable,
            "message": "Timescale ensure operation completed.",
            "before": before.model_dump(),
            "after": after.model_dump(),
        }

    def get_summary(self) -> SystemSummaryResponse:
        return SystemSummaryResponse(
            generated_at=datetime.now(timezone.utc),
            counts=self.get_counts(),
            latest_readings=self.get_latest_readings(),
            device_states=self.get_device_states(),
            timescale_status=self.get_timescale_status(),
        )