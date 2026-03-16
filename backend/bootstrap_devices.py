from __future__ import annotations

import os
from dataclasses import dataclass

from backend.control.heater_controller import HeaterController
from backend.devices.feeder_device import FeederDevice
from backend.devices.heater_device import HeaterDevice
from backend.devices.wavemaker_device import WavemakerDevice
from backend.hardware.gpio_hal import GPIOHAL
from backend.hardware.hal import HardwareAbstractionLayer
from backend.hardware.mock_hal import MockHAL
from backend.services.device_manager import DeviceManager
from backend.services.sensor_service import SensorService


def _get_env_str(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value if value else default


def _get_env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def create_hal() -> HardwareAbstractionLayer:
    driver = _get_env_str("BATTLE_REEF_HAL", "mock").lower()
    if driver == "gpio":
        return GPIOHAL()
    return MockHAL()


@dataclass(frozen=True)
class AppServices:
    hal: HardwareAbstractionLayer
    device_manager: DeviceManager
    sensor_service: SensorService
    heater_controller: HeaterController


def build_services() -> AppServices:
    hal = create_hal()
    device_manager = DeviceManager()
    sensor_service = SensorService(hal)

    heater_name = _get_env_str("HEATER_DEVICE_NAME", "heater_main")
    heater_relay = _get_env_str("HEATER_RELAY_CHANNEL", "relay_1")

    feeder_name = _get_env_str("FEEDER_DEVICE_NAME", "feeder_main")
    feeder_channel = _get_env_str("FEEDER_RELAY_CHANNEL", "relay_2")

    wavemaker_name = _get_env_str("WAVEMAKER_DEVICE_NAME", "wavemaker_left")
    wavemaker_pwm = _get_env_str("WAVEMAKER_PWM_CHANNEL", "pwm_1")

    heater = HeaterDevice(
        name=heater_name,
        hal=hal,
        relay_channel=heater_relay,
    )
    feeder = FeederDevice(
        name=feeder_name,
        hal=hal,
        channel=feeder_channel,
    )
    wavemaker = WavemakerDevice(
        name=wavemaker_name,
        hal=hal,
        pwm_channel=wavemaker_pwm,
    )

    device_manager.register(heater)
    device_manager.register(feeder)
    device_manager.register(wavemaker)

    heater_controller = HeaterController(
        device_manager=device_manager,
        sensor_service=sensor_service,
        heater_name=heater_name,
        target_temp_f=_get_env_float("HEATER_TARGET_TEMP_F", 78.5),
        hysteresis_f=_get_env_float("HEATER_HYSTERESIS_F", 0.5),
        max_temp_f=_get_env_float("HEATER_MAX_TEMP_F", 82.0),
    )

    return AppServices(
        hal=hal,
        device_manager=device_manager,
        sensor_service=sensor_service,
        heater_controller=heater_controller,
    )


services = build_services()

hal = services.hal
manager = services.device_manager
sensors = services.sensor_service
heater_control = services.heater_controller


def get_services() -> AppServices:
    return services


def get_system_status() -> dict[str, object]:
    return {
        "hal": hal.metadata(),
        "device_count": len(manager.inventory()),
        "devices": manager.inventory(),
    }