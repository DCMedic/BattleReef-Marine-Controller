from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryIngestRequest(BaseModel):
    sensor_key: str = Field(..., min_length=1, examples=["tank_temp_main"])
    timestamp: datetime = Field(..., examples=["2026-03-10T22:00:00Z"])
    value: float = Field(..., examples=[77.8])
    unit: str = Field(..., min_length=1, examples=["F"])
    quality: str = Field(default="good", min_length=1, examples=["good"])
    source_node: str = Field(..., min_length=1, examples=["simulator_node"])


class TelemetryResponse(BaseModel):
    id: int
    sensor_key: str
    source_node: str
    timestamp: datetime
    value: float
    unit: str
    quality: str


class TelemetryListResponse(BaseModel):
    items: list[TelemetryResponse]


class TelemetryHistoryPoint(BaseModel):
    timestamp: datetime
    value: float


class TelemetryHistorySeries(BaseModel):
    sensor_key: str
    unit: str
    points: list[TelemetryHistoryPoint]


class TelemetryHistoryResponse(BaseModel):
    series: list[TelemetryHistorySeries]