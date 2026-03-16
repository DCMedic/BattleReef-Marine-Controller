from __future__ import annotations

from typing import Any

from backend.hardware.hal import HardwareAbstractionLayer


class GPIOHAL(HardwareAbstractionLayer):
    def __init__(self) -> None:
        self._digital: dict[str, bool] = {}
        self._pwm: dict[str, float] = {}

    def digital_write(self, channel: str, state: bool) -> None:
        self._digital[channel] = state

    def digital_read(self, channel: str) -> bool:
        return self._digital.get(channel, False)

    def analog_read(self, channel: str) -> float:
        return 0.0

    def pwm_write(self, channel: str, duty_cycle: float) -> None:
        self._pwm[channel] = max(0.0, min(100.0, duty_cycle))

    def read_temperature(self, channel: str) -> float:
        return 0.0

    def read_ph(self, channel: str) -> float:
        return 0.0

    def read_salinity(self, channel: str) -> float:
        return 0.0

    def metadata(self) -> dict[str, Any]:
        return {
            "driver": "gpio",
            "digital_channels": list(self._digital.keys()),
            "pwm_channels": list(self._pwm.keys()),
        }