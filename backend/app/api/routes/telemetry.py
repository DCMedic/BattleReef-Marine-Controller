from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.sensor_catalog import DEFAULT_HISTORY_SENSOR_KEYS, SENSOR_CATALOG
from app.db.session import get_db
from app.schemas.telemetry import (
    TelemetryHistoryResponse,
    TelemetryListResponse,
    TelemetryResponse,
)
from app.services.telemetry_service import TelemetryService


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/catalog")
def get_telemetry_catalog() -> dict[str, object]:
    return {
        "items": SENSOR_CATALOG,
        "count": len(SENSOR_CATALOG),
    }


@router.get("/latest", response_model=TelemetryListResponse)
def get_latest_telemetry(
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> TelemetryListResponse:
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
    sensor_keys: str = Query(default=",".join(DEFAULT_HISTORY_SENSOR_KEYS)),
    limit: int = Query(default=120, ge=10, le=2000),
    db: Session = Depends(get_db),
) -> TelemetryHistoryResponse:
    requested_keys = [item.strip() for item in sensor_keys.split(",") if item.strip()]

    service = TelemetryService(db)
    series = service.history_for_sensors(sensor_keys=requested_keys, limit=limit)

    return TelemetryHistoryResponse(series=series)


@router.get("/window")
def get_telemetry_window(
    sensor_key: str = Query(...),
    days: int = Query(default=3, ge=1, le=365),
    max_points: int = Query(default=288, ge=24, le=2000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    service = TelemetryService(db)
    return service.window_for_sensor(
        sensor_key=sensor_key,
        days=days,
        max_points=max_points,
    )
