# BattleReef MQTT Topic Conventions

## Base Namespace
All MQTT topics should use the `battlereef/` base namespace.

## Telemetry
Telemetry messages are published under:

- `battlereef/telemetry/<sensor_key>`

Examples:

- `battlereef/telemetry/tank_temp_main`
- `battlereef/telemetry/tank_ph_main`
- `battlereef/telemetry/tank_salinity_main`
- `battlereef/telemetry/sump_level_main`

## Commands
Device command topics are published under:

- `battlereef/cmd/<device_key>/set`

Examples:

- `battlereef/cmd/heater_main/set`
- `battlereef/cmd/return_pump_main/set`
- `battlereef/cmd/ato_pump_main/set`

## State
Device state topics are published under:

- `battlereef/state/<device_key>`

Examples:

- `battlereef/state/heater_main`
- `battlereef/state/return_pump_main`
- `battlereef/state/ato_pump_main`

## Health
Health topics are published under:

- `battlereef/health/<component_type>/<component_key>`

Examples:

- `battlereef/health/backend/api`
- `battlereef/health/node/sump_node`

## Telemetry Payload Shape

```json
{
  "sensor_key": "tank_temp_main",
  "timestamp": "2026-03-10T20:20:00Z",
  "value": 78.5,
  "unit": "F",
  "quality": "good",
  "source_node": "sump_node"
}


To run the simulator locally on Windows, install `paho-mqtt` in your local Python environment if needed:

```powershell
pip install paho-mqtt