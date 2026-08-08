from __future__ import annotations

import ssl
from pathlib import Path

import paho.mqtt.client as mqtt

from app.config import Settings


def configure_mqtt_security(client: mqtt.Client, settings: Settings) -> None:
    """Apply authenticated TLS settings to a Paho MQTT client.

    Production identity is derived from the X.509 client certificate by Mosquitto.
    Username/password support is retained only for explicit non-TLS migration use.
    """
    if settings.mqtt_tls_enabled:
        required_paths = {
            "CA certificate": settings.mqtt_tls_ca_cert,
            "client certificate": settings.mqtt_tls_client_cert,
            "client private key": settings.mqtt_tls_client_key,
        }
        missing = [label for label, path in required_paths.items() if not Path(path).is_file()]
        if missing:
            raise FileNotFoundError(
                "MQTT mTLS is enabled but required material is missing: " + ", ".join(missing)
            )

        client.tls_set(
            ca_certs=settings.mqtt_tls_ca_cert,
            certfile=settings.mqtt_tls_client_cert,
            keyfile=settings.mqtt_tls_client_key,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
            cert_reqs=ssl.CERT_REQUIRED,
        )
        client.tls_insecure_set(not settings.mqtt_tls_check_hostname)
        return

    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
