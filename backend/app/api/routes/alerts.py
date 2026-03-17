from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", summary="List active alerts")
def list_alerts() -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [],
        "count": 0,
        "status": "ok",
    }


@router.get("/health", summary="Get alert subsystem health")
def alerts_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "alerts",
    }