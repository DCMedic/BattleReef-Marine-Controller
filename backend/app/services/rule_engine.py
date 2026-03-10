from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.telemetry import TelemetryReading
from app.rules.temperature_control import (
    TemperatureRuleSettings,
    evaluate_temperature_control,
)
from app.schemas.command import CommandCreateRequest
from app.services.command_service import CommandService


class RuleEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.command_service = CommandService(db)
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

        command = self.command_service.create(
            CommandCreateRequest(
                requested_by="rule_engine.temperature_control",
                target_device=decision["target_device"],
                command_type=decision["command_type"],
                command_payload=decision["command_payload"],
            ),
            status="queued",
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
        }