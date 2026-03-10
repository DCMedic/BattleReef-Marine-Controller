from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.system import SystemSummaryResponse
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/summary", response_model=SystemSummaryResponse)
def get_system_summary(
    db: Session = Depends(get_db),
):
    service = SystemService(db)
    return service.get_summary()


@router.get("/health")
def get_system_health(
    db: Session = Depends(get_db),
):
    service = SystemService(db)
    summary = service.get_summary()

    return {
        "status": "ok",
        "generated_at": summary.generated_at,
        "timescale_status": summary.timescale_status.model_dump(),
        "counts": summary.counts.model_dump(),
    }


@router.post("/ensure-timescale")
def ensure_timescale(
    db: Session = Depends(get_db),
):
    service = SystemService(db)
    return service.ensure_timescale()