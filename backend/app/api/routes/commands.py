from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.command import CommandCreateRequest, CommandListResponse, CommandResponse
from app.services.command_service import CommandService
from app.services.rule_engine import RuleEngineService
from app.services.schedule_engine import ScheduleEngine

router = APIRouter(prefix="/commands", tags=["commands"])


def _command_response(record) -> CommandResponse:
    return CommandResponse(
        id=record.id,
        correlation_id=record.correlation_id,
        requested_at=record.requested_at,
        requested_by=record.requested_by,
        target_device=record.target_device,
        command_type=record.command_type,
        command_payload=record.command_payload,
        delivery_policy=record.delivery_policy,
        status=record.status,
        dispatch_attempts=record.dispatch_attempts,
        max_attempts=record.max_attempts,
        last_dispatched_at=record.last_dispatched_at,
        ack_deadline=record.ack_deadline,
        acknowledged_at=record.acknowledged_at,
        verified_at=record.verified_at,
        completed_at=record.completed_at,
        error_message=record.error_message,
    )


@router.get("", response_model=CommandListResponse)
def list_commands(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    service = CommandService(db)
    records = service.list_recent(limit=limit)
    return CommandListResponse(items=[_command_response(record) for record in records])


@router.post("", response_model=CommandResponse)
def create_command(
    payload: CommandCreateRequest,
    db: Session = Depends(get_db),
):
    service = CommandService(db)
    record = service.create_command(payload)
    return _command_response(record)


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
    engine = ScheduleEngine(db)
    return engine.evaluate()
