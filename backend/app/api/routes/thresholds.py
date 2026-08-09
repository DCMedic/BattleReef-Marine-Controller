from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService
from app.services.threshold_config_service import ThresholdConfigService

router = APIRouter(prefix="/thresholds", tags=["thresholds"])


class ThresholdUpdateRequest(BaseModel):
    min: float | None = None
    max: float | None = None
    severity: str = Field(..., pattern="^(warning|critical)$")
    enabled: bool = True


class ThresholdPresetApplyRequest(BaseModel):
    preset_key: str


def _audit_config(db: Session, principal: Principal, event_type: str, message: str, details: dict[str, Any]) -> None:
    AuditService(db).append(AuditEventCreate(
        event_type=event_type, source="api.thresholds", actor_type="user", actor_id=principal.username,
        entity_type="threshold_configuration", message=message, details={"role": principal.role, **details},
    ))


@router.get("")
def list_thresholds() -> dict[str, Any]:
    service = ThresholdConfigService()
    items = service.list_thresholds()
    return {"items": items, "count": len(items), "active_profile": service.get_active_profile()}


@router.get("/presets")
def list_threshold_presets() -> dict[str, Any]:
    service = ThresholdConfigService()
    items = service.list_presets()
    return {"items": items, "count": len(items), "active_profile": service.get_active_profile()}


@router.post("/presets/apply")
def apply_threshold_preset(payload: ThresholdPresetApplyRequest, principal: Principal = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        result = ThresholdConfigService().apply_preset(payload.preset_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit_config(db, principal, "operator.threshold_preset_applied", f"Threshold preset {payload.preset_key} applied.", {"preset_key": payload.preset_key})
    return result


@router.delete("/presets/active")
def clear_active_preset(principal: Principal = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> dict[str, Any]:
    result = ThresholdConfigService().clear_active_profile()
    _audit_config(db, principal, "operator.threshold_preset_cleared", "Active threshold preset cleared.", {})
    return result


@router.put("/{sensor_key}")
def update_threshold(sensor_key: str, payload: ThresholdUpdateRequest, principal: Principal = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        result = ThresholdConfigService().update_threshold(sensor_key=sensor_key, min_value=payload.min, max_value=payload.max, severity=payload.severity, enabled=payload.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit_config(db, principal, "operator.threshold_updated", f"Threshold configuration updated for {sensor_key}.", {"sensor_key": sensor_key, "min": payload.min, "max": payload.max, "severity": payload.severity, "enabled": payload.enabled})
    return result


@router.delete("/{sensor_key}")
def reset_threshold(sensor_key: str, principal: Principal = Depends(require_role("engineer")), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        result = ThresholdConfigService().reset_threshold(sensor_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit_config(db, principal, "operator.threshold_reset", f"Threshold configuration reset for {sensor_key}.", {"sensor_key": sensor_key})
    return result
