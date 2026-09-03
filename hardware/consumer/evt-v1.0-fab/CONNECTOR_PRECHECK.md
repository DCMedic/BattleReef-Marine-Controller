# Production connector architecture precheck

Decision: use mixed keyed/latching connector families, subject to the actual module load budget, harness drawings, and enclosure insertion/access check.

## Candidate families

- Signal/module harnesses: Molex Micro-Lock Plus 2.00 mm. The family is polarized and positive-locking, supports 2–42 circuits, and is rated up to 4.7 A by family configuration. Candidate single-row parts are 3.4 A/contact; candidate dual-row parts are 2.8 A/contact. Production current must be derated using the applicable product specification, wire gauge, circuit loading, and enclosure temperature.
- Power-bearing harnesses: Molex Micro-Fit 3.0, right-angle through-hole, polarized and positive-locking. The selected candidate header series is listed at 8.5 A/contact and 600 V, but the actual harness current remains subject to terminal, wire, temperature, circuit-loading, and mating-cycle derating.
- Service/debug: Micro-Lock Plus 8-circuit is the current candidate because all eight existing nets are used. A Tag-Connect conversion would require a controlled pinout/fixture change rather than a footprint-only substitution.

Primary manufacturer references:

- <https://www.molex.com/en-us/products/connectors/wire-to-board-connectors/micro-lock-plus-connectors>
- <https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/505/505575/5055750590_sd.pdf>
- <https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/220/220201/2202010471_sd.pdf>
- <https://www.molex.com/en-us/products/connectors/wire-to-board-connectors/micro-fit-connectors>
- <https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/430/43045/430450921_sd.pdf>

## CM5 power correction and remaining hold

The prior `J_CM5` assigned one pin to `5V_SYS` and one pin to `3V3_SYS`. The candidate 16-circuit dual-row Micro-Lock Plus header is rated 2.8 A maximum per contact before application derating. Raspberry Pi documents a CM5 5 V / 5 A input capability and requires all six 5 V input pins on the used 100-pin connector to be connected. It also defines CM5 3.3 V as an output and prohibits externally powered pins while CM5 is off. The former single 5 V contact/0.20 mm escape and external 3.3 V assignment were therefore unsafe and have been removed from the deterministic generator.

Official Raspberry Pi reference: <https://www.raspberrypi.com/documentation/computers/compute-module.html#compute-module-5-io-board>

`J_CM5` is now signal-only, with pins 1, 2, 15 and 16 assigned to GND. The generated PCB carries an explicit `J_CM5 SIGNAL ONLY - CM5 POWER NOT IMPLEMENTED` marking, and source validation rejects any reintroduction of a power rail at this connector.

Required disposition: implement and review the actual CM5 carrier and a dedicated protected 5 V path with all CM5 5 V and ground pins, sufficient contacts/copper, sequencing and backfeed control. The present branch contains no such carrier or power interface. See `BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.md`.

## Orientation and mis-mating

The proposed Micro-Fit power candidates are right-angle parts intended to mate toward the nearest board edge. The Micro-Lock signal candidates are provisionally vertical/top-entry. Neither orientation is frozen until the released enclosure CAD and module/harness endpoints are assembled in 3D.

Polarization prevents a housing from being rotated into its mate; it does not necessarily prevent two same-family harnesses with the same circuit count from being cross-connected. Final harness control must prevent cross-mating by keyed variants where available, unique circuit counts or families, constrained branch lengths, and durable function/pin-1 labels. Color alone is not treated as poka-yoke.

## No-footprint rule

No candidate is to be placed into the generator until its exact manufacturer land pattern, keepout, height, board edge relationship, mating direction, terminal/wire selection, and application current are verified. A generic pitch-equivalent footprint is not acceptable.
