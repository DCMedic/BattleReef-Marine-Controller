# BRMC Consumer v1.0 CM5 carrier, harness, and load schedule

Document ID: BRMC-ELEC-EVT-020  
Revision: B
Date: 2026-09-03  
Status: **RELEASE CANDIDATE - EVT ARCHITECTURE FROZEN; SYSTEM LOAD CLOSURE HOLD**

## Disposition

Item 2 is **OPEN**. The prototype architecture, official CM5 endpoint, exact
GPIO mapping, signal-only interface, independent CM5 power boundary, and
proposed conductor constructions are now controlled. The unsafe former CM5
power assignments and connector-footprint mismatch are corrected in the
generated PCB. Closure is still prohibited because several non-CM5 loads,
protection settings, maximum installed harness lengths, production harness
drawings, mating-orientation inspections, and measured startup/transient data
do not exist. The companion CSV retains those facts as explicit HOLD rows.

## Controlled prototype architecture

For BRMC Consumer EVT v1.0:

- The compute endpoint is the official Raspberry Pi Compute Module 5 IO Board,
  revision 2, used as an external bench-EVT carrier. It is not represented as
  mounted inside the Consumer enclosure.
- CM5IO is powered independently at J11 by the official Raspberry Pi 27 W USB-C
  power supply or an electrically equivalent, approved 5 V/5 A USB-PD source.
  CM5 power does not come from the BRMC 24 V input or `5V_SYS`.
- The only BRMC-to-CM5IO connection is the 16-conductor, 3.3 V signal harness
  between backplane J_CM5 and CM5IO J8. Pins 2/4 (+5 V) and 1/17 (+3V3) of J8
  are deliberately not populated in this harness.
- CM5IO display, RF, USB, Ethernet, storage, and fan connections remain local
  to CM5IO. The custom integrated CM5 carrier is deferred to a controlled
  post-EVT revision and shall not silently inherit this prototype layout.

This boundary prevents a nominal 5 A CM5 envelope plus the display and BRMC
logic from being assigned to the v0.9 6 A TPSM63606 rail.

## Controlled official sources

| Source | Controlled identification / applicability |
|---|---|
| CM5 datasheet | Raspberry Pi RP-008180-DS-7, build 2026-06-08; local source SHA-256 `80070fefd8db6e8abc6e146c8b7b5fb318ba129cc1e28826936d547fde79c863` |
| CM5IO datasheet | Raspberry Pi RP-008182-DS-2; local source SHA-256 `ca45baa18ff67d39ae58b05454f7ce229451ff077befdea606e7e708ecc83cb1` |
| CM5IO revision-2 KiCad design ZIP | Raspberry Pi RP-008099-DD-1; SHA-256 `48b14a6757b0edc0ac110331445f35a4212b5ce432bdcec6605c99431b59496b` |
| Official CM5IO PCB | `CM5IO.kicad_pcb`; SHA-256 `728ec772d1bdf6ff2c9f7a81fd8ff00164c894d002221f522f627ae3f8945026` |
| Official GPIO schematic sheet | `CM5_GPIO.kicad_sch`; SHA-256 `8ffe39b0224a6934c04516d779c69923ef5c033de557275619377f67e2ea3593` |
| Current BRMC KiCad generator/PCB | Controls J_CM5 and the 220 x 78 backplane at the evaluated branch commit |
| v0.9 BOM, harness map, and preliminary CPL | Architecture/load intent only where not implemented in the current KiCad source |

Official references:

- <https://pip-assets.raspberrypi.com/categories/944-raspberry-pi-compute-module-5/documents/RP-008180-DS-7-cm5-datasheet.pdf>
- <https://pip-assets.raspberrypi.com/categories/1097-raspberry-pi-compute-module-5-io-board/documents/RP-008182-DS-2-cm5io-datasheet.pdf>
- <https://pip.raspberrypi.com/categories/1098-design-files>
- <https://www.raspberrypi.com/products/compute-module-5-io-board/>

## Official CM5IO endpoint definition

The official design establishes a 160 x 90 mm board. Its four PCB mounting
holes are 2.7 mm M2.5 clearance holes at `(11,13)`, `(132.5,13)`, `(11,82)`,
and `(132.5,82)` relative to the lower-left board outline. These dimensions are
not applied to the Consumer enclosure because the EVT carrier is external.

CM5IO J11 is the controlled power endpoint: 5 V, up to 5 A negotiated with a
compatible USB-C PD source. Alternate back-powering through GPIO J8 is not
allowed in BRMC EVT. CM5IO USB 3 ports have an approximately 1.2 A combined
limit per the CM5IO datasheet; USB loads remain inside the separate 5 V/5 A
carrier envelope.

J8 is a Toby Electronics `THD-20-R`, 2 x 20, 2.54 mm vertical through-hole
header. It is unshrouded. GPIO voltage reference is 3.3 V by the official
default population. The active BRMC mapping is:

| J_CM5 | BRMC signal | CM5IO J8 | CM5/GPIO function |
|---:|---|---:|---|
| 1 | GND | 6 | GND |
| 2 | GND | 9 | GND |
| 3 | I2C_SCL | 5 | GPIO3 / SCL1 |
| 4 | I2C_SDA | 3 | GPIO2 / SDA1 |
| 5 | CM5_TX | 8 | GPIO14 / TXD |
| 6 | CM5_RX | 10 | GPIO15 / RXD |
| 7 | CM5_HEARTBEAT | 11 | GPIO17 |
| 8 | SAFETY_ACK | 13 | GPIO27 |
| 9 | SPI_SCK | 23 | GPIO11 / SCLK |
| 10 | SPI_MISO | 21 | GPIO9 / MISO |
| 11 | SPI_MOSI | 19 | GPIO10 / MOSI |
| 12 | SPI_CS0 | 24 | GPIO8 / CE0 |
| 13 | GPIO_AUX0 | 15 | GPIO22 |
| 14 | GPIO_AUX1 | 16 | GPIO23 |
| 15 | GND | 20 | GND |
| 16 | GND | 25 | GND |

All signal conductors are 3.3 V logic or ground. CM5IO J8 pins 1/17 (+3V3),
2/4 (+5V), and all unlisted pins are no-connect in HARN-CM5-SIG. No voltage
rail may cross J_CM5.

## J_CM5 production implementation

The BRMC board connector is now controlled as Molex C-Grid III
`90130-1116`: 16 circuits, two rows, 2.54 mm pitch, vertical through-hole,
shrouded/polarized with latch, 1.60 mm PCB, 3 A/contact and 350 V maximum. The
generator uses manufacturer circuit numbering, 1.00 mm finished holes,
2.54 mm grids, and the drawing's 22.66 x 9.75 mm nominal maximum body envelope.
Mating housing is `90142-0016`; the 26/28 AWG female crimp terminal is
`90119-2121`.

The CM5IO end uses Molex housing `90142-0040` and the same terminal on J8.
Because J8 itself is unshrouded, that end is not mechanically keyed by the
header. The build drawing must require red pin-1 marking, a labelled keyed
backshell/strain relief, two-person first-article inspection, and 100%
continuity/short/orientation test before connection. This is a release HOLD,
not a paperwork-only warning.

Manufacturer references:

- <https://www.molex.com/en-us/products/part-detail/901301116>
- <https://www.molex.com/en-us/products/part-detail/901420016>
- <https://www.molex.com/en-us/products/part-detail/901420040>
- <https://www.molex.com/en-us/products/part-detail/901192121>

## Power/load boundary and worst-case schedule

| Load/domain | Expected continuous | Calculated worst case/design allowance | Release disposition |
|---|---:|---:|---|
| CM5 + CM5IO local peripherals | 0.9 A preliminary operating estimate; not qualified | 5.0 A at 5 V (25 W) input envelope; source sized 5 A continuous | Independently supplied at J11; PROVISIONAL until EVT current/inrush capture |
| CM5IO USB 3 ports | use-dependent | approximately 1.2 A combined limit, included in the 5 A carrier envelope | Local CM5IO load; no BRMC harness current |
| Waveshare 10.1-inch DSI LCD (C) | approximately 0.52 A at 5 V documented | 1.0 A design allowance | 22 AWG proposal; measure startup/backlight peak |
| Main logic + STM32 safety MCU | not derivable from supplied netlist | TBD | HOLD; no implemented schematic or rail current model |
| Isolated CAN/RS-485 | not derivable | TBD; NXE2S0505MC is 2 W class | HOLD; operating load/conversion loss absent |
| Rear I/O and analog | not derivable | TBD | HOLD; actual endpoint rail/pin allocation absent |
| 0-10 V / low-side outputs | load and simultaneity dependent | TBD at 24 V | HOLD; external loads and duty cycle absent |
| Service/debug interfaces | configuration dependent | TBD | HOLD; permanent versus fixture-only endpoint not frozen |
| 24 V source | load dependent | 2.5 A continuous adapter limit, 60 W | Wire can be sized; system sufficiency/eFuse settings remain HOLD |

The schedule intentionally does not synthesize a false total from component
names. A BOM without an implemented schematic, actual rail connections,
operating modes, external loads, and protection settings cannot establish
worst-case simultaneous current.

## Wire gauge and voltage drop

Warm-copper voltage drop uses `Vdrop = 2 x L x I x R20 x 1.25` for a supply
and return pair. Resistance values are 20 AWG 0.03331 ohm/m, 22 AWG 0.05296
ohm/m, and 26 AWG 0.1339 ohm/m.

| Harness | Maximum one-way length | Design current | Controlled proposal | Warm drop | Disposition |
|---|---:|---:|---|---:|---|
| HARN-01 24 V input | 0.50 m | 2.5 A | 2 x 20 AWG stranded Cu, 105 C | 0.104 V, 0.43% | PROVISIONAL; 18 AWG is not electrically required, but connector/eFuse/temperature-rise validation remains |
| HARN-04 display 5 V | 0.50 m | 1.0 A | 2 x 22 AWG stranded Cu, 105 C | 0.066 V, 1.32% | PROVISIONAL; verify connector and measured inrush |
| HARN-CM5-SIG | 0.30 m | signal only | 16 x 26 AWG stranded Cu, 105 C | not a power-drop path | PROVISIONAL; required by common terminal range and test controls |
| CM5IO J11 power | standard PSU lead | 5.0 A | official 27 W USB-C PSU assembly | qualified as a complete PSU/cable assembly, not a BRMC loose-wire harness | PROVISIONAL pending local plug variant and procurement record |

The earlier 18 AWG 24 V proposal is therefore not inherited. Twenty AWG meets
the adapter-limited current and voltage-drop target at 0.50 m; 18 AWG may be
retained only for mechanical robustness or a connector requirement established
by the released harness drawing.

## Signal-only cable requirements

- CM5 signal: 16 x 26 AWG, 105 C stranded copper, maximum 0.30 m. Route over a
  ground reference where possible; interleave the four assigned ground returns;
  keep SPI clock away from raw pH/ORP nodes. Validate I2C capacitance and SPI
  signal integrity at the released length.
- Display: Raspberry Pi-compatible 22-pin-to-15-pin MIPI DSI cable/adapter for
  the selected CM5IO display port and Waveshare orientation. Preserve 100 ohm
  differential construction; do not substitute discrete wires; minimum bend
  radius 5 mm pending the cable manufacturer's larger requirement.
- RF: Raspberry Pi-approved 50 ohm micro-coax and antenna assembly; do not
  classify it by power-wire AWG. Select the exact cable/antenna/bulkhead MPN and
  validate antenna clearance at EVT.
- CAN and RS-485: 120 ohm twisted pair with the released reference/shield,
  termination, bias, length, and isolation strategy. Keep separated from
  switching power and raw analog paths.
- I2C/SPI/UART/service: short ground-referenced signal bundles; establish
  maximum length from interface timing/capacitance rather than ampacity.

## Companion schedule and closure evidence

`BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.csv` is normative for
connector, pin, load, conductor, voltage-drop, protection, routing, and status.
`RELEASED_EVT_INTERFACE` means only that the named endpoint mapping is frozen
for this EVT architecture; it does not authorize fabrication or production.

Item 2 changes to CLOSED only when:

- every HOLD/TBD power row in the CSV has an evidenced maximum load, protection
  setting, conductor/contact rating, and released maximum length;
- HARN-CM5-SIG and other applicable production harness drawings freeze terminal
  cavity numbers, labels, keying/strain relief, length, and 100% test criteria;
- CM5IO J8 mating orientation and the corrected J_CM5 footprint are verified
  against first-article hardware and manufacturer drawings;
- startup, steady-state, shutdown/backfeed, and transient captures close the
  5 V display/logic and 24 V budgets with thermal and voltage-drop margins;
- a real schematic/netlist establishes the main-logic, safety, isolation,
  Rear-I/O, analog, 0-10 V, and service loads; and
- the independent qualified electrical/layout review approves the implemented
  evidence. Until then Item 2 and the fabrication release remain OPEN.
