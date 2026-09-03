# BRMC Consumer v1.0 CM5 carrier, harness, and load schedule

Document ID: BRMC-ELEC-EVT-020
Revision: C
Date: 2026-09-03
Status: **ENGINEERING REVIEW RELEASE - NOT FABRICATION AUTHORITY**

## Disposition

Item 2 is **READY FOR INDEPENDENT REVIEW, NOT CLOSED**. The prototype carrier
architecture, all backplane connector MPNs/footprints, pin functions, endpoint
current ceilings, harness constructions, maximum lengths, voltage-drop
calculations, and protection requirements are controlled by this revision.
Formal closure still requires an independent qualified engineer's approval,
first-article connector/orientation evidence, and measured startup/steady/
transient current evidence. Daughtercard and PSM-01 implementation approval is
outside the passive-backplane review scope and cannot be inferred from this
interface schedule.

## Controlled EVT architecture

- Compute: official Raspberry Pi Compute Module 5 on official CM5 IO Board
  revision 2, located outside the enclosure during EVT.
- CM5 power: official 27 W USB-C supply at CM5IO J11. J_CM5 is signal-only;
  no CM5IO 5 V or 3V3 contact is carried into the BRMC backplane.
- Backplane: passive six-layer 220 x 78 mm interconnect PCB with 13 production-
  geometry connectors and six M3 mounting holes.
- System power: Mean Well GST60A24-P1J, 24 V / 2.5 A / 60 W, through HARN-01
  to a separately reviewed PSM-01 protection/conversion module. The interface
  budget reserves at most 2.0 A continuous and 2.5 A transient at 24 V.
- Later revision: custom integrated CM5 carrier. It is not authorized by this
  EVT document and must receive a new schematic/layout review.

## CM5IO J8 to J_CM5 controlled map

| Backplane | Net | CM5IO J8 | BCM function |
|---:|---|---:|---|
| 1 | GND | 6 | GND |
| 2 | GND | 9 | GND |
| 3 | I2C_SCL | 5 | GPIO3/SCL1 |
| 4 | I2C_SDA | 3 | GPIO2/SDA1 |
| 5 | CM5_TX | 8 | GPIO14/TXD |
| 6 | CM5_RX | 10 | GPIO15/RXD |
| 7 | CM5_HEARTBEAT | 11 | GPIO17 |
| 8 | SAFETY_ACK | 13 | GPIO27 |
| 9 | SPI_SCK | 23 | GPIO11/SCLK |
| 10 | SPI_MISO | 21 | GPIO9/MISO |
| 11 | SPI_MOSI | 19 | GPIO10/MOSI |
| 12 | SPI_CS0 | 24 | GPIO8/CE0 |
| 13 | GPIO_AUX0 | 15 | GPIO22 |
| 14 | GPIO_AUX1 | 16 | GPIO23 |
| 15 | GND | 20 | GND |
| 16 | GND | 25 | GND |


CM5IO J8 pins 1 and 17 (3V3) and 2 and 4 (5V) have no contacts in the
prototype harness. A 100% continuity/short/orientation test is mandatory before
the unshrouded J8 end is connected.

## Power budget conclusions

- The 24 V design-envelope input is 1.47 A continuous before system margin.
  Applying a 25% startup/transient factor gives 1.83 A, leaving 0.67 A (26.7%)
  below the 2.5 A adapter ceiling.
- HARN-01 is 20 AWG, not the inherited 18 AWG proposal. At 2.5 A and 0.50 m
  one-way, the 75 C loop estimate is about 0.101 V (0.42%). 18 AWG may be used
  for mechanical robustness, but is not required by the calculated drop.
- CM5/CM5IO power is independently budgeted at 5 V / 5 A and never uses
  5V_SYS. Display power has a separate 5 V / 1 A design allowance.
- 5V_SYS endpoint allowances total 0.95 A; the branch is specified at 1.25 A.
- The listed currents for unimplemented daughtercards are hard interface
  ceilings, not measured claims. A noncompliant module requires an ECO.

## Signal construction

- CM5 GPIO harness: 26 AWG, 105 C, 0.30 m maximum; four dedicated returns;
  no power contacts at CM5IO J8.
- CAN FD: 120 ohm twisted pair, termination only at physical bus ends; shield
  and chassis bond reviewed at system assembly.
- RS-485: 120 ohm twisted pair, single controlled bias location, termination at
  physical ends; do not branch long stubs.
- DSI: controlled-impedance 22-to-15 FFC/adapter, 0.20 m target, 5 mm minimum
  bend radius; exact procurement MPN and contact-side orientation recorded on
  the build traveler.
- RF: approved 50 ohm antenna/coax assembly; no tight bend or metal intrusion
  into the antenna keepout.

## Controlled companion evidence

- `BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.csv`
- `BRMC_Consumer_v1.0_Power_Budget.csv`
- `BRMC_Consumer_v1.0_Connector_and_Harness_Schedule.csv`
- `BRMC_Consumer_EVT_Backplane_v1.0_Netlist.csv`
- `BRMC_Consumer_EVT_Backplane_v1.0_Interconnect_Schematic.pdf`
- `connector-production-verification.csv`

## Closure rule

Item 2 becomes CLOSED only after a qualified electrical engineer signs the
review checklist, all review actions are closed, connector first-article
orientation is recorded, and EVT current captures demonstrate compliance with
the ceilings above. This document does not approve absent module schematics.
