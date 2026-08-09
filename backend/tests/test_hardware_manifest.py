from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.sensor_catalog import SENSOR_CATALOG
from app.services.physical_verification_service import PhysicalVerificationService


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "hardware" / "verification-package-v1.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_verification_manifest_sensor_keys_exist_in_catalog() -> None:
    manifest = _manifest()
    catalog_keys = {item["sensor_key"] for item in SENSOR_CATALOG}
    manifest_keys = {item["sensor_key"] for item in manifest["channels"]}
    assert manifest_keys <= catalog_keys


def test_verification_manifest_thresholds_match_runtime_contract() -> None:
    thresholds = _manifest()["verification_thresholds"]
    assert thresholds["heater_power_on_min_w"] == PhysicalVerificationService.HEATER_POWER_ON_MIN_W
    assert thresholds["return_pump_power_on_min_w"] == PhysicalVerificationService.RETURN_PUMP_POWER_ON_MIN_W
    assert thresholds["return_flow_on_min_gph"] == PhysicalVerificationService.RETURN_FLOW_ON_MIN_GPH
    assert thresholds["return_pump_rpm_on_min"] == PhysicalVerificationService.RETURN_PUMP_RPM_ON_MIN
    assert thresholds["temperature_pair_max_delta_f"] == PhysicalVerificationService.TEMP_PAIR_MAX_DELTA_F
    assert thresholds["sump_level_pair_max_delta_in"] == PhysicalVerificationService.SUMP_LEVEL_PAIR_MAX_DELTA_IN
    assert thresholds["max_evidence_age_seconds"] == PhysicalVerificationService.MAX_EVIDENCE_AGE_SECONDS


def test_sensor_pair_verification_has_degraded_and_critical_bands() -> None:
    status, _, delta = PhysicalVerificationService.verify_sensor_pair(78.0, 78.8, 1.5)
    assert status == "verified"
    assert delta == pytest.approx(0.8)

    status, _, delta = PhysicalVerificationService.verify_sensor_pair(78.0, 80.0, 1.5)
    assert status == "degraded"
    assert delta == pytest.approx(2.0)

    status, _, delta = PhysicalVerificationService.verify_sensor_pair(78.0, 82.0, 1.5)
    assert status == "critical"
    assert delta == pytest.approx(4.0)


def test_missing_redundant_evidence_is_unknown_not_verified() -> None:
    status, reason, delta = PhysicalVerificationService.verify_sensor_pair(78.0, None, 1.5)
    assert status == "unknown"
    assert reason == "missing_or_stale_redundant_sensor_evidence"
    assert delta is None
