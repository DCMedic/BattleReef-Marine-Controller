from __future__ import annotations

from abc import ABC, abstractmethod


class HardwareAbstractionLayer(ABC):
    @abstractmethod
    def set_relay(self, channel: str, state: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_pwm(self, channel: str, duty_cycle_percent: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_temperature_f(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def read_ph(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def read_salinity_ppt(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def metadata(self) -> dict[str, object]:
        raise NotImplementedError