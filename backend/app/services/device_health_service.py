from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.runtime_alerts import runtime_alerts
from app.db.models.command import CommandRecord
from app.db.models.device_health import DeviceHealthRecord
from app.db.models.device_state import DeviceStateRecord
from app.db.models.telemetry import TelemetryReading
from app.schemas.audit import AuditEventCreate
from app.services.audit_service import AuditService


class DeviceHealthService:
    """Derive device/node health from persisted evidence and independent physical verification."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def classify(score: float, has_evidence: bool = True) -> str:
        if not has_evidence:
            return "unknown"
        if score >= 85:
            return "healthy"
        if score >= 60:
            return "degraded"
        return "critical"

    @staticmethod
    def freshness_penalty(age_seconds: float | None) -> tuple[float, str | None]:
        if age_seconds is None:
            return 80.0, "no_recent_evidence"
        if age_seconds > 300:
            return 70.0, "evidence_stale_over_5m"
        if age_seconds > 120:
            return 40.0, "evidence_stale_over_2m"
        if age_seconds > 60:
            return 15.0, "evidence_stale_over_1m"
        return 0.0, None

    def _keys(self) -> list[str]:
        keys = {row[0] for row in self.db.query(TelemetryReading.source_node).distinct().all()}
        keys.update(row[0] for row in self.db.query(DeviceStateRecord.device_key).distinct().all())
        keys.update(row[0] for row in self.db.query(CommandRecord.target_device).distinct().all())
        return sorted(k for k in keys if k)

    def evaluate_device(self, device_key: str, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        window_start = now - timedelta(hours=24)
        telemetry = (
            self.db.query(TelemetryReading)
            .filter(TelemetryReading.source_node == device_key)
            .order_by(desc(TelemetryReading.reading_time))
            .limit(25)
            .all()
        )
        state = self.db.query(DeviceStateRecord).filter(DeviceStateRecord.device_key == device_key).first()
        commands = (
            self.db.query(CommandRecord)
            .filter(CommandRecord.target_device == device_key, CommandRecord.requested_at >= window_start)
            .order_by(desc(CommandRecord.requested_at))
            .limit(50)
            .all()
        )

        seen_times = [r.reading_time for r in telemetry]
        if state is not None:
            seen_times.append(state.updated_at)
        seen_times.extend(c.completed_at for c in commands if c.completed_at is not None)
        last_seen = max(seen_times) if seen_times else None
        age_seconds = max(0.0, (now - last_seen).total_seconds()) if last_seen else None

        score = 100.0
        reasons: list[str] = []
        penalty, reason = self.freshness_penalty(age_seconds)
        score -= penalty
        if reason:
            reasons.append(reason)

        bad_quality = sum(1 for r in telemetry if str(r.quality).lower() != "good")
        if bad_quality:
            score -= min(30.0, bad_quality * 6.0)
            reasons.append(f"telemetry_quality_non_good:{bad_quality}")

        failures = [c for c in commands if c.status in {"failed", "timeout"}]
        state_mismatches = [c for c in failures if "mismatch" in str(c.error_message or "").lower()]
        if failures:
            score -= min(45.0, len(failures) * 15.0)
            reasons.append(f"command_failures_24h:{len(failures)}")
        if state_mismatches:
            score -= min(35.0, len(state_mismatches) * 20.0)
            reasons.append(f"ack_state_mismatches_24h:{len(state_mismatches)}")

        latencies = [
            (c.acknowledged_at - c.last_dispatched_at).total_seconds() * 1000.0
            for c in commands
            if c.acknowledged_at is not None
            and c.last_dispatched_at is not None
            and c.acknowledged_at >= c.last_dispatched_at
        ]
        ack_latency_ms = mean(latencies) if latencies else None
        if ack_latency_ms is not None and ack_latency_ms > 5000:
            score -= 25.0
            reasons.append("ack_latency_over_5s")
        elif ack_latency_ms is not None and ack_latency_ms > 2000:
            score -= 10.0
            reasons.append("ack_latency_over_2s")

        physical_alerts = [
            item
            for item in runtime_alerts.list_active()
            if item.get("source") == "physical_verification"
            and (item.get("metadata") or {}).get("device_key") == device_key
        ]
        physical_critical = [item for item in physical_alerts if item.get("severity") == "critical"]
        physical_warning = [item for item in physical_alerts if item.get("severity") != "critical"]
        if physical_critical:
            score -= 60.0
            reasons.append(f"independent_physical_critical_failures:{len(physical_critical)}")
        if physical_warning:
            score -= min(25.0, len(physical_warning) * 15.0)
            reasons.append(f"independent_physical_degraded_checks:{len(physical_warning)}")

        score = max(0.0, min(100.0, round(score, 1)))
        has_evidence = bool(telemetry or state or commands or physical_alerts)
        status = self.classify(score, has_evidence)
        return {
            "device_key": device_key,
            "status": status,
            "score": score,
            "last_seen_at": last_seen,
            "age_seconds": age_seconds,
            "ack_latency_ms": round(ack_latency_ms, 1) if ack_latency_ms is not None else None,
            "consecutive_failures": len(failures),
            "evidence": {
                "telemetry_samples": len(telemetry),
                "non_good_quality_samples": bad_quality,
                "commands_24h": len(commands),
                "command_failures_24h": len(failures),
                "ack_state_mismatches_24h": len(state_mismatches),
                "independent_physical_critical_failures": [item["key"] for item in physical_critical],
                "independent_physical_degraded_checks": [item["key"] for item in physical_warning],
                "reasons": reasons,
            },
            "evaluated_at": now,
        }

    def evaluate_all(self) -> list[DeviceHealthRecord]:
        results: list[DeviceHealthRecord] = []
        for key in self._keys():
            snapshot = self.evaluate_device(key)
            record = self.db.query(DeviceHealthRecord).filter(DeviceHealthRecord.device_key == key).first()
            previous_status = record.status if record is not None else None
            if record is None:
                record = DeviceHealthRecord(device_key=key)
            record.status = snapshot["status"]
            record.score = snapshot["score"]
            record.last_seen_at = snapshot["last_seen_at"]
            record.ack_latency_ms = snapshot["ack_latency_ms"]
            record.consecutive_failures = snapshot["consecutive_failures"]
            record.evidence = snapshot["evidence"]
            record.evaluated_at = snapshot["evaluated_at"]
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            self._sync_alert(record)
            if previous_status != record.status:
                AuditService(self.db).append(
                    AuditEventCreate(
                        event_type="health.device_status_changed",
                        severity="critical" if record.status == "critical" else "warning" if record.status == "degraded" else "info",
                        outcome=record.status,
                        source="device_health",
                        actor_type="system",
                        actor_id="device_health_monitor",
                        entity_type="device",
                        entity_id=record.device_key,
                        message=f"Device health changed from {previous_status or 'unobserved'} to {record.status}.",
                        details={"score": record.score, "evidence": record.evidence},
                    )
                )
            results.append(record)
        return results

    @staticmethod
    def _sync_alert(record: DeviceHealthRecord) -> None:
        key = f"device_health_{record.device_key}"
        if record.status in {"degraded", "critical"}:
            runtime_alerts.upsert(
                key=key,
                severity="critical" if record.status == "critical" else "warning",
                title="Device Health Degraded",
                message=f"{record.device_key} health is {record.status} ({record.score:.0f}/100).",
                source="device_health",
                metadata={"device_key": record.device_key, "score": record.score, "evidence": record.evidence},
            )
        else:
            runtime_alerts.clear(key)

    def list_health(self) -> list[DeviceHealthRecord]:
        return self.db.query(DeviceHealthRecord).order_by(DeviceHealthRecord.score.asc()).all()
