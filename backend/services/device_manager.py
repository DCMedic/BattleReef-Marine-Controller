from __future__ import annotations

from typing import Any

from backend.devices.base_device import BaseDevice


class DeviceManager:
    def __init__(self) -> None:
        self._devices: dict[str, BaseDevice] = {}

    def register(self, device: BaseDevice) -> None:
        if device.name in self._devices:
            raise ValueError(f"Device already registered: {device.name}")
        self._devices[device.name] = device

    def get(self, name: str) -> BaseDevice:
        if name not in self._devices:
            raise KeyError(f"Unknown device: {name}")
        return self._devices[name]

    def command(self, name: str, action: str, value: Any | None = None) -> dict[str, Any]:
        device = self.get(name)
        return device.execute(action, value)

    def inventory(self) -> list[dict[str, Any]]:
        return [device.snapshot() for device in self._devices.values()]