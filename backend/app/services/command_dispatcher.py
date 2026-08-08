import json
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt

from app.config import get_settings
from app.core.runtime_alerts import runtime_alerts
from app.db.session import SessionLocal
from app.mqtt.topics import device_command_topic
from app.services.command_service import CommandService

settings = get_settings()

_dispatcher_started = False
_dispatcher_lock = threading.Lock()
_dispatch_client: Optional[mqtt.Client] = None


def _build_message(record) -> dict:
    return {
        "command_id": record.id,
        "correlation_id": record.correlation_id,
        "requested_at": record.requested_at.isoformat(),
        "requested_by": record.requested_by,
        "target_device": record.target_device,
        "command_type": record.command_type,
        "command_payload": record.command_payload,
        "delivery_policy": record.delivery_policy,
        "dispatch_attempt": int(record.dispatch_attempts or 0) + 1,
    }


def _connect_client() -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{settings.mqtt_client_id}-dispatcher",
    )

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    while True:
        try:
            print(f"[DISPATCH] Attempting connection to {settings.mqtt_host}:{settings.mqtt_port}")
            client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            client.loop_start()
            print("[DISPATCH] Connected to MQTT broker")
            return client
        except Exception as exc:
            print(f"[DISPATCH] MQTT connection failed: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


def _handle_expired_commands(command_service: CommandService) -> None:
    for record in command_service.list_expired_dispatched():
        attempts = int(record.dispatch_attempts or 0)
        reason = f"ack_timeout_after_attempt_{attempts}"

        if CommandService.retry_safe(record.delivery_policy) and attempts < int(record.max_attempts or 1):
            command_service.mark_retry_pending(record, reason)
            print(
                f"[DISPATCH] RETRY_PENDING command_id={record.id} "
                f"policy={record.delivery_policy} attempts={attempts}/{record.max_attempts}"
            )
            continue

        command_service.mark_timeout(record, reason)
        print(
            f"[DISPATCH] TIMEOUT command_id={record.id} device={record.target_device} "
            f"policy={record.delivery_policy} attempts={attempts}/{record.max_attempts}"
        )

        alert_key = f"command_delivery_{record.id}"
        severity = "critical" if record.delivery_policy == "safety_critical" else "warning"
        runtime_alerts.upsert(
            key=alert_key,
            severity=severity,
            title="Command Delivery Failure",
            message=(
                f"Command {record.id} to {record.target_device} was not confirmed "
                f"after {attempts} dispatch attempt(s)."
            ),
            source="command_dispatcher",
            metadata={
                "command_id": record.id,
                "correlation_id": record.correlation_id,
                "target_device": record.target_device,
                "command_type": record.command_type,
                "delivery_policy": record.delivery_policy,
                "dispatch_attempts": attempts,
                "max_attempts": record.max_attempts,
                "reason": reason,
            },
        )


def _dispatch_once(client: mqtt.Client) -> None:
    db = SessionLocal()

    try:
        command_service = CommandService(db)
        _handle_expired_commands(command_service)
        dispatchable = command_service.list_dispatchable(limit=20)

        for record in dispatchable:
            try:
                topic = device_command_topic(record.target_device)
                payload = json.dumps(_build_message(record))
                result = client.publish(topic, payload, qos=1)

                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    raise RuntimeError(f"mqtt_publish_failed_rc_{result.rc}")

                command_service.mark_dispatched(record)

                print(
                    f"[DISPATCH] SENT command_id={record.id} "
                    f"correlation_id={record.correlation_id} device={record.target_device} "
                    f"topic={topic} attempt={record.dispatch_attempts}/{record.max_attempts}"
                )

            except Exception as exc:
                command_service.mark_failed(record, str(exc))
                print(
                    f"[DISPATCH] FAILED command_id={record.id} "
                    f"device={record.target_device} error={exc}"
                )

    except Exception as exc:
        db.rollback()
        print(f"[DISPATCH] Dispatch cycle error: {exc}")

    finally:
        db.close()


def _dispatcher_worker() -> None:
    global _dispatch_client

    client = _connect_client()
    _dispatch_client = client

    while True:
        _dispatch_once(client)
        time.sleep(2)


def start_command_dispatcher() -> None:
    global _dispatcher_started

    with _dispatcher_lock:
        if _dispatcher_started:
            print("[DISPATCH] Dispatcher already started, skipping duplicate startup")
            return

        thread = threading.Thread(
            target=_dispatcher_worker,
            name="command-dispatcher",
            daemon=True,
        )
        thread.start()

        _dispatcher_started = True
        print("[DISPATCH] Dispatcher thread started")
