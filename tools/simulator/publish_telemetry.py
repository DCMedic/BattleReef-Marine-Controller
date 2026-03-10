import json
import math
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "battlereef-simulator")
PUBLISH_INTERVAL_SECONDS = int(os.getenv("PUBLISH_INTERVAL_SECONDS", "5"))

TOPICS = {
    "temperature": "battlereef/telemetry/tank_temp_main",
    "ph": "battlereef/telemetry/tank_ph_main",
    "salinity": "battlereef/telemetry/tank_salinity_main",
    "water_level": "battlereef/telemetry/sump_level_main",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_payload(client: mqtt.Client, topic: str, payload: dict) -> None:
    body = json.dumps(payload)
    result = client.publish(topic, body)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"[SIM] Published to {topic}: {body}")
    else:
        print(f"[SIM] Publish failed to {topic} with rc={result.rc}")


def connect_with_retry(client: mqtt.Client) -> None:
    while True:
        try:
            print(f"[SIM] Attempting MQTT connection to {MQTT_HOST}:{MQTT_PORT}")
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            print("[SIM] Connected to MQTT broker")
            return
        except Exception as exc:
            print(f"[SIM] MQTT connection failed: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    connect_with_retry(client)
    client.loop_start()

    tick = 0

    try:
        while True:
            tick += 1

            temperature = 78.0 + math.sin(tick / 6) * 0.7 + random.uniform(-0.15, 0.15)
            ph = 8.15 + math.sin(tick / 10) * 0.08 + random.uniform(-0.02, 0.02)
            salinity = 35.0 + math.sin(tick / 14) * 0.4 + random.uniform(-0.05, 0.05)
            water_level = 9.5 + math.sin(tick / 18) * 0.12 + random.uniform(-0.02, 0.02)

            publish_payload(
                client,
                TOPICS["temperature"],
                {
                    "sensor_key": "tank_temp_main",
                    "timestamp": utc_now(),
                    "value": round(temperature, 2),
                    "unit": "F",
                    "quality": "good",
                    "source_node": "simulator_node",
                },
            )

            publish_payload(
                client,
                TOPICS["ph"],
                {
                    "sensor_key": "tank_ph_main",
                    "timestamp": utc_now(),
                    "value": round(ph, 2),
                    "unit": "pH",
                    "quality": "good",
                    "source_node": "simulator_node",
                },
            )

            publish_payload(
                client,
                TOPICS["salinity"],
                {
                    "sensor_key": "tank_salinity_main",
                    "timestamp": utc_now(),
                    "value": round(salinity, 2),
                    "unit": "ppt",
                    "quality": "good",
                    "source_node": "simulator_node",
                },
            )

            publish_payload(
                client,
                TOPICS["water_level"],
                {
                    "sensor_key": "sump_level_main",
                    "timestamp": utc_now(),
                    "value": round(water_level, 2),
                    "unit": "in",
                    "quality": "good",
                    "source_node": "simulator_node",
                },
            )

            time.sleep(PUBLISH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("[SIM] Stopping simulator...")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()