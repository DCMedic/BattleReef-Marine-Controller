from __future__ import annotations

from typing import Any

from backend.devices.base_device import BaseDevice
from backend.hardware.hal import HardwareAbstractionLayer


class WavemakerDevice(BaseDevice):
    def __init__(self, name: str, hal: HardwareAbstractionLayer, pwm_channel: str) -> None:
        super().__init__(name=name, kind="wavemaker")
        self.hal = hal
        self.pwm_channel = pwm_channel
        self.state.attributes.update(
            {
                "intensity": 0.0,
                "pwm_channel": pwm_channel,
            }
        )

    def set_intensity(self, intensity: float) -> dict[str, Any]:
        safe_value = max(0.0, min(100.0, float(intensity)))
        self.hal.pwm_write(self.pwm_channel, safe_value)
        self.update_state("set_intensity", intensity=safe_value)
        return self.snapshot()

    def off(self) -> dict[str, Any]:
        return self.set_intensity(0.0)

    def execute(self, action: str, value: Any | None = None) -> dict[str, Any]:
        normalized = action.strip().lower()
        if normalized in {"set", "intensity", "set_intensity"}:
            if value is None:
                raise ValueError("Intensity value is required")
            return self.set_intensity(float(value))
        if normalized == "off":
            return self.off()
        raise ValueError(f"Unsupported wavemaker action: {action}")