from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schedule import (
    ScheduleCreateRequest,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=ScheduleListResponse)
def list_schedules(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    records = service.list_schedules(limit=limit)

    return ScheduleListResponse(
        items=[
            ScheduleResponse(
                id=record.id,
                device_key=record.device_key,
                schedule_type=record.schedule_type,
                name=record.name,
                enabled=record.enabled,
                config_payload=record.config_payload,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]
    )


@router.post("", response_model=ScheduleResponse)
def create_schedule(
    payload: ScheduleCreateRequest,
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    record = service.create_schedule(payload)

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


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    record = service.update_schedule(schedule_id, payload)

    if record is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

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


@router.post("/seed-defaults", response_model=ScheduleListResponse)
def seed_default_schedules(
    db: Session = Depends(get_db),
):
    service = ScheduleService(db)
    records = service.seed_defaults_if_empty()

    return ScheduleListResponse(
        items=[
            ScheduleResponse(
                id=record.id,
                device_key=record.device_key,
                schedule_type=record.schedule_type,
                name=record.name,
                enabled=record.enabled,
                config_payload=record.config_payload,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ]
    )