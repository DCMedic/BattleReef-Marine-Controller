from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SystemCounts(BaseModel):
    telemetry_readings: int
    commands_total: int
    commands_queued: int
    commands_dispatched: int
    commands_completed: int
    commands_failed: int
    device_states: int


class SensorLatestReading(BaseModel):
    sensor_key: str
    source_node: str
    reading_time: datetime
    value: float
    unit: str
    quality: str


class DeviceStateSummary(BaseModel):
    device_key: str
    state_payload: dict[str, Any]
    state_source: str
    updated_at: datetime


class TimescaleStatus(BaseModel):
    extension_installed: bool
    telemetry_is_hypertable: bool


class SystemSummaryResponse(BaseModel):
    generated_at: datetime
    counts: SystemCounts
    latest_readings: list[SensorLatestReading]
    device_states: list[DeviceStateSummary]
    timescale_status: TimescaleStatus