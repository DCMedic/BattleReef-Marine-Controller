from datetime import datetime

from pydantic import BaseModel, Field


class ScheduleCreateRequest(BaseModel):
    device_key: str = Field(..., min_length=1)
    schedule_type: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    enabled: bool = True
    config_payload: dict


class ScheduleUpdateRequest(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    config_payload: dict | None = None


class ScheduleResponse(BaseModel):
    id: int
    device_key: str
    schedule_type: str
    name: str
    enabled: bool
    config_payload: dict
    created_at: datetime
    updated_at: datetime


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]