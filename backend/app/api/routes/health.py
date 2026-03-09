from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {
        "status": "ok",
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
def readiness_check():
    return {
        "status": "ready",
        "checks": {
            "api": "ok",
        },
    }