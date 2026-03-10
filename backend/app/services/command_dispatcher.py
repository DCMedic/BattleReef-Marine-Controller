import json
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt

from app.config import get_settings
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
        "requested_at": record.requested_at.isoformat(),
        "requested_by": record.requested_by,
        "target_device": record.target_device,
        "command_type": record.command_type,
        "command_payload": record.command_payload,
    }


def _connect_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{settings.mqtt_client_id}-dispatcher")

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


def _dispatch_once(client: mqtt.Client) -> None:
    db = SessionLocal()
    try:
        command_service = CommandService(db)
        queued = command_service.list_queued(limit=20)

        for record in queued:
            topic = device_command_topic(record.target_device)
            message = _build_message(record)
            payload = json.dumps(message)

            result = client.publish(topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                command_service.mark_dispatched(record)
                print(
                    f"[DISPATCH] Command dispatched "
                    f"command_id={record.id} topic={topic} target_device={record.target_device}"
                )
            else:
                command_service.mark_failed(record, f"mqtt_publish_failed_rc_{result.rc}")
                print(
                    f"[DISPATCH] Command dispatch failed "
                    f"command_id={record.id} topic={topic} rc={result.rc}"
                )
    except Exception as exc:
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

        thread = threading.Thread(target=_dispatcher_worker, name="command-dispatcher", daemon=True)
        thread.start()

        _dispatcher_started = True
        print("[DISPATCH] Dispatcher thread started")