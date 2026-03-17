from __future__ import annotations

from app.devices.base_device import BaseDevice


class DeviceManager:
    def __init__(self) -> None:
        self._devices: dict[str, BaseDevice] = {}

    def register(self, device: BaseDevice) -> None:
        self._devices[device.name] = device

    def get(self, name: str) -> BaseDevice:
        if name not in self._devices:
            raise KeyError(f"Device '{name}' not found.")
        return self._devices[name]

    def inventory(self) -> list[dict[str, object]]:
        return [device.snapshot() for device in self._devices.values()]

    def command(
        self,
        name: str,
        action: str,
        value: float | int | str | None = None,
    ) -> dict[str, object]:
        device = self.get(name)
        return device.command(action=action, value=value)