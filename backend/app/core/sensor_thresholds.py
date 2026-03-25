from __future__ import annotations

import os
from typing import Any


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    cleaned = raw.strip()
    return cleaned if cleaned else default


SENSOR_THRESHOLDS: dict[str, dict[str, Any]] = {
    "orp_main": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_ORP_MIN_MV", 300.0),
        "max": _env_float("THRESHOLD_ORP_MAX_MV", 450.0),
        "label": "ORP",
        "unit": "mV",
    },
    "dissolved_oxygen_main": {
        "severity": "critical",
        "min": _env_float("THRESHOLD_DO_MIN_MG_L", 6.0),
        "label": "Dissolved Oxygen",
        "unit": "mg/L",
    },
    "room_co2_main": {
        "severity": "warning",
        "max": _env_float("THRESHOLD_ROOM_CO2_MAX_PPM", 1200.0),
        "label": "Room CO2",
        "unit": "ppm",
    },
    "flow_return_main": {
        "severity": "critical",
        "min": _env_float("THRESHOLD_FLOW_RETURN_MIN_GPH", 500.0),
        "label": "Return Flow",
        "unit": "gph",
    },
    "flow_manifold_main": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_FLOW_MANIFOLD_MIN_GPH", 150.0),
        "label": "Manifold Flow",
        "unit": "gph",
    },
    "par_left": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_PAR_LEFT_MIN", 120.0),
        "max": _env_float("THRESHOLD_PAR_LEFT_MAX", 350.0),
        "label": "PAR Left",
        "unit": "umol/m2/s",
    },
    "par_center": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_PAR_CENTER_MIN", 150.0),
        "max": _env_float("THRESHOLD_PAR_CENTER_MAX", 400.0),
        "label": "PAR Center",
        "unit": "umol/m2/s",
    },
    "par_right": {
        "severity": "warning",
        "min": _env_float("THRESHOLD_PAR_RIGHT_MIN", 120.0),
        "max": _env_float("THRESHOLD_PAR_RIGHT_MAX", 350.0),
        "label": "PAR Right",
        "unit": "umol/m2/s",
    },
}

LEAK_EXPECTED_DRY_VALUE = _env_str("THRESHOLD_LEAK_EXPECTED_STATE", "dry").lower()
LEAK_SENSOR_KEYS = ["leak_probe_a", "leak_probe_b"]