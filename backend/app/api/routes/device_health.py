from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.db.session import get_db
from app.services.device_health_service import DeviceHealthService

router = APIRouter(prefix="/device-health", tags=["device-health"])


class DeviceHealthResponse(BaseModel):
    device_key: str
    status: str
    score: float
    last_seen_at: datetime | None
    ack_latency_ms: float | None
    consecutive_failures: int
    evidence: dict
    evaluated_at: datetime


def _response(record) -> DeviceHealthResponse:
    return DeviceHealthResponse(
        device_key=record.device_key,
        status=record.status,
        score=record.score,
        last_seen_at=record.last_seen_at,
        ack_latency_ms=record.ack_latency_ms,
        consecutive_failures=record.consecutive_failures,
        evidence=record.evidence or {},
        evaluated_at=record.evaluated_at,
    )


@router.get("", response_model=list[DeviceHealthResponse])
def list_device_health(db: Session = Depends(get_db)):
    return [_response(r) for r in DeviceHealthService(db).list_health()]


@router.post("/evaluate", response_model=list[DeviceHealthResponse])
def evaluate_device_health(
    _: Principal = Depends(require_role("engineer")),
    db: Session = Depends(get_db),
):
    return [_response(r) for r in DeviceHealthService(db).evaluate_all()]
