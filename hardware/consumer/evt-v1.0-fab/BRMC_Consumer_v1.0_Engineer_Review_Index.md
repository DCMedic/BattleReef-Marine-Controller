# BRMC Consumer v1.0 independent engineering review index

Revision: C
Date: 2026-09-03
Status: **ENGINEERING REVIEW RELEASE - NOT FABRICATION AUTHORITY**

This set is complete for review of the modular passive backplane scope. It is not a complete integrated-product design package because PSM-01 and daughtercard implementation schematics/layouts do not exist in the controlled repository.

## Review order

1. Read the electrical engineering review package PDF.
2. Review the interconnect schematic, pinout and netlist together.
3. Review the KiCad PCB/rules and the exact successful CI manufacturing artifact.
4. Review power/connector/harness schedules and mechanical base evidence.
5. Record findings in the checklist and sign the disposition page only after actions close.

## Controlled files

- `BRMC_Consumer_v1.0_Electrical_Engineering_Review_Package.pdf`
- `BRMC_Consumer_EVT_Backplane_v1.0_Interconnect_Schematic.pdf`
- `BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb`
- `BRMC_Consumer_EVT_Backplane_v1.0.kicad_pro`
- `BRMC_Consumer_EVT_Backplane_v1.0.kicad_dru`
- `generate_brmc_evt.py`
- `generate_engineering_review_package.py`
- `validate_brmc_evt.py`
- `BRMC_Consumer_EVT_Backplane_v1.0_Pinout.csv`
- `BRMC_Consumer_EVT_Backplane_v1.0_Netlist.csv`
- `BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.md`
- `BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.csv`
- `BRMC_Consumer_v1.0_Power_Budget.csv`
- `BRMC_Consumer_v1.0_Connector_and_Harness_Schedule.csv`
- `connector-production-verification.csv`
- `independent-review-checklist.csv`
- `BRMC_Consumer_v1.0_Enclosure_Base_Mounting_Verification.md`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE.step`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_Drawing.pdf`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_dimensions.csv`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_interference.csv`
- `release-status.json`
- `release-gate-evidence.json`
- `EXTERNAL_GATE_HANDOFF.md`

## Configuration control

Use the `SHA256SUMS` manifest in the successful CI manufacturing artifact for byte-level configuration hashes. The source index intentionally does not pre-compute hashes because text checkout normalization and the PDF runtime can vary by platform.
