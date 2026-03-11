from sqlalchemy.orm import Session

from app.schemas.command import CommandCreateRequest
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService
from app.services.telemetry_service import TelemetryService


class RuleEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.telemetry_service = TelemetryService(db)
        self.command_service = CommandService(db)
        self.device_state_service = DeviceStateService(db)

    def evaluate_temperature_rule(
        self,
        sensor_key: str = "tank_temp_main",
        target_device: str = "heater_main",
        low_threshold_f: float = 77.5,
        high_threshold_f: float = 78.3,
    ) -> dict:
        current_mode = self.device_state_service.get_mode(target_device)

        if current_mode == "manual":
            return {
                "action_taken": False,
                "reason": "device_in_manual_mode",
                "target_device": target_device,
                "mode": current_mode,
            }

        records = self.telemetry_service.latest_by_sensor(sensor_key=sensor_key, limit=1)
        if not records:
            return {
                "action_taken": False,
                "reason": "no_temperature_reading",
                "target_device": target_device,
                "mode": current_mode,
            }

        latest = records[0]
        temperature_f = latest.value_double

        if temperature_f < low_threshold_f:
            payload = CommandCreateRequest(
                requested_by="rule_engine.temperature_control",
                target_device=target_device,
                command_type="set_power",
                command_payload={
                    "power": True,
                    "mode": "auto",
                    "reason": "temperature_below_low_threshold",
                    "temperature_f": round(temperature_f, 2),
                    "low_threshold_f": low_threshold_f,
                    "high_threshold_f": high_threshold_f,
                },
            )

            record, created = self.command_service.create_if_not_duplicate(payload)

            return {
                "action_taken": created,
                "command_id": record.id,
                "status": record.status,
                "target_device": target_device,
                "temperature_f": round(temperature_f, 2),
                "mode": current_mode,
                "reason": "heater_on" if created else "duplicate_command_suppressed",
            }

        if temperature_f > high_threshold_f:
            payload = CommandCreateRequest(
                requested_by="rule_engine.temperature_control",
                target_device=target_device,
                command_type="set_power",
                command_payload={
                    "power": False,
                    "mode": "auto",
                    "reason": "temperature_above_high_threshold",
                    "temperature_f": round(temperature_f, 2),
                    "low_threshold_f": low_threshold_f,
                    "high_threshold_f": high_threshold_f,
                },
            )

            record, created = self.command_service.create_if_not_duplicate(payload)

            return {
                "action_taken": created,
                "command_id": record.id,
                "status": record.status,
                "target_device": target_device,
                "temperature_f": round(temperature_f, 2),
                "mode": current_mode,
                "reason": "heater_off" if created else "duplicate_command_suppressed",
            }

        return {
            "action_taken": False,
            "reason": "temperature_within_band",
            "target_device": target_device,
            "temperature_f": round(temperature_f, 2),
            "mode": current_mode,
            "low_threshold_f": low_threshold_f,
            "high_threshold_f": high_threshold_f,
        }