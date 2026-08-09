from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.routes.commands import _command_response
from app.core.runtime_alerts import runtime_alerts
from app.core.sensor_thresholds import LEAK_EXPECTED_DRY_VALUE
from app.schemas.command import CommandCreateRequest
from app.services.audit_service import AuditService, GENESIS_HASH
from app.services.command_service import CommandService
from app.services.mqtt_listener import _ack_topic_identity, _telemetry_topic_identity
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


def test_audit_hash_is_deterministic_and_tamper_sensitive() -> None:
    values = dict(
        occurred_at=datetime(2026, 8, 8, 18, 58, tzinfo=timezone.utc),
        event_type="security.ack_rejected",
        severity="critical",
        outcome="rejected",
        source="mqtt_listener",
        actor_type="mqtt_identity",
        actor_id="heater_main",
        entity_type="command",
        entity_id="42",
        correlation_id="corr-42",
        message="ACK rejected.",
        details={"reason": "ack_correlation_id_mismatch"},
        previous_hash=GENESIS_HASH,
    )
    first = AuditService.calculate_hash(**values)
    second = AuditService.calculate_hash(**values)
    assert first == second
    assert len(first) == 64

    tampered = dict(values)
    tampered["message"] = "ACK accepted."
    assert AuditService.calculate_hash(**tampered) != first


def test_authenticated_mqtt_topic_namespaces_bind_identity() -> None:
    assert _telemetry_topic_identity("battlereef/telemetry/node-17/tank_temp_main") == (
        "node-17",
        "tank_temp_main",
    )
    assert _ack_topic_identity("battlereef/ack/heater_main") == "heater_main"

    with pytest.raises(ValueError, match="invalid_telemetry_topic_namespace"):
        _telemetry_topic_identity("battlereef/telemetry/tank_temp_main")

    with pytest.raises(ValueError, match="invalid_ack_topic_namespace"):
        _ack_topic_identity("battlereef/ack/heater_main/forged")


def test_command_intent_normalizes_power_variants() -> None:
    assert CommandService._intent("set_power", {"power": False}) == ("set_power", False)
    assert CommandService._intent("power", {"state": "off"}) == ("set_power", False)
    assert CommandService._intent("power", {"state": "on"}) == ("set_power", True)


def test_command_delivery_policies_protect_one_shot_actions() -> None:
    safety = CommandCreateRequest(
        requested_by="safety_watchdog",
        target_device="heater_main",
        command_type="set_power",
        command_payload={"power": False},
    )
    feed = CommandCreateRequest(
        requested_by="schedule_engine",
        target_device="feeder_main",
        command_type="trigger_feed",
        command_payload={"duration_seconds": 5},
    )
    light = CommandCreateRequest(
        requested_by="schedule_engine",
        target_device="lights_main",
        command_type="set_intensity",
        command_payload={"intensity": 60},
    )

    assert CommandService.delivery_policy_for(safety) == "safety_critical"
    assert CommandService.retry_safe("safety_critical") is True
    assert CommandService.timeout_seconds_for("safety_critical") == 5
    assert CommandService.delivery_policy_for(feed) == "one_shot"
    assert CommandService.retry_safe("one_shot") is False
    assert CommandService.delivery_policy_for(light) == "state_setting"
    assert CommandService.retry_safe("state_setting") is True


def test_power_ack_must_match_requested_physical_state() -> None:
    off_command = SimpleNamespace(command_type="set_power", command_payload={"power": False})

    verified, reason = CommandService.verify_ack_state(off_command, {"power": False})
    assert verified is True
    assert reason == "power_state_verified"

    verified, reason = CommandService.verify_ack_state(off_command, {"power": True})
    assert verified is False
    assert reason == "ack_power_state_mismatch"

    verified, reason = CommandService.verify_ack_state(off_command, {})
    assert verified is False
    assert reason == "ack_missing_power_state"


def test_one_shot_ack_can_report_explicit_failure() -> None:
    feed_command = SimpleNamespace(
        command_type="trigger_feed",
        command_payload={"duration_seconds": 5},
    )

    verified, _ = CommandService.verify_ack_state(feed_command, {"success": True})
    assert verified is True

    verified, reason = CommandService.verify_ack_state(feed_command, {"success": False})
    assert verified is False
    assert reason == "one_shot_device_reported_failure"


def test_command_api_response_includes_delivery_metadata() -> None:
    now = datetime(2026, 8, 8, 18, 0, tzinfo=timezone.utc)
    record = SimpleNamespace(
        id=42,
        correlation_id="8c230c4e-431b-4e9b-a91f-f47c79f8d9b0",
        requested_at=now,
        requested_by="safety_watchdog",
        target_device="heater_main",
        command_type="set_power",
        command_payload={"power": False},
        delivery_policy="safety_critical",
        status="dispatched",
        dispatch_attempts=1,
        max_attempts=4,
        last_dispatched_at=now,
        ack_deadline=now,
        acknowledged_at=None,
        verified_at=None,
        completed_at=None,
        error_message=None,
    )

    response = _command_response(record)
    assert response.correlation_id == record.correlation_id
    assert response.delivery_policy == "safety_critical"
    assert response.dispatch_attempts == 1
    assert response.max_attempts == 4


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
