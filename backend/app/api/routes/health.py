from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
def readiness_check() -> dict[str, object]:
    return {
        "status": "ready",
        "checks": {
            "api": "ok",
        },
    }