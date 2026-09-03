# BRMC Consumer EVT v1.0 modular backplane

This directory contains the deterministic KiCad source generator and reviewable generated source for the 220 × 78 mm, six-layer BRMC Consumer modular prototype backplane.

## Scope

This is an engineering EVT bare-board package for the module-interconnect backplane represented by `BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb`. It is not the complete integrated BRMC Consumer main logic/power PCB or rear precision-analog PCB described by the v0.9 architecture. It does not authorize commercial production or connection of mains voltage.

The connector footprints are embedded prototype header geometry. They are not substitutes for production MPN/footprint verification or an assembly BOM.

Power nets use short 0.20 mm connector escape neck-downs where required by the 2.54 mm through-hole pitch, widen after leaving the connector field, and use the controlled 1.50 mm 24 V and 2.00 mm 5 V/GND trunks on B.Cu. These neck-downs remain subject to current/thermal review for the actual EVT module loads.

## Automated gates

The GitHub workflow regenerates the committed KiCad sources, rejects source drift, fills the L2/L5 GND zones in an archived manufacturing copy, runs KiCad 9 DRC on that filled board, exports Gerber/drill/position/IPC-D-356/STEP outputs, verifies the L2/L5 Gerbers contain filled GND-plane regions, verifies the complete output set, and checksums every artifact. A successful run proves the checked backplane artifact passed those automated gates for that commit.

## Release holds

`release-status.json` is authoritative for release disposition. The L2/L5 ground-reference planes are now implemented and covered by the source, KiCad DRC, and Gerber-content gates. Fabrication release remains held until the mounting pattern is mechanically checked against the enclosure/standoffs, the fabricator returns an approved stackup/DFM response, connector MPNs and mating orientation are verified for the intended EVT harness, and an independent qualified electrical/layout review is recorded.

The pH/ORP guarded analog section, conductivity AFE, power-stage validation, EMC/ESD, thermal, and ingress-protection gates remain outside this backplane package and retain the holds from the controlled v0.8/v0.9 work.

`release-gate-evidence.json` is the machine-readable external-gate record. `EXTERNAL_GATE_HANDOFF.md` explains the exact evidence needed to close it; the fabricator, connector, and independent-review CSV files are controlled return forms. Blank approval fields are intentional and must not be completed without source evidence from the named external party or responsible engineer.

`CONNECTOR_PRECHECK.md` records the selected mixed-family candidate architecture and the rejected-as-drawn CM5 power path. Candidate MPNs are not production approvals and have not been substituted into the PCB generator.
