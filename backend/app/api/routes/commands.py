from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.db.session import get_db
from app.schemas.audit import AuditEventCreate
from app.schemas.command import CommandCreateRequest, CommandListResponse, CommandResponse
from app.services.audit_service import AuditService
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
def list_commands(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)):
    return CommandListResponse(items=[_command_response(r) for r in CommandService(db).list_recent(limit=limit)])


@router.post("", response_model=CommandResponse)
def create_command(
    payload: CommandCreateRequest,
    principal: Principal = Depends(require_role("operator")),
    db: Session = Depends(get_db),
):
    authenticated_payload = payload.model_copy(update={"requested_by": principal.username})
    record = CommandService(db).create_command(authenticated_payload)
    AuditService(db).append(AuditEventCreate(
        event_type="operator.command_created", source="api.commands", actor_type=principal.principal_type,
        actor_id=principal.username, entity_type="command", entity_id=str(record.id),
        correlation_id=record.correlation_id, message=f"Command {record.id} created for {record.target_device}.",
        details={"role": principal.role, "target_device": record.target_device, "command_type": record.command_type, "delivery_policy": record.delivery_policy},
    ))
    return _command_response(record)


@router.post("/evaluate/temperature")
def evaluate_temperature_rule(
    principal: Principal = Depends(require_role("engineer")),
    db: Session = Depends(get_db),
):
    AuditService(db).append(AuditEventCreate(event_type="operator.rule_evaluation_requested", source="api.commands", actor_type=principal.principal_type, actor_id=principal.username, message="Manual temperature rule evaluation requested", details={"role": principal.role}))
    return RuleEngineService(db).evaluate_temperature_rule()


@router.post("/evaluate/schedule")
def evaluate_schedule_rules(
    principal: Principal = Depends(require_role("engineer")),
    db: Session = Depends(get_db),
):
    AuditService(db).append(AuditEventCreate(event_type="operator.schedule_evaluation_requested", source="api.commands", actor_type=principal.principal_type, actor_id=principal.username, message="Manual schedule evaluation requested", details={"role": principal.role}))
    return ScheduleEngine(db).evaluate()
