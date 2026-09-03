# BRMC Consumer v1.0 enclosure-base mounting verification

Document ID: BRMC-MECH-EVT-010  
Revision: B
Date: 2026-09-03  
Units: millimetres unless stated otherwise  
Status: **RELEASE CANDIDATE - ENGINEERING APPROVAL HOLD**

## Disposition

Item 1 is **OPEN**. The selected process and complete six-boss CNC definition
are now controlled, and the nominal supplied-assembly interference check
passes. The package is approval-ready but cannot be marked released because
the controlled assembly does not include populated PCB component bodies,
connector mates, routed harnesses, thermal hardware, or service-tool
envelopes. No responsible mechanical-engineer approval or fabricator DFM
acceptance is present.

## Controlled inputs and conflict resolution

1. Current branch generator and generated KiCad PCB control the v1.0 EVT
   backplane outline, hole references, and 3.20 mm NPTH definition.
2. `BRMC_Consumer_v0.8_Exact_Display_Manufacturing_Assembly.step`, SHA-256
   `1e1f78229c2624be0a0ecc7766795e55c19090104cca487c9a2ebd9da287a810`,
   controls the available enclosure/display geometry.
3. `BRMC_v0.9_Main_PCB_Outline_and_Mounting.dxf`, SHA-256
   `db5b9649be9386a0024e809063a1d1ceec5d66952b2cd83004b765efaa52687f`,
   is supporting evidence only. It contains one model-space circle at
   PCB-centred `(0,+32)`, radius 1.6, with no board outline or other five holes.

The v0.9 DXF cannot independently establish a six-hole release pattern. The
current deterministic KiCad source independently confirms all six axes. The
request's coordinate values are correct, but its H2-H5 naming order differs
from the current KiCad references; this document preserves the KiCad names.

## Datum transformation and verified hole axes

PCB datum P is the board centre. Enclosure datums are A, the exterior bottom
plane at Z=0; B, the longitudinal centre plane X=0; and C, the transverse
centre plane Y=57.5. The PCB underside/support plane is Z=8.00. Transform from
KiCad coordinates `(Xk,Yk)` to enclosure coordinates:

`Xe = Xk - 110; Ye = Yk + 18.5; Ze = 8.00`.

| Ref | KiCad X | KiCad Y | PCB-centred X | PCB-centred Y | Enclosure X | Enclosure Y |
|---|---:|---:|---:|---:|---:|---:|
| H1 | 7 | 7 | -103 | -32 | -103 | 25.5 |
| H2 | 110 | 7 | 0 | -32 | 0 | 25.5 |
| H3 | 213 | 7 | +103 | -32 | +103 | 25.5 |
| H4 | 7 | 71 | -103 | +32 | -103 | 89.5 |
| H5 | 110 | 71 | 0 | +32 | 0 | 89.5 |
| H6 | 213 | 71 | +103 | +32 | +103 | 89.5 |

## Controlled CNC 6061 boss definition

| Characteristic | Controlled release-candidate value |
|---|---|
| Base material/process | 6061-T6 aluminum to ASTM B209/B221; CNC-machined integral bosses; no inserts |
| Boss axes | Enclosure X/Y above; true position diameter 0.20 to A-B-C |
| Boss outside diameter | 10.00 +/-0.10 |
| Boss height | 5.00 +/-0.05 above nominal inner floor Z3.00 |
| PCB support plane | Z=8.00 +/-0.05 to datum A; six tops coplanar within 0.10 |
| Boss perpendicularity | 0.10 to A over the 5 mm height |
| PCB hole | diameter 3.20 NPTH, controlled by current KiCad source |
| Thread | M3 x 0.5-6H blind; full thread depth 4.30 minimum |
| Tap drill | diameter 2.50 +0.10/-0.00; depth 5.30 +/-0.20 from boss top |
| Residual base below tap drill | 2.70 nominal to exterior datum A |
| Screw/washer | M3x6 ISO 7380-1 A4-70 button head; 0.5 mm PA66 or PEEK washer |
| Screw engagement | 3.9 mm nominal after 1.6 mm PCB and 0.5 mm washer; verify no bottoming |
| Assembly torque | 0.35 +/-0.05 N.m with marine-compatible anti-seize; confirm during EVT |
| PCB-to-inner-floor clearance | 5.00 nominal from Z3 floor to Z8 PCB underside |
| Finish | Type II Class 2 black anodize, sealed, 12-25 micrometres per MIL-PRF-8625; mask threads and identified datum/bond surfaces |
| General tolerances | ISO 2768-mK; critical dimensions and GD&T above take precedence |
| Edge/surface requirement | break edges 0.2-0.5; remove burrs; Ra 3.2 micrometres unless noted |

The STEP represents the nominal 2.50 mm tap-drill cylinder rather than modeled
helical threads. Drawing 010-BASE-01 controls the M3 thread.

## Interference, clearance, and service review

The generator hash-checks and imports the exact v0.8 assembly, verifies 20
solids and the base envelope `X=-142.5..142.5`, `Y=0..115`, `Z=0..34`, places
each OD10 x 5 boss, then calculates intersection volume and minimum distance
against every one of the 19 non-base solids. The machine-readable report
contains 114 checks and no positive-volume intersection.

Nearest nominal clearances in the supplied geometry are:

| Boss row | Display carrier | Rear-I/O board | Other supplied solids |
|---|---:|---:|---:|
| Y=25.5, H1-H3 | 6.084 | 73.700 | 19.461 or greater, excluding intended enclosure interfaces |
| Y=89.5, H4-H6 | 66.827 | 9.700 | 17.500 or greater |

These results confirm the bosses do not collide with the supplied enclosure,
display carrier, display solids, rear-I/O envelope, or walls at nominal
geometry. They cannot confirm missing objects. In particular, the supplied
Main PCB is a featureless 220 x 78 x 1.6 solid without holes/components, and
there are no connector-mate, harness/bend-radius, heatsink, thermal-interface,
screwdriver-access, or service-removal envelopes. The final tolerance-aware
assembly check must include them.

## Release-candidate evidence

- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE.step`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_Drawing.pdf`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_dimensions.csv`
- `BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_interference.csv`
- `generate_mechanical_release_candidate.py`

## Remaining closure evidence

Item 1 changes to CLOSED only when:

- the responsible mechanical engineer approves Revision B's datums, CNC
  process, material, boss/thread/tolerance design, finish, and fastener stack;
- the enclosure fabricator accepts machinability, tolerances, thread depth,
  anodize masking, and sealing/warpage controls;
- a controlled assembly supplies populated PCB/component bodies, production
  connector mates, routed harnesses/bend radii, thermal hardware, and service
  tool/removal envelopes;
- the tolerance-aware final interference/service-access check passes and is
  signed; and
- the candidate STEP and 010-BASE-01 drawing are promoted to a signed RELEASED
  revision. Until then they shall not be used as fabrication authority.
