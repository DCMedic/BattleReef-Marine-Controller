# Verification Node V1 Firmware Contract

## Identity

- MQTT certificate CN: `verification_node_main`
- MQTT client ID should be stable and derived from the device identity plus a short hardware identifier.
- The private key must remain local to the node and must never be checked into Git.
- Production firmware must validate the broker CA and broker hostname.

## MQTT

Broker: BattleReef Mosquitto TLS listener on port 8883.

Publish namespace:

`battlereef/telemetry/verification_node_main/<sensor_key>`

The node does not subscribe to actuator command topics in V1. This preserves its read-mostly evidence role.

## Telemetry payload

```json
{
  "sensor_key": "power_heater_main",
  "source_node": "verification_node_main",
  "timestamp": "2026-08-09T00:00:00Z",
  "value": 247.6,
  "unit": "W",
  "quality": "good"
}
```

The payload identity must always match the certificate-controlled topic identity.

## Required channels

| Sensor key | Source | Unit | Nominal sample interval | Required |
|---|---|---|---:|---|
| `power_heater_main` | RS485 energy meter | W | 5 s | yes |
| `power_return_pump_main` | RS485 energy meter | W | 5 s | yes |
| `flow_return_main` | 4-20 mA or pulse flow meter | gph | 5 s | yes |
| `rpm_return_pump_main` | pulse/tach | rpm | 5 s | optional |
| `tank_temp_verify` | independent RTD transmitter | F | 10 s | yes |
| `sump_level_verify` | ultrasonic transmitter | in | 10 s | yes |

## Quality rules

`good` means the raw interface succeeded, range/scaling is valid, the sample is fresh, and local diagnostics detected no sensor/open-loop fault.

`bad` should be published when the node knows the measurement is invalid. Examples include Modbus CRC/timeouts after retry exhaustion, 4-20 mA loop current below a configured open-loop threshold, impossible pulse frequency, sensor self-diagnostic failure, or calibration invalidation.

Do not fabricate a numeric fallback value and label it `good` when the source is unavailable.

## 4-20 mA conversion

Each analog channel must use configurable engineering endpoints rather than hard-coded ADC counts:

`engineering_value = low_value + ((current_mA - 4.0) / 16.0) * (high_value - low_value)`

Clamp only for display; do not hide out-of-range current from diagnostics. A low current such as <3.6 mA should normally become a sensor/loop fault rather than zero engineering value.

## Modbus

Recommended initial map:

- Address 1: heater energy meter
- Address 2: return-pump energy meter

The firmware adapter should expose a generic `read_active_power_w(address)` interface. Vendor-specific Modbus registers belong in a device-driver module so replacing the energy meter does not alter the telemetry layer.

Retries must be bounded. After retry exhaustion, publish degraded/bad quality and increment a local diagnostic counter rather than blocking the whole acquisition loop.

## Pulse input

Pulse-derived flow/RPM measurements must use hardware pulse counters where practical. Sample calculations should be based on elapsed monotonic time, not wall-clock time, so NTP corrections cannot create false frequency spikes.

## Local watchdog

The ESP32 hardware/task watchdog should be enabled. The node should automatically reboot after an unrecoverable acquisition/network deadlock, but preserve a reboot reason counter in nonvolatile storage and publish that diagnostic after reconnect.

## Offline behavior

The verification node does not actuate equipment when isolated from BattleReef. If MQTT is unavailable, it continues sampling and may buffer a small bounded set of recent measurements locally. Recovery publishing must preserve original timestamps and must not flood the broker with an unbounded backlog.

## Configuration

Configuration includes:

- MQTT endpoint and CA
- per-sensor enabled state
- Modbus address/register profile
- 4-20 mA scaling endpoints
- pulse K-factor
- sample period
- calibration offset/gain

Production configuration changes require authenticated local service access or a future signed remote-configuration mechanism. V1 does not accept arbitrary configuration over an unauthenticated web page.

## Diagnostics

The node should publish or expose locally:

- uptime
- firmware version/build hash
- certificate expiration date if available
- Ethernet link state
- MQTT reconnect count
- per-channel sample/error counters
- Modbus timeout/CRC counters
- analog loop-fault count
- watchdog reset reason

Diagnostic telemetry should use a separate `diagnostic_*` sensor/key namespace or a future node-health topic so it does not masquerade as physical process evidence.

## Secure update direction

V1 may use physical/USB firmware updates during commissioning. Before unattended field deployment, firmware updates should move to signed images with anti-rollback/version controls. OTA should not be enabled merely because the ESP32 supports it.

## Acceptance tests

1. Certificate-authenticated connection succeeds; certificate-less connection fails.
2. The node cannot publish outside its ACL namespace.
3. Each sensor publishes at its required cadence for one hour without drift or memory growth.
4. Disconnecting each sensor produces non-good quality rather than a fabricated valid value.
5. Removing Ethernet causes controlled reconnect behavior without watchdog storms.
6. Broker restart results in automatic TLS reconnect.
7. NTP time correction does not corrupt pulse-derived flow/RPM.
8. Restart reason is observable after forced watchdog reset.
9. Each Modbus meter can be independently disconnected without blocking other channels.
10. A 72-hour observation soak completes before the node is declared production-ready.
