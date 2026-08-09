# BattleReef Verification Node V1

## Purpose

The Verification Node is a dedicated, read-mostly evidence collector that independently verifies critical actuator and sensor behavior. It is intentionally separated from the primary actuator controller so a single device failure cannot simultaneously create a control action and fabricate the evidence that the action succeeded.

## Baseline controller

Primary candidate: Erqos EQSP32CE industrial ESP32-S3 PLC.

Reasons for selection:
- 10/100 Ethernet plus Wi-Fi/BLE
- protected RS485, RS232, and CAN interfaces
- eight configurable 0-10 V / 4-20 mA inputs
- protected field I/O and DIN-rail form factor
- 10-28 VDC industrial supply range
- sufficient pulse/digital I/O for flow/tach feedback
- ESP32-S3 ecosystem suitable for BattleReef MQTT/TLS client firmware

The controller should operate as MQTT identity `verification_node_main` with its own X.509 certificate. It is not permitted to actuate the heater or return pump in V1.

## System architecture

```text
                    BattleReef Verification Node V1

  120 VAC branch loads              Saltwater / process evidence
  --------------------              ----------------------------
  Heater ----[Energy Meter]--RS485----+
                                       |
  Pump ------[Energy Meter]--RS485-----+       +-------------------+
                                               |   EQSP32CE PLC     |
  Return line ---[Flow Meter]--4-20mA/pulse----|                   |
                                               | RS485 / 4-20mA /  |
  Pump tach ------------------pulse-------------| pulse / Ethernet  |
                                               |                   |
  Tank ----[Independent Temp TX]--4-20mA--------|                   |
                                               |                   |
  Sump ----[Ultrasonic Level]----4-20mA---------|                   |
                                               +---------+---------+
                                                         |
                                                   Ethernet/TLS
                                                         |
                                                    Mosquitto 8883
                                                         |
                                                   BattleReef API
```

## Independence rules

1. The verification node must use a separate X.509 identity from actuator nodes.
2. Heater and pump power evidence must come from dedicated electrical measurement channels, never from the actuator controller's own reported state.
3. `tank_temp_verify` must use a physically separate probe and preferably a different signal-conditioning path from `tank_temp_main`.
4. `sump_level_verify` should use a different measurement principle from the primary level sensor. V1 prefers non-contact ultrasonic 4-20 mA sensing.
5. Return-pump verification should use at least two independent domains in production: electrical power plus hydraulic flow. RPM/tach is a third optional domain.
6. Missing or stale evidence means `unknown`; it must never be converted to `verified`.
7. The node is read-only with respect to critical actuators in V1.

## Mains safety boundary

No ESP32 GPIO, ADC, breadboard, hobby current sensor, or exposed low-voltage development electronics may connect directly to 120 VAC. Heater and pump power measurements must use enclosed/listed or otherwise appropriately certified energy-measurement equipment installed inside a suitable mains enclosure. Field installation must comply with applicable electrical code and should be performed by a qualified person.

The verification PLC and all low-voltage sensors are powered from a separate 24 VDC Class 2 DIN-rail supply.

## Recommended evidence channels

### Heater power

`power_heater_main`, watts. Preferred interface: dedicated single-phase energy meter with RS485 Modbus RTU. A suitable engineering candidate is the Eastron SDM120-M because it measures active power/current and supports RS485 Modbus; its published operational voltage range includes 120 VAC service.

### Return-pump power

`power_return_pump_main`, watts. Use a second dedicated meter rather than mathematically subtracting other loads from an aggregate meter.

### Return flow

`flow_return_main`, GPH. Production candidate should be a no-moving-parts electromagnetic meter with corrosion-resistant wetted materials. The firmware supports either pulse or 4-20 mA input. Final sensor sizing must be based on measured operating flow and pipe diameter; a 20 GPM meter is not appropriate for a loop that can exceed 1,200 GPH.

### Return-pump RPM

`rpm_return_pump_main`, RPM. Optional. Accept only a genuine tachometer or independent rotational sensor. Do not republish the commanded motor speed as measured RPM.

### Redundant tank temperature

`tank_temp_verify`, degrees F. Preferred field architecture is an independent RTD/PT100 probe with industrial transmitter output to a 4-20 mA input. It must not share the same probe, ADC, or cable as the primary sensor.

### Redundant sump level

`sump_level_verify`, inches. Preferred V1 approach is a non-contact ultrasonic 4-20 mA sensor mounted above the sump. This avoids continuous seawater contact and provides a different failure mode from a primary immersed/pressure/float sensor.

## Initial I/O allocation

| PLC interface | Signal | BattleReef sensor key | Notes |
|---|---|---|---|
| RS485 address 1 | Heater energy meter | `power_heater_main` | Read active power W |
| RS485 address 2 | Return-pump energy meter | `power_return_pump_main` | Read active power W |
| AI1 4-20 mA | Return flow | `flow_return_main` | Alternate pulse input supported |
| DI/Pulse 1 | Pump tach | `rpm_return_pump_main` | Optional |
| AI2 4-20 mA | Redundant temperature | `tank_temp_verify` | Independent transmitter |
| AI3 4-20 mA | Redundant sump level | `sump_level_verify` | Ultrasonic preferred |
| Ethernet | BattleReef MQTT | n/a | MQTT/TLS 8883 |
| RS485 spare | Future verification meter | reserved | Expansion |
| AI4-AI8 | Future evidence | reserved | ORP/DO/leak/power expansions |

## Network and security

- Preferred transport: wired Ethernet.
- MQTT: TLS 1.2+ to port 8883.
- Client certificate CN: `verification_node_main`.
- Publish-only ACL under `battlereef/telemetry/verification_node_main/#`.
- No command-topic subscription is required for normal V1 operation.
- Local configuration should be disabled or authenticated after commissioning.
- Firmware must use monotonic sample sequencing and UTC timestamps synchronized by NTP.

## Power and enclosure

Use a 24 VDC DIN-rail Class 2 supply sized for the PLC plus all 4-20 mA loops with at least 30% reserve. A 60 W / 2.5 A supply is ample for V1 and leaves expansion margin.

Use a nonmetallic NEMA 4X/IP66 enclosure in the fish-room/sump environment, with DIN rail, separated mains and SELV/low-voltage wiring zones, strain-relieved cable glands, ferrules, terminal blocks, and a drip-loop-friendly cable entry layout. If the energy meters are mounted in the same physical enclosure, use a listed enclosure and internal barriers/spacing appropriate for mains wiring; otherwise use a separate mains metering enclosure and route only RS485 to the verification node.

## Prototype phases

### Phase 1 - Bench node

Build the EQSP32CE + 24 VDC supply + simulated 4-20 mA inputs + RS485 meter bench. Implement certificate provisioning, Modbus reads, telemetry publishing, watchdog, and local diagnostics. No aquarium equipment is connected.

### Phase 2 - Low-voltage sensor integration

Install independent temperature and sump-level sensors. Validate scaling, plausibility, stale-data handling, calibration offsets, and sensor disagreement alerts.

### Phase 3 - Power evidence

Install heater and return-pump energy meters in a proper mains enclosure. Validate OFF/ON thresholds over at least 30 stable samples per state and under normal line-voltage variation.

### Phase 4 - Hydraulic verification

Install and calibrate the return-flow sensor. Validate normal range, pump-off residual flow, restart transients, and blocked/partially restricted return scenarios.

### Phase 5 - Acceptance and soak

Run at least 72 hours in observation-only mode. BattleReef may alert and audit but should not add any new autonomous shutdown behavior based solely on the new evidence until the commissioning record is complete.

## Exit criteria

Verification Node V1 is commissioned when all required channels publish authenticated telemetry, evidence remains within calibrated bounds during normal operation, injected contradictions are detected, missing evidence becomes `unknown`, the audit trail records state changes, and the node completes a 72-hour observation soak without unexplained verification failures.
