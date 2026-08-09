from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models.telemetry import TelemetryReading


class TelemetryPlausibilityService:
    """Evaluate whether a reading is physically plausible before automation trusts it."""

    ABSOLUTE_BOUNDS: dict[str, tuple[float, float]] = {
        "tank_temp_main": (50.0, 100.0),
        "tank_ph_main": (5.5, 9.5),
        "tank_salinity_main": (20.0, 45.0),
        "sump_level_main": (0.0, 24.0),
        "flow_return_main": (0.0, 2000.0),
        "flow_manifold_main": (0.0, 1000.0),
        "power_monitor_main": (0.0, 2500.0),
        "power_heater_main": (0.0, 1000.0),
        "dissolved_oxygen_main": (0.0, 20.0),
        "orp_main": (-500.0, 1000.0),
    }

    MAX_STEP: dict[str, float] = {
        "tank_temp_main": 2.0,
        "tank_ph_main": 0.35,
        "tank_salinity_main": 1.5,
        "sump_level_main": 1.5,
        "dissolved_oxygen_main": 1.5,
        "orp_main": 125.0,
    }

    def __init__(self, db: Session):
        self.db = db

    def evaluate(self, sensor_key: str, value: float, source_node: str, reading_time: datetime) -> dict[str, Any]:
        reasons: list[str] = []
        bounds = self.ABSOLUTE_BOUNDS.get(sensor_key)
        if bounds and not (bounds[0] <= value <= bounds[1]):
            reasons.append(f"outside_absolute_bounds:{bounds[0]}:{bounds[1]}")

        previous = (
            self.db.query(TelemetryReading)
            .filter(
                TelemetryReading.sensor_key == sensor_key,
                TelemetryReading.source_node == source_node,
                TelemetryReading.quality == "good",
            )
            .order_by(desc(TelemetryReading.reading_time))
            .first()
        )
        max_step = self.MAX_STEP.get(sensor_key)
        if previous is not None and max_step is not None:
            age = max(0.0, (reading_time - previous.reading_time).total_seconds())
            if age <= 300 and abs(value - float(previous.value_double)) > max_step:
                reasons.append(f"implausible_step_change:{round(abs(value - float(previous.value_double)), 4)}")

        if sensor_key == "tank_salinity_main" and previous is not None and abs(value - float(previous.value_double)) >= 1.0:
            cutoff = reading_time - timedelta(minutes=5)
            sump = (
                self.db.query(TelemetryReading)
                .filter(
                    TelemetryReading.sensor_key == "sump_level_main",
                    TelemetryReading.source_node == source_node,
                    TelemetryReading.reading_time >= cutoff,
                    TelemetryReading.quality == "good",
                )
                .order_by(desc(TelemetryReading.reading_time))
                .limit(2)
                .all()
            )
            if len(sump) >= 2 and abs(float(sump[0].value_double) - float(sump[-1].value_double)) < 0.25:
                reasons.append("salinity_change_not_supported_by_sump_level")

        return {"plausible": not reasons, "quality": "good" if not reasons else "suspect", "reasons": reasons}
