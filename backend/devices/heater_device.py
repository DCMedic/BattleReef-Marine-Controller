from __future__ import annotations

from typing import Any

from backend.hardware.hal import HardwareAbstractionLayer
from .base_device import BaseDevice


class HeaterDevice(BaseDevice):
    def __init__(self, name: str, hal: HardwareAbstractionLayer, relay_channel: str) -> None:
        super().__init__(name=name, kind="heater")
        self.hal = hal
        self.relay_channel = relay_channel
        self.state.attributes.update({
            "power": False,
            "relay_channel": relay_channel,
        })

    def on(self) -> dict[str, Any]:
        self.hal.digital_write(self.relay_channel, True)
        self.update_state("on", power=True)
        return self.snapshot()

    def off(self) -> dict[str, Any]:
        self.hal.digital_write(self.relay_channel, False)
        self.update_state("off", power=False)
        return self.snapshot()

    def execute(self, action: str, value: Any | None = None) -> dict[str, Any]:
        normalized = action.strip().lower()
        if normalized == "on":
            return self.on()
        if normalized == "off":
            return self.off()
        raise ValueError(f"Unsupported heater action: {action}")