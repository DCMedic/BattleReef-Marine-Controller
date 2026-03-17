from __future__ import annotations

from app.hardware.hal import HardwareAbstractionLayer


class GPIOHAL(HardwareAbstractionLayer):
    def __init__(self) -> None:
        self._relay_state: dict[str, bool] = {}
        self._pwm_state: dict[str, int] = {}

    def set_relay(self, channel: str, state: bool) -> None:
        self._relay_state[channel] = bool(state)

    def set_pwm(self, channel: str, duty_cycle_percent: int) -> None:
        self._pwm_state[channel] = max(0, min(100, int(duty_cycle_percent)))

    def read_temperature_f(self) -> float:
        return 78.0

    def read_ph(self) -> float:
        return 8.2

    def read_salinity_ppt(self) -> float:
        return 35.0

    def metadata(self) -> dict[str, object]:
        return {
            "driver": "gpio",
            "relay_channels": self._relay_state,
            "pwm_channels": self._pwm_state,
        }