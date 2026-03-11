from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.device_state import DeviceStateResponse
from app.services.device_state_service import DeviceStateService

router = APIRouter(prefix="/device-states", tags=["device-states"])


@router.get("/{device_key}", response_model=DeviceStateResponse)
def get_device_state(
    device_key: str,
    db: Session = Depends(get_db),
):
    service = DeviceStateService(db)
    record = service.get_by_device_key(device_key)

    if record is None:
        raise HTTPException(status_code=404, detail="Device state not found")

    return DeviceStateResponse(
        id=record.id,
        device_key=record.device_key,
        state_payload=record.state_payload,
        state_source=record.state_source,
        updated_at=record.updated_at,
    )


@router.post("/{device_key}/mode/{mode}", response_model=DeviceStateResponse)
def set_device_mode(
    device_key: str,
    mode: str,
    db: Session = Depends(get_db),
):
    normalized_mode = mode.lower().strip()

    if normalized_mode not in {"auto", "manual"}:
        raise HTTPException(status_code=400, detail="Mode must be 'auto' or 'manual'")

    service = DeviceStateService(db)
    record = service.set_mode(device_key=device_key, mode=normalized_mode)

    return DeviceStateResponse(
        id=record.id,
        device_key=record.device_key,
        state_payload=record.state_payload,
        state_source=record.state_source,
        updated_at=record.updated_at,
    )