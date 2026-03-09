from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class TelemetryIngestRequest(BaseModel):
    sensor_key: str = Field(..., examples=["tank_temp_main"])
    timestamp: datetime
    value: float = Field(..., examples=[78.4])
    unit: str = Field(..., examples=["F"])
    quality: Literal["good", "warning", "bad"] = "good"
    source_node: str = Field(..., examples=["sump_node"])


@router.post("")
def ingest_telemetry(payload: TelemetryIngestRequest):
    return {
        "accepted": True,
        "message": "Telemetry payload accepted.",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload.model_dump(mode="json"),
    }


@router.get("/latest")
def get_latest_telemetry():
    return {
        "items": [
            {
                "sensor_key": "tank_temp_main",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": 78.4,
                "unit": "F",
                "quality": "good",
                "source_node": "sump_node",
            }
        ]
    }