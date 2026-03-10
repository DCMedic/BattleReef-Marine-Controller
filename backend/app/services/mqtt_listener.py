import json
import logging

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.telemetry_service import TelemetryService
from app.services.rule_engine import RuleEngineService

logger = logging.getLogger(__name__)
settings = get_settings()

MQTT_TOPIC = "reef/telemetry/#"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("[MQTT] Connected to broker")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"[MQTT] Subscribed to topic {MQTT_TOPIC}")
    else:
        logger.error(f"[MQTT] Connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception as exc:
        logger.error(f"[MQTT] Invalid JSON payload: {exc}")
        return

    db: Session = SessionLocal()

    try:
        telemetry_service = TelemetryService(db)

        record = telemetry_service.ingest(payload)

        logger.info(
            f"[MQTT] Ingested telemetry id={record.id} "
            f"sensor_key={record.sensor_key} "
            f"value={record.value_double} {record.unit}"
        )

        if record.sensor_key == "tank_temp_main":
            rule_engine = RuleEngineService(db)
            result = rule_engine.evaluate_temperature_rule()

            if result.get("action_taken"):
                logger.info(
                    f"[RULE] Temperature rule triggered "
                    f"command_id={result['command_id']} "
                    f"device={result['target_device']}"
                )
            else:
                logger.debug("[RULE] Temperature within acceptable range")

    except Exception as exc:
        logger.exception(f"[MQTT] Processing error: {exc}")

    finally:
        db.close()


def start_mqtt_listener():
    client = mqtt.Client(client_id=settings.mqtt_client_id)

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)

    logger.info("[MQTT] Listener starting")
    client.loop_start()