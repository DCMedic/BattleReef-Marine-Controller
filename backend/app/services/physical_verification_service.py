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
    """Cross-check device-reported state against fresh independent physical evidence."""

    RETURN_FLOW_ON_MIN_GPH = 150.0
    HEATER_POWER_ON_MIN_W = 10.0
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
    def verify_binary_with_signal(cls, reported_on: bool | None, signal_value: float | None, on_threshold: float) -> tuple[str, str]:
        if reported_on is None or signal_value is None:
            return "unknown", "missing_or_stale_independent_evidence"
        physically_on = signal_value >= on_threshold
        if reported_on and not physically_on:
            return "critical", "device_reports_on_but_independent_signal_is_off"
        if not reported_on and physically_on:
            return "critical", "device_reports_off_but_independent_signal_is_on"
        return "verified", "reported_state_matches_independent_signal"

    def evaluate(self) -> list[dict[str, Any]]:
        results = [self._verify_return_pump(), self._verify_heater_power_signature()]
        for result in results:
            self._sync_result(result)
        return results

    def _verify_return_pump(self) -> dict[str, Any]:
        state = self._device_state("return_pump_main") or self._device_state("pump_return_main")
        flow = self._latest_sensor("flow_return_main")
        reported_on = self._power(state)
        flow_gph = float(flow.value_double) if flow is not None else None
        status, reason = self.verify_binary_with_signal(reported_on, flow_gph, self.RETURN_FLOW_ON_MIN_GPH)
        return {"key": "return_pump_flow", "device_key": "return_pump_main", "status": status, "reason": reason, "flow_gph": flow_gph, "reported_power": reported_on}

    def _verify_heater_power_signature(self) -> dict[str, Any]:
        state = self._device_state("heater_main")
        heater_power = self._latest_sensor("power_heater_main")
        reported_on = self._power(state)
        power_w = float(heater_power.value_double) if heater_power is not None else None
        status, reason = self.verify_binary_with_signal(reported_on, power_w, self.HEATER_POWER_ON_MIN_W)
        return {"key": "heater_power_signature", "device_key": "heater_main", "status": status, "reason": reason, "power_w": power_w, "reported_power": reported_on}

    def _sync_result(self, result: dict[str, Any]) -> None:
        alert_key = f"physical_verification_{result['key']}"
        active_keys = {item["key"] for item in runtime_alerts.list_active()}
        was_active = alert_key in active_keys
        if result["status"] == "critical":
            runtime_alerts.upsert(key=alert_key, severity="critical", title="Independent Physical Verification Failed", message=result["reason"], source="physical_verification", metadata=result)
            if not was_active:
                AuditService(self.db).append(AuditEventCreate(event_type="safety.physical_verification_failed", severity="critical", outcome="failed", source="physical_verification", actor_type="system", actor_id="physical_verification_monitor", entity_type="device", entity_id=result["device_key"], message=f"Independent physical verification failed: {result['reason']}.", details=result))
        elif result["status"] == "verified":
            if runtime_alerts.clear(alert_key) and was_active:
                AuditService(self.db).append(AuditEventCreate(event_type="safety.physical_verification_recovered", severity="info", outcome="verified", source="physical_verification", actor_type="system", actor_id="physical_verification_monitor", entity_type="device", entity_id=result["device_key"], message="Independent physical verification recovered.", details=result))
