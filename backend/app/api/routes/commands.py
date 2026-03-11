from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.command import CommandCreateRequest, CommandListResponse, CommandResponse
from app.services.command_service import CommandService
from app.services.rule_engine import RuleEngineService

router = APIRouter(prefix="/commands", tags=["commands"])


@router.get("", response_model=CommandListResponse)
def list_commands(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    service = CommandService(db)
    records = service.list_recent(limit=limit)

    return CommandListResponse(
        items=[
            CommandResponse(
                id=record.id,
                requested_at=record.requested_at,
                requested_by=record.requested_by,
                target_device=record.target_device,
                command_type=record.command_type,
                command_payload=record.command_payload,
                status=record.status,
                acknowledged_at=record.acknowledged_at,
                completed_at=record.completed_at,
                error_message=record.error_message,
            )
            for record in records
        ]
    )


@router.post("", response_model=CommandResponse)
def create_command(
    payload: CommandCreateRequest,
    db: Session = Depends(get_db),
):
    service = CommandService(db)
    record = service.create_command(payload)

    return CommandResponse(
        id=record.id,
        requested_at=record.requested_at,
        requested_by=record.requested_by,
        target_device=record.target_device,
        command_type=record.command_type,
        command_payload=record.command_payload,
        status=record.status,
        acknowledged_at=record.acknowledged_at,
        completed_at=record.completed_at,
        error_message=record.error_message,
    )


@router.post("/evaluate/temperature")
def evaluate_temperature_rule(
    db: Session = Depends(get_db),
):
    service = RuleEngineService(db)
    return service.evaluate_temperature_rule()


@router.post("/evaluate/schedule")
def evaluate_schedule_rules(
    db: Session = Depends(get_db),
):
    service = RuleEngineService(db)
    return service.evaluate_scheduled_automation()