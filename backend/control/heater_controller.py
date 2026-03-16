from __future__ import annotations


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

    def evaluate(self) -> dict[str, Any]:
        telemetry = self.sensor_service.read_all()
        current_temp = float(telemetry["temperature_f"])

        lower_bound = self.target_temp_f - self.hysteresis_f
        upper_bound = self.target_temp_f + self.hysteresis_f

        if current_temp >= self.max_temp_f:
            device_state = self.device_manager.command(self.heater_name, "off")
            return {
                "decision": "emergency_off",
                "reason": "temperature exceeded maximum safe limit",
                "telemetry": telemetry,
                "device": device_state,
            }

        if current_temp < lower_bound:
            device_state = self.device_manager.command(self.heater_name, "on")
            return {
                "decision": "heater_on",
                "reason": "temperature below lower bound",
                "telemetry": telemetry,
                "device": device_state,
            }

        if current_temp > upper_bound:
            device_state = self.device_manager.command(self.heater_name, "off")
            return {
                "decision": "heater_off",
                "reason": "temperature above upper bound",
                "telemetry": telemetry,
                "device": device_state,
            }

        device_state = self.device_manager.get(self.heater_name).snapshot()
        return {
            "decision": "hold",
            "reason": "temperature within acceptable range",
            "telemetry": telemetry,
            "device": device_state,
        }