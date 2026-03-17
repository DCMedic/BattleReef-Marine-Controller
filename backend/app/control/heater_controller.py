from __future__ import annotations

from app.services.device_manager import DeviceManager
from app.services.sensor_service import SensorService


class HeaterController:
    def __init__(
        self,
        device_manager: DeviceManager,
        sensor_service: SensorService,
        heater_name: str,
        target_temp_f: float = 78.5,
        hysteresis_f: float = 0.5,
        max_temp_f: float = 82.0,
    ) -> None:
        self.device_manager = device_manager
        self.sensor_service = sensor_service
        self.heater_name = heater_name
        self.target_temp_f = target_temp_f
        self.hysteresis_f = hysteresis_f
        self.max_temp_f = max_temp_f

    def evaluate(self) -> dict[str, object]:
        telemetry = self.sensor_service.read_all()
        temperature_f = float(telemetry["temperature_f"])

        heater = self.device_manager.get(self.heater_name)
        heater_snapshot = heater.snapshot()
        heater_is_on = bool(heater_snapshot["attributes"].get("power", False))

        if temperature_f >= self.max_temp_f:
            result = self.device_manager.command(
                name=self.heater_name,
                action="set_power",
                value=False,
            )
            return {
                "decision": "emergency_off",
                "reason": (
                    f"Temperature {temperature_f:.2f}F exceeded max threshold "
                    f"{self.max_temp_f:.2f}F."
                ),
                "telemetry": telemetry,
                "device": result,
            }

        lower_bound = self.target_temp_f - self.hysteresis_f
        upper_bound = self.target_temp_f + self.hysteresis_f

        if temperature_f <= lower_bound and not heater_is_on:
            result = self.device_manager.command(
                name=self.heater_name,
                action="set_power",
                value=True,
            )
            return {
                "decision": "heater_on",
                "reason": (
                    f"Temperature {temperature_f:.2f}F is below lower bound "
                    f"{lower_bound:.2f}F."
                ),
                "telemetry": telemetry,
                "device": result,
            }

        if temperature_f >= upper_bound and heater_is_on:
            result = self.device_manager.command(
                name=self.heater_name,
                action="set_power",
                value=False,
            )
            return {
                "decision": "heater_off",
                "reason": (
                    f"Temperature {temperature_f:.2f}F is above upper bound "
                    f"{upper_bound:.2f}F."
                ),
                "telemetry": telemetry,
                "device": result,
            }

        return {
            "decision": "hold",
            "reason": f"Temperature {temperature_f:.2f}F is within control band.",
            "telemetry": telemetry,
            "device": heater_snapshot,
        }