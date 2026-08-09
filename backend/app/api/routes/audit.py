from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit import AuditEventListResponse, AuditEventResponse, AuditIntegrityResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


def _response(record) -> AuditEventResponse:
    return AuditEventResponse(
        id=record.id,
        occurred_at=record.occurred_at,
        event_type=record.event_type,
        severity=record.severity,
        outcome=record.outcome,
        source=record.source,
        actor_type=record.actor_type,
        actor_id=record.actor_id,
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        correlation_id=record.correlation_id,
        message=record.message,
        details=record.details,
        previous_hash=record.previous_hash,
        event_hash=record.event_hash,
    )


@router.get("", response_model=AuditEventListResponse, summary="List persistent audit events")
def list_audit_events(
    limit: int = Query(default=100, ge=1, le=1000),
    event_type: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    correlation_id: str | None = None,
    db: Session = Depends(get_db),
):
    records = AuditService(db).list_events(
        limit=limit,
        event_type=event_type,
        severity=severity,
        source=source,
        correlation_id=correlation_id,
    )
    return AuditEventListResponse(items=[_response(record) for record in records], count=len(records))


@router.get("/integrity", response_model=AuditIntegrityResponse, summary="Verify audit hash chain")
def verify_audit_integrity(
    limit: int = Query(default=10000, ge=1, le=100000),
    db: Session = Depends(get_db),
):
    return AuditIntegrityResponse(**AuditService(db).verify_chain(limit=limit))
