from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.runtime_alerts import runtime_alerts
from app.core.sensor_thresholds import LEAK_EXPECTED_DRY_VALUE, LEAK_SENSOR_KEYS
from app.schemas.command import CommandCreateRequest
from app.services.command_service import CommandService
from app.services.telemetry_service import TelemetryService
from app.services.threshold_config_service import ThresholdConfigService


class SafetyWatchdogService:
    """
    Evaluates critical safety conditions and issues protective commands.

    Current protections:
    - High temperature heater cutoff
    - Low sump level return pump shutdown
    - Telemetry stale detection
    - UI-configurable threshold monitoring
    - Leak probe monitoring
    """

    def __init__(self, db: Session):
        self.db = db
        self.telemetry_service = TelemetryService(db)
        self.command_service = CommandService(db)
        self.threshold_service = ThresholdConfigService()

        self.heater_device_key = os.getenv("HEATER_DEVICE_NAME", "heater_main")
        self.return_pump_device_key = os.getenv("RETURN_PUMP_DEVICE_NAME", "return_pump_main")

        self.max_temp_f = float(os.getenv("WATCHDOG_MAX_TEMP_F", "81.5"))
        self.min_sump_level_in = float(os.getenv("WATCHDOG_MIN_SUMP_LEVEL_IN", "9.20"))
        self.telemetry_stale_seconds = int(os.getenv("WATCHDOG_TELEMETRY_STALE_SECONDS", "120"))
        self.command_cooldown_seconds = int(os.getenv("WATCHDOG_COMMAND_COOLDOWN_SECONDS", "120"))

    def evaluate(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)

        latest_records = self.telemetry_service.latest(limit=500)
        latest_by_sensor: dict[str, Any] = {}

        for record in latest_records:
            if record.sensor_key not in latest_by_sensor:
                latest_by_sensor[record.sensor_key] = record

        results: list[dict[str, Any]] = []

        results.append(self._check_telemetry_staleness(now, latest_by_sensor))
        results.append(self._check_temperature(now, latest_by_sensor))
        results.append(self._check_sump_level(now, latest_by_sensor))
        results.extend(self._check_threshold_sensors(latest_by_sensor))
        results.extend(self._check_leak_probes(latest_by_sensor))

        return {
            "evaluated_at": now.isoformat(),
            "results": results,
            "active_alerts": runtime_alerts.list_active(),
        }

    def _check_telemetry_staleness(self, now: datetime, latest_by_sensor: dict[str, Any]) -> dict[str, Any]:
        required_sensors = [
            "tank_temp_main",
            "tank_ph_main",
            "tank_salinity_main",
            "sump_level_main",
        ]

        stale_sensors: list[str] = []

        for sensor_key in required_sensors:
            record = latest_by_sensor.get(sensor_key)

            if record is None:
                stale_sensors.append(sensor_key)
                continue

            age_seconds = (now - record.reading_time).total_seconds()

            if age_seconds > self.telemetry_stale_seconds:
                stale_sensors.append(sensor_key)

        if stale_sensors:
            runtime_alerts.upsert(
                key="telemetry_stale",
                severity="critical",
                title="Telemetry Stale",
                message="One or more critical telemetry feeds are stale or missing.",
                source="safety_watchdog",
                metadata={
                    "stale_sensors": stale_sensors,
                    "threshold_seconds": self.telemetry_stale_seconds,
                },
            )
            return {
                "check": "telemetry_stale",
                "status": "alert",
                "stale_sensors": stale_sensors,
            }

        runtime_alerts.clear("telemetry_stale")
        return {
            "check": "telemetry_stale",
            "status": "ok",
        }

    def _check_temperature(self, now: datetime, latest_by_sensor: dict[str, Any]) -> dict[str, Any]:
        record = latest_by_sensor.get("tank_temp_main")

        if record is None:
            return {
                "check": "high_temperature",
                "status": "no_data",
            }

        temp_f = float(record.value_double)

        if temp_f >= self.max_temp_f:
            command_id = self._issue_protective_command_if_needed(
                device_key=self.heater_device_key,
                command_type="set_power",
                command_payload={
                    "power": False,
                    "reason": "watchdog_high_temperature_cutoff",
                    "temperature_f": temp_f,
                    "max_temp_f": self.max_temp_f,
                },
                now=now,
            )

            runtime_alerts.upsert(
                key="high_temperature",
                severity="critical",
                title="High Temperature Cutoff",
                message="Tank temperature exceeded the safety threshold. Heater shutdown requested.",
                source="safety_watchdog",
                metadata={
                    "temperature_f": temp_f,
                    "max_temp_f": self.max_temp_f,
                    "heater_device_key": self.heater_device_key,
                    "command_id": command_id,
                },
            )

            return {
                "check": "high_temperature",
                "status": "protective_action_requested",
                "temperature_f": temp_f,
                "command_id": command_id,
            }

        runtime_alerts.clear("high_temperature")
        return {
            "check": "high_temperature",
            "status": "ok",
            "temperature_f": temp_f,
        }

    def _check_sump_level(self, now: datetime, latest_by_sensor: dict[str, Any]) -> dict[str, Any]:
        record = latest_by_sensor.get("sump_level_main")

        if record is None:
            return {
                "check": "low_sump_level",
                "status": "no_data",
            }

        sump_level_in = float(record.value_double)

        if sump_level_in <= self.min_sump_level_in:
            command_id = self._issue_protective_command_if_needed(
                device_key=self.return_pump_device_key,
                command_type="set_power",
                command_payload={
                    "power": False,
                    "reason": "watchdog_low_sump_level_cutoff",
                    "sump_level_in": sump_level_in,
                    "min_sump_level_in": self.min_sump_level_in,
                },
                now=now,
            )

            runtime_alerts.upsert(
                key="low_sump_level",
                severity="critical",
                title="Low Sump Level Protection",
                message="Sump level dropped below the safety threshold. Return pump shutdown requested.",
                source="safety_watchdog",
                metadata={
                    "sump_level_in": sump_level_in,
                    "min_sump_level_in": self.min_sump_level_in,
                    "return_pump_device_key": self.return_pump_device_key,
                    "command_id": command_id,
                },
            )

            return {
                "check": "low_sump_level",
                "status": "protective_action_requested",
                "sump_level_in": sump_level_in,
                "command_id": command_id,
            }

        runtime_alerts.clear("low_sump_level")
        return {
            "check": "low_sump_level",
            "status": "ok",
            "sump_level_in": sump_level_in,
        }

    def _check_threshold_sensors(self, latest_by_sensor: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        thresholds = self.threshold_service.get_effective_thresholds()

        for sensor_key, config in thresholds.items():
            if not bool(config.get("enabled", True)):
                runtime_alerts.clear(f"threshold_{sensor_key}")
                results.append({
                    "check": sensor_key,
                    "status": "disabled",
                })
                continue

            record = latest_by_sensor.get(sensor_key)

            if record is None:
                results.append({
                    "check": sensor_key,
                    "status": "no_data",
                })
                continue

            value = float(record.value_double)
            min_value = config.get("min")
            max_value = config.get("max")
            severity = config.get("severity", "warning")
            label = config.get("label", sensor_key)
            unit = config.get("unit")

            too_low = min_value is not None and value < min_value
            too_high = max_value is not None and value > max_value

            alert_key = f"threshold_{sensor_key}"

            if too_low or too_high:
                direction = "below" if too_low else "above"
                boundary = min_value if too_low else max_value

                runtime_alerts.upsert(
                    key=alert_key,
                    severity=severity,
                    title=f"{label} Threshold Alert",
                    message=f"{label} is {direction} the configured threshold.",
                    source="safety_watchdog",
                    metadata={
                        "sensor_key": sensor_key,
                        "value": value,
                        "unit": unit,
                        "direction": direction,
                        "threshold": boundary,
                    },
                )

                results.append({
                    "check": sensor_key,
                    "status": "alert",
                    "value": value,
                    "direction": direction,
                    "threshold": boundary,
                })
            else:
                runtime_alerts.clear(alert_key)
                results.append({
                    "check": sensor_key,
                    "status": "ok",
                    "value": value,
                })

        return results

    def _check_leak_probes(self, latest_by_sensor: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for sensor_key in LEAK_SENSOR_KEYS:
            record = latest_by_sensor.get(sensor_key)

            if record is None:
                results.append({
                    "check": sensor_key,
                    "status": "no_data",
                })
                continue

            raw_value = str(record.value_double if record.value_double is not None else record.value_text or "").lower()
            alert_key = f"leak_{sensor_key}"

            if raw_value and raw_value != LEAK_EXPECTED_DRY_VALUE:
                runtime_alerts.upsert(
                    key=alert_key,
                    severity="critical",
                    title="Leak Detected",
                    message=f"{sensor_key} indicates a leak or wet condition.",
                    source="safety_watchdog",
                    metadata={
                        "sensor_key": sensor_key,
                        "value": raw_value,
                        "expected": LEAK_EXPECTED_DRY_VALUE,
                    },
                )

                results.append({
                    "check": sensor_key,
                    "status": "alert",
                    "value": raw_value,
                })
            else:
                runtime_alerts.clear(alert_key)
                results.append({
                    "check": sensor_key,
                    "status": "ok",
                    "value": raw_value or LEAK_EXPECTED_DRY_VALUE,
                })

        return results

    def _issue_protective_command_if_needed(
        self,
        *,
        device_key: str,
        command_type: str,
        command_payload: dict[str, Any],
        now: datetime,
    ) -> int | None:
        last_command = self.command_service.get_last_command_for_device(device_key)

        if last_command and last_command.requested_at:
            age_seconds = (now - last_command.requested_at).total_seconds()
            if age_seconds < self.command_cooldown_seconds:
                return last_command.id

        record = self.command_service.create_command(
            CommandCreateRequest(
                requested_by="safety_watchdog",
                target_device=device_key,
                command_type=command_type,
                command_payload=command_payload,
            )
        )
        return record.id