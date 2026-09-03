# BRMC Consumer v1.0 CM5 carrier, harness and load schedule

Document ID: BRMC-ELEC-EVT-020  
Revision: A  
Date: 2026-09-03  
Status: **HOLD - INCOMPLETE IMPLEMENTATION**

## Disposition

Item 2 is **OPEN**. This review resolves an unsafe power assignment in the
current generator and establishes a controlled endpoint/load schedule, but the
repository does not contain an actual CM5 carrier schematic/layout or a
released endpoint harness drawing. The v0.9 integrated-carrier definition and
the v1.0 modular-backplane source are different architectures and cannot be
treated as one released implementation.

## Sources and applicability

- Current branch `hardware/consumer/evt-v1.0-fab`: authoritative for the actual
  generated 220 x 78 EVT backplane.
- v0.9 EVT BOM, Internal Harness Map and Main PCB preliminary CPL: architecture
  intent only where not implemented in current KiCad.
- Raspberry Pi Compute Module 5 datasheet, release 3 / document
  RP-008180-DS-7, build 2026-06-08: authoritative CM5 electrical interface.
- Raspberry Pi CM5 IO Board datasheet, RP-008182-DS-2, and official reference
  design: implementation reference, not BRMC verification evidence.
- Waveshare 10.1inch DSI LCD (C) product documentation: 5 V load reference.

## Actual repository implementation

| Definition | What it actually contains | Status |
|---|---|---|
| v0.9 BOM/CPL | CM5104032 at U10; two Hirose DF40C-100DS-0.4V(51) receptacles J10/J11; preliminary centres X97/X123, Y36 | Architecture intent; no matching KiCad schematic/layout supplied |
| Current v1.0 KiCad | Generic 2x8, 2.54 mm `J_CM5` on a modular backplane | Not a CM5 carrier or a 200-pin CM5 endpoint |
| Current change | `J_CM5` is now `CM5_SIGNAL_HARNESS`; pins 1,2,15,16 are GND and pins 3-14 signals; no 5 V, 3.3 V, 12 V or 24 V | Corrected safety state; power remains unimplemented |

The earlier `J_CM5` single 5 V contact and 0.20 mm escape were unsuitable for a
5 A class CM5 feed. Its `3V3_SYS` pin also created an unverified external supply
path into a CM5 endpoint. Both assignments were removed from the deterministic
generator and a PCB silkscreen HOLD marking was added. Validation now fails if
power is reintroduced to `J_CM5`.

## CM5 endpoint requirements

The CM5 has two 100-pin connectors: pins 1-100 on connector 1 and 101-200 on
connector 2. A BRMC carrier must control at least the following groups.

| Group | CM5 pins | Requirement / BRMC disposition |
|---|---|---|
| Main 5 V input | 77,79,81,83,85,87 | 4.75-5.25 V; connect all six with adequate copper. BRMC implementation absent. |
| Connector-1 grounds | 1,2,7,8,13,14,22,23,32,33,42,43,52,53,59,60,65,66,71,74,98 | All grounds on a used connector must connect. |
| 3.3 V output | 84,86 | Output only; 300 mA per pin, 600 mA total. Do not drive from `3V3_SYS`. |
| 1.8 V output | 88,90 | Output only; 300 mA per pin, 600 mA total. |
| GPIO reference | 78 | Must connect to CM5 3.3 V or 1.8 V; must not float or be grounded. |
| RTC battery | 76 | 2.5-3.5 V if used; implementation absent. |
| Power/control | 92,93,94,96,99 | PWR_Button, nRPIBOOT, CC1, CC2, PMIC_Enable; treatment absent. |
| Display control | 80,82,97,100 | SCL0, SDA0, CAM_GPIO0/1 as required by selected DSI interface. |
| GPIO/UART/SPI/I2C | 24-58 as assigned | Exact GPIO-number/function and level mapping is absent; abstract signal names are insufficient. |
| Ethernet | 3-19 as used | Magnetics, LEDs, fan signals and routing must follow reference design; implementation absent. |
| USB2/PCIe controls | 101-114 | 90 ohm USB2; PCIe controls and clock required if used; implementation absent. |
| MIPI0 | 115,117,121,123,127,129,133,135,139,141 | 100 ohm pairs; determine lane count/interface and FFC adapter mapping. |
| USB3-0 | 128,130,134,136,140,142 | 90 ohm pairs; implementation/use not controlled. |
| HDMI1 / USB3-1 | 143-171 | Implementation/use not controlled. |
| MIPI1 / HDMI0 | 170-200 | Implementation/use not controlled. |
| Connector-2 grounds | 107,108,113,114,119,120,125,126,131,132,137,138,144,150,155,156,161,162,167,168,173,174,179,180,185,186,191,192,197,198 | Connect all if connector 2 is used. |

Differential-pair requirements include 100 ohm MIPI pair matching within
0.15 mm and 90 ohm USB/PCIe routing as applicable. No signal may be externally
powered while CM5 is off. Power-up order is 5 V, PMIC_Enable, CM5 3.3 V, then
CM5 1.8 V.

The v0.9 Hirose receptacle is not accepted merely because it has 100 contacts.
The current CM5 datasheet identifies Amphenol 10164227-1001A1RLF for 1.5 mm
stacking with no underside clearance and 10164227-1004A1RLF for 4.0 mm stacking
with 2.5 mm underside clearance. BRMC must verify the selected receptacle's
mechanical compatibility, stack height, land pattern, underside clearance and
mated orientation against the actual CM5 revision and enclosure.

## Power budget

Values labelled *source limit* or *design envelope* are not measured BRMC
consumption. Unknown loads remain unknown; they are not converted into invented
numbers.

| Load | Nominal / expected | Worst-case design allowance | Basis and disposition |
|---|---:|---:|---|
| CM5 module | 0.9 A typical operating; 0.4 A typical idle at 5 V | 5.0 A at 5 V | Official typicals and 5 V/5 A input capability; actual BRMC peak not measured |
| Waveshare 10.1 DSI LCD (C) | approx. 0.52 A at 5 V with backlight | 1.0 A at 5 V provisional | Product documentation plus startup/lot margin; measure EVT peak |
| Main logic + STM32 safety MCU | unknown | TBD | No implemented schematic/netlist or load model |
| Isolated CAN/RS-485 domain | unknown | TBD; NXE2S0505MC output is 2 W class | Device population known; operating load and conversion loss not closed |
| Rear I/O analog circuitry | unknown | TBD | Population known; power pins and harness allocation absent |
| 0-10 V / low-side outputs | load-dependent | TBD at 24 V | External loads, duty cycle and simultaneous-channel case absent |
| USB/service/peripherals | configuration-dependent | TBD | Carrier endpoint and peripheral policy absent |

The known CM5 design envelope (5.0 A) plus provisional display allocation
(1.0 A) already consumes the full 6 A rating of the v0.9 TPSM63606 before main
logic, isolated interfaces, Rear I/O, conversion loss, startup margin or
transient margin. The v0.9 single 6 A `5V_MAIN` architecture is therefore **not
approved as a worst-case system supply**. Closure requires either a measured,
qualified lower system envelope with controlled peripheral limits or a revised
power tree with separate/greater-capacity protected rails and validated copper,
thermal and transient performance.

The 24 V source is a frozen 60 W / 2.5 A adapter. Its 2.5 A rating caps external
continuous input, but it does not prove eFuse settings, wire/contact temperature,
inrush behaviour or downstream simultaneous-load sufficiency.

## Wire selection and voltage drop

Copper voltage-drop calculations use conductor resistance at 20 C and a 1.25
resistance multiplier for a conservative warm-harness estimate. Formula:

`Vdrop = 2 x length x current x resistance_per_metre x 1.25`.

| Path | Candidate max one-way length | Design current | Candidate conductors | Warm Vdrop | Status |
|---|---:|---:|---|---:|---|
| HARN-01 24 V input | 0.50 m | 2.5 A | 2 x 20 AWG stranded Cu, 105 C | 0.104 V (0.43%) | PROVISIONAL; 18 AWG is not required by current/voltage-drop calculation, but may be retained for robustness after terminal/route review |
| HARN-04 display 5 V | 0.50 m | 1.0 A | 2 x 22 AWG stranded Cu, 105 C | 0.066 V (1.32%) | PROVISIONAL; verify display connector and measured inrush |
| Dedicated CM5 5 V candidate | 0.30 m | 5.0 A total | 2 x 20 AWG 5 V + 2 x 20 AWG GND, 2.5 A/conductor, 105 C | 0.062 V (1.23%) | HOLD; connector, source, eFuse and carrier absent |

Resistance basis: 20 AWG 0.03331 ohm/m and 22 AWG 0.05296 ohm/m at 20 C.
These maximum lengths are design proposals, not measured harness routings. If a
released route exceeds them, recalculate and revise the gauge.

## Harness disposition

The companion CSV is the controlled row-level schedule. Summary:

| Harness | Construction | Status / reason |
|---|---|---|
| HARN-01 | Two power conductors; proposed 20 AWG stranded Cu 105 C | PROVISIONAL; M12-to-board pin map, contact rating, length and eFuse settings not controlled |
| HARN-02 | Power conductors sized separately; impedance/ground-aware signal bundle for SPI/I2C/control | HOLD; 20-pin pinout, load, connectors and length absent |
| HARN-03 | 15-position 1.0 mm FFC plus verified 22-pin/CM5 MIPI adapter as required | HOLD; exact DSI pin map, orientation and adapter absent; min bend radius 5 mm from v0.9 map |
| HARN-04 | Two-wire 22 AWG candidate | PROVISIONAL; connector MPN, load-switch/eFuse and inrush test absent |
| HARN-05 | Raspberry Pi approved 50 ohm micro-coax/antenna assembly | HOLD; cable/antenna MPN, bulkhead and RF/enclosure validation absent |
| CAN | 120 ohm twisted pair, controlled shield/reference strategy | HOLD; endpoints/length/termination not released |
| RS-485 | 120 ohm twisted pair, controlled shield/reference strategy | HOLD; endpoints/length/bias/termination not released |
| I2C/SPI/UART | Ground-referenced short internal signal harness; no power-current AWG selection | HOLD; exact endpoint pin mapping and max lengths absent |

## Required closure evidence

Item 2 may be changed to CLOSED only when:

- the architecture decision is frozen: integrated CM5 J10/J11 carrier or a
  separately identified CM5 carrier plus signal/power harnesses;
- the matching KiCad schematic and PCB implement all used CM5 pins, all grounds,
  GPIO_VREF, sequencing/backfeed protection and differential-pair constraints;
- every connector/contact/terminal MPN, mating orientation and exact pin map is
  verified to manufacturer drawings and actual endpoint hardware;
- maximum harness lengths and routing are released;
- measured startup, steady-state and transient loads close the power budget,
  regulator/eFuse/copper/thermal margins and voltage-drop limits;
- the complete CSV has no HOLD/TBD rows and an independent qualified reviewer
  approves the electrical/layout implementation.

## Controlled companion

`BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.csv` is normative for
row-level pin/load/wire status. Blank or `TBD` entries are intentional blockers.
