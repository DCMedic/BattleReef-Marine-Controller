from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.command import CommandCreateRequest
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService
from app.services.schedule_service import ScheduleService


class ScheduleEngine:
    """Evaluate schedules and issue canonical, deduplicated device commands."""

    INTENSITY_PRESETS = {
        "low": 30,
        "medium": 60,
        "high": 90,
    }

    def __init__(self, db: Session):
        self.db = db
        self.schedule_service = ScheduleService(db)
        self.command_service = CommandService(db)
        self.device_state_service = DeviceStateService(db)

    def evaluate(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        results: list[dict[str, Any]] = []

        for schedule in self.schedule_service.list_schedules(limit=500):
            if not schedule.enabled:
                continue

            payload = schedule.config_payload or {}
            schedule_type = schedule.schedule_type

            if self.device_state_service.get_mode(schedule.device_key) == "manual":
                results.append(
                    {
                        "device": schedule.device_key,
                        "schedule": schedule.name,
                        "status": "skipped_manual_mode",
                    }
                )
                continue

            if schedule_type == "lighting":
                result = self._handle_lighting(schedule, payload, now)
            elif schedule_type == "feeding":
                result = self._handle_feeding(schedule, payload, now)
            elif schedule_type == "flow":
                result = self._handle_flow(schedule, payload, now)
            elif schedule_type == "time_window":
                result = self._handle_legacy_time_window(schedule, payload, now)
            elif schedule_type == "event":
                result = self._handle_legacy_event(schedule, payload, now)
            else:
                result = {
                    "device": schedule.device_key,
                    "schedule": schedule.name,
                    "status": "unknown_schedule_type",
                    "schedule_type": schedule_type,
                }

            results.append(result)

        return {
            "evaluated_at": now.isoformat(),
            "schedule_hour_utc": now.hour,
            "results": results,
        }

    def _queue(
        self,
        *,
        schedule,
        command_type: str,
        command_payload: dict[str, Any],
        requested_by: str,
        duplicate_window_seconds: int = 60,
    ) -> dict[str, Any]:
        record, created = self.command_service.create_if_not_duplicate(
            CommandCreateRequest(
                requested_by=requested_by,
                target_device=schedule.device_key,
                command_type=command_type,
                command_payload=command_payload,
            ),
            duplicate_window_seconds=duplicate_window_seconds,
        )
        return {
            "device": schedule.device_key,
            "schedule": schedule.name,
            "status": "command_queued" if created else "duplicate_suppressed",
            "command_id": record.id,
            "command_type": command_type,
        }

    @staticmethod
    def _hour_in_window(hour: int, start: int, end: int) -> bool:
        if start == end:
            return True
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    def _handle_lighting(self, schedule, payload: dict[str, Any], now: datetime) -> dict[str, Any]:
        start = int(payload.get("start_hour_utc", 14))
        end = int(payload.get("end_hour_utc", 23))
        desired_power = self._hour_in_window(now.hour, start, end)
        return self._queue(
            schedule=schedule,
            command_type="set_power",
            command_payload={
                "power": desired_power,
                "mode": "auto",
                "reason": "schedule_lighting_window",
                "schedule_name": schedule.name,
            },
            requested_by="schedule_engine.lighting",
        )

    def _handle_feeding(self, schedule, payload: dict[str, Any], now: datetime) -> dict[str, Any]:
        hour = int(payload.get("hour_utc", -1))
        minute = int(payload.get("minute_utc", 0))
        duration = float(payload.get("duration_seconds", 5))

        if now.hour != hour or now.minute != minute:
            return {
                "device": schedule.device_key,
                "schedule": schedule.name,
                "status": "not_trigger_time",
            }

        last_command = self.command_service.get_last_command_for_device(schedule.device_key)
        if last_command and last_command.requested_at:
            if now - last_command.requested_at < timedelta(minutes=55):
                return {
                    "device": schedule.device_key,
                    "schedule": schedule.name,
                    "status": "cooldown_active",
                    "command_id": last_command.id,
                }

        return self._queue(
            schedule=schedule,
            command_type="trigger_feed",
            command_payload={
                "duration_seconds": duration,
                "mode": "auto",
                "reason": "scheduled_feeding_window",
                "schedule_name": schedule.name,
                "requested_at": now.isoformat(),
            },
            requested_by="schedule_engine.feeding",
            duplicate_window_seconds=3600,
        )

    def _normalize_intensity(self, value: Any) -> int:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in self.INTENSITY_PRESETS:
                return self.INTENSITY_PRESETS[normalized]
            value = float(normalized)

        intensity = int(float(value))
        if intensity < 0 or intensity > 100:
            raise ValueError("flow intensity must be between 0 and 100")
        return intensity

    def _handle_flow(self, schedule, payload: dict[str, Any], now: datetime) -> dict[str, Any]:
        day_start = int(payload.get("day_start_hour_utc", 12))
        day_end = int(payload.get("day_end_hour_utc", 23))
        raw_intensity = (
            payload.get("day_intensity", "high")
            if self._hour_in_window(now.hour, day_start, day_end)
            else payload.get("night_intensity", "low")
        )
        intensity = self._normalize_intensity(raw_intensity)

        return self._queue(
            schedule=schedule,
            command_type="set_intensity",
            command_payload={
                "power": intensity > 0,
                "intensity": intensity,
                "mode": "auto",
                "reason": "scheduled_flow_profile",
                "schedule_name": schedule.name,
            },
            requested_by="schedule_engine.flow",
        )

    def _handle_legacy_time_window(
        self,
        schedule,
        payload: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        start = payload.get("start_hour")
        end = payload.get("end_hour")
        if start is None or end is None:
            return {"device": schedule.device_key, "schedule": schedule.name, "status": "invalid_config"}

        desired_power = self._hour_in_window(now.hour, int(start), int(end))
        return self._queue(
            schedule=schedule,
            command_type="set_power",
            command_payload={"power": desired_power, "mode": "auto", "schedule_name": schedule.name},
            requested_by="schedule_engine.legacy_time_window",
        )

    def _handle_legacy_event(
        self,
        schedule,
        payload: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        hour = payload.get("hour")
        minute = int(payload.get("minute", 0))
        if hour is None:
            return {
                "device": schedule.device_key,
                "schedule": schedule.name,
                "status": "invalid_event_config",
            }
        if now.hour != int(hour) or now.minute != minute:
            return {
                "device": schedule.device_key,
                "schedule": schedule.name,
                "status": "not_trigger_time",
            }

        command_type = str(payload.get("command_type", "trigger_feed"))
        command_payload = dict(payload.get("command_payload", {}))
        if command_type == "trigger_feed" and "duration_seconds" not in command_payload:
            command_payload["duration_seconds"] = float(payload.get("duration_seconds", 5))
        command_payload.setdefault("mode", "auto")
        command_payload.setdefault("schedule_name", schedule.name)
        command_payload.setdefault("requested_at", now.isoformat())

        return self._queue(
            schedule=schedule,
            command_type=command_type,
            command_payload=command_payload,
            requested_by="schedule_engine.legacy_event",
            duplicate_window_seconds=int(payload.get("cooldown_minutes", 60)) * 60,
        )
