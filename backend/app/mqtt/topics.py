MQTT_NAMESPACE = "battlereef"

TOPIC_TELEMETRY_ROOT = f"{MQTT_NAMESPACE}/telemetry"
TOPIC_TELEMETRY_SENSORS_ROOT = f"{TOPIC_TELEMETRY_ROOT}/sensors"
TOPIC_TELEMETRY_TEMPERATURE = f"{TOPIC_TELEMETRY_SENSORS_ROOT}/temperature"
TOPIC_TELEMETRY_PH = f"{TOPIC_TELEMETRY_SENSORS_ROOT}/ph"
TOPIC_TELEMETRY_SALINITY = f"{TOPIC_TELEMETRY_SENSORS_ROOT}/salinity"
TOPIC_TELEMETRY_WATER_LEVEL = f"{TOPIC_TELEMETRY_SENSORS_ROOT}/water_level"

TOPIC_STATE_ROOT = f"{MQTT_NAMESPACE}/state"
TOPIC_STATE_HEATER = f"{TOPIC_STATE_ROOT}/heater"
TOPIC_STATE_RETURN_PUMP = f"{TOPIC_STATE_ROOT}/return_pump"
TOPIC_STATE_ATO = f"{TOPIC_STATE_ROOT}/ato"

TOPIC_CMD_ROOT = f"{MQTT_NAMESPACE}/cmd"
TOPIC_CMD_HEATER_SET = f"{TOPIC_CMD_ROOT}/heater/set"
TOPIC_CMD_RETURN_PUMP_SET = f"{TOPIC_CMD_ROOT}/return_pump/set"
TOPIC_CMD_ATO_SET = f"{TOPIC_CMD_ROOT}/ato/set"

TOPIC_ACK_ROOT = f"{MQTT_NAMESPACE}/ack"

TOPIC_HEALTH_ROOT = f"{MQTT_NAMESPACE}/health"
TOPIC_HEALTH_BACKEND = f"{TOPIC_HEALTH_ROOT}/backend/api"
TOPIC_HEALTH_NODE_SUMP = f"{TOPIC_HEALTH_ROOT}/node/sump"

TOPIC_TELEMETRY_SUBSCRIBE_ALL = f"{TOPIC_TELEMETRY_ROOT}/#"
TOPIC_ACK_SUBSCRIBE_ALL = f"{TOPIC_ACK_ROOT}/#"


def telemetry_sensor_topic(sensor_type: str) -> str:
    return f"{TOPIC_TELEMETRY_SENSORS_ROOT}/{sensor_type}"


def telemetry_sensor_key_topic(sensor_key: str) -> str:
    return f"{TOPIC_TELEMETRY_ROOT}/{sensor_key}"


def outlet_command_topic(outlet_key: str) -> str:
    return f"{TOPIC_CMD_ROOT}/outlets/{outlet_key}/set"


def outlet_state_topic(outlet_key: str) -> str:
    return f"{TOPIC_STATE_ROOT}/outlets/{outlet_key}"


def device_command_topic(device_key: str) -> str:
    return f"{TOPIC_CMD_ROOT}/{device_key}/set"


def device_ack_topic(device_key: str) -> str:
    return f"{TOPIC_ACK_ROOT}/{device_key}"