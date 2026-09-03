# BRMC Consumer EVT v1.0 modular backplane

This directory is the controlled engineer-review release for the 220 × 78 mm,
six-layer BRMC Consumer modular prototype backplane. The design is generated
deterministically; review the generated KiCad source and the exact successful
CI manufacturing artifact together.

## Controlled scope

The PCB is a passive module-interconnect backplane. It is not the complete
integrated main logic/power board or rear precision-analog board described by
the older v0.9 architecture. The EVT compute endpoint is an official Raspberry
Pi CM5 IO Board revision 2, independently powered at J11 by an official 27 W
USB-C supply. `J_CM5` is a signal-only 16-circuit interface; CM5 power is not
carried on the backplane.

The current generator implements production geometry for all 13 board
connectors:

- Molex C-Grid III 90130-1216 at `J_CM5` and 90130-1224 at `J_MCU`;
- Molex KK 254 22-23-20x1 headers for sensor, field-bus, safety and service
  interfaces; and
- Molex Micro-Fit 3.0 43045-0600/-0400/-0800 right-angle headers, including
  the manufacturer-pattern locator holes, for `J_PWR`, `J_AO` and `J_PWRMOD`.

`connector-production-verification.csv` freezes the design selection and cites
the governing manufacturer evidence. Independent drawing comparison,
first-article keying/orientation, crimp inspection and mating-access acceptance
remain required approval evidence; the file does not claim those events have
already occurred.

## Electrical definition

The source generator, pinout, interconnect schematic, machine-readable netlist,
power budget and harness schedule together define the board-only electrical
interface. A component-level KiCad schematic/ERC result is not asserted because
this artifact contains no active circuitry. The CI validator instead reconciles
the generated endpoint schedule to the PCB and its IPC-D-356 export.

Power routing uses 1.50 mm `24V_IN` and 2.00 mm `5V_SYS` B.Cu trunks. Connector
fan-out is segregated by copper layer, with L2 and L5 reserved as continuous GND
reference planes. GND connector pads connect directly to those planes. The
review package records calculated interface ceilings, conductor gauges,
maximum harness lengths, warm voltage drop and branch-protection requirements.
Unimplemented PSM-01 and daughtercard circuits must be independently reviewed
as separate design objects and must comply with the controlled ceilings.

## Automated gates

The GitHub workflow regenerates all controlled source and review artifacts,
rejects drift, fills the L2/L5 planes in an archived manufacturing copy, runs
KiCad 9 DRC, exports Gerber/drill/position/IPC-D-356/STEP outputs, reconciles
the netlist, validates the complete package, and checksums every artifact. Only
an artifact from a successful run for the exact reviewed commit is acceptable.

## Review package

Start with `BRMC_Consumer_v1.0_Engineer_Review_Index.md` and
`BRMC_Consumer_v1.0_Electrical_Engineering_Review_Package.pdf`. The
interconnect PDF, CSV schedules, KiCad files, enclosure-base candidate and
external return forms are all included in the CI artifact.

## Release status

`release-status.json` and `release-gate-evidence.json` are authoritative. This
revision is **complete for independent engineering review of the passive
backplane scope**, but it is **not a prototype fabrication release**. The
following approvals/evidence cannot be self-issued and remain external gates:

- responsible mechanical engineer approval of the CNC 6061 base and a
  tolerance-aware populated/harness/thermal/service fit record;
- fabricator-returned stackup and DFM approval tied to the exact CI artifact;
- independent qualified electrical/layout review with all findings closed;
- connector/harness first-article orientation, crimp, continuity and access
  evidence; and
- measured EVT startup, steady-state, transient/fault and thermal evidence.

Commercial production, mains connection, and approval of absent module designs
remain prohibited.
