from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.schemas.command import CommandCreateRequest
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService
from app.services.schedule_service import ScheduleService
from app.services.telemetry_service import TelemetryService


class RuleEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.telemetry_service = TelemetryService(db)
        self.command_service = CommandService(db)
        self.device_state_service = DeviceStateService(db)
        self.schedule_service = ScheduleService(db)

    def _device_is_manual(self, device_key: str) -> bool:
        return self.device_state_service.get_mode(device_key) == "manual"

    def _create_auto_command_if_needed(
        self,
        target_device: str,
        command_type: str,
        command_payload: dict,
        requested_by: str,
    ) -> dict:
        payload = CommandCreateRequest(
            requested_by=requested_by,
            target_device=target_device,
            command_type=command_type,
            command_payload=command_payload,
        )

        record, created = self.command_service.create_if_not_duplicate(payload)

        return {
            "action_taken": created,
            "command_id": record.id,
            "status": record.status,
            "target_device": target_device,
            "reason": "command_created" if created else "duplicate_command_suppressed",
        }

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
            result = self._create_auto_command_if_needed(
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
                requested_by="rule_engine.temperature_control",
            )
            result["temperature_f"] = round(temperature_f, 2)
            result["mode"] = current_mode
            return result

        if temperature_f > high_threshold_f:
            result = self._create_auto_command_if_needed(
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
                requested_by="rule_engine.temperature_control",
            )
            result["temperature_f"] = round(temperature_f, 2)
            result["mode"] = current_mode
            return result

        return {
            "action_taken": False,
            "reason": "temperature_within_band",
            "target_device": target_device,
            "temperature_f": round(temperature_f, 2),
            "mode": current_mode,
            "low_threshold_f": low_threshold_f,
            "high_threshold_f": high_threshold_f,
        }

    def evaluate_scheduled_automation(self) -> dict:
        now = datetime.now(timezone.utc)
        hour = now.hour

        results: list[dict] = []

        lighting_schedules = self.schedule_service.list_enabled_by_type("lighting")
        feeding_schedules = self.schedule_service.list_enabled_by_type("feeding")
        flow_schedules = self.schedule_service.list_enabled_by_type("flow")

        for schedule in lighting_schedules:
            device_key = schedule.device_key
            if self._device_is_manual(device_key):
                results.append(
                    {"device": device_key, "action_taken": False, "reason": "device_in_manual_mode"}
                )
                continue

            start_hour = int(schedule.config_payload.get("start_hour_utc", 14))
            end_hour = int(schedule.config_payload.get("end_hour_utc", 23))
            lights_should_be_on = start_hour <= hour < end_hour

            results.append(
                self._create_auto_command_if_needed(
                    target_device=device_key,
                    command_type="set_power",
                    command_payload={
                        "power": lights_should_be_on,
                        "mode": "auto",
                        "reason": "schedule_lighting_window",
                        "scheduled_state": "on" if lights_should_be_on else "off",
                        "schedule_hour_utc": hour,
                        "schedule_name": schedule.name,
                    },
                    requested_by="rule_engine.schedule.lights",
                )
            )

        for schedule in feeding_schedules:
            device_key = schedule.device_key
            if self._device_is_manual(device_key):
                results.append(
                    {"device": device_key, "action_taken": False, "reason": "device_in_manual_mode"}
                )
                continue

            scheduled_hour = int(schedule.config_payload.get("hour_utc", -1))
            duration_seconds = int(schedule.config_payload.get("duration_seconds", 5))

            if scheduled_hour == hour:
                results.append(
                    self._create_auto_command_if_needed(
                        target_device=device_key,
                        command_type="trigger_feed",
                        command_payload={
                            "duration_seconds": duration_seconds,
                            "mode": "auto",
                            "reason": "scheduled_feeding_window",
                            "schedule_hour_utc": hour,
                            "schedule_name": schedule.name,
                            "requested_at": now.isoformat(),
                        },
                        requested_by="rule_engine.schedule.feeder",
                    )
                )
            else:
                results.append(
                    {
                        "device": device_key,
                        "action_taken": False,
                        "reason": "outside_feeding_window",
                        "schedule_name": schedule.name,
                    }
                )

        for schedule in flow_schedules:
            device_key = schedule.device_key
            if self._device_is_manual(device_key):
                results.append(
                    {"device": device_key, "action_taken": False, "reason": "device_in_manual_mode"}
                )
                continue

            day_start = int(schedule.config_payload.get("day_start_hour_utc", 12))
            day_end = int(schedule.config_payload.get("day_end_hour_utc", 23))
            day_intensity = str(schedule.config_payload.get("day_intensity", "high"))
            night_intensity = str(schedule.config_payload.get("night_intensity", "low"))

            desired_intensity = day_intensity if day_start <= hour < day_end else night_intensity

            results.append(
                self._create_auto_command_if_needed(
                    target_device=device_key,
                    command_type="set_intensity",
                    command_payload={
                        "power": True,
                        "intensity": desired_intensity,
                        "mode": "auto",
                        "reason": "scheduled_flow_profile",
                        "schedule_hour_utc": hour,
                        "schedule_name": schedule.name,
                    },
                    requested_by="rule_engine.schedule.wavemakers",
                )
            )

        return {
            "evaluated_at": now.isoformat(),
            "schedule_hour_utc": hour,
            "results": results,
        }