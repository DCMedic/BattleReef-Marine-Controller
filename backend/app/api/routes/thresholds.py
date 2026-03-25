from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.threshold_config_service import ThresholdConfigService


router = APIRouter(prefix="/thresholds", tags=["thresholds"])


class ThresholdUpdateRequest(BaseModel):
    min: float | None = None
    max: float | None = None
    severity: str = Field(..., pattern="^(warning|critical)$")
    enabled: bool = True


class ThresholdPresetApplyRequest(BaseModel):
    preset_key: str


@router.get("")
def list_thresholds() -> dict[str, Any]:
    service = ThresholdConfigService()
    items = service.list_thresholds()

    return {
        "items": items,
        "count": len(items),
        "active_profile": service.get_active_profile(),
    }


@router.get("/presets")
def list_threshold_presets() -> dict[str, Any]:
    service = ThresholdConfigService()
    items = service.list_presets()

    return {
        "items": items,
        "count": len(items),
        "active_profile": service.get_active_profile(),
    }


@router.post("/presets/apply")
def apply_threshold_preset(payload: ThresholdPresetApplyRequest) -> dict[str, Any]:
    service = ThresholdConfigService()

    try:
        return service.apply_preset(payload.preset_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/presets/active")
def clear_active_preset() -> dict[str, Any]:
    service = ThresholdConfigService()
    return service.clear_active_profile()


@router.put("/{sensor_key}")
def update_threshold(sensor_key: str, payload: ThresholdUpdateRequest) -> dict[str, Any]:
    service = ThresholdConfigService()

    try:
        return service.update_threshold(
            sensor_key=sensor_key,
            min_value=payload.min,
            max_value=payload.max,
            severity=payload.severity,
            enabled=payload.enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{sensor_key}")
def reset_threshold(sensor_key: str) -> dict[str, Any]:
    service = ThresholdConfigService()

    try:
        return service.reset_threshold(sensor_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc