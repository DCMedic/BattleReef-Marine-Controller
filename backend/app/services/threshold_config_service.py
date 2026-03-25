from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.core.sensor_thresholds import (
    DEFAULT_SENSOR_THRESHOLDS,
    clone_default_thresholds,
    merge_threshold_overrides,
)


class ThresholdConfigService:
    def __init__(self) -> None:
        data_dir = Path(os.getenv("BATTLEREEF_DATA_DIR", "/app/data"))
        data_dir.mkdir(parents=True, exist_ok=True)

        self.filepath = data_dir / "threshold_overrides.json"

    def _read_overrides(self) -> dict[str, dict[str, Any]]:
        if not self.filepath.exists():
            return {}

        try:
            with self.filepath.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            if not isinstance(data, dict):
                return {}

            normalized: dict[str, dict[str, Any]] = {}

            for sensor_key, values in data.items():
                if isinstance(sensor_key, str) and isinstance(values, dict):
                    normalized[sensor_key] = values

            return normalized
        except Exception:
            return {}

    def _write_overrides(self, overrides: dict[str, dict[str, Any]]) -> None:
        with self.filepath.open("w", encoding="utf-8") as handle:
            json.dump(overrides, handle, indent=2, sort_keys=True)

    def list_thresholds(self) -> list[dict[str, Any]]:
        overrides = self._read_overrides()
        merged = merge_threshold_overrides(clone_default_thresholds(), overrides)

        items: list[dict[str, Any]] = []

        for sensor_key, config in merged.items():
            items.append(
                {
                    "sensor_key": sensor_key,
                    "label": config.get("label", sensor_key),
                    "unit": config.get("unit"),
                    "severity": config.get("severity", "warning"),
                    "min": config.get("min"),
                    "max": config.get("max"),
                    "enabled": bool(config.get("enabled", True)),
                    "has_override": sensor_key in overrides,
                    "default": DEFAULT_SENSOR_THRESHOLDS.get(sensor_key, {}),
                    "effective": config,
                }
            )

        items.sort(key=lambda item: item["label"])
        return items

    def get_effective_thresholds(self) -> dict[str, dict[str, Any]]:
        overrides = self._read_overrides()
        return merge_threshold_overrides(clone_default_thresholds(), overrides)

    def update_threshold(
        self,
        *,
        sensor_key: str,
        min_value: float | None,
        max_value: float | None,
        severity: str,
        enabled: bool,
    ) -> dict[str, Any]:
        if sensor_key not in DEFAULT_SENSOR_THRESHOLDS:
            raise ValueError(f"Unknown threshold sensor_key: {sensor_key}")

        if severity not in {"warning", "critical"}:
            raise ValueError("Severity must be 'warning' or 'critical'")

        overrides = self._read_overrides()

        overrides[sensor_key] = {
            "min": min_value,
            "max": max_value,
            "severity": severity,
            "enabled": enabled,
        }

        self._write_overrides(overrides)

        return self._build_single_threshold(sensor_key)

    def reset_threshold(self, sensor_key: str) -> dict[str, Any]:
        if sensor_key not in DEFAULT_SENSOR_THRESHOLDS:
            raise ValueError(f"Unknown threshold sensor_key: {sensor_key}")

        overrides = self._read_overrides()

        if sensor_key in overrides:
            del overrides[sensor_key]

        self._write_overrides(overrides)

        return self._build_single_threshold(sensor_key)

    def _build_single_threshold(self, sensor_key: str) -> dict[str, Any]:
        overrides = self._read_overrides()
        merged = merge_threshold_overrides(clone_default_thresholds(), overrides)
        config = merged[sensor_key]

        return {
            "sensor_key": sensor_key,
            "label": config.get("label", sensor_key),
            "unit": config.get("unit"),
            "severity": config.get("severity", "warning"),
            "min": config.get("min"),
            "max": config.get("max"),
            "enabled": bool(config.get("enabled", True)),
            "has_override": sensor_key in overrides,
            "default": DEFAULT_SENSOR_THRESHOLDS.get(sensor_key, {}),
            "effective": config,
        }