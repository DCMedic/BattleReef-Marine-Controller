import json
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import SessionLocal
from app.mqtt.topics import TOPIC_TELEMETRY_SUBSCRIBE_ALL
from app.schemas.telemetry import TelemetryIngestRequest
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
        print(f"[MQTT] Subscribed to {TOPIC_TELEMETRY_SUBSCRIBE_ALL}")
    else:
        print(f"[MQTT] Connect callback returned non-success code: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    if reason_code == 0:
        print("[MQTT] Disconnected cleanly from broker")
    else:
        print(f"[MQTT] Unexpected disconnect from broker. reason_code={reason_code}")


def on_message(client, userdata, msg):
    db: Optional[Session] = None

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        telemetry = TelemetryIngestRequest(
            sensor_key=payload["sensor_key"],
            timestamp=payload["timestamp"],
            value=payload["value"],
            unit=payload["unit"],
            quality=payload.get("quality", "good"),
            source_node=payload["source_node"],
        )

        db = SessionLocal()

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

    except Exception as exc:
        topic = getattr(msg, "topic", "<unknown>")
        print(f"[MQTT] Processing error for topic '{topic}': {exc}")

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