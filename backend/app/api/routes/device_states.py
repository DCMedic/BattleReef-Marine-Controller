from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.device_state import (
    DeviceStateListResponse,
    DeviceStateResponse,
    DeviceStateUpsertRequest,
)
from app.services.device_state_service import DeviceStateService

router = APIRouter(prefix="/device-states", tags=["device-states"])


@router.get("", response_model=DeviceStateListResponse)
def list_device_states(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    service = DeviceStateService(db)
    records = service.list_all(limit=limit)

    return DeviceStateListResponse(
        items=[
            DeviceStateResponse(
                id=record.id,
                device_key=record.device_key,
                state_payload=record.state_payload,
                state_source=record.state_source,
                updated_at=record.updated_at,
            )
            for record in records
        ]
    )


@router.get("/{device_key}", response_model=DeviceStateResponse)
def get_device_state(
    device_key: str,
    db: Session = Depends(get_db),
):
    service = DeviceStateService(db)
    record = service.get_by_device_key(device_key)

    if record is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Device state not found")

    return DeviceStateResponse(
        id=record.id,
        device_key=record.device_key,
        state_payload=record.state_payload,
        state_source=record.state_source,
        updated_at=record.updated_at,
    )


@router.post("", response_model=DeviceStateResponse)
def upsert_device_state(
    payload: DeviceStateUpsertRequest,
    db: Session = Depends(get_db),
):
    service = DeviceStateService(db)
    record = service.upsert(payload)

    return DeviceStateResponse(
        id=record.id,
        device_key=record.device_key,
        state_payload=record.state_payload,
        state_source=record.state_source,
        updated_at=record.updated_at,
    )