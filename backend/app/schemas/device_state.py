from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeviceStateUpsertRequest(BaseModel):
    device_key: str = Field(..., min_length=1, examples=["heater_main"])
    state_payload: dict[str, Any] = Field(..., examples=[{"power": True, "mode": "auto"}])
    state_source: str = Field(default="system", min_length=1, examples=["rule_engine"])


class DeviceStateResponse(BaseModel):
    id: int
    device_key: str
    state_payload: dict[str, Any]
    state_source: str
    updated_at: datetime


class DeviceStateListResponse(BaseModel):
    items: list[DeviceStateResponse]