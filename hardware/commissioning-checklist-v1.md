# Independent Verification Package V1 Commissioning Checklist

Use this checklist when bringing a real verification node or sensor channel into service. A channel is not authoritative merely because it publishes MQTT telemetry.

## 1. Installation safety

- [ ] AC mains measurement hardware is enclosed, galvanically isolated, and appropriately listed/certified for the installation.
- [ ] No BattleReef GPIO, ADC, breadboard, exposed development board, or aquarium-water probe is directly connected to mains potential.
- [ ] Electrical installation follows applicable local code and manufacturer instructions.
- [ ] Saltwater-exposed flow/level/temperature components are rated for continuous immersion or wetted service as applicable.
- [ ] Verification wiring is physically separated from actuator-control wiring where practical.

## 2. Identity and security

- [ ] Verification node has a unique X.509 certificate and private key.
- [ ] Certificate CN matches the intended BattleReef node identity.
- [ ] Private key is not shared with an actuator node.
- [ ] Mosquitto ACL permits only the verification node's telemetry namespace.
- [ ] Test connection without the client certificate is rejected.

## 3. Channel registration

For every installed channel:

- [ ] Sensor key exactly matches `hardware/verification-package-v1.json`.
- [ ] Unit matches the manifest and sensor catalog.
- [ ] `source_node` matches the authenticated MQTT topic identity.
- [ ] Nominal readings arrive with `quality=good`.
- [ ] Local sensor/self-test failures produce non-good quality or no reading rather than fabricated normal data.

## 4. Heater verification

- [ ] With heater commanded OFF, `power_heater_main` remains below the configured ON threshold.
- [ ] With heater commanded ON, `power_heater_main` rises above the configured ON threshold.
- [ ] Repeat at least five OFF/ON cycles.
- [ ] Verify BattleReef reports `verified` when relay state and power agree.
- [ ] Inject/produce an OFF + power-present contradiction and confirm a critical physical-verification alert and audit event.
- [ ] Restore normal state and confirm recovery is audited.

## 5. Return pump verification

- [ ] With pump OFF, `power_return_pump_main` is below threshold.
- [ ] With pump OFF, `flow_return_main` is below threshold after hydraulic coast-down.
- [ ] With pump ON, circuit power exceeds threshold.
- [ ] With pump ON, flow exceeds the configured minimum.
- [ ] If RPM is available, OFF/ON states cross the configured RPM threshold.
- [ ] Verify at least two independent channels support normal pump state before considering the pump fully verified.
- [ ] Test pump ON + zero/low flow and confirm a critical hydraulic contradiction.
- [ ] Test pump OFF + power present and confirm a critical electrical contradiction.

## 6. Temperature redundancy

- [ ] `tank_temp_main` and `tank_temp_verify` are on physically independent sensing paths.
- [ ] Both probes are stabilized in the same water volume for calibration.
- [ ] Record at least 30 stable paired samples.
- [ ] Normal disagreement stays within 1.5 F or the subsequently approved calibrated threshold.
- [ ] A disagreement above the warning threshold produces a degraded verification state.
- [ ] A disagreement above twice the threshold produces a critical verification state.

## 7. Sump-level redundancy

- [ ] `sump_level_main` and `sump_level_verify` use independent inputs and preferably different sensing mechanisms.
- [ ] Record at least 30 stable paired samples at normal operating level.
- [ ] Test at a second known level if safely possible.
- [ ] Normal disagreement remains within 0.5 in or the subsequently approved calibrated threshold.
- [ ] Warning and critical disagreement bands behave as expected.

## 8. Evidence freshness and fail-safe behavior

- [ ] Stop each verification feed in turn and confirm evidence older than 120 seconds becomes `unknown` rather than `verified`.
- [ ] Confirm stale verification data cannot silently sustain a healthy physical-verification state.
- [ ] Confirm suspect/quarantined telemetry is excluded from physical verification.
- [ ] Confirm suspect leak-probe telemetry remains fail-safe and cannot be interpreted as dry.

## 9. Audit and health integration

- [ ] Physical verification failure creates a tamper-evident audit event.
- [ ] Critical contradiction imposes the expected device-health penalty.
- [ ] Degraded/redundancy warnings impose a smaller health penalty than critical contradictions.
- [ ] Recovery clears the active physical-verification alert and creates a recovery audit event.

## 10. Acceptance record

Record the following outside source control in the installation/maintenance record:

- node certificate identity,
- hardware serial numbers,
- sensor/interface model and revision,
- calibration date and reference method,
- measured OFF and ON baselines,
- approved thresholds,
- installation photographs/diagram,
- commissioning operator,
- commissioning date,
- next planned verification/calibration date.

Do not store private keys, passwords, or other secrets in the commissioning record or Git repository.
