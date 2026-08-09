from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.runtime_alerts import runtime_alerts
from app.db.models.device_state import DeviceStateRecord
from app.db.models.telemetry import TelemetryReading
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService


class PhysicalVerificationService:
    """Cross-check device-reported state and critical sensors against fresh independent evidence."""

    RETURN_FLOW_ON_MIN_GPH = 150.0
    RETURN_PUMP_POWER_ON_MIN_W = 5.0
    RETURN_PUMP_RPM_ON_MIN = 300.0
    HEATER_POWER_ON_MIN_W = 10.0
    TEMP_PAIR_MAX_DELTA_F = 1.5
    SUMP_LEVEL_PAIR_MAX_DELTA_IN = 0.5
    MAX_EVIDENCE_AGE_SECONDS = 120

    def __init__(self, db: Session):
        self.db = db

    def _latest_sensor(self, sensor_key: str) -> TelemetryReading | None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.MAX_EVIDENCE_AGE_SECONDS)
        return (
            self.db.query(TelemetryReading)
            .filter(
                TelemetryReading.sensor_key == sensor_key,
                TelemetryReading.quality == "good",
                TelemetryReading.reading_time >= cutoff,
            )
            .order_by(desc(TelemetryReading.reading_time))
            .first()
        )

    def _device_state(self, device_key: str) -> DeviceStateRecord | None:
        record = self.db.query(DeviceStateRecord).filter(DeviceStateRecord.device_key == device_key).first()
        if record is None or record.updated_at is None:
            return None
        age = (datetime.now(timezone.utc) - record.updated_at).total_seconds()
        return record if age <= self.MAX_EVIDENCE_AGE_SECONDS else None

    @staticmethod
    def _power(state: DeviceStateRecord | None) -> bool | None:
        if state is None or not isinstance(state.state_payload, dict):
            return None
        value = state.state_payload.get("power")
        return value if isinstance(value, bool) else None

    @classmethod
    def verify_binary_with_signal(
        cls,
        reported_on: bool | None,
        signal_value: float | None,
        on_threshold: float,
    ) -> tuple[str, str]:
        if reported_on is None or signal_value is None:
            return "unknown", "missing_or_stale_independent_evidence"
        physically_on = signal_value >= on_threshold
        if reported_on and not physically_on:
            return "critical", "device_reports_on_but_independent_signal_is_off"
        if not reported_on and physically_on:
            return "critical", "device_reports_off_but_independent_signal_is_on"
        return "verified", "reported_state_matches_independent_signal"

    @staticmethod
    def verify_sensor_pair(
        primary_value: float | None,
        verify_value: float | None,
        max_delta: float,
    ) -> tuple[str, str, float | None]:
        if primary_value is None or verify_value is None:
            return "unknown", "missing_or_stale_redundant_sensor_evidence", None
        delta = abs(primary_value - verify_value)
        if delta > max_delta * 2:
            return "critical", "redundant_sensor_disagreement_extreme", delta
        if delta > max_delta:
            return "degraded", "redundant_sensor_disagreement", delta
        return "verified", "redundant_sensors_agree", delta

    def evaluate(self) -> list[dict[str, Any]]:
        results = [
            self._verify_return_pump(),
            self._verify_heater_power_signature(),
            self._verify_temperature_pair(),
            self._verify_sump_level_pair(),
        ]
        for result in results:
            self._sync_result(result)
        return results

    def _verify_return_pump(self) -> dict[str, Any]:
        state = self._device_state("return_pump_main") or self._device_state("pump_return_main")
        reported_on = self._power(state)
        flow = self._latest_sensor("flow_return_main")
        power = self._latest_sensor("power_return_pump_main")
        rpm = self._latest_sensor("rpm_return_pump_main")

        flow_gph = float(flow.value_double) if flow is not None else None
        power_w = float(power.value_double) if power is not None else None
        rpm_value = float(rpm.value_double) if rpm is not None else None

        evidence = {
            "reported_power": reported_on,
            "flow_gph": flow_gph,
            "power_w": power_w,
            "rpm": rpm_value,
        }
        if reported_on is None:
            return {
                "key": "return_pump_multisignal",
                "device_key": "return_pump_main",
                "status": "unknown",
                "reason": "missing_or_stale_device_state",
                **evidence,
            }

        available = 0
        contradictions: list[str] = []

        if power_w is not None:
            available += 1
            electrically_on = power_w >= self.RETURN_PUMP_POWER_ON_MIN_W
            if reported_on != electrically_on:
                contradictions.append("pump_power_state_contradiction")

        if flow_gph is not None:
            available += 1
            hydraulically_on = flow_gph >= self.RETURN_FLOW_ON_MIN_GPH
            if reported_on and not hydraulically_on:
                contradictions.append("pump_reports_on_but_flow_is_low")
            elif not reported_on and hydraulically_on:
                contradictions.append("pump_reports_off_but_flow_continues")

        if rpm_value is not None:
            available += 1
            rotating = rpm_value >= self.RETURN_PUMP_RPM_ON_MIN
            if reported_on != rotating:
                contradictions.append("pump_rpm_state_contradiction")

        if available == 0:
            status, reason = "unknown", "missing_or_stale_independent_evidence"
        elif contradictions:
            status, reason = "critical", ";".join(contradictions)
        elif available == 1:
            status, reason = "degraded", "single_independent_signal_only"
        else:
            status, reason = "verified", "return_pump_state_supported_by_multiple_independent_signals"

        return {
            "key": "return_pump_multisignal",
            "device_key": "return_pump_main",
            "status": status,
            "reason": reason,
            "evidence_channels": available,
            **evidence,
        }

    def _verify_heater_power_signature(self) -> dict[str, Any]:
        state = self._device_state("heater_main")
        heater_power = self._latest_sensor("power_heater_main")
        reported_on = self._power(state)
        power_w = float(heater_power.value_double) if heater_power is not None else None
        status, reason = self.verify_binary_with_signal(reported_on, power_w, self.HEATER_POWER_ON_MIN_W)
        return {
            "key": "heater_power_signature",
            "device_key": "heater_main",
            "status": status,
            "reason": reason,
            "power_w": power_w,
            "reported_power": reported_on,
        }

    def _verify_temperature_pair(self) -> dict[str, Any]:
        primary = self._latest_sensor("tank_temp_main")
        verify = self._latest_sensor("tank_temp_verify")
        primary_f = float(primary.value_double) if primary is not None else None
        verify_f = float(verify.value_double) if verify is not None else None
        status, reason, delta = self.verify_sensor_pair(primary_f, verify_f, self.TEMP_PAIR_MAX_DELTA_F)
        return {
            "key": "tank_temperature_redundancy",
            "device_key": "temperature_sensing",
            "status": status,
            "reason": reason,
            "primary_f": primary_f,
            "verify_f": verify_f,
            "delta_f": round(delta, 3) if delta is not None else None,
            "max_delta_f": self.TEMP_PAIR_MAX_DELTA_F,
        }

    def _verify_sump_level_pair(self) -> dict[str, Any]:
        primary = self._latest_sensor("sump_level_main")
        verify = self._latest_sensor("sump_level_verify")
        primary_in = float(primary.value_double) if primary is not None else None
        verify_in = float(verify.value_double) if verify is not None else None
        status, reason, delta = self.verify_sensor_pair(primary_in, verify_in, self.SUMP_LEVEL_PAIR_MAX_DELTA_IN)
        return {
            "key": "sump_level_redundancy",
            "device_key": "sump_level_sensing",
            "status": status,
            "reason": reason,
            "primary_in": primary_in,
            "verify_in": verify_in,
            "delta_in": round(delta, 3) if delta is not None else None,
            "max_delta_in": self.SUMP_LEVEL_PAIR_MAX_DELTA_IN,
        }

    def _sync_result(self, result: dict[str, Any]) -> None:
        alert_key = f"physical_verification_{result['key']}"
        active = {item["key"]: item for item in runtime_alerts.list_active()}
        previous = active.get(alert_key)
        was_active = previous is not None
        previous_severity = previous.get("severity") if previous else None

        if result["status"] in {"critical", "degraded"}:
            severity = "critical" if result["status"] == "critical" else "warning"
            runtime_alerts.upsert(
                key=alert_key,
                severity=severity,
                title="Independent Physical Verification Failed" if severity == "critical" else "Independent Verification Degraded",
                message=result["reason"],
                source="physical_verification",
                metadata=result,
            )
            if not was_active or previous_severity != severity:
                AuditService(self.db).append(
                    AuditEventCreate(
                        event_type="safety.physical_verification_failed" if severity == "critical" else "safety.physical_verification_degraded",
                        severity=severity,
                        outcome=result["status"],
                        source="physical_verification",
                        actor_type="system",
                        actor_id="physical_verification_monitor",
                        entity_type="device",
                        entity_id=result["device_key"],
                        message=f"Independent physical verification {result['status']}: {result['reason']}.",
                        details=result,
                    )
                )
        elif result["status"] == "verified":
            if runtime_alerts.clear(alert_key) and was_active:
                AuditService(self.db).append(
                    AuditEventCreate(
                        event_type="safety.physical_verification_recovered",
                        severity="info",
                        outcome="verified",
                        source="physical_verification",
                        actor_type="system",
                        actor_id="physical_verification_monitor",
                        entity_type="device",
                        entity_id=result["device_key"],
                        message="Independent physical verification recovered.",
                        details=result,
                    )
                )
