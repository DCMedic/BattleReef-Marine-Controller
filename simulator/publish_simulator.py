from __future__ import annotations

import json
import math
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

TOPIC_BASE = "battlereef/telemetry"
SOURCE_NODE = "simulator_node"


def connect_client() -> mqtt.Client:
  client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="battlereef-simulator")

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
  payload = {
      "sensor_key": sensor_key,
      "source_node": SOURCE_NODE,
      "reading_time": datetime.now(timezone.utc).isoformat(),
      "value": value,
      "unit": unit,
      "quality": quality,
  }

  client.publish(f"{TOPIC_BASE}/{sensor_key}", json.dumps(payload))


def main() -> None:
  client = connect_client()
  t = 0.0

  while True:
      t += 0.1

      publish_reading(client, "tank_temp_main", round(77.8 + math.sin(t) * 0.5, 2), "F")
      publish_reading(client, "tank_ph_main", round(8.12 + math.sin(t / 2) * 0.07, 2), "pH")
      publish_reading(client, "tank_salinity_main", round(35.1 + math.sin(t / 3) * 0.2, 2), "ppt")
      publish_reading(client, "sump_level_main", round(9.45 + math.sin(t / 4) * 0.08, 2), "in")

      publish_reading(client, "orp_main", round(365 + math.sin(t / 2) * 15, 1), "mV")
      publish_reading(client, "dissolved_oxygen_main", round(6.9 + math.sin(t / 3) * 0.4, 2), "mg/L")

      publish_reading(client, "flow_return_main", round(820 + math.sin(t / 4) * 30, 1), "gph")
      publish_reading(client, "flow_manifold_main", round(310 + math.sin(t / 5) * 20, 1), "gph")

      light_phase = max(0.0, math.sin(t / 6))
      publish_reading(client, "par_left", round(180 + light_phase * 90, 1), "umol/m2/s")
      publish_reading(client, "par_center", round(220 + light_phase * 120, 1), "umol/m2/s")
      publish_reading(client, "par_right", round(170 + light_phase * 85, 1), "umol/m2/s")

      publish_reading(client, "leak_probe_a", "dry", "state")
      publish_reading(client, "leak_probe_b", "dry", "state")

      publish_reading(client, "room_co2_main", round(640 + math.sin(t / 8) * 60, 0), "ppm")
      publish_reading(client, "power_monitor_main", round(485 + math.sin(t / 4) * 25, 1), "W")
      publish_reading(client, "voc_main", round(85 + math.sin(t / 7) * 15 + random.uniform(-3, 3), 0), "ppb")
      publish_reading(client, "ambient_temp_room", round(74.2 + math.sin(t / 6) * 1.5, 2), "F")
      publish_reading(client, "ambient_humidity_room", round(54 + math.sin(t / 5) * 4, 1), "%")

      time.sleep(3)


if __name__ == "__main__":
  main()