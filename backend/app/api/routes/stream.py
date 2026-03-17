from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(prefix="/stream", tags=["stream"])


@router.get("", summary="Get stream service status")
def stream_status() -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "service": "telemetry_stream",
        "status": "online",
        "description": "Real-time telemetry streaming service",
    }


@router.get("/health", summary="Stream subsystem health check")
def stream_health() -> dict[str, str]:
    return {
        "service": "stream",
        "status": "ok",
    }


@router.get("/latest", summary="Get latest telemetry snapshot")
def latest_stream_data() -> dict[str, object]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature_f": 78.0,
        "ph": 8.2,
        "salinity_ppt": 35.0,
        "source": "mock_stream",
    }
