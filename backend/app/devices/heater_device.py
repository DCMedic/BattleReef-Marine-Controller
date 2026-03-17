from __future__ import annotations

from datetime import datetime, timezone

from app.devices.base_device import BaseDevice
from app.hardware.hal import HardwareAbstractionLayer


class HeaterDevice(BaseDevice):
    def __init__(
        self,
        name: str,
        hal: HardwareAbstractionLayer,
        relay_channel: str,
    ) -> None:
        super().__init__(name=name, kind="heater")
        self.hal = hal
        self.relay_channel = relay_channel
        self.attributes = {
            "relay_channel": relay_channel,
            "power": False,
        }

    def _mark_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def command(self, action: str, value: float | int | str | None = None) -> dict[str, object]:
        if action != "set_power":
            raise ValueError(f"Unsupported heater action: {action}")

        power = bool(value)
        self.hal.set_relay(self.relay_channel, power)
        self.attributes["power"] = power
        self.last_command = f"set_power:{power}"
        self._mark_updated()
        return self.snapshot()