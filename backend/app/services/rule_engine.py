from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.telemetry import TelemetryReading
from app.rules.temperature_control import (
    TemperatureRuleSettings,
    evaluate_temperature_control,
)
from app.schemas.command import CommandCreateRequest
from app.schemas.device_state import DeviceStateUpsertRequest
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService


class RuleEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.command_service = CommandService(db)
        self.device_state_service = DeviceStateService(db)
        self.temperature_settings = TemperatureRuleSettings()

    def evaluate_temperature_rule(self) -> dict:
        stmt = (
            select(TelemetryReading)
            .where(TelemetryReading.sensor_key == self.temperature_settings.sensor_key)
            .order_by(TelemetryReading.reading_time.desc())
            .limit(1)
        )
        latest = self.db.scalar(stmt)

        if latest is None:
            return {
                "evaluated": True,
                "rule": "temperature_control",
                "action_taken": False,
                "reason": "no_temperature_reading_available",
            }

        decision = evaluate_temperature_control(
            temperature_f=latest.value_double,
            settings=self.temperature_settings,
        )

        if decision is None:
            return {
                "evaluated": True,
                "rule": "temperature_control",
                "action_taken": False,
                "reason": "temperature_within_band",
                "temperature_f": latest.value_double,
                "low_threshold_f": self.temperature_settings.low_threshold_f,
                "high_threshold_f": self.temperature_settings.high_threshold_f,
            }

        desired_power = decision["command_payload"].get("power")
        current_state = self.device_state_service.get_by_device_key(decision["target_device"])

        if current_state is not None:
            current_power = current_state.state_payload.get("power")
            if current_power == desired_power:
                return {
                    "evaluated": True,
                    "rule": "temperature_control",
                    "action_taken": False,
                    "reason": "desired_state_already_set",
                    "temperature_f": latest.value_double,
                    "target_device": decision["target_device"],
                    "desired_power": desired_power,
                    "current_state": current_state.state_payload,
                }

        command, created = self.command_service.create_if_not_duplicate(
            CommandCreateRequest(
                requested_by="rule_engine.temperature_control",
                target_device=decision["target_device"],
                command_type=decision["command_type"],
                command_payload=decision["command_payload"],
            ),
            status="queued",
        )

        if not created:
            return {
                "evaluated": True,
                "rule": "temperature_control",
                "action_taken": False,
                "reason": "duplicate_command_suppressed",
                "temperature_f": latest.value_double,
                "command_id": command.id,
                "target_device": command.target_device,
                "command_type": command.command_type,
                "command_payload": command.command_payload,
                "status": command.status,
            }

        state_record = self.device_state_service.upsert(
            DeviceStateUpsertRequest(
                device_key=decision["target_device"],
                state_payload={
                    "power": desired_power,
                    "mode": "auto",
                    "reason": decision["command_payload"].get("reason"),
                    "last_command_id": command.id,
                },
                state_source="rule_engine.temperature_control",
            )
        )

        return {
            "evaluated": True,
            "rule": "temperature_control",
            "action_taken": True,
            "temperature_f": latest.value_double,
            "command_id": command.id,
            "target_device": command.target_device,
            "command_type": command.command_type,
            "command_payload": command.command_payload,
            "status": command.status,
            "device_state_id": state_record.id,
            "device_state": state_record.state_payload,
        }