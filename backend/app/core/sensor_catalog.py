from __future__ import annotations

from typing import Any


SENSOR_CATALOG: list[dict[str, Any]] = [
    {"sensor_key": "tank_temp_main", "label": "Tank Temperature", "unit": "F", "category": "aquarium_core", "description": "Primary display tank water temperature."},
    {"sensor_key": "tank_temp_verify", "label": "Tank Temperature Verify", "unit": "F", "category": "verification", "description": "Independent secondary water-temperature channel used to challenge the primary temperature sensor."},
    {"sensor_key": "tank_ph_main", "label": "pH", "unit": "pH", "category": "aquarium_core", "description": "Primary aquarium pH reading."},
    {"sensor_key": "tank_salinity_main", "label": "Salinity", "unit": "ppt", "category": "aquarium_core", "description": "Primary aquarium salinity reading."},
    {"sensor_key": "sump_level_main", "label": "Sump Level", "unit": "in", "category": "aquarium_core", "description": "Main sump water level."},
    {"sensor_key": "sump_level_verify", "label": "Sump Level Verify", "unit": "in", "category": "verification", "description": "Independent secondary sump-level channel used to verify the primary level sensor."},
    {"sensor_key": "orp_main", "label": "ORP", "unit": "mV", "category": "water_quality", "description": "Oxidation reduction potential for water cleanliness and stability."},
    {"sensor_key": "dissolved_oxygen_main", "label": "Dissolved Oxygen", "unit": "mg/L", "category": "water_quality", "description": "Dissolved oxygen concentration in aquarium water."},
    {"sensor_key": "flow_return_main", "label": "Return Flow", "unit": "gph", "category": "verification", "description": "Independent flow rate through the main return line, used to verify return-pump operation."},
    {"sensor_key": "flow_manifold_main", "label": "Manifold Flow", "unit": "gph", "category": "flow", "description": "Flow rate through the secondary manifold or branch line."},
    {"sensor_key": "rpm_return_pump_main", "label": "Return Pump RPM", "unit": "rpm", "category": "verification", "description": "Optional independent tachometer or controller feedback used as a third return-pump verification signal."},
    {"sensor_key": "par_left", "label": "PAR Left", "unit": "umol/m2/s", "category": "lighting", "description": "Photosynthetically active radiation at the left side of the tank."},
    {"sensor_key": "par_center", "label": "PAR Center", "unit": "umol/m2/s", "category": "lighting", "description": "Photosynthetically active radiation at the center of the tank."},
    {"sensor_key": "par_right", "label": "PAR Right", "unit": "umol/m2/s", "category": "lighting", "description": "Photosynthetically active radiation at the right side of the tank."},
    {"sensor_key": "leak_probe_a", "label": "Leak Probe A", "unit": "state", "category": "safety", "description": "Leak detection probe near aquarium or sump area A."},
    {"sensor_key": "leak_probe_b", "label": "Leak Probe B", "unit": "state", "category": "safety", "description": "Leak detection probe near aquarium or sump area B."},
    {"sensor_key": "room_co2_main", "label": "Room CO2", "unit": "ppm", "category": "room_environment", "description": "Ambient room carbon dioxide concentration."},
    {"sensor_key": "power_monitor_main", "label": "Power Draw", "unit": "W", "category": "power", "description": "Live aggregate system power consumption."},
    {"sensor_key": "power_heater_main", "label": "Heater Power", "unit": "W", "category": "verification", "description": "Independent isolated heater-circuit power measurement used to verify heater relay state."},
    {"sensor_key": "power_return_pump_main", "label": "Return Pump Power", "unit": "W", "category": "verification", "description": "Independent isolated return-pump circuit power measurement used alongside flow to verify pump state."},
    {"sensor_key": "voc_main", "label": "VOC", "unit": "ppb", "category": "room_environment", "description": "Volatile organic compounds near the aquarium system."},
    {"sensor_key": "ambient_temp_room", "label": "Ambient Temperature", "unit": "F", "category": "room_environment", "description": "Fish room ambient air temperature."},
    {"sensor_key": "ambient_humidity_room", "label": "Ambient Humidity", "unit": "%", "category": "room_environment", "description": "Fish room relative humidity."},
]


DEFAULT_HISTORY_SENSOR_KEYS: list[str] = [item["sensor_key"] for item in SENSOR_CATALOG]
