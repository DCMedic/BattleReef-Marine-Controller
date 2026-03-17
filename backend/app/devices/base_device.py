from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class BaseDevice:
    def __init__(self, name: str, kind: str) -> None:
        self.name = name
        self.kind = kind
        self.online = True
        self.enabled = True
        self.last_command: str | None = None
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.attributes: dict[str, Any] = {}

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "online": self.online,
            "enabled": self.enabled,
            "last_command": self.last_command,
            "last_updated": self.last_updated,
            "attributes": self.attributes,
        }

    def command(self, action: str, value: float | int | str | None = None) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement command().")