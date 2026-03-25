from __future__ import annotations

import json
import math
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
PUBLISH_INTERVAL_SECONDS = float(os.getenv("SIMULATOR_PUBLISH_INTERVAL_SECONDS", "3"))

TOPIC_BASE = "battlereef/telemetry"
SOURCE_NODE = "simulator_node"


def connect_client() -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="battlereef-simulator",
    )

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


def publish_reading(
    client: mqtt.Client,
    sensor_key: str,
    value: float | int | str,
    unit: str,
    quality: str = "good",
) -> None:
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "sensor_key": sensor_key,
        "source_node": SOURCE_NODE,
        "reading_time": now,
        "timestamp": now,
        "value": value,
        "unit": unit,
        "quality": quality,
    }

    topic = f"{TOPIC_BASE}/{sensor_key}"
    client.publish(topic, json.dumps(payload))
    print(f"[SIM] Published {sensor_key}={value} {unit}")


def bounded(value: float, minimum: float, maximum: float, digits: int = 2) -> float:
    return round(max(minimum, min(maximum, value)), digits)


def leak_state(probability_wet: float = 0.003) -> str:
    return "wet" if random.random() < probability_wet else "dry"


def main() -> None:
    client = connect_client()
    t = 0.0

    while True:
        t += 0.12

        # Core aquarium telemetry
        tank_temp = bounded(78.1 + math.sin(t) * 0.45 + random.uniform(-0.08, 0.08), 76.5, 80.5)
        tank_ph = bounded(8.14 + math.sin(t / 2.3) * 0.08 + random.uniform(-0.01, 0.01), 7.85, 8.45)
        tank_salinity = bounded(35.0 + math.sin(t / 3.1) * 0.18 + random.uniform(-0.03, 0.03), 33.5, 36.5)
        sump_level = bounded(9.42 + math.sin(t / 4.4) * 0.09 + random.uniform(-0.01, 0.01), 8.8, 10.0)

        publish_reading(client, "tank_temp_main", tank_temp, "F")
        publish_reading(client, "tank_ph_main", tank_ph, "pH")
        publish_reading(client, "tank_salinity_main", tank_salinity, "ppt")
        publish_reading(client, "sump_level_main", sump_level, "in")

        # Water quality
        orp = bounded(365 + math.sin(t / 2.8) * 18 + random.uniform(-2, 2), 280, 450, 1)
        dissolved_oxygen = bounded(6.9 + math.sin(t / 3.3) * 0.35 + random.uniform(-0.05, 0.05), 5.5, 8.5)

        publish_reading(client, "orp_main", orp, "mV")
        publish_reading(client, "dissolved_oxygen_main", dissolved_oxygen, "mg/L")

        # Flow
        return_flow = bounded(820 + math.sin(t / 3.8) * 35 + random.uniform(-5, 5), 450, 1000, 1)
        manifold_flow = bounded(310 + math.sin(t / 4.6) * 22 + random.uniform(-4, 4), 120, 420, 1)

        publish_reading(client, "flow_return_main", return_flow, "gph")
        publish_reading(client, "flow_manifold_main", manifold_flow, "gph")

        # PAR / lighting
        # Creates a day-like cycle with left/center/right variation
        daylight = max(0.0, math.sin(t / 5.5))
        par_left = bounded(90 + daylight * 180 + random.uniform(-4, 4), 0, 450, 1)
        par_center = bounded(120 + daylight * 240 + random.uniform(-5, 5), 0, 550, 1)
        par_right = bounded(85 + daylight * 170 + random.uniform(-4, 4), 0, 450, 1)

        publish_reading(client, "par_left", par_left, "umol/m2/s")
        publish_reading(client, "par_center", par_center, "umol/m2/s")
        publish_reading(client, "par_right", par_right, "umol/m2/s")

        # Leak probes
        publish_reading(client, "leak_probe_a", leak_state(), "state")
        publish_reading(client, "leak_probe_b", leak_state(), "state")

        # Room environment
        room_co2 = bounded(720 + math.sin(t / 6.5) * 75 + random.uniform(-8, 8), 500, 1800, 0)
        voc = bounded(95 + math.sin(t / 7.2) * 18 + random.uniform(-4, 4), 20, 400, 0)
        ambient_temp = bounded(74.5 + math.sin(t / 5.8) * 1.8 + random.uniform(-0.15, 0.15), 68, 82)
        humidity = bounded(54 + math.sin(t / 6.1) * 4.5 + random.uniform(-0.4, 0.4), 35, 75, 1)

        publish_reading(client, "room_co2_main", room_co2, "ppm")
        publish_reading(client, "voc_main", voc, "ppb")
        publish_reading(client, "ambient_temp_room", ambient_temp, "F")
        publish_reading(client, "ambient_humidity_room", humidity, "%")

        # Power draw
        # Ties loosely to lighting and pumps
        power_draw = bounded(
            420
            + daylight * 110
            + (return_flow - 800) * 0.12
            + (manifold_flow - 300) * 0.08
            + random.uniform(-6, 6),
            250,
            700,
            1,
        )

        publish_reading(client, "power_monitor_main", power_draw, "W")

        time.sleep(PUBLISH_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()