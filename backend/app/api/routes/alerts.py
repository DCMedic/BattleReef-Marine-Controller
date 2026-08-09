from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.runtime_alerts import runtime_alerts
from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService


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
    return {"status": "ok", "service": "alerts"}


@router.delete("/{alert_key}", summary="Clear a single active alert")
def clear_alert(alert_key: str, db: Session = Depends(get_db)) -> dict[str, object]:
    active = next((item for item in runtime_alerts.list_active() if item["key"] == alert_key), None)
    cleared = runtime_alerts.clear(alert_key)
    if not cleared:
        raise HTTPException(status_code=404, detail="Alert not found")

    AuditService(db).append(
        AuditEventCreate(
            event_type="operator.alert_cleared",
            source="api.alerts",
            actor_type="operator",
            actor_id="api_client",
            entity_type="runtime_alert",
            entity_id=alert_key,
            message=f"Active alert {alert_key} was manually cleared.",
            details={"alert": active or {}},
        )
    )
    return {"status": "ok", "cleared": alert_key}


@router.delete("", summary="Clear all active alerts")
def clear_all_alerts(db: Session = Depends(get_db)) -> dict[str, object]:
    items = runtime_alerts.list_active()
    for item in items:
        runtime_alerts.clear(item["key"])

    AuditService(db).append(
        AuditEventCreate(
            event_type="operator.alerts_cleared_all",
            severity="warning" if items else "info",
            source="api.alerts",
            actor_type="operator",
            actor_id="api_client",
            entity_type="runtime_alert_collection",
            message=f"Operator cleared {len(items)} active alert(s).",
            details={"cleared_keys": [item["key"] for item in items]},
        )
    )
    return {"status": "ok", "cleared_count": len(items)}
