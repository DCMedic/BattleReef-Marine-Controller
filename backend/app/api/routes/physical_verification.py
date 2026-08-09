from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.authz import Principal, require_role
from app.db.session import get_db
from app.services.physical_verification_service import PhysicalVerificationService

router = APIRouter(prefix="/physical-verification", tags=["physical-verification"])


@router.post("/evaluate")
def evaluate_physical_state(
    principal: Principal = Depends(require_role("engineer")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    results = PhysicalVerificationService(db).evaluate()
    return {"requested_by": principal.username, "items": results, "count": len(results)}
