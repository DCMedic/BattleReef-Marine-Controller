MQTT_NAMESPACE = "aquarium"

TELEMETRY_SENSORS_TEMPERATURE = f"{MQTT_NAMESPACE}/telemetry/sensors/temperature"
TELEMETRY_SENSORS_PH = f"{MQTT_NAMESPACE}/telemetry/sensors/ph"
TELEMETRY_SENSORS_SALINITY = f"{MQTT_NAMESPACE}/telemetry/sensors/salinity"
TELEMETRY_SENSORS_WATER_LEVEL = f"{MQTT_NAMESPACE}/telemetry/sensors/water_level"

STATE_HEATER = f"{MQTT_NAMESPACE}/state/heater"
STATE_RETURN_PUMP = f"{MQTT_NAMESPACE}/state/return_pump"
STATE_ATO = f"{MQTT_NAMESPACE}/state/ato"

CMD_HEATER_SET = f"{MQTT_NAMESPACE}/cmd/heater/set"
CMD_RETURN_PUMP_SET = f"{MQTT_NAMESPACE}/cmd/return_pump/set"
CMD_ATO_SET = f"{MQTT_NAMESPACE}/cmd/ato/set"

HEALTH_BACKEND = f"{MQTT_NAMESPACE}/health/backend/api"
HEALTH_NODE_SUMP = f"{MQTT_NAMESPACE}/health/node/sump"


def outlet_command_topic(outlet_key: str) -> str:
    return f"{MQTT_NAMESPACE}/cmd/outlets/{outlet_key}/set"


def outlet_state_topic(outlet_key: str) -> str:
    return f"{MQTT_NAMESPACE}/state/outlets/{outlet_key}"