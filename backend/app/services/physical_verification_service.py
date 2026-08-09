from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.runtime_alerts import runtime_alerts
from app.db.models.device_state import DeviceStateRecord
from app.db.models.telemetry import TelemetryReading
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService


class PhysicalVerificationService:
    """Cross-check device-reported state against independent physical evidence."""

    RETURN_FLOW_ON_MIN_GPH = 150.0
    HEATER_STUCK_POWER_DELTA_W = 75.0

    def __init__(self, db: Session):
        self.db = db

    def _latest_sensor(self, sensor_key: str) -> TelemetryReading | None:
        return (
            self.db.query(TelemetryReading)
            .filter(TelemetryReading.sensor_key == sensor_key, TelemetryReading.quality == "good")
            .order_by(desc(TelemetryReading.reading_time))
            .first()
        )

    def _device_state(self, device_key: str) -> DeviceStateRecord | None:
        return self.db.query(DeviceStateRecord).filter(DeviceStateRecord.device_key == device_key).first()

    @staticmethod
    def _power(state: DeviceStateRecord | None) -> bool | None:
        if state is None or not isinstance(state.state_payload, dict):
            return None
        value = state.state_payload.get("power")
        return value if isinstance(value, bool) else None

    def evaluate(self) -> list[dict[str, Any]]:
        results = [self._verify_return_pump(), self._verify_heater_power_signature()]
        for result in results:
            self._sync_result(result)
        return results

    def _verify_return_pump(self) -> dict[str, Any]:
        state = self._device_state("return_pump_main") or self._device_state("pump_return_main")
        flow = self._latest_sensor("flow_return_main")
        reported_on = self._power(state)
        if reported_on is None or flow is None:
            return {"key": "return_pump_flow", "status": "unknown", "reason": "missing_state_or_flow_evidence"}
        flow_gph = float(flow.value_double)
        if reported_on and flow_gph < self.RETURN_FLOW_ON_MIN_GPH:
            return {"key": "return_pump_flow", "status": "critical", "reason": "pump_reports_on_but_flow_is_low", "flow_gph": flow_gph}
        if not reported_on and flow_gph >= self.RETURN_FLOW_ON_MIN_GPH:
            return {"key": "return_pump_flow", "status": "critical", "reason": "pump_reports_off_but_flow_continues", "flow_gph": flow_gph}
        return {"key": "return_pump_flow", "status": "verified", "reason": "reported_state_matches_flow", "flow_gph": flow_gph}

    def _verify_heater_power_signature(self) -> dict[str, Any]:
        state = self._device_state("heater_main")
        power = self._latest_sensor("power_monitor_main")
        reported_on = self._power(state)
        if reported_on is None or power is None:
            return {"key": "heater_power_signature", "status": "unknown", "reason": "missing_state_or_power_evidence"}

        # Compare current power with recent good baseline samples while the heater was reported off.
        recent = (
            self.db.query(TelemetryReading)
            .filter(TelemetryReading.sensor_key == "power_monitor_main", TelemetryReading.quality == "good")
            .order_by(desc(TelemetryReading.reading_time))
            .limit(20)
            .all()
        )
        current_w = float(power.value_double)
        if len(recent) < 4:
            return {"key": "heater_power_signature", "status": "unknown", "reason": "insufficient_power_baseline", "power_w": current_w}
        baseline = min(float(r.value_double) for r in recent)
        delta = current_w - baseline
        if reported_on is False and delta >= self.HEATER_STUCK_POWER_DELTA_W:
            return {"key": "heater_power_signature", "status": "critical", "reason": "heater_reports_off_but_power_signature_present", "power_w": current_w, "baseline_w": baseline, "delta_w": round(delta, 1)}
        return {"key": "heater_power_signature", "status": "verified", "reason": "heater_state_not_contradicted_by_power", "power_w": current_w, "baseline_w": baseline, "delta_w": round(delta, 1)}

    def _sync_result(self, result: dict[str, Any]) -> None:
        alert_key = f"physical_verification_{result['key']}"
        if result["status"] == "critical":
            runtime_alerts.upsert(
                key=alert_key,
                severity="critical",
                title="Independent Physical Verification Failed",
                message=result["reason"],
                source="physical_verification",
                metadata=result,
            )
            AuditService(self.db).append(AuditEventCreate(
                event_type="safety.physical_verification_failed",
                severity="critical",
                outcome="failed",
                source="physical_verification",
                actor_type="system",
                actor_id="physical_verification_monitor",
                entity_type="verification_rule",
                entity_id=result["key"],
                message=f"Independent physical verification failed: {result['reason']}.",
                details=result,
            ))
        elif result["status"] == "verified":
            runtime_alerts.clear(alert_key)
