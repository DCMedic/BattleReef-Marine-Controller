# BRMC Consumer EVT v1.0 modular backplane

This directory contains the deterministic KiCad source generator and reviewable generated source for the 220 × 78 mm, six-layer BRMC Consumer modular prototype backplane.

## Scope

This is an engineering EVT bare-board package for the module-interconnect backplane represented by `BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb`. It is not the complete integrated BRMC Consumer main logic/power PCB or rear precision-analog PCB described by the v0.9 architecture. It does not authorize commercial production or connection of mains voltage.

The connector footprints are embedded prototype header geometry. They are not substitutes for production MPN/footprint verification or an assembly BOM.

## Automated gates

The GitHub workflow regenerates the committed KiCad sources, rejects source drift, runs KiCad 9 DRC, exports Gerber/drill/position/IPC-D-356/STEP outputs, verifies the output set and checksums every artifact. A successful run proves the checked backplane artifact passed those automated gates for that commit.

## Release holds

`release-status.json` is authoritative for release disposition. The fabrication release remains held until the reserved L2/L5 ground-reference pours are implemented and checked, the mounting pattern is mechanically checked against the enclosure/standoffs, the fabricator returns an approved stackup/DFM response, connector MPNs and mating orientation are verified for the intended EVT harness, and an independent qualified electrical/layout review is recorded.

The pH/ORP guarded analog section, conductivity AFE, power-stage validation, EMC/ESD, thermal, and ingress-protection gates remain outside this backplane package and retain the holds from the controlled v0.8/v0.9 work.
