from __future__ import annotations

from typing import Any

from backend.hardware.hal import HardwareAbstractionLayer


class MockHAL(HardwareAbstractionLayer):
    def __init__(self) -> None:
        self.digital_channels: dict[str, bool] = {}
        self.analog_channels: dict[str, float] = {}
        self.pwm_channels: dict[str, float] = {}
        self.temperature_channels: dict[str, float] = {"temp_main": 78.2}
        self.ph_channels: dict[str, float] = {"ph_main": 8.10}
        self.salinity_channels: dict[str, float] = {"salinity_main": 35.0}

    def digital_write(self, channel: str, state: bool) -> None:
        self.digital_channels[channel] = state

    def digital_read(self, channel: str) -> bool:
        return self.digital_channels.get(channel, False)

    def analog_read(self, channel: str) -> float:
        return self.analog_channels.get(channel, 0.0)

    def pwm_write(self, channel: str, duty_cycle: float) -> None:
        self.pwm_channels[channel] = max(0.0, min(100.0, duty_cycle))

    def read_temperature(self, channel: str) -> float:
        return self.temperature_channels.get(channel, 0.0)

    def read_ph(self, channel: str) -> float:
        return self.ph_channels.get(channel, 0.0)

    def read_salinity(self, channel: str) -> float:
        return self.salinity_channels.get(channel, 0.0)

    def metadata(self) -> dict[str, Any]:
        return {
            "driver": "mock",
            "digital_channels": list(self.digital_channels.keys()),
            "temperature_channels": list(self.temperature_channels.keys()),
            "ph_channels": list(self.ph_channels.keys()),
            "salinity_channels": list(self.salinity_channels.keys()),
            "pwm_channels": list(self.pwm_channels.keys()),
        }