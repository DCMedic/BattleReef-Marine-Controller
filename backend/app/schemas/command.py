from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CommandCreateRequest(BaseModel):
    requested_by: str = Field(..., min_length=1, examples=["rule_engine"])
    target_device: str = Field(..., min_length=1, examples=["heater_main"])
    command_type: str = Field(..., min_length=1, examples=["set_power"])
    command_payload: dict[str, Any] = Field(..., examples=[{"power": True}])


class CommandResponse(BaseModel):
    id: int
    requested_at: datetime
    requested_by: str
    target_device: str
    command_type: str
    command_payload: dict[str, Any]
    status: str
    acknowledged_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class CommandListResponse(BaseModel):
    items: list[CommandResponse]