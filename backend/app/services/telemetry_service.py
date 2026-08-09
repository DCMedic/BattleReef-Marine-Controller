from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.runtime_alerts import runtime_alerts
from app.db.models.telemetry import TelemetryRecord
from app.schemas.audit import AuditEventCreate
from app.schemas.telemetry import TelemetryIngestRequest
from app.services.audit_service import AuditService
from app.services.telemetry_plausibility_service import TelemetryPlausibilityService


def _parse_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
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
        plausibility = TelemetryPlausibilityService(self.db).evaluate(payload.sensor_key, float(payload.value), payload.source_node, parsed_time)
        effective_quality = payload.quality if payload.quality.lower() != "good" else plausibility["quality"]
        record = self.model(sensor_key=payload.sensor_key, source_node=payload.source_node, reading_time=parsed_time, value_double=float(payload.value), unit=payload.unit, quality=effective_quality)
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        except Exception:
            self.db.rollback()
            raise

        alert_key = f"telemetry_plausibility_{payload.source_node}_{payload.sensor_key}"
        active_keys = {item["key"] for item in runtime_alerts.list_active()}
        was_active = alert_key in active_keys
        if not plausibility["plausible"]:
            runtime_alerts.upsert(key=alert_key, severity="warning", title="Telemetry Quarantined", message=f"{payload.sensor_key} produced an implausible reading; automation will not trust it.", source="telemetry_plausibility", metadata={"sensor_key": payload.sensor_key, "source_node": payload.source_node, "value": float(payload.value), "reasons": plausibility["reasons"]})
            if not was_active:
                AuditService(self.db).append(AuditEventCreate(event_type="telemetry.reading_quarantined", severity="warning", outcome="quarantined", source="telemetry_plausibility", actor_type="mqtt_identity", actor_id=payload.source_node, entity_type="sensor", entity_id=payload.sensor_key, message=f"Telemetry reading from {payload.sensor_key} was stored as suspect and excluded from trusted automation.", details={"value": float(payload.value), "unit": payload.unit, "reasons": plausibility["reasons"]}))
        elif runtime_alerts.clear(alert_key) and was_active:
            AuditService(self.db).append(AuditEventCreate(event_type="telemetry.sensor_plausibility_recovered", severity="info", outcome="recovered", source="telemetry_plausibility", actor_type="mqtt_identity", actor_id=payload.source_node, entity_type="sensor", entity_id=payload.sensor_key, message=f"{payload.sensor_key} returned to plausible trusted telemetry.", details={"value": float(payload.value), "unit": payload.unit}))
        return record

    def latest(self, limit: int = 100) -> list[TelemetryRecord]:
        return self.db.query(self.model).order_by(desc(self.model.reading_time)).limit(limit).all()

    def latest_by_sensor(self, sensor_key: str, limit: int = 1, trusted_only: bool = False) -> list[TelemetryRecord]:
        query = self.db.query(self.model).filter(self.model.sensor_key == sensor_key)
        if trusted_only:
            query = query.filter(self.model.quality == "good")
        return query.order_by(desc(self.model.reading_time)).limit(limit).all()

    def history_for_sensors(self, sensor_keys: list[str], limit: int = 120) -> dict[str, list[dict[str, Any]]]:
        if not sensor_keys:
            return {}
        records = self.db.query(self.model).filter(self.model.sensor_key.in_(sensor_keys)).order_by(desc(self.model.reading_time)).limit(max(limit * len(sensor_keys), limit)).all()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[record.sensor_key].append({"timestamp": record.reading_time.isoformat(), "value": _record_numeric_value(record), "unit": record.unit, "quality": record.quality})
        return {sensor_key: list(reversed(grouped.get(sensor_key, [])[:limit])) for sensor_key in sensor_keys}

    def window_for_sensor(self, *, sensor_key: str, days: int = 3, max_points: int = 288, end_time: datetime | None = None) -> dict[str, Any]:
        end_time = end_time or datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        records = self.db.query(self.model).filter(self.model.sensor_key == sensor_key, self.model.reading_time >= start_time, self.model.reading_time <= end_time).order_by(asc(self.model.reading_time)).all()
        if not records:
            return {"sensor_key": sensor_key, "unit": None, "days": days, "max_points": max_points, "points": [], "latest_value": None, "latest_timestamp": None, "min_value": None, "max_value": None}
        reduced_points = self._downsample_points([{"timestamp": r.reading_time.isoformat(), "value": _record_numeric_value(r)} for r in records], max_points=max_points)
        values = [float(point["value"]) for point in reduced_points]
        return {"sensor_key": sensor_key, "unit": records[-1].unit, "days": days, "max_points": max_points, "points": reduced_points, "latest_value": reduced_points[-1]["value"], "latest_timestamp": reduced_points[-1]["timestamp"], "min_value": min(values), "max_value": max(values)}

    def _downsample_points(self, points: list[dict[str, Any]], *, max_points: int) -> list[dict[str, Any]]:
        if len(points) <= max_points:
            return points
        bucket_size = len(points) / max_points
        reduced: list[dict[str, Any]] = []
        for bucket_index in range(max_points):
            start = int(math.floor(bucket_index * bucket_size))
            end = int(math.floor((bucket_index + 1) * bucket_size))
            bucket = points[start:end] if end > start else [points[start]]
            if bucket:
                reduced.append({"timestamp": bucket[-1]["timestamp"], "value": round(sum(float(item["value"]) for item in bucket) / len(bucket), 3)})
        return reduced
