from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/tanks", tags=["tanks"])


@router.get("", summary="List configured aquarium tanks")
def list_tanks() -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": 1,
        "items": [
            {
                "tank_id": "reef_display",
                "name": "Reef Display Tank",
                "volume_gallons": 120,
                "status": "online",
                "description": "Primary reef display aquarium",
            }
        ],
    }


@router.get("/{tank_id}", summary="Get tank configuration")
def get_tank(tank_id: str) -> dict[str, object]:
    return {
        "tank_id": tank_id,
        "name": "Reef Display Tank",
        "volume_gallons": 120,
        "status": "online",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sensors": [
            "temperature",
            "ph",
            "salinity",
        ],
        "devices": [
            "heater_main",
            "feeder_main",
            "wavemaker_left",
            "wavemaker_right",
        ],
    }


@router.get("/health", summary="Tank subsystem health")
def tanks_health() -> dict[str, str]:
    return {
        "service": "tanks",
        "status": "ok",
    }