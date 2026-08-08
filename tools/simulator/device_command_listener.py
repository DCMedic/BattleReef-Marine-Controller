import json
import os
import ssl
import time

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "device-simulator")
MQTT_IDENTITY = os.getenv("MQTT_IDENTITY", "device-simulator")
MQTT_CA_CERT = os.getenv("MQTT_CA_CERT", "/run/battlereef-mqtt/ca.crt")
MQTT_CLIENT_CERT = os.getenv("MQTT_CLIENT_CERT", "/run/battlereef-mqtt/device-simulator.crt")
MQTT_CLIENT_KEY = os.getenv("MQTT_CLIENT_KEY", "/run/battlereef-mqtt/device-simulator.key")

TOPIC_SUBSCRIBE = "battlereef/cmd/#"
ACK_ROOT = "battlereef/ack"


def ack_topic_for_device(device_key: str) -> str:
    return f"{ACK_ROOT}/{device_key}"


def configure_tls(client: mqtt.Client) -> None:
    client.tls_set(
        ca_certs=MQTT_CA_CERT,
        certfile=MQTT_CLIENT_CERT,
        keyfile=MQTT_CLIENT_KEY,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
        cert_reqs=ssl.CERT_REQUIRED,
    )
    client.tls_insecure_set(False)


def build_state_payload(command_type: str, command_payload: dict, command_id: int) -> dict:
    state_payload: dict = {
        "mode": command_payload.get("mode", "manual"),
        "applied": True,
        "last_command_id": command_id,
    }

    if command_type == "set_power":
        state_payload["power"] = command_payload.get("power")
    elif command_type == "set_intensity":
        state_payload["intensity"] = command_payload.get("intensity")
        if "power" in command_payload:
            state_payload["power"] = command_payload.get("power")
    elif command_type == "trigger_feed":
        state_payload["success"] = True
        state_payload["last_feed_seconds"] = command_payload.get("duration_seconds")
    else:
        state_payload["raw_command_type"] = command_type
        state_payload["raw_command_payload"] = command_payload

    return state_payload


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[DEVICE] Connected securely as {MQTT_IDENTITY} to {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(TOPIC_SUBSCRIBE, qos=1)
        print(f"[DEVICE] Development aggregate simulator subscribed to {TOPIC_SUBSCRIBE}")
    else:
        print(f"[DEVICE] Connection failed with reason_code={reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print(f"[DEVICE] Received command on {msg.topic}: {json.dumps(payload)}")

        command_id = payload["command_id"]
        correlation_id = payload["correlation_id"]
        device_key = payload["target_device"]
        command_type = payload["command_type"]
        command_payload = payload["command_payload"]

        expected_topic = f"battlereef/cmd/{device_key}"
        if msg.topic != expected_topic:
            raise ValueError(f"command_topic_target_mismatch_expected_{expected_topic}")

        state_payload = build_state_payload(command_type, command_payload, command_id)
        ack_payload = {
            "command_id": command_id,
            "correlation_id": correlation_id,
            "device_key": device_key,
            "state_payload": state_payload,
            "state_source": "device_simulator_mtls",
        }

        ack_topic = ack_topic_for_device(device_key)
        result = client.publish(ack_topic, json.dumps(ack_payload), qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[DEVICE] Published verified-shape ACK to {ack_topic}: {json.dumps(ack_payload)}")
        else:
            print(f"[DEVICE] Failed to publish ACK for command_id={command_id} rc={result.rc}")

    except Exception as exc:
        print(f"[DEVICE] Failed to process message on {msg.topic}: {exc}")


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    configure_tls(client)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            print(f"[DEVICE] Attempting authenticated MQTT connection to {MQTT_HOST}:{MQTT_PORT}")
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever()
        except Exception as exc:
            print(f"[DEVICE] MQTT connection failed: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
