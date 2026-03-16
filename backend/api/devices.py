from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from backend.bootstrap_devices import get_services, get_system_status


router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


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


@router.get(
    "",
    summary="List all registered devices",
)
def list_devices() -> list[dict[str, Any]]:
    services = get_services()
    return services.device_manager.inventory()


@router.get(
    "/status",
    summary="Get backend device-layer status",
)
def device_system_status() -> dict[str, Any]:
    return get_system_status()


@router.get(
    "/telemetry",
    response_model=TelemetryResponse,
    summary="Read current telemetry from the sensor service",
    responses={500: {"model": ErrorResponse}},
)
def get_telemetry() -> TelemetryResponse:
    services = get_services()
    try:
        data = services.sensor_service.read_all()
        return TelemetryResponse(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read telemetry: {exc}",
        ) from exc


@router.get(
    "/{device_name}",
    response_model=DeviceCommandResponse,
    summary="Get a single device snapshot by name",
    responses={404: {"model": ErrorResponse}},
)
def get_device(device_name: str) -> DeviceCommandResponse:
    services = get_services()
    try:
        device = services.device_manager.get(device_name)
        return DeviceCommandResponse(**device.snapshot())
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{device_name}/command",
    response_model=DeviceCommandResponse,
    summary="Send a command to a device",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def command_device(
    device_name: str,
    payload: DeviceCommandRequest,
) -> DeviceCommandResponse:
    services = get_services()

    try:
        result = services.device_manager.command(
            name=device_name,
            action=payload.action,
            value=payload.value,
        )
        return DeviceCommandResponse(**result)

    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected device command failure: {exc}",
        ) from exc


@router.post(
    "/heater/evaluate",
    response_model=HeaterEvaluationResponse,
    summary="Evaluate heater control logic against current telemetry",
    responses={500: {"model": ErrorResponse}},
)
def evaluate_heater() -> HeaterEvaluationResponse:
    services = get_services()

    try:
        result = services.heater_controller.evaluate()
        return HeaterEvaluationResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Heater evaluation failed: {exc}",
        ) from exc