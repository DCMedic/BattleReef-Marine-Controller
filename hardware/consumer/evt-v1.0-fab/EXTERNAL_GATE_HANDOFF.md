# BRMC Consumer EVT v1.0 external gate handoff

Revision C — 2026-09-03
Status: **ENGINEERING REVIEW RELEASE — NOT FABRICATION AUTHORITY**

This handoff applies only to the 220 × 78 mm passive modular backplane, its
prototype CM5IO endpoint/harness interfaces and its CNC 6061 enclosure-base
candidate. It does not approve absent PSM-01, daughtercard, rear-I/O or custom
CM5-carrier designs.

## Handoff package

Begin with `BRMC_Consumer_v1.0_Electrical_Engineering_Review_Package.pdf` and
`BRMC_Consumer_v1.0_Engineer_Review_Index.md`. Review the exact successful CI
artifact named `BRMC-Consumer-EVT-v1.0-Fabrication`; its `SHA256SUMS` file is
the configuration record.

| Gate | Handoff disposition | Evidence required to close |
| --- | --- | --- |
| Item 1 / six-hole enclosure base | Ready for responsible-ME review | signed Rev B drawing/CAD disposition; tolerance-aware populated, harness, thermal and service-access fit record; CNC fabricator acceptance |
| Fabricator stackup/DFM | Awaiting vendor return | quote/job ID, controlled stackup, DFM report, exceptions disposition, name and date |
| Item 2 / carrier, loads and harnesses | Ready for qualified-EE review | signed review; all actions closed; first-article CM5IO/connector orientation and harness inspection; measured EVT currents within limits |
| Backplane connectors | Design frozen for review | drawing-to-footprint audit for 13 connectors plus first-article MPN, keying, crimp and access evidence |
| Independent electrical/layout review | Awaiting reviewer | qualified reviewer, completed checklist, report, approving disposition and date |

## Item 1 mechanical datum

The controlled PCB is 220.000 × 78.000 mm. With PCB center as datum, the six
3.20 mm NPTH axes are X = −103/0/+103 mm and Y = −32/+32 mm. In the enclosure
datum of the Rev B base candidate they are:

| Hole | PCB-centered X,Y (mm) | Enclosure X,Y (mm) |
| --- | ---: | ---: |
| H1 | −103, −32 | −103, 25.5 |
| H2 | 0, −32 | 0, 25.5 |
| H3 | +103, −32 | +103, 25.5 |
| H4 | −103, +32 | −103, 89.5 |
| H5 | 0, +32 | 0, 89.5 |
| H6 | +103, +32 | +103, 89.5 |

The CNC 6061-T6 base candidate defines integral OD 10.00 ±0.10 mm bosses,
height 5.00 ±0.05 mm, support plane Z = 8.00 ±0.05 mm, M3×0.5-6H blind threads,
minimum 4.30 mm full thread, M3×6 screws with washers and nominal 3.9 mm
engagement. The drawing controls datum/tolerance details. The nominal supplied-
assembly check contains 114 boss-to-nonbase-solid comparisons with zero
positive-volume intersections. Since the supplied assembly omits populated
module, harness, thermal and service-tool solids, the signed tolerance-aware
final fit review remains mandatory.

## Item 2 electrical boundary

The CM5 endpoint is an official Raspberry Pi CM5 IO Board revision 2 powered
independently at J11 by an official 27 W USB-C supply. J_CM5 is signal-only and
maps exactly to J8 as recorded in the harness schedule. The 24 V system path is
limited to 2.5 A; its calculated 1.47 A continuous envelope becomes 1.83 A with
25% startup/transient margin. HARN-01 is specified as 20 AWG, 105 °C copper;
the calculated warm 0.5 m loop drop at 2.5 A is 0.101 V (0.42%).

All other power-carrying harnesses have a controlled source/destination, pin
group, voltage, expected/worst/allowance current, conductor, maximum length,
warm drop and protection relationship in
`BRMC_Consumer_v1.0_Connector_and_Harness_Schedule.csv`. Signal-only DSI, RF,
GPIO, CAN and RS-485 constructions are controlled separately.

## Return instructions

- Fabricator: complete `fabricator-stackup-dfm-request.csv` and return a
  controlled stackup/DFM record tied to the reviewed commit and artifact.
- Electrical/layout reviewer: complete `independent-review-checklist.csv`,
  attach findings, and sign the PDF disposition page after all blocking actions
  are closed.
- Mechanical reviewer: mark up/sign the base drawing and attach the tolerance-
  aware final fit/interference record.
- Build/test owner: retain connector/harness travelers, first-article photos or
  inspection data, and startup/steady/transient/fault current captures.

Do not change either authorization flag to `true` until the evidence is
committed and the post-approval KiCad/manufacturing workflow passes for the
exact released revision.
