from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.telemetry import (
    TelemetryIngestRequest,
    TelemetryLatestResponse,
    TelemetryResponse,
)
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", response_model=TelemetryResponse)
def ingest_telemetry(
    payload: TelemetryIngestRequest,
    db: Session = Depends(get_db),
):
    service = TelemetryService(db)
    record = service.ingest(payload)
    return TelemetryResponse(
        id=record.id,
        sensor_key=record.sensor_key,
        source_node=record.source_node,
        timestamp=record.reading_time,
        value=record.value_double,
        unit=record.unit,
        quality=record.quality,
    )


@router.get("/latest", response_model=TelemetryLatestResponse)
def get_latest_telemetry(
    db: Session = Depends(get_db),
):
    service = TelemetryService(db)
    records = service.latest()
    return TelemetryLatestResponse(
        items=[
            TelemetryResponse(
                id=record.id,
                sensor_key=record.sensor_key,
                source_node=record.source_node,
                timestamp=record.reading_time,
                value=record.value_double,
                unit=record.unit,
                quality=record.quality,
            )
            for record in records
        ]
    )