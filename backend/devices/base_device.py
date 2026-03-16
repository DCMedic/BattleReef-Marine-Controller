from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class DeviceState:
    name: str
    kind: str
    online: bool = True
    enabled: bool = True
    last_command: str | None = None
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    attributes: dict[str, Any] = field(default_factory=dict)


class BaseDevice(ABC):
    def __init__(self, name: str, kind: str) -> None:
        self.state = DeviceState(name=name, kind=kind)

    @property
    def name(self) -> str:
        return self.state.name

    @property
    def kind(self) -> str:
        return self.state.kind

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.state.name,
            "kind": self.state.kind,
            "online": self.state.online,
            "enabled": self.state.enabled,
            "last_command": self.state.last_command,
            "last_updated": self.state.last_updated,
            "attributes": self.state.attributes,
        }

    def update_state(self, command: str, **attributes: Any) -> None:
        self.state.last_command = command
        self.state.last_updated = datetime.now(UTC).isoformat()
        self.state.attributes.update(attributes)

    @abstractmethod
    def execute(self, action: str, value: Any | None = None) -> dict[str, Any]:
        raise NotImplementedError