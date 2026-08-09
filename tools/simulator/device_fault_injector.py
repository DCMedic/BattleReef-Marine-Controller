"""Development-only actuator fault injector.

Uses the development device-simulator certificate and the real MQTT command/ACK
contract. Never deploy this process or its aggregate certificate to production.

FAULT_MODE values: normal, drop_ack, delayed_ack, wrong_state, explicit_failure.
"""
from __future__ import annotations

import json
import os
import ssl
import time

import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "8883"))
DEVICE = os.getenv("FAULT_DEVICE", "heater_main")
MODE = os.getenv("FAULT_MODE", "normal").strip().lower()
DELAY = float(os.getenv("FAULT_DELAY_SECONDS", "8"))
CA = os.getenv("MQTT_CA_CERT", "ops/mosquitto/certs/ca.crt")
CERT = os.getenv("MQTT_CLIENT_CERT", "ops/mosquitto/certs/device-simulator.crt")
KEY = os.getenv("MQTT_CLIENT_KEY", "ops/mosquitto/certs/device-simulator.key")


def desired_state(command: dict) -> dict:
    kind = command.get("command_type")
    payload = command.get("command_payload") or {}
    if kind in {"set_power", "power"}:
        value = payload.get("power", payload.get("state"))
        if isinstance(value, str):
            value = value.lower() in {"on", "true", "1"}
        return {"power": bool(value)}
    if kind == "set_intensity":
        return {"intensity": payload.get("intensity")}
    if kind in {"trigger_feed", "feed"}:
        return {"success": True}
    return {"success": True}


def on_message(client, userdata, msg):
    command = json.loads(msg.payload.decode("utf-8"))
    print(f"[FAULT] received mode={MODE} topic={msg.topic} command={command}")
    if MODE == "drop_ack":
        print("[FAULT] intentionally dropping ACK")
        return
    if MODE == "delayed_ack":
        print(f"[FAULT] delaying ACK by {DELAY}s")
        time.sleep(DELAY)

    state = desired_state(command)
    if MODE == "wrong_state":
        if "power" in state:
            state["power"] = not state["power"]
        elif "intensity" in state and isinstance(state["intensity"], (int, float)):
            state["intensity"] = max(0, min(100, 100 - state["intensity"]))
        else:
            state["success"] = False
    elif MODE == "explicit_failure":
        state = {"success": False}

    ack = {
        "command_id": command["command_id"],
        "correlation_id": command.get("correlation_id"),
        "device_key": DEVICE,
        "state_payload": state,
        "state_source": f"fault_injector:{MODE}",
    }
    topic = f"battlereef/ack/{DEVICE}"
    client.publish(topic, json.dumps(ack), qos=1)
    print(f"[FAULT] published {topic}: {ack}")


def main() -> None:
    if MODE not in {"normal", "drop_ack", "delayed_ack", "wrong_state", "explicit_failure"}:
        raise SystemExit(f"unsupported FAULT_MODE={MODE}")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"fault-injector-{DEVICE}")
    client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY, tls_version=ssl.PROTOCOL_TLS_CLIENT, cert_reqs=ssl.CERT_REQUIRED)
    client.tls_insecure_set(False)
    client.on_message = on_message
    client.connect(HOST, PORT, 60)
    client.subscribe(f"battlereef/cmd/{DEVICE}/set", qos=1)
    print(f"[FAULT] listening for {DEVICE} commands in {MODE} mode")
    client.loop_forever()


if __name__ == "__main__":
    main()
