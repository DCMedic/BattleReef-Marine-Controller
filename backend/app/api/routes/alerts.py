from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.runtime_alerts import runtime_alerts


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", summary="List active alerts")
def list_alerts() -> dict[str, object]:
    items = runtime_alerts.list_active()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "count": len(items),
        "status": "ok",
    }


@router.get("/health", summary="Get alert subsystem health")
def alerts_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "alerts",
    }