# BattleReef Independent Verification Hardware

This directory defines the hardware evidence layer used to verify that physical equipment and critical sensors are behaving consistently with BattleReef commands and device reports.

## Design objective

BattleReef must not treat a device's self-reported state as proof of physical behavior. Critical actuators should be challenged by at least one independent measurement path, and critical environmental values should have an independent comparison channel where practical.

Version 1 focuses on six evidence channels:

- `power_heater_main`: isolated heater-circuit real-power measurement.
- `power_return_pump_main`: isolated return-pump real-power measurement.
- `flow_return_main`: independent return-line hydraulic flow.
- `rpm_return_pump_main`: optional independent pump tach/RPM feedback.
- `tank_temp_verify`: independent secondary tank-temperature probe.
- `sump_level_verify`: independent secondary sump-level probe.

The machine-readable contract is in `verification-package-v1.json`.

## Safety boundary

BattleReef software is not a substitute for electrical protection. Any sensor attached to AC mains must use a galvanically isolated, enclosed, appropriately listed/certified measurement interface installed according to applicable electrical code. Do not connect aquarium-controller GPIO, ADC, breadboards, or exposed low-voltage hobby electronics directly to mains conductors.

Where possible, current/power measurement should be non-invasive or provided by an isolated metering module. Aquatic sensors must be selected for continuous saltwater exposure and installed so a failed sensor cannot create an electrical path into aquarium water.

## Evidence topology

### Heater

The heater controller/relay reports `power=true|false`, while an electrically independent meter publishes `power_heater_main` in watts. BattleReef compares the two. A heater that reports OFF while the independent circuit still consumes heater-like power is treated as a critical contradiction. A heater that reports ON while the circuit is not drawing meaningful power is also a contradiction.

The independent meter must not obtain its value from the heater controller's own commanded state or internal software variable.

### Return pump

Return-pump verification uses different physical domains whenever available:

1. reported device state,
2. dedicated circuit power (`power_return_pump_main`),
3. hydraulic output (`flow_return_main`), and
4. optional rotational evidence (`rpm_return_pump_main`).

This lets BattleReef distinguish several failure classes. Power without flow suggests a blocked/stalled pump or hydraulic obstruction. Flow without expected circuit power suggests a measurement/configuration fault or an alternate flow source. Reported ON with neither power nor flow is likely a command/device-state failure.

### Temperature

`tank_temp_verify` should use a physically separate probe and preferably an independent interface from `tank_temp_main`. The goal is not merely redundancy but common-mode-failure reduction. The secondary probe should not share the same ADC channel, connector, or software driver when practical.

### Sump level

`sump_level_verify` should use a second sensing path. A different technology is preferred when feasible, for example continuous analog/pressure/ultrasonic measurement paired with a discrete optical or float reference. The verification channel is intended to detect disagreement, not necessarily replace the primary sensor.

## Node architecture

A production verification node should have its own BattleReef MQTT certificate identity and publish only its authorized telemetry namespace over mTLS. A suitable node architecture is:

- isolated low-voltage power supply,
- MCU/Linux edge node with watchdog,
- separate isolated inputs for mains-derived measurements,
- protected sensor inputs,
- hardware watchdog/reset path,
- local timestamping with monotonic fallback,
- per-channel calibration constants stored in nonvolatile configuration,
- unique device certificate/private key,
- no actuator-control authority unless explicitly required.

A verification node should ideally be unable to actuate the device it is verifying. That separation reduces the chance that one compromised controller can both change a physical state and forge the evidence proving that state.

## MQTT telemetry contract

Each channel uses the existing authenticated telemetry namespace:

`battlereef/telemetry/<node-identity>/<sensor-key>`

Payload example:

```json
{
  "sensor_key": "power_heater_main",
  "source_node": "verification-node-01",
  "reading_time": "2026-08-09T01:00:00Z",
  "timestamp": "2026-08-09T01:00:00Z",
  "value": 287.4,
  "unit": "W",
  "quality": "good"
}
```

Nodes must never publish `quality=good` merely because communication succeeded. Local sensor faults, calibration failures, impossible ADC values, checksum failures, and self-test failures should publish a non-good quality value or suppress the reading so BattleReef fails to `unknown` rather than accepting bad evidence.

## Commissioning sequence

1. Verify certificate identity and broker ACLs before connecting the node to production telemetry.
2. Confirm each channel reports the expected sensor key, unit, and source node.
3. Record at least 30 stable samples in each required physical state from `verification-package-v1.json`.
4. Compare the primary and verification temperature/level channels and record normal offsets.
5. Exercise heater OFF and ON states and confirm the independent power channel crosses the configured threshold reliably.
6. Exercise return pump OFF and ON states and confirm dedicated power and flow channels transition consistently.
7. If RPM feedback is available, verify RPM falls below and rises above the configured threshold with pump state.
8. Run the existing physical fault injector and confirm BattleReef raises the expected alerts/audit events.
9. Only after successful commissioning should the evidence channel be considered authoritative for automated physical verification.

## Maintenance

Recalibrate or revalidate a channel after sensor replacement, electrical work, plumbing changes, pump replacement, heater replacement, firmware changes affecting sampling, or unexplained drift. Verification sensors should themselves be included in device-health monitoring and periodic plausibility checks.
