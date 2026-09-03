# BRMC Consumer EVT v1.0 external gate handoff

This handoff applies only to the 220 × 78 mm modular prototype backplane in this directory. It is not an approval of the integrated main logic/power or rear precision-analog boards.

## Current disposition

The KiCad 9.0.9 CI baseline at commit `7ee8025b67477b51e17edb343fe79a6a2d4b94c9` passed with zero DRC violations, zero unconnected pads, and zero footprint errors. The archived artifact contains six copper layers, separate PTH/NPTH drills, IPC-D-356, position data, STEP, and checksums. That automated result does not close the four external gates below.

| Gate | Current disposition | Required evidence |
| --- | --- | --- |
| Six-hole enclosure fit | Blocked | Released enclosure base/boss CAD or drawing and signed coordinate/tolerance comparison |
| Fabricator stackup/DFM | Awaiting vendor | Returned stackup, DFM report, job/quote ID, named approval, and date |
| Production connectors | Blocked | All 13 board and mate MPNs plus drawing/footprint/orientation verification |
| Independent review | Awaiting reviewer | Qualified reviewer identity, qualifications, completed checklist, findings, disposition, and date |

## Mechanical finding

The PCB datum is the upper-left corner of the rectangular Edge.Cuts outline. The board pattern is three columns by two rows:

| Hole | X (mm) | Y (mm) | Drill (mm) |
| --- | ---: | ---: | ---: |
| H1 | 7.000 | 7.000 | 3.200 |
| H2 | 110.000 | 7.000 | 3.200 |
| H3 | 213.000 | 7.000 | 3.200 |
| H4 | 7.000 | 71.000 | 3.200 |
| H5 | 110.000 | 71.000 | 3.200 |
| H6 | 213.000 | 71.000 | 3.200 |

The available v0.7 base-shell STEP has no standoff or hole geometry, and the v0.7 220 × 78 PCB STEP is an unperforated envelope. The six bosses found in the v0.2 assembly are for a different 245 × 60 mm PCB: their local pattern is X = 6.5/122.5/238.5 mm and Y = 5/52 mm. That obsolete pattern is not valid evidence for this board.

Mechanical closure must compare all six nominal axes and the complete tolerance stack, including the 3.2 mm PCB holes, boss/insert location, screw clearance, standoff height, component/copper clearance, and enclosure collision/access. A bounding-box fit alone is not acceptance.

## Fabricator return

Send the CI manufacturing artifact together with `fabricator-stackup-dfm-request.csv`. The fabricator must identify the exact material/construction it will build, confirm every stated capability, and return its DFM output. Verbal or portal-only “looks good” responses are not controlled evidence; retain a PDF, email export, or signed job record.

## Connector verification

The generated footprints are unkeyed prototype header geometry. `connector-production-verification.csv` intentionally has blank production fields. A connector is not verified until both halves and the real mating direction are frozen against manufacturer drawings and the KiCad geometry is checked pad-by-pad.

## Independent review

The reviewer must be independent of the layout author and demonstrably experienced with multi-layer low-voltage power, embedded buses, PCB layout, and DFM. They must receive the exact CI artifact and complete `independent-review-checklist.csv`. Fabricator DFM is not a substitute for electrical/layout review.

## Release rule

Do not change either authorization flag to `true` until the evidence is committed, independently reproducible, and the post-approval KiCad/manufacturing workflow passes for the exact released commit.
