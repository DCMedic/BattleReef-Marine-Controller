from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.schemas.schedule import ScheduleCreateRequest, ScheduleListResponse, ScheduleResponse, ScheduleUpdateRequest
from app.services.audit_service import AuditService
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"])


def _response(record) -> ScheduleResponse:
    return ScheduleResponse(
        id=record.id,
        device_key=record.device_key,
        schedule_type=record.schedule_type,
        name=record.name,
        enabled=record.enabled,
        config_payload=record.config_payload,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _audit(db: Session, event_type: str, record, message: str) -> None:
    AuditService(db).append(
        AuditEventCreate(
            event_type=event_type,
            source="api.schedules",
            actor_type="operator",
            actor_id="api_client",
            entity_type="schedule",
            entity_id=str(record.id),
            message=message,
            details={
                "device_key": record.device_key,
                "schedule_type": record.schedule_type,
                "name": record.name,
                "enabled": record.enabled,
                "config_payload": record.config_payload,
            },
        )
    )


@router.get("", response_model=ScheduleListResponse)
def list_schedules(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)) -> ScheduleListResponse:
    records = ScheduleService(db).list_schedules(limit=limit)
    return ScheduleListResponse(items=[_response(record) for record in records])


@router.post("", response_model=ScheduleResponse)
def create_schedule(payload: ScheduleCreateRequest, db: Session = Depends(get_db)) -> ScheduleResponse:
    record = ScheduleService(db).create_schedule(payload)
    _audit(db, "operator.schedule_created", record, f"Schedule {record.id} created for {record.device_key}.")
    return _response(record)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: int, payload: ScheduleUpdateRequest, db: Session = Depends(get_db)) -> ScheduleResponse:
    record = ScheduleService(db).update_schedule(schedule_id, payload)
    if record is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    _audit(db, "operator.schedule_updated", record, f"Schedule {record.id} updated.")
    return _response(record)


@router.post("/seed-defaults", response_model=ScheduleListResponse)
def seed_default_schedules(db: Session = Depends(get_db)) -> ScheduleListResponse:
    records = ScheduleService(db).seed_defaults_if_empty()
    AuditService(db).append(
        AuditEventCreate(
            event_type="operator.schedule_defaults_seeded",
            source="api.schedules",
            actor_type="operator",
            actor_id="api_client",
            entity_type="schedule_collection",
            message=f"Default schedule seed operation completed with {len(records)} schedule(s).",
            details={"schedule_ids": [record.id for record in records]},
        )
    )
    return ScheduleListResponse(items=[_response(record) for record in records])
