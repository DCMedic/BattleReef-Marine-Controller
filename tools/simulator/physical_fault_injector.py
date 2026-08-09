from __future__ import annotations

import json
import os
import ssl
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_IDENTITY = os.getenv("MQTT_IDENTITY", "simulator_node")
MQTT_CA_CERT = os.getenv("MQTT_CA_CERT", "ops/mosquitto/certs/ca.crt")
MQTT_CLIENT_CERT = os.getenv("MQTT_CLIENT_CERT", "ops/mosquitto/certs/simulator_node.crt")
MQTT_CLIENT_KEY = os.getenv("MQTT_CLIENT_KEY", "ops/mosquitto/certs/simulator_node.key")

SCENARIOS = {
    "salinity_spike": ("tank_salinity_main", 42.0, "ppt"),
    "return_flow_zero": ("flow_return_main", 0.0, "gph"),
    "return_flow_present": ("flow_return_main", 820.0, "gph"),
    "heater_power_present": ("power_heater_main", 250.0, "W"),
    "heater_power_zero": ("power_heater_main", 0.0, "W"),
}


def main() -> None:
    scenario = os.getenv("PHYSICAL_FAULT") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if scenario not in SCENARIOS:
        raise SystemExit(f"Choose one of: {', '.join(sorted(SCENARIOS))}")

    sensor_key, value, unit = SCENARIOS[scenario]
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"physical-fault-{scenario}")
    client.tls_set(ca_certs=MQTT_CA_CERT, certfile=MQTT_CLIENT_CERT, keyfile=MQTT_CLIENT_KEY, tls_version=ssl.PROTOCOL_TLS_CLIENT, cert_reqs=ssl.CERT_REQUIRED)
    client.tls_insecure_set(False)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    now = datetime.now(timezone.utc).isoformat()
    payload = {"sensor_key": sensor_key, "source_node": MQTT_IDENTITY, "reading_time": now, "timestamp": now, "value": value, "unit": unit, "quality": "good"}
    topic = f"battlereef/telemetry/{MQTT_IDENTITY}/{sensor_key}"
    info = client.publish(topic, json.dumps(payload), qos=1)
    info.wait_for_publish()
    print(f"Injected {scenario}: {topic} -> {payload}")
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
