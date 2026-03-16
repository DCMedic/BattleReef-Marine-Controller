from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.hardware.hal import HardwareAbstractionLayer


class SensorService:
    def __init__(self, hal: HardwareAbstractionLayer) -> None:
        self.hal = hal

    def read_all(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "temperature_f": float(self.hal.read_temperature("temp_main")),
            "ph": float(self.hal.read_ph("ph_main")),
            "salinity_ppt": float(self.hal.read_salinity("salinity_main")),
        }