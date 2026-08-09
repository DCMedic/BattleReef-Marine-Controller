from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.schemas.device_state import DeviceStateResponse
from app.services.audit_service import AuditService
from app.services.device_state_service import DeviceStateService

router = APIRouter(prefix="/device-states", tags=["device-states"])


def _response(record) -> DeviceStateResponse:
    return DeviceStateResponse(id=record.id, device_key=record.device_key, state_payload=record.state_payload, state_source=record.state_source, updated_at=record.updated_at)


@router.get("/{device_key}", response_model=DeviceStateResponse)
def get_device_state(device_key: str, db: Session = Depends(get_db)) -> DeviceStateResponse:
    record = DeviceStateService(db).get_by_device_key(device_key)
    if record is None:
        raise HTTPException(status_code=404, detail="Device state not found")
    return _response(record)


@router.post("/{device_key}/mode/{mode}", response_model=DeviceStateResponse)
def set_device_mode(
    device_key: str,
    mode: str,
    principal: Principal = Depends(require_role("engineer")),
    db: Session = Depends(get_db),
) -> DeviceStateResponse:
    normalized_mode = mode.lower().strip()
    if normalized_mode not in {"auto", "manual"}:
        raise HTTPException(status_code=400, detail="Mode must be 'auto' or 'manual'")
    record = DeviceStateService(db).set_mode(device_key=device_key, mode=normalized_mode)
    AuditService(db).append(AuditEventCreate(
        event_type="operator.device_mode_changed", severity="warning", source="api.device_states",
        actor_type=principal.principal_type, actor_id=principal.username, entity_type="device", entity_id=device_key,
        message=f"Device {device_key} mode changed to {normalized_mode}.",
        details={"role": principal.role, "mode": normalized_mode},
    ))
    return _response(record)
