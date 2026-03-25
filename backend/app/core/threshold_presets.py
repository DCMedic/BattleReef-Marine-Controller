from __future__ import annotations

from typing import Any


THRESHOLD_PRESETS: dict[str, dict[str, Any]] = {
    "mixed_reef": {
        "key": "mixed_reef",
        "label": "Mixed Reef",
        "description": "Balanced thresholds for mixed coral systems with moderate lighting and flow.",
        "thresholds": {
            "orp_main": {
                "min": 300.0,
                "max": 450.0,
                "severity": "warning",
                "enabled": True,
            },
            "dissolved_oxygen_main": {
                "min": 6.0,
                "max": None,
                "severity": "critical",
                "enabled": True,
            },
            "room_co2_main": {
                "min": None,
                "max": 1200.0,
                "severity": "warning",
                "enabled": True,
            },
            "flow_return_main": {
                "min": 500.0,
                "max": None,
                "severity": "critical",
                "enabled": True,
            },
            "flow_manifold_main": {
                "min": 150.0,
                "max": None,
                "severity": "warning",
                "enabled": True,
            },
            "par_left": {
                "min": 120.0,
                "max": 350.0,
                "severity": "warning",
                "enabled": True,
            },
            "par_center": {
                "min": 150.0,
                "max": 400.0,
                "severity": "warning",
                "enabled": True,
            },
            "par_right": {
                "min": 120.0,
                "max": 350.0,
                "severity": "warning",
                "enabled": True,
            },
        },
    },
    "sps_dominant": {
        "key": "sps_dominant",
        "label": "SPS Dominant",
        "description": "Higher lighting, stronger flow, and tighter oxygen expectations for SPS-heavy systems.",
        "thresholds": {
            "orp_main": {
                "min": 325.0,
                "max": 450.0,
                "severity": "warning",
                "enabled": True,
            },
            "dissolved_oxygen_main": {
                "min": 6.5,
                "max": None,
                "severity": "critical",
                "enabled": True,
            },
            "room_co2_main": {
                "min": None,
                "max": 1000.0,
                "severity": "warning",
                "enabled": True,
            },
            "flow_return_main": {
                "min": 650.0,
                "max": None,
                "severity": "critical",
                "enabled": True,
            },
            "flow_manifold_main": {
                "min": 220.0,
                "max": None,
                "severity": "warning",
                "enabled": True,
            },
            "par_left": {
                "min": 200.0,
                "max": 450.0,
                "severity": "warning",
                "enabled": True,
            },
            "par_center": {
                "min": 250.0,
                "max": 500.0,
                "severity": "warning",
                "enabled": True,
            },
            "par_right": {
                "min": 200.0,
                "max": 450.0,
                "severity": "warning",
                "enabled": True,
            },
        },
    },
    "fish_only": {
        "key": "fish_only",
        "label": "Fish-Only",
        "description": "Relaxed lighting thresholds with practical flow, gas exchange, and room-safety monitoring.",
        "thresholds": {
            "orp_main": {
                "min": 280.0,
                "max": 425.0,
                "severity": "warning",
                "enabled": True,
            },
            "dissolved_oxygen_main": {
                "min": 5.5,
                "max": None,
                "severity": "critical",
                "enabled": True,
            },
            "room_co2_main": {
                "min": None,
                "max": 1400.0,
                "severity": "warning",
                "enabled": True,
            },
            "flow_return_main": {
                "min": 350.0,
                "max": None,
                "severity": "critical",
                "enabled": True,
            },
            "flow_manifold_main": {
                "min": 100.0,
                "max": None,
                "severity": "warning",
                "enabled": True,
            },
            "par_left": {
                "min": 0.0,
                "max": 250.0,
                "severity": "warning",
                "enabled": True,
            },
            "par_center": {
                "min": 0.0,
                "max": 300.0,
                "severity": "warning",
                "enabled": True,
            },
            "par_right": {
                "min": 0.0,
                "max": 250.0,
                "severity": "warning",
                "enabled": True,
            },
        },
    },
}