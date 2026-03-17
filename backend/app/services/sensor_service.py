from __future__ import annotations

from datetime import datetime, timezone

from app.hardware.hal import HardwareAbstractionLayer


class SensorService:
    def __init__(self, hal: HardwareAbstractionLayer) -> None:
        self.hal = hal

    def read_all(self) -> dict[str, object]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature_f": self.hal.read_temperature_f(),
            "ph": self.hal.read_ph(),
            "salinity_ppt": self.hal.read_salinity_ppt(),
        }