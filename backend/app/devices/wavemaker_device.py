from __future__ import annotations

from datetime import datetime, timezone

from app.devices.base_device import BaseDevice
from app.hardware.hal import HardwareAbstractionLayer


class WavemakerDevice(BaseDevice):
    def __init__(
        self,
        name: str,
        hal: HardwareAbstractionLayer,
        pwm_channel: str,
    ) -> None:
        super().__init__(name=name, kind="wavemaker")
        self.hal = hal
        self.pwm_channel = pwm_channel
        self.attributes = {
            "pwm_channel": pwm_channel,
            "intensity": 0,
            "power": False,
        }

    def _mark_updated(self) -> None:
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def command(self, action: str, value: float | int | str | None = None) -> dict[str, object]:
        if action == "set_power":
            power = bool(value)
            if not power:
                self.hal.set_pwm(self.pwm_channel, 0)
                self.attributes["intensity"] = 0
            self.attributes["power"] = power
            self.last_command = f"set_power:{power}"
            self._mark_updated()
            return self.snapshot()

        if action == "set_intensity":
            intensity = int(float(value)) if value is not None else 0
            if intensity < 0 or intensity > 100:
                raise ValueError("Intensity must be between 0 and 100.")

            self.hal.set_pwm(self.pwm_channel, intensity)
            self.attributes["intensity"] = intensity
            self.attributes["power"] = intensity > 0
            self.last_command = f"set_intensity:{intensity}"
            self._mark_updated()
            return self.snapshot()

        raise ValueError(f"Unsupported wavemaker action: {action}")