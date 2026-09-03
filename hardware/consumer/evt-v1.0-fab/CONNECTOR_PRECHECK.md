# Production connector implementation precheck

Document status: **DESIGN FROZEN FOR INDEPENDENT REVIEW — FIRST-ARTICLE
VERIFICATION REQUIRED**

All 13 backplane connector references now use controlled production-family
geometry in the deterministic PCB generator. Exact board MPNs, mating housings,
contacts, ratings, footprints, pin-1 conventions and evidence references are in
`connector-production-verification.csv`.

## Implemented families

- `J_CM5`, `J_MCU`: Molex C-Grid III 2.54 mm through-hole headers. `J_CM5`
  uses gold-plated 90130-1216 and is signal-only; `J_MCU` uses 90130-1224.
- `J_PH`, `J_ORP`, `J_EC`, `J_TEMP`, `J_CAN`, `J_485`, `J_SAFE`, `J_SVC`:
  Molex KK 254 single-row friction-lock headers sized to the controlled pinout.
- `J_PWR`, `J_AO`, `J_PWRMOD`: Molex Micro-Fit 3.0 right-angle through-hole
  headers with exact 3.00 mm dual-row pitch and manufacturer-pattern 3.00 mm
  PCB locator holes.

Header headline current ratings are not used as harness design current. The
load schedule applies the lower contact/terminal/wire/branch limit and records
the derated interface allowance for each circuit.

## CM5 correction

The obsolete single-contact CM5 power concept is removed. The EVT CM5 and CM5IO
are powered only through CM5IO J11. J_CM5 maps sixteen signal/return contacts to
CM5IO revision-2 J8; J8 5 V and 3V3 contacts are deliberately not fitted. The
PCB and validator reject any backplane power rail on J_CM5.

Because CM5IO J8 is unshrouded, the 40-circuit housing key does not alone prove
orientation. The first harness requires a 100% pin-to-pin continuity test,
adjacent-short test, red pin-1 marking, keyed strain relief, and reviewer-witnessed
first mating before power is applied.

## Remaining approval work

The independent reviewer must compare every pad/drill/body/courtyard/pin-1
detail with the cited manufacturer drawing and record the result. The first
article must verify:

- actual board and mating MPN markings;
- contact and crimp compatibility with the released conductor gauge;
- polarization, pin-1, insertion direction and cross-mating controls;
- latch, bend-radius, pull/service and enclosure-wall access; and
- continuity, isolation and absence of unintended power at CM5IO J8.

These are controlled review/inspection actions, not missing design assumptions.
