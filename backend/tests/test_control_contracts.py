from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.runtime_alerts import runtime_alerts
from app.core.sensor_thresholds import LEAK_EXPECTED_DRY_VALUE
from app.services.command_service import CommandService
from app.services.safety_watchdog import SafetyWatchdogService
from app.services.schedule_engine import ScheduleEngine
from app.services.telemetry_service import _parse_timestamp


def test_parse_timestamp_accepts_pydantic_datetime() -> None:
    value = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)
    assert _parse_timestamp(value) == value


def test_parse_timestamp_normalizes_iso_zulu() -> None:
    parsed = _parse_timestamp("2026-08-08T12:00:00Z")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0


def test_command_intent_normalizes_power_variants() -> None:
    assert CommandService._intent("set_power", {"power": False}) == ("set_power", False)
    assert CommandService._intent("power", {"state": "off"}) == ("set_power", False)
    assert CommandService._intent("power", {"state": "on"}) == ("set_power", True)


def test_schedule_intensity_presets_are_bounded() -> None:
    engine = object.__new__(ScheduleEngine)
    assert engine._normalize_intensity("low") == 30
    assert engine._normalize_intensity("medium") == 60
    assert engine._normalize_intensity("high") == 90
    assert engine._normalize_intensity(0) == 0
    assert engine._normalize_intensity(100) == 100


def test_leak_probe_zero_is_dry_and_one_is_alert() -> None:
    watchdog = object.__new__(SafetyWatchdogService)
    runtime_alerts.clear("leak_leak_probe_a")

    dry_record = SimpleNamespace(value_double=0.0, value_text=None)
    dry_result = watchdog._check_leak_probes({"leak_probe_a": dry_record})[0]
    assert LEAK_EXPECTED_DRY_VALUE == "0.0"
    assert dry_result["status"] == "ok"

    wet_record = SimpleNamespace(value_double=1.0, value_text=None)
    wet_result = watchdog._check_leak_probes({"leak_probe_a": wet_record})[0]
    assert wet_result["status"] == "alert"

    runtime_alerts.clear("leak_leak_probe_a")
