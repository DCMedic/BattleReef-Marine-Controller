from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.schemas.command import CommandCreateRequest
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService
from app.services.schedule_service import ScheduleService


class ScheduleEngine:
    """
    Evaluates active schedules and issues commands when needed.
    Supports:
    - time-window schedules (on/off)
    - event schedules (feeding, triggers)
    """

    def __init__(self, db: Session):
        self.db = db
        self.schedule_service = ScheduleService(db)
        self.command_service = CommandService(db)
        self.device_state_service = DeviceStateService(db)

    def evaluate(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        hour = now.hour
        minute = now.minute

        schedules = self.schedule_service.list_schedules(limit=500)

        results: List[Dict[str, Any]] = []

        for schedule in schedules:
            if not schedule.enabled:
                continue

            payload = schedule.config_payload or {}
            schedule_type = schedule.schedule_type

            if schedule_type == "time_window":
                result = self._handle_time_window(schedule, payload, hour)
            elif schedule_type == "event":
                result = self._handle_event(schedule, payload, hour, minute, now)
            else:
                result = {
                    "device": schedule.device_key,
                    "status": "unknown_schedule_type",
                }

            results.append(result)

        return {
            "evaluated_at": now.isoformat(),
            "schedule_hour_utc": hour,
            "results": results,
        }

    # --------------------------
    # TIME WINDOW (existing)
    # --------------------------
    def _handle_time_window(self, schedule, payload, hour):
        start = payload.get("start_hour")
        end = payload.get("end_hour")

        if start is None or end is None:
            return {"device": schedule.device_key, "status": "invalid_config"}

        in_window = start <= hour < end
        desired_state = "on" if in_window else "off"

        device_key = schedule.device_key

        current_state = self.device_state_service.get_by_device_key(device_key)

        current_mode = (
            current_state.state_payload.get("mode")
            if current_state and current_state.state_payload
            else "auto"
        )

        if current_mode != "auto":
            return {"device": device_key, "status": "skipped_manual_mode"}

        last_state = (
            current_state.state_payload.get("power")
            if current_state and current_state.state_payload
            else None
        )

        if last_state == desired_state:
            return {"device": device_key, "status": "no_change"}

        command = self.command_service.create_command(
            CommandCreateRequest(
                requested_by="schedule_engine",
                target_device=device_key,
                command_type="power",
                command_payload={"state": desired_state},
            )
        )

        self.device_state_service.set_state(
            device_key=device_key,
            state_payload={"power": desired_state, "mode": "auto"},
            source="schedule_engine",
        )

        return {
            "device": device_key,
            "status": "command_sent",
            "new_state": desired_state,
            "command_id": command.id,
        }

    # --------------------------
    # EVENT (NEW)
    # --------------------------
    def _handle_event(self, schedule, payload, hour, minute, now):
        trigger_hour = payload.get("hour")
        trigger_minute = payload.get("minute", 0)
        cooldown_minutes = payload.get("cooldown_minutes", 60)

        device_key = schedule.device_key

        if trigger_hour is None:
            return {"device": device_key, "status": "invalid_event_config"}

        # Check if we are at trigger time (within same minute)
        if not (hour == trigger_hour and minute == trigger_minute):
            return {"device": device_key, "status": "not_trigger_time"}

        # Check cooldown
        last_command = self.command_service.get_last_command_for_device(device_key)

        if last_command and last_command.requested_at:
            delta = now - last_command.requested_at

            if delta < timedelta(minutes=cooldown_minutes):
                return {
                    "device": device_key,
                    "status": "cooldown_active",
                }

        # Fire event (e.g., feeding)
        command = self.command_service.create_command(
            CommandCreateRequest(
                requested_by="schedule_engine",
                target_device=device_key,
                command_type="trigger",
                command_payload={"action": "execute"},
            )
        )

        return {
            "device": device_key,
            "status": "event_triggered",
            "command_id": command.id,
        }