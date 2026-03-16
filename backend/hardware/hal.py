from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class HardwareAbstractionLayer(ABC):
    @abstractmethod
    def digital_write(self, channel: str, state: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def digital_read(self, channel: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def analog_read(self, channel: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def pwm_write(self, channel: str, duty_cycle: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_temperature(self, channel: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def read_ph(self, channel: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def read_salinity(self, channel: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        raise NotImplementedError