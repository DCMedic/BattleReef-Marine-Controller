from __future__ import annotations

from datetime import datetime, timezone

from app.devices.base_device import BaseDevice
from app.hardware.hal import HardwareAbstractionLayer


class FeederDevice(BaseDevice):
    def __init__(
        self,
        name: str,
        hal: HardwareAbstractionLayer,
        channel: str,
    ) -> None:
        super().__init__(name=name, kind="feeder")
        self.hal = hal
        self.channel = channel
        self.attributes = {
            "channel": channel,
            "last_feed_seconds": 0.0,
            "power": False,
        }

    def _mark_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def command(self, action: str, value: float | int | str | None = None) -> dict[str, object]:
        if action == "feed":
            duration_seconds = float(value) if value is not None else 3.0
            if duration_seconds <= 0:
                raise ValueError("Feed duration must be greater than zero.")

            self.hal.set_relay(self.channel, True)
            self.hal.set_relay(self.channel, False)

            self.attributes["last_feed_seconds"] = duration_seconds
            self.attributes["power"] = False
            self.last_command = f"feed:{duration_seconds}"
            self._mark_updated()
            return self.snapshot()

        if action == "set_power":
            power = bool(value)
            self.hal.set_relay(self.channel, power)
            self.attributes["power"] = power
            self.last_command = f"set_power:{power}"
            self._mark_updated()
            return self.snapshot()

        raise ValueError(f"Unsupported feeder action: {action}")