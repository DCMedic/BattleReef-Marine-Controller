from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=120)
    severity: str = "info"
    outcome: str = "success"
    source: str
    actor_type: str = "system"
    actor_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    correlation_id: str | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEventResponse(BaseModel):
    id: int
    occurred_at: datetime
    event_type: str
    severity: str
    outcome: str
    source: str
    actor_type: str
    actor_id: str | None
    entity_type: str | None
    entity_id: str | None
    correlation_id: str | None
    message: str
    details: dict[str, Any]
    previous_hash: str | None
    event_hash: str


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    count: int


class AuditIntegrityResponse(BaseModel):
    valid: bool
    checked: int
    first_invalid_id: int | None = None
    reason: str | None = None
