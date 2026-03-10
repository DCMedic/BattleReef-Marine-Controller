from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.telemetry import (
    TelemetryHistoryResponse,
    TelemetryListResponse,
    TelemetryResponse,
)
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/latest", response_model=TelemetryListResponse)
def get_latest_telemetry(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    service = TelemetryService(db)
    records = service.latest(limit=limit)

    return TelemetryListResponse(
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


@router.get("/history", response_model=TelemetryHistoryResponse)
def get_telemetry_history(
    sensor_keys: str = Query(
        default="tank_temp_main,tank_ph_main,tank_salinity_main,sump_level_main"
    ),
    limit: int = Query(default=120, ge=10, le=1000),
    db: Session = Depends(get_db),
):
    requested_keys = [item.strip() for item in sensor_keys.split(",") if item.strip()]

    service = TelemetryService(db)
    series = service.history_for_sensors(sensor_keys=requested_keys, limit=limit)

    return TelemetryHistoryResponse(series=series)