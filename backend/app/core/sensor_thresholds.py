from __future__ import annotations

import os
from copy import deepcopy
from typing import Any


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


DEFAULT_SENSOR_THRESHOLDS: dict[str, dict[str, Any]] = {
    "orp_main": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_ORP_MIN_MV", 300.0),
        "max": _env_float("THRESHOLD_ORP_MAX_MV", 450.0),
        "label": "ORP",
        "unit": "mV",
        "enabled": True,
    },
    "dissolved_oxygen_main": {
        "severity": "critical",
        "min": _env_float("THRESHOLD_DO_MIN_MG_L", 6.0),
        "max": None,
        "label": "Dissolved Oxygen",
        "unit": "mg/L",
        "enabled": True,
    },
    "room_co2_main": {
        "severity": "warning",
        "min": None,
        "max": _env_float("THRESHOLD_ROOM_CO2_MAX_PPM", 1200.0),
        "label": "Room CO2",
        "unit": "ppm",
        "enabled": True,
    },
    "flow_return_main": {
        "severity": "critical",
        "min": _env_float("THRESHOLD_FLOW_RETURN_MIN_GPH", 500.0),
        "max": None,
        "label": "Return Flow",
        "unit": "gph",
        "enabled": True,
    },
    "flow_manifold_main": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_FLOW_MANIFOLD_MIN_GPH", 150.0),
        "max": None,
        "label": "Manifold Flow",
        "unit": "gph",
        "enabled": True,
    },
    "par_left": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_PAR_LEFT_MIN", 120.0),
        "max": _env_float("THRESHOLD_PAR_LEFT_MAX", 350.0),
        "label": "PAR Left",
        "unit": "umol/m2/s",
        "enabled": True,
    },
    "par_center": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_PAR_CENTER_MIN", 150.0),
        "max": _env_float("THRESHOLD_PAR_CENTER_MAX", 400.0),
        "label": "PAR Center",
        "unit": "umol/m2/s",
        "enabled": True,
    },
    "par_right": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_PAR_RIGHT_MIN", 120.0),
        "max": _env_float("THRESHOLD_PAR_RIGHT_MAX", 350.0),
        "label": "PAR Right",
        "unit": "umol/m2/s",
        "enabled": True,
    },
}

# Leak probes use the same numeric telemetry contract as every other sensor:
# 0.0 = dry, 1.0 = wet. Any non-dry value is treated fail-safe as a leak.
LEAK_EXPECTED_DRY_VALUE = _env_float("THRESHOLD_LEAK_DRY_VALUE", 0.0)
LEAK_SENSOR_KEYS = ["leak_probe_a", "leak_probe_b"]


def clone_default_thresholds() -> dict[str, dict[str, Any]]:
    return deepcopy(DEFAULT_SENSOR_THRESHOLDS)


def merge_threshold_overrides(
    defaults: dict[str, dict[str, Any]],
    overrides: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    merged = clone_default_thresholds()

    for sensor_key, override_values in overrides.items():
        if sensor_key not in merged:
            continue

        for field_name, value in override_values.items():
            merged[sensor_key][field_name] = value

    return merged
