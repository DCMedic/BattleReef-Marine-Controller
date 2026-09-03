# BRMC Consumer v1.0 enclosure-base mounting verification

Document ID: BRMC-MECH-EVT-010  
Revision: A  
Date: 2026-09-03  
Units: millimetres unless stated otherwise  
Status: **HOLD - NOT RELEASED FOR FABRICATION**

## Disposition

Item 1 is **OPEN**. The six-hole coordinate set is confirmed in the current
KiCad source, but the supplied enclosure base does not contain bosses and the
v0.9 mounting DXF is incomplete. The controlled package also lacks component,
connector, harness and thermal solid geometry needed for a final interference
review. The accompanying STEP and drawing are therefore a traceable
**PROVISIONAL DESIGN CANDIDATE**, not a released enclosure definition.

## Controlled evidence and source priority

1. Current branch generator and generated KiCad PCB at the evaluated commit.
   These control the actual v1.0 EVT backplane outline and hole references.
2. `BRMC_Consumer_v0.8_Exact_Display_Manufacturing_Assembly.step`, SHA-256
   `1e1f78229c2624be0a0ecc7766795e55c19090104cca487c9a2ebd9da287a810`.
3. `BRMC_v0.9_Main_PCB_Outline_and_Mounting.dxf`, SHA-256
   `db5b9649be9386a0024e809063a1d1ceec5d66952b2cd83004b765efaa52687f`.

The v0.9 DXF declares millimetres but contains only one model-space entity: a
circle centred at `(0, 32)` with radius 1.6. It contains neither the board
outline nor the other five holes and cannot independently establish a released
six-hole pattern. The current deterministic KiCad generator and NPTH output do
establish all six holes.

## Datum transformation and verified hole axes

PCB datum P is the board centre. Enclosure candidate datums are: A, the
interior base-floor support surface at Z = 3.0 in the v0.8 assembly; B, the
enclosure/PCB longitudinal centre plane X = 0; and C, the PCB transverse centre
plane Y = 57.5. The board underside/support plane is Z = 8.0. Transformation
from current KiCad coordinates `(Xk, Yk)` to enclosure assembly coordinates is:

`Xe = Xk - 110; Ye = Yk + 18.5; Ze = 8.0`.

| Ref | KiCad X | KiCad Y | PCB-centred X | PCB-centred Y | Enclosure X | Enclosure Y |
|---|---:|---:|---:|---:|---:|---:|
| H1 | 7 | 7 | -103 | -32 | -103 | 25.5 |
| H2 | 110 | 7 | 0 | -32 | 0 | 25.5 |
| H3 | 213 | 7 | +103 | -32 | +103 | 25.5 |
| H4 | 7 | 71 | -103 | +32 | -103 | 89.5 |
| H5 | 110 | 71 | 0 | +32 | 0 | 89.5 |
| H6 | 213 | 71 | +103 | +32 | +103 | 89.5 |

The coordinate set in the fabrication request is correct, but its H2-H5 label
assignment is not the label assignment in the authoritative current KiCad
source. This document preserves the actual KiCad references shown above.

## Candidate boss definition - not approved

The following values are an engineering candidate needed to expose the design
decision and support CAD review. They are not inherited released dimensions.

| Characteristic | Candidate value | Proposed tolerance/status |
|---|---:|---|
| Boss axes | Enclosure X/Y in table above | true position diameter 0.30 to A-B-C; HOLD |
| Boss outside diameter | 10.00 | +/-0.20; HOLD |
| Boss top/support plane | Z = 8.00 | +/-0.10 to A; HOLD |
| Boss height above inner floor | 5.00 | derived from Z3 floor to Z8 PCB underside; HOLD |
| PCB hole | diameter 3.20 NPTH | controlled by current KiCad source |
| Insert candidate | SPIROL 29M3-3.56, item 151032, M3 x 0.5 | HOLD pending material/process approval |
| Insert pilot | diameter 3.99 | +0.08/-0.00 per insert manufacturer; HOLD |
| Pilot depth | 4.10 minimum | candidate; bottom must remain closed; HOLD |
| Insert length | 3.56 nominal | manufacturer value |
| Screw | M3 x 0.5 | length/head/washer HOLD pending assembly stack |
| Minimum thread engagement | 3.0 target, not to exceed available insert thread | HOLD pending screw stack |
| PCB-to-inner-floor clearance | 5.00 nominal | direct v0.8 geometry result |

The insert manufacturer's generic guidance recommends boss diameter based on
insert diameter and host material/process. The package does not control base
material, moulding/printing process, draft, ribbing, shrink allowance, or
insertion method. Therefore the boss OD, pilot, tolerance and insert cannot be
released until those inputs are approved by the enclosure fabricator.

General tolerance proposal for otherwise-undimensioned candidate geometry:
ISO 2768-mK. This is a proposal only; it is not a substitute for material- and
process-specific DFM approval.

Insert reference sources:

- <https://shop.spirol.com/item/series-29-30-short-heat-ultrasonic-insert-metric/series-29-short-heat-ultrasonic-insert-metric/151032>
- <https://www.spirol.com/resources/white-papers/how-to-design-the-proper-hole-for-heat-ultrasonic-inserts/>

## Interference and clearance check

Six OD10 x 5 boss envelopes were placed on the verified axes and checked
against all 20 solids in the exact-display assembly. There were no positive
volume intersections with any non-base solid. The boss tops contact the nominal
featureless PCB underside at Z8 as intended. Nearest non-penetrating nominal
distances in the supplied envelope assembly were:

| Boss row | Rear-I/O board | Display carrier | Other displayed/front solids |
|---|---:|---:|---:|
| Y = 25.5 (H1-H3) | 73.7 | 6.084 | 19.461 or greater, excluding touching housing interface |
| Y = 89.5 (H4-H6) | 9.7 | 66.827 | 17.5 or greater |

This check proves only nominal envelope non-penetration in the supplied v0.8
assembly. It does **not** prove clearance to component bodies, connector mating
volumes, cable bend radii, harness clips, heatsinks/thermal interfaces, screw
heads/tools, or service paths because those solids are absent. The Main PCB
solid itself is a 220 x 78 x 1.6 rectangular block with no holes or components.

## Required closure evidence

Item 1 may be changed to CLOSED only after all of the following exist:

- responsible mechanical engineer approves the datum scheme, material,
  process, insert, boss geometry, tolerance and screw stack;
- fabricator DFM confirms pilot/boss/rib design for the selected material and
  process;
- a released component-populated PCB STEP, connector mating envelopes, display
  carrier, rear I/O, thermal hardware and routed harness envelopes are assembled
  with the base;
- tolerance-aware interference, cable routing and service-access review passes;
- the candidate STEP/drawing is superseded by a signed released revision.

## Candidate artifacts

- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_PROVISIONAL.step`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_PROVISIONAL_Drawing.pdf`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_PROVISIONAL_dimensions.csv`

These artifacts intentionally contain `PROVISIONAL` in their names and shall
not be used as released tooling or fabrication authority.
