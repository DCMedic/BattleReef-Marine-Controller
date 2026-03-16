from __future__ import annotations

from typing import Any

from backend.devices.base_device import BaseDevice
from backend.hardware.hal import HardwareAbstractionLayer


class FeederDevice(BaseDevice):
    def __init__(self, name: str, hal: HardwareAbstractionLayer, channel: str) -> None:
        super().__init__(name=name, kind="feeder")
        self.hal = hal
        self.channel = channel
        self.state.attributes.update(
            {
                "last_feed_seconds": 0,
                "channel": channel,
            }
        )

    def feed(self, seconds: int = 2) -> dict[str, Any]:
        self.hal.digital_write(self.channel, True)
        self.hal.digital_write(self.channel, False)
        self.update_state("feed", last_feed_seconds=seconds)
        return self.snapshot()

    def execute(self, action: str, value: Any | None = None) -> dict[str, Any]:
        normalized = action.strip().lower()
        if normalized == "feed":
            seconds = int(value) if value is not None else 2
            return self.feed(seconds=seconds)
        raise ValueError(f"Unsupported feeder action: {action}")