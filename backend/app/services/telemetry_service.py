from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.db.models.telemetry import TelemetryRecord
from app.schemas.telemetry import TelemetryIngestRequest


def _parse_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _record_numeric_value(record: TelemetryRecord) -> float:
    return float(record.value_double)


class TelemetryService:
    def __init__(self, db: Session):
        self.db = db
        self.model = TelemetryRecord

    def ingest(self, payload: TelemetryIngestRequest) -> TelemetryRecord:
        parsed_time = _parse_timestamp(payload.timestamp)

        record = self.model(
            sensor_key=payload.sensor_key,
            source_node=payload.source_node,
            reading_time=parsed_time,
            value_double=float(payload.value),
            unit=payload.unit,
            quality=payload.quality,
        )

        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        except Exception:
            self.db.rollback()
            raise

        return record

    def latest(self, limit: int = 100) -> list[TelemetryRecord]:
        return (
            self.db.query(self.model)
            .order_by(desc(self.model.reading_time))
            .limit(limit)
            .all()
        )

    def history_for_sensors(
        self,
        sensor_keys: list[str],
        limit: int = 120,
    ) -> dict[str, list[dict[str, Any]]]:
        if not sensor_keys:
            return {}

        records = (
            self.db.query(self.model)
            .filter(self.model.sensor_key.in_(sensor_keys))
            .order_by(desc(self.model.reading_time))
            .limit(max(limit * len(sensor_keys), limit))
            .all()
        )

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for record in records:
            grouped[record.sensor_key].append(
                {
                    "timestamp": record.reading_time.isoformat(),
                    "value": _record_numeric_value(record),
                    "unit": record.unit,
                    "quality": record.quality,
                }
            )

        final: dict[str, list[dict[str, Any]]] = {}

        for sensor_key in sensor_keys:
            points = list(reversed(grouped.get(sensor_key, [])[:limit]))
            final[sensor_key] = points

        return final

    def window_for_sensor(
        self,
        *,
        sensor_key: str,
        days: int = 3,
        max_points: int = 288,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        start_time = end_time - timedelta(days=days)

        records = (
            self.db.query(self.model)
            .filter(self.model.sensor_key == sensor_key)
            .filter(self.model.reading_time >= start_time)
            .filter(self.model.reading_time <= end_time)
            .order_by(asc(self.model.reading_time))
            .all()
        )

        if not records:
            return {
                "sensor_key": sensor_key,
                "unit": None,
                "days": days,
                "max_points": max_points,
                "points": [],
                "latest_value": None,
                "latest_timestamp": None,
                "min_value": None,
                "max_value": None,
            }

        unit = records[-1].unit

        normalized_points = [
            {
                "timestamp": record.reading_time.isoformat(),
                "value": _record_numeric_value(record),
            }
            for record in records
        ]

        reduced_points = self._downsample_points(normalized_points, max_points=max_points)
        values = [float(point["value"]) for point in reduced_points]

        return {
            "sensor_key": sensor_key,
            "unit": unit,
            "days": days,
            "max_points": max_points,
            "points": reduced_points,
            "latest_value": reduced_points[-1]["value"],
            "latest_timestamp": reduced_points[-1]["timestamp"],
            "min_value": min(values),
            "max_value": max(values),
        }

    def _downsample_points(
        self,
        points: list[dict[str, Any]],
        *,
        max_points: int,
    ) -> list[dict[str, Any]]:
        if len(points) <= max_points:
            return points

        bucket_size = len(points) / max_points
        reduced: list[dict[str, Any]] = []

        for bucket_index in range(max_points):
            start = int(math.floor(bucket_index * bucket_size))
            end = int(math.floor((bucket_index + 1) * bucket_size))
            bucket = points[start:end] if end > start else [points[start]]

            if not bucket:
                continue

            avg_value = sum(float(item["value"]) for item in bucket) / len(bucket)
            timestamp = bucket[-1]["timestamp"]

            reduced.append(
                {
                    "timestamp": timestamp,
                    "value": round(avg_value, 3),
                }
            )

        return reduced
