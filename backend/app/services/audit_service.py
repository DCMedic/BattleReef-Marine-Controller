from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models.audit_event import AuditEventRecord
from app.schemas.audit import AuditEventCreate

AUDIT_LOCK_ID = 424242
GENESIS_HASH = "0" * 64


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.model = AuditEventRecord

    @staticmethod
    def canonical_payload(
        *,
        occurred_at: datetime,
        event_type: str,
        severity: str,
        outcome: str,
        source: str,
        actor_type: str,
        actor_id: str | None,
        entity_type: str | None,
        entity_id: str | None,
        correlation_id: str | None,
        message: str,
        details: dict[str, Any],
        previous_hash: str | None,
    ) -> str:
        payload = {
            "occurred_at": occurred_at.astimezone(timezone.utc).isoformat(),
            "event_type": event_type,
            "severity": severity,
            "outcome": outcome,
            "source": source,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "correlation_id": correlation_id,
            "message": message,
            "details": details,
            "previous_hash": previous_hash,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

    @classmethod
    def calculate_hash(cls, **kwargs) -> str:
        return hashlib.sha256(cls.canonical_payload(**kwargs).encode("utf-8")).hexdigest()

    def append(self, event: AuditEventCreate) -> AuditEventRecord:
        # Serialize writers so the append-only hash chain has a single deterministic head.
        self.db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": AUDIT_LOCK_ID})
        previous = self.db.scalar(select(self.model).order_by(self.model.id.desc()).limit(1))
        previous_hash = previous.event_hash if previous is not None else GENESIS_HASH
        occurred_at = datetime.now(timezone.utc)

        values = dict(
            occurred_at=occurred_at,
            event_type=event.event_type,
            severity=event.severity,
            outcome=event.outcome,
            source=event.source,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            correlation_id=event.correlation_id,
            message=event.message,
            details=event.details,
            previous_hash=previous_hash,
        )
        event_hash = self.calculate_hash(**values)
        record = self.model(**values, event_hash=event_hash)

        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def list_events(
        self,
        *,
        limit: int = 100,
        event_type: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        correlation_id: str | None = None,
    ) -> list[AuditEventRecord]:
        stmt = select(self.model)
        if event_type:
            stmt = stmt.where(self.model.event_type == event_type)
        if severity:
            stmt = stmt.where(self.model.severity == severity)
        if source:
            stmt = stmt.where(self.model.source == source)
        if correlation_id:
            stmt = stmt.where(self.model.correlation_id == correlation_id)
        stmt = stmt.order_by(self.model.id.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def verify_chain(self, limit: int = 10000) -> dict[str, Any]:
        records = list(self.db.scalars(select(self.model).order_by(self.model.id.asc()).limit(limit)).all())
        expected_previous = GENESIS_HASH

        for record in records:
            if record.previous_hash != expected_previous:
                return {
                    "valid": False,
                    "checked": records.index(record),
                    "first_invalid_id": record.id,
                    "reason": "previous_hash_mismatch",
                }

            calculated = self.calculate_hash(
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
                details=record.details or {},
                previous_hash=record.previous_hash,
            )
            if calculated != record.event_hash:
                return {
                    "valid": False,
                    "checked": records.index(record),
                    "first_invalid_id": record.id,
                    "reason": "event_hash_mismatch",
                }
            expected_previous = record.event_hash

        return {"valid": True, "checked": len(records), "first_invalid_id": None, "reason": None}
