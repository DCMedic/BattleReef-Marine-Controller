from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.schemas.system import SystemSummaryResponse
from app.services.audit_service import AuditService
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/summary", response_model=SystemSummaryResponse)
def get_system_summary(db: Session = Depends(get_db)) -> SystemSummaryResponse:
    return SystemService(db).get_summary()


@router.get("/health")
def get_system_health(db: Session = Depends(get_db)) -> dict[str, object]:
    summary = SystemService(db).get_summary()
    return {"status": "ok", "generated_at": summary.generated_at, "timescale_status": summary.timescale_status.model_dump(), "counts": summary.counts.model_dump()}


@router.post("/ensure-timescale")
def ensure_timescale(
    principal: Principal = Depends(require_role("administrator")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = SystemService(db).ensure_timescale()
    AuditService(db).append(AuditEventCreate(
        event_type="administrator.ensure_timescale", severity="warning", source="api.system",
        actor_type=principal.principal_type, actor_id=principal.username, entity_type="database", entity_id="timescaledb",
        message="TimescaleDB ensure operation requested.", details={"role": principal.role, "result": result},
    ))
    return result
