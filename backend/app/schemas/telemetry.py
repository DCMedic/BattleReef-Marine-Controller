from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TelemetryIngestRequest(BaseModel):
    sensor_key: str = Field(..., min_length=1, examples=["tank_temp_main"])
    timestamp: datetime
    value: float = Field(..., examples=[78.4])
    unit: str = Field(..., min_length=1, examples=["F"])
    quality: Literal["good", "warning", "bad"] = "good"
    source_node: str = Field(..., min_length=1, examples=["sump_node"])


class TelemetryResponse(BaseModel):
    id: int
    sensor_key: str
    source_node: str
    timestamp: datetime
    value: float
    unit: str
    quality: str


class TelemetryLatestResponse(BaseModel):
    items: list[TelemetryResponse]