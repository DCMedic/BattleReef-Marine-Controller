from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

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


@router.delete("/{alert_key}", summary="Clear a single active alert")
def clear_alert(alert_key: str) -> dict[str, object]:
    cleared = runtime_alerts.clear(alert_key)

    if not cleared:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "status": "ok",
        "cleared": alert_key,
    }


@router.delete("", summary="Clear all active alerts")
def clear_all_alerts() -> dict[str, object]:
    items = runtime_alerts.list_active()

    for item in items:
        runtime_alerts.clear(item["key"])

    return {
        "status": "ok",
        "cleared_count": len(items),
    }