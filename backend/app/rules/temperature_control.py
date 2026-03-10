from dataclasses import dataclass


@dataclass(slots=True)
class TemperatureRuleSettings:
    sensor_key: str = "tank_temp_main"
    heater_device_key: str = "heater_main"
    low_threshold_f: float = 77.5
    high_threshold_f: float = 78.3
    enabled: bool = True


def evaluate_temperature_control(
    temperature_f: float,
    settings: TemperatureRuleSettings,
) -> dict | None:
    if not settings.enabled:
        return None

    if temperature_f < settings.low_threshold_f:
        return {
            "target_device": settings.heater_device_key,
            "command_type": "set_power",
            "command_payload": {
                "power": True,
                "reason": "temperature_below_low_threshold",
                "temperature_f": temperature_f,
                "low_threshold_f": settings.low_threshold_f,
                "high_threshold_f": settings.high_threshold_f,
            },
        }

    if temperature_f > settings.high_threshold_f:
        return {
            "target_device": settings.heater_device_key,
            "command_type": "set_power",
            "command_payload": {
                "power": False,
                "reason": "temperature_above_high_threshold",
                "temperature_f": temperature_f,
                "low_threshold_f": settings.low_threshold_f,
                "high_threshold_f": settings.high_threshold_f,
            },
        }

    return None