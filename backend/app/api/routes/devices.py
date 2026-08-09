from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.bootstrap_devices import get_services, get_system_status
from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceCommandRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=50)
    value: float | int | str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Action must not be empty.")
        return cleaned


class DeviceCommandResponse(BaseModel):
    name: str
    kind: str
    online: bool
    enabled: bool
    last_command: str | None
    last_updated: str
    attributes: dict[str, Any]


class TelemetryResponse(BaseModel):
    timestamp: str
    temperature_f: float
    ph: float
    salinity_ppt: float


class HeaterEvaluationResponse(BaseModel):
    decision: Literal["emergency_off", "heater_on", "heater_off", "hold"]
    reason: str
    telemetry: dict[str, Any]
    device: dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str


@router.get("")
def list_devices() -> list[dict[str, Any]]:
    return get_services().device_manager.inventory()


@router.get("/status")
def device_system_status() -> dict[str, Any]:
    return get_system_status()


@router.get("/telemetry", response_model=TelemetryResponse)
def get_telemetry() -> TelemetryResponse:
    try:
        return TelemetryResponse(**get_services().sensor_service.read_all())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read telemetry: {exc}") from exc


@router.get("/{device_name}", response_model=DeviceCommandResponse)
def get_device(device_name: str) -> DeviceCommandResponse:
    try:
        return DeviceCommandResponse(**get_services().device_manager.get(device_name).snapshot())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{device_name}/command", response_model=DeviceCommandResponse)
def command_device(
    device_name: str,
    payload: DeviceCommandRequest,
    principal: Principal = Depends(require_role("operator")),
    db: Session = Depends(get_db),
) -> DeviceCommandResponse:
    try:
        result = get_services().device_manager.command(name=device_name, action=payload.action, value=payload.value)
        AuditService(db).append(AuditEventCreate(
            event_type="operator.direct_device_command", severity="warning", source="api.devices", actor_type=principal.principal_type,
            actor_id=principal.username, entity_type="device", entity_id=device_name,
            message=f"Direct device command {payload.action} executed for {device_name}.",
            details={"role": principal.role, "action": payload.action, "value": payload.value, "result": result},
        ))
        return DeviceCommandResponse(**result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected device command failure: {exc}") from exc


@router.post("/heater/evaluate", response_model=HeaterEvaluationResponse)
def evaluate_heater(
    principal: Principal = Depends(require_role("engineer")),
    db: Session = Depends(get_db),
) -> HeaterEvaluationResponse:
    try:
        result = get_services().heater_controller.evaluate()
        AuditService(db).append(AuditEventCreate(
            event_type="operator.direct_heater_evaluation", source="api.devices", actor_type=principal.principal_type, actor_id=principal.username,
            entity_type="device", entity_id="heater", message="Direct heater automation evaluation requested.",
            details={"role": principal.role, "decision": result.get("decision")},
        ))
        return HeaterEvaluationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Heater evaluation failed: {exc}") from exc
