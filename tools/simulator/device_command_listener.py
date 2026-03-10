import json
import os
import time

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "battlereef-device-listener")

TOPIC_SUBSCRIBE = "battlereef/cmd/#"


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
    except Exception as exc:
        print(f"[DEVICE] Failed to decode message on {msg.topic}: {exc}")


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