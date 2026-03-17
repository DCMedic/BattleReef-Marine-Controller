from __future__ import annotations

import random

from app.hardware.hal import HardwareAbstractionLayer


class MockHAL(HardwareAbstractionLayer):
    def __init__(self) -> None:
        self._relay_state: dict[str, bool] = {}
        self._pwm_state: dict[str, int] = {}
        self._temperature_f = 78.0
        self._ph = 8.2
        self._salinity_ppt = 35.0

    def set_relay(self, channel: str, state: bool) -> None:
        self._relay_state[channel] = bool(state)

    def set_pwm(self, channel: str, duty_cycle_percent: int) -> None:
        self._pwm_state[channel] = max(0, min(100, int(duty_cycle_percent)))

    def read_temperature_f(self) -> float:
        self._temperature_f += random.uniform(-0.1, 0.1)
        return round(self._temperature_f, 2)

    def read_ph(self) -> float:
        self._ph += random.uniform(-0.02, 0.02)
        return round(self._ph, 2)

    def read_salinity_ppt(self) -> float:
        self._salinity_ppt += random.uniform(-0.05, 0.05)
        return round(self._salinity_ppt, 2)

    def metadata(self) -> dict[str, object]:
        return {
            "driver": "mock",
            "relay_channels": self._relay_state,
            "pwm_channels": self._pwm_state,
        }