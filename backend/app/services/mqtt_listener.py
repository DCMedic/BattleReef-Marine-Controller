from __future__ import annotations

import json
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.runtime_alerts import runtime_alerts
from app.db.session import SessionLocal
from app.mqtt.topics import TOPIC_ACK_SUBSCRIBE_ALL, TOPIC_TELEMETRY_SUBSCRIBE_ALL
from app.schemas.device_state import DeviceStateUpsertRequest
from app.schemas.telemetry import TelemetryIngestRequest
from app.services.command_service import CommandService
from app.services.device_state_service import DeviceStateService
from app.services.rule_engine import RuleEngineService
from app.services.telemetry_service import TelemetryService

settings = get_settings()

_mqtt_client: Optional[mqtt.Client] = None
_listener_started = False
_listener_lock = threading.Lock()


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[MQTT] Connected to broker at {settings.mqtt_host}:{settings.mqtt_port}")
        client.subscribe(TOPIC_TELEMETRY_SUBSCRIBE_ALL)
        client.subscribe(TOPIC_ACK_SUBSCRIBE_ALL)
        print(f"[MQTT] Subscribed to {TOPIC_TELEMETRY_SUBSCRIBE_ALL}")
        print(f"[MQTT] Subscribed to {TOPIC_ACK_SUBSCRIBE_ALL}")
    else:
        print(f"[MQTT] Connect callback returned non-success code: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    if reason_code == 0:
        print("[MQTT] Disconnected cleanly from broker")
    else:
        print(f"[MQTT] Unexpected disconnect from broker. reason_code={reason_code}")


def _handle_telemetry(payload: dict, db: Session) -> None:
    reading_time = payload.get("reading_time") or payload.get("timestamp")

    if reading_time is None:
        raise ValueError("Telemetry payload missing reading_time/timestamp")

    telemetry = TelemetryIngestRequest(
        sensor_key=payload["sensor_key"],
        timestamp=reading_time,
        value=payload["value"],
        unit=payload["unit"],
        quality=payload.get("quality", "good"),
        source_node=payload["source_node"],
    )

    telemetry_service = TelemetryService(db)
    record = telemetry_service.ingest(telemetry)

    print(
        f"[MQTT] Ingested telemetry id={record.id} "
        f"sensor_key={record.sensor_key} value={record.value_double} {record.unit}"
    )

    if record.sensor_key == "tank_temp_main":
        rule_engine = RuleEngineService(db)
        result = rule_engine.evaluate_temperature_rule()

        if result.get("action_taken"):
            print(
                f"[RULE] Temperature rule triggered "
                f"command_id={result['command_id']} "
                f"target_device={result['target_device']} "
                f"status={result['status']}"
            )
        else:
            print(
                f"[RULE] Temperature rule evaluated with no action. "
                f"reason={result.get('reason')}"
            )


def _command_failure_alert(record, reason: str, *, security_event: bool = False) -> None:
    severity = "critical" if record.delivery_policy == "safety_critical" or security_event else "warning"
    runtime_alerts.upsert(
        key=f"command_delivery_{record.id}",
        severity=severity,
        title="Command Verification Failure",
        message=f"Command {record.id} to {record.target_device} could not be verified: {reason}.",
        source="mqtt_ack_listener",
        metadata={
            "command_id": record.id,
            "correlation_id": record.correlation_id,
            "target_device": record.target_device,
            "command_type": record.command_type,
            "delivery_policy": record.delivery_policy,
            "reason": reason,
            "security_event": security_event,
        },
    )


def _handle_ack(payload: dict, db: Session) -> None:
    command_id = payload.get("command_id")
    correlation_id = payload.get("correlation_id")
    device_key = payload.get("device_key")
    state_payload = payload.get("state_payload", {})
    state_source = payload.get("state_source", "device_ack")

    if command_id is None or device_key is None:
        raise ValueError("ACK payload must include command_id and device_key")
    if not isinstance(state_payload, dict):
        raise ValueError("ACK state_payload must be an object")

    command_service = CommandService(db)
    device_state_service = DeviceStateService(db)

    record = command_service.get_by_id(int(command_id))
    if record is None:
        print(f"[ACK] No command found for command_id={command_id}")
        return

    if record.status == "completed":
        print(f"[ACK] Duplicate ACK ignored for completed command_id={command_id}")
        return

    if device_key != record.target_device:
        reason = f"ack_device_mismatch_expected_{record.target_device}_got_{device_key}"
        command_service.mark_failed(record, reason)
        _command_failure_alert(record, reason, security_event=True)
        print(f"[ACK] REJECTED command_id={command_id} reason={reason}")
        return

    if correlation_id is not None and correlation_id != record.correlation_id:
        reason = "ack_correlation_id_mismatch"
        command_service.mark_failed(record, reason)
        _command_failure_alert(record, reason, security_event=True)
        print(f"[ACK] REJECTED command_id={command_id} reason={reason}")
        return

    if record.status not in {"dispatched", "acknowledged"}:
        reason = f"ack_invalid_command_state_{record.status}"
        _command_failure_alert(record, reason, security_event=True)
        print(f"[ACK] REJECTED command_id={command_id} reason={reason}")
        return

    if record.status == "dispatched":
        command_service.mark_acknowledged(record)

    verified, verification_reason = command_service.verify_ack_state(record, state_payload)
    if not verified:
        command_service.mark_failed(record, verification_reason)
        _command_failure_alert(record, verification_reason)
        print(
            f"[ACK] VERIFICATION_FAILED command_id={record.id} "
            f"device_key={device_key} reason={verification_reason}"
        )
        return

    command_service.mark_verified(record)

    state_record = device_state_service.upsert(
        DeviceStateUpsertRequest(
            device_key=device_key,
            state_payload=state_payload,
            state_source=state_source,
        )
    )

    command_service.mark_completed(record)
    runtime_alerts.clear(f"command_delivery_{record.id}")

    print(
        f"[ACK] VERIFIED command_id={record.id} correlation_id={record.correlation_id} "
        f"device_key={device_key} device_state_id={state_record.id}"
    )


def on_message(client, userdata, msg):
    db: Optional[Session] = None
    payload: dict = {}

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        db = SessionLocal()

        if msg.topic.startswith("battlereef/telemetry/"):
            _handle_telemetry(payload, db)
        elif msg.topic.startswith("battlereef/ack/"):
            _handle_ack(payload, db)
        else:
            print(f"[MQTT] Received message on unhandled topic {msg.topic}")

    except Exception as exc:
        if db is not None:
            db.rollback()
        topic = getattr(msg, "topic", "<unknown>")
        print(
            f"[MQTT] Processing error for topic '{topic}': {exc} | "
            f"payload={json.dumps(payload)}"
        )

    finally:
        if db is not None:
            db.close()


def _mqtt_worker():
    global _mqtt_client

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=settings.mqtt_client_id)

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=2, max_delay=30)

    _mqtt_client = client

    while True:
        try:
            print(f"[MQTT] Attempting connection to {settings.mqtt_host}:{settings.mqtt_port}")
            client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            client.loop_forever()
        except Exception as exc:
            print(f"[MQTT] Broker connection failed: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


def start_mqtt_listener():
    global _listener_started

    with _listener_lock:
        if _listener_started:
            print("[MQTT] Listener already started, skipping duplicate startup")
            return

        thread = threading.Thread(target=_mqtt_worker, name="mqtt-listener", daemon=True)
        thread.start()

        _listener_started = True
        print("[MQTT] Listener thread started")
