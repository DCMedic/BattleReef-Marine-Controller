from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any


class RuntimeAlertStore:
    """
    Thread-safe in-memory alert store for active watchdog/safety alerts.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._alerts_by_key: dict[str, dict[str, Any]] = {}

    def upsert(
        self,
        *,
        key: str,
        severity: str,
        title: str,
        message: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            existing = self._alerts_by_key.get(key)

            if existing:
                existing["severity"] = severity
                existing["title"] = title
                existing["message"] = message
                existing["source"] = source
                existing["metadata"] = metadata or {}
                existing["updated_at"] = now
                return dict(existing)

            record = {
                "key": key,
                "severity": severity,
                "title": title,
                "message": message,
                "source": source,
                "metadata": metadata or {},
                "active": True,
                "created_at": now,
                "updated_at": now,
            }
            self._alerts_by_key[key] = record
            return dict(record)

    def clear(self, key: str) -> bool:
        with self._lock:
            if key in self._alerts_by_key:
                del self._alerts_by_key[key]
                return True
            return False

    def list_active(self) -> list[dict[str, Any]]:
        with self._lock:
            return sorted(
                (dict(item) for item in self._alerts_by_key.values()),
                key=lambda x: x["updated_at"],
                reverse=True,
            )


runtime_alerts = RuntimeAlertStore()