import json
import os
import time

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "battlereef-device-listener")

TOPIC_SUBSCRIBE = "battlereef/cmd/#"
ACK_ROOT = "battlereef/ack"


def ack_topic_for_device(device_key: str) -> str:
    return f"{ACK_ROOT}/{device_key}"


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[DEVICE] Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(TOPIC_SUBSCRIBE)
        print(f"[DEVICE] Subscribed to {TOPIC_SUBSCRIBE}")
    else:
        print(f"[DEVICE] Connection failed with reason_code={reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print(f"[DEVICE] Received command on {msg.topic}: {json.dumps(payload)}")

        command_id = payload["command_id"]
        device_key = payload["target_device"]
        command_payload = payload["command_payload"]

        state_payload = {
            "power": command_payload.get("power"),
            "mode": "auto",
            "last_command_id": command_id,
            "applied": True,
        }

        ack_payload = {
            "command_id": command_id,
            "device_key": device_key,
            "state_payload": state_payload,
            "state_source": "device_listener",
        }

        ack_topic = ack_topic_for_device(device_key)
        result = client.publish(ack_topic, json.dumps(ack_payload))

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[DEVICE] Published ACK to {ack_topic}: {json.dumps(ack_payload)}")
        else:
            print(f"[DEVICE] Failed to publish ACK for command_id={command_id} rc={result.rc}")

    except Exception as exc:
        print(f"[DEVICE] Failed to process message on {msg.topic}: {exc}")


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            print(f"[DEVICE] Attempting MQTT connection to {MQTT_HOST}:{MQTT_PORT}")
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_forever()
        except Exception as exc:
            print(f"[DEVICE] MQTT connection failed: {exc}. Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()