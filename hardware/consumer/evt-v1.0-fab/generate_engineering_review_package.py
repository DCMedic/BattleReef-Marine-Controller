#!/usr/bin/env python3
"""Generate the controlled BRMC Consumer EVT independent-review package.

The package freezes the present modular-backplane interface. It deliberately
does not claim that absent daughtercard/power-module schematics or physical
EVT measurements exist. Numerical endpoint allowances are interface design
limits; a module must remain below them to be compatible with this prototype.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
DATE = "2026-09-03"
REV = "C"
STATUS = "ENGINEERING REVIEW RELEASE - NOT FABRICATION AUTHORITY"
rl_config.invariant = 1  # byte-for-byte reproducible PDFs for CI/source-drift checks
COPPER_TEMP_FACTOR = 1.216  # 20 C to 75 C, alpha=0.00393/C
OHM_PER_M_20C = {20: 0.0333, 22: 0.0530, 24: 0.0842, 26: 0.1339}


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    with (ROOT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def drop(awg: int, amps: float, one_way_m: float) -> tuple[float, float]:
    resistance = OHM_PER_M_20C[awg] * COPPER_TEMP_FACTOR * 2 * one_way_m
    return resistance, resistance * amps


CONNECTORS = [
    dict(Ref="J_CM5", Interface="CM5IO J8 signal-only", Board_MPN="Molex 90130-1216", Circuits="2x8 / 16", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="90142-0016 + 90119-2121; CM5IO end 90142-0040 + 90119-2121", Rating="350 V; 3 A/contact; -55..125 C header", Footprint="embedded C-Grid III drawing envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle; circuit 1 at left/lower row in top view", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 901301216/901420016/901192121; CM5IO rev2 J8"),
    dict(Ref="J_MCU", Interface="safety MCU daughtercard", Board_MPN="Molex 90130-1224", Circuits="2x12 / 24", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="90142-0024; 90119-2110 power / 90119-2121 signal", Rating="350 V; 3 A/contact; -55..125 C header", Footprint="embedded C-Grid III drawing envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle; manufacturer column numbering", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 901301224/901420024; pinout CSV"),
    dict(Ref="J_PH", Interface="Atlas EZO pH isolated carrier", Board_MPN="Molex 22-23-2051", Circuits="1x5", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3057 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; PH keyed label", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 22232051; Atlas isolated-carrier data"),
    dict(Ref="J_ORP", Interface="Atlas EZO ORP isolated carrier", Board_MPN="Molex 22-23-2051", Circuits="1x5", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3057 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; ORP keyed label", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 22232051; Atlas isolated-carrier data"),
    dict(Ref="J_EC", Interface="Atlas EZO EC isolated carrier", Board_MPN="Molex 22-23-2051", Circuits="1x5", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3057 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; EC keyed label", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 22232051; Atlas isolated-carrier data"),
    dict(Ref="J_TEMP", Interface="digital temperature endpoint", Board_MPN="Molex 22-23-2041", Circuits="1x4", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3047 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 22-23-2041 family drawing; pinout CSV"),
    dict(Ref="J_PWR", Interface="protected 24/5/12 V source", Board_MPN="Molex 43045-0600", Circuits="2x3 / 6", Pitch_mm="3.00", Orientation="right-angle toward lower edge", Mating="43025-0600 + 43030-0007", Rating="600 V; header 8.5 A/contact; terminal/wire limits apply", Footprint="Molex/KiCad 430450201-SD geometry; 1.02 mm drills; 3.00 mm locator", Pin1="square pad; polarization latch faces board interior", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 430450600/430250600; KiCad Connector_Molex footprint"),
    dict(Ref="J_CAN", Interface="isolated CAN FD daughtercard", Board_MPN="Molex 22-23-2061", Circuits="1x6", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3067 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex KK 254 family; pinout CSV"),
    dict(Ref="J_485", Interface="isolated RS-485 daughtercard", Board_MPN="Molex 22-23-2071", Circuits="1x7", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3077 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex KK 254 family; pinout CSV"),
    dict(Ref="J_AO", Interface="8-channel 0-10 V module", Board_MPN="Molex 43045-0400", Circuits="2x2 / 4", Pitch_mm="3.00", Orientation="right-angle toward lower edge", Mating="43025-0400 + 43030-0007", Rating="600 V; header 8.5 A/contact; terminal/wire limits apply", Footprint="Molex/KiCad 430450201-SD geometry; 1.02 mm drills; 3.00 mm locator", Pin1="square pad; polarization latch faces board interior", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 43045/43025; KiCad Connector_Molex footprint"),
    dict(Ref="J_PWRMOD", Interface="power-module field bus", Board_MPN="Molex 43045-0800", Circuits="2x4 / 8", Pitch_mm="3.00", Orientation="right-angle toward lower edge", Mating="43025-0800 + 43030-0007", Rating="600 V; header 8.5 A/contact; terminal/wire limits apply", Footprint="Molex/KiCad 430450201-SD geometry; 1.02 mm drills; two 3.00 mm locators", Pin1="square pad; polarization latch faces board interior", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex 43045/43025; KiCad Connector_Molex footprint"),
    dict(Ref="J_SAFE", Interface="24 V safety-relay driver", Board_MPN="Molex 22-23-2041", Circuits="1x4", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3047 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex KK 254 family; pinout CSV"),
    dict(Ref="J_SVC", Interface="fixture-only SWD/UART", Board_MPN="Molex 22-23-2081", Circuits="1x8", Pitch_mm="2.54", Orientation="vertical top-entry", Mating="22-01-3087 + 08-50-0032", Rating="500 V; 4 A/contact; -40..80 C", Footprint="embedded KK 254 envelope; 1.00 mm drill / 1.80 mm pad", Pin1="square pad; silk triangle", Status="DESIGN_FROZEN_FOR_REVIEW", Evidence="Molex KK 254 family; pinout CSV"),
]


POWER = [
    dict(Rail="CM5IO 5V", Endpoint="CM5 + CM5IO local loads", Nominal_V=5.0, Expected_A=0.9, Calculated_Worst_A=5.0, Design_Allowance_A=5.0, Basis="Official CM5 input envelope; external carrier", Protection="Official 27 W USB-C PSU and CM5IO input protection", Included_24V_Input="NO", Status="FROZEN_INTERFACE_TEST_CONFIRMATION_REQUIRED"),
    dict(Rail="DISPLAY_5V", Endpoint="Waveshare 10.1inch DSI LCD (C)", Nominal_V=5.0, Expected_A=0.52, Calculated_Worst_A=0.80, Design_Allowance_A=1.00, Basis="Controlled display record plus 25% margin", Protection="PSM-01 dedicated 1.25 A protected branch", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="5V_SYS", Endpoint="J_MCU safety-MCU module", Nominal_V=5.0, Expected_A=0.10, Calculated_Worst_A=0.20, Design_Allowance_A=0.25, Basis="Interface allocation; daughtercard must comply", Protection="PSM-01 5V_SYS 1.25 A branch limit", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="5V_SYS", Endpoint="J_PH isolated pH carrier", Nominal_V=5.0, Expected_A=0.015, Calculated_Worst_A=0.05, Design_Allowance_A=0.10, Basis="Atlas 15 mA nominal; isolation/startup margin", Protection="Module OFF control; shared 5V_SYS branch", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="5V_SYS", Endpoint="J_ORP isolated ORP carrier", Nominal_V=5.0, Expected_A=0.015, Calculated_Worst_A=0.05, Design_Allowance_A=0.10, Basis="Atlas 15 mA nominal; isolation/startup margin", Protection="Module OFF control; shared 5V_SYS branch", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="5V_SYS", Endpoint="J_EC isolated EC carrier", Nominal_V=5.0, Expected_A=0.015, Calculated_Worst_A=0.05, Design_Allowance_A=0.10, Basis="Atlas 15 mA nominal; isolation/startup margin", Protection="Module OFF control; shared 5V_SYS branch", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="5V_SYS", Endpoint="J_CAN isolated CAN FD module", Nominal_V=5.0, Expected_A=0.08, Calculated_Worst_A=0.15, Design_Allowance_A=0.20, Basis="ISO1042 plus isolated-converter interface allocation", Protection="Daughtercard input fuse/current limit required", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="5V_SYS", Endpoint="J_485 isolated RS-485 module", Nominal_V=5.0, Expected_A=0.08, Calculated_Worst_A=0.15, Design_Allowance_A=0.20, Basis="ISO1410 plus isolated-converter interface allocation", Protection="Daughtercard input fuse/current limit required", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="3V3_SYS", Endpoint="J_TEMP + J_SVC reference", Nominal_V=3.3, Expected_A=0.03, Calculated_Worst_A=0.08, Design_Allowance_A=0.10, Basis="Interface allocation; source owned by J_MCU daughtercard", Protection="100 mA current-limited output; no external backfeed", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="12V_SYS", Endpoint="reserved prototype auxiliary", Nominal_V=12.0, Expected_A=0.0, Calculated_Worst_A=0.20, Design_Allowance_A=0.25, Basis="Reserved interface ceiling; no present load", Protection="PSM-01 0.50 A protected branch", Included_24V_Input="YES", Status="RESERVED_NO_LOAD"),
    dict(Rail="24V_IN", Endpoint="J_AO 8-channel 0-10 V module electronics", Nominal_V=24.0, Expected_A=0.12, Calculated_Worst_A=0.20, Design_Allowance_A=0.25, Basis="High-impedance voltage outputs; external loads excluded", Protection="0.35 A daughtercard branch protection required", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="24V_IN", Endpoint="J_PWRMOD external power-module electronics", Nominal_V=24.0, Expected_A=0.25, Calculated_Worst_A=0.40, Design_Allowance_A=0.50, Basis="Prototype module interface ceiling; switched loads use separate supply", Protection="0.75 A branch fuse/eFuse required", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
    dict(Rail="24V_IN", Endpoint="J_SAFE relay-driver electronics", Nominal_V=24.0, Expected_A=0.04, Calculated_Worst_A=0.08, Design_Allowance_A=0.10, Basis="One 24 V relay/contactor-driver allocation", Protection="0.20 A branch protection and flyback on daughtercard", Included_24V_Input="YES", Status="DESIGN_LIMIT_FOR_REVIEW"),
]


def harness_rows() -> list[dict]:
    rows = []

    def add(record, source, dest, connectors, pins, function, voltage, expected,
            worst, allowance, awg, conductors, contact, length, protection,
            routing, status, evidence):
        if awg:
            resistance, voltage_drop = drop(awg, float(allowance), float(length))
            conductor = f"{awg} AWG stranded Cu, UL1007 or equivalent, 105 C"
            vd = f"{voltage_drop:.3f}"
            pct = f"{100*voltage_drop/float(voltage):.2f}" if float(voltage) else "N/A"
        else:
            conductor = "signal cable; see construction"
            resistance = 0
            vd = pct = "N/A"
        rows.append(dict(Record=record, Source=source, Destination=dest,
                         Connector_MPNs=connectors, Pin_or_group=pins,
                         Function=function, Nominal_voltage_V=voltage,
                         Expected_continuous_A=expected,
                         Calculated_worst_case_A=worst,
                         Design_derated_allowance_A=allowance,
                         Proposed_conductor=conductor, Conductors=conductors,
                         Connector_contact_rating_A=contact,
                         Max_one_way_length_m=length,
                         Warm_loop_resistance_ohm=f"{resistance:.4f}" if awg else "N/A",
                         Warm_voltage_drop_V=vd, Voltage_drop_percent=pct,
                         Fuse_eFuse_relationship=protection,
                         Routing_separation=routing, Status=status,
                         Evidence_or_review_dependency=evidence))

    add("HARN-01", "Phoenix Contact M12 panel inlet 1419742", "PSM-01 protected power module", "Panel 1419742; PSM end 43025-0600/43030-0007", "24V/GND", "24 V system input", 24, 1.47, 2.50, 2.50, 20, 2, 7.0, 0.50, "PSM input eFuse target 2.35 A; Mean Well source 2.5 A", "twist pair; separate from raw analog", "FROZEN_FOR_REVIEW", "20 AWG selected from drop and terminal range; 18 AWG optional only for handling margin")
    add("HARN-02A", "PSM-01", "Backplane J_PWR", "43025-0600/43030-0007 to 43045-0600", "1=24V; 2=GND", "protected 24 V rail", 24, 0.41, 0.68, 0.85, 20, 2, 7.0, 0.35, "1.0 A protected branch", "route along lower wall; away from analog", "FROZEN_FOR_REVIEW", "Interface ceiling set by J_AO/J_PWRMOD/J_SAFE allocations")
    add("HARN-02B", "PSM-01", "Backplane J_PWR", "43025-0600/43030-0007 to 43045-0600", "3=5V; 4=GND", "5V_SYS", 5, 0.305, 0.85, 1.00, 22, 2, 7.0, 0.35, "1.25 A protected branch", "route away from pH/ORP probe leads", "FROZEN_FOR_REVIEW", "Endpoint interface allocations total 0.95 A")
    add("HARN-02C", "PSM-01", "Backplane J_PWR", "43025-0600/43030-0007 to 43045-0600", "5=12V; 6=GND", "reserved 12V_SYS", 12, 0.0, 0.20, 0.25, 22, 2, 7.0, 0.35, "0.50 A protected branch", "route with power bundle", "FROZEN_FOR_REVIEW", "Reserved; no present load permitted without ECO")
    add("HARN-03", "CM5IO J17", "Waveshare display DSI", "CM5IO 22-pin FFC to display 15-pin FFC adapter", "MIPI pairs/grounds", "MIPI DSI signal", 0, 0, 0, 0, None, "controlled-impedance 22-to-15 FFC assembly", "signal only", 0.20, "not applicable", "100 ohm differential construction; >=5 mm bend radius; no fold", "PROCUREMENT_SELECTION_FOR_REVIEW", "Exact cable MPN and contact-side orientation require reviewer/procurement confirmation")
    add("HARN-04", "PSM-01 dedicated 5 V output", "Waveshare display power input", "locking 2-pin harness; endpoint housing per display build drawing", "+5V/GND", "display power", 5, 0.52, 0.80, 1.00, 22, 2, 3.0, 0.50, "dedicated 1.25 A current-limited branch", "do not parallel raw pH/ORP or DSI pairs", "FROZEN_WIRE_REQUIREMENT", "Connector at display must be confirmed against purchased display revision")
    add("HARN-CM5-SIG", "Backplane J_CM5", "CM5IO J8", "90142-0016/90119-2121 to 90142-0040/90119-2121", "16 conductors; exact map in schedule", "3.3 V GPIO and four returns; no power", 3.3, 0, 0, 0, None, "16x 26 AWG; active/return organization", "3 A/contact", 0.30, "no 5 V or 3V3 contacts fitted at J8", "separate from 24 V; continuity/short test before mating", "FROZEN_FOR_REVIEW", "First article must verify unshrouded J8 orientation")
    add("HARN-MCU-PWR", "Backplane J_MCU", "Safety MCU daughtercard", "90142-0024; 90119-2110 power / -2121 signal", "1=5V; 2/24=GND; 3=3V3 return source", "MCU module power/3V3 ownership", 5, 0.10, 0.20, 0.25, 22, 4, 3.0, 0.30, "shared 5V_SYS; daughtercard 3V3 output limited 0.10 A", "bundle signals with returns; keep SWD short", "FROZEN_FOR_REVIEW", "Daughtercard schematic is a separate approval object")
    for key, name in (("PH", "pH"), ("ORP", "ORP"), ("EC", "conductivity")):
        add(f"HARN-{key}", f"Backplane J_{key}", f"Atlas isolated {name} carrier", "22-01-3057/08-50-0032 to 22-23-2051", "1=5V;2=GND;3=SCL;4=SDA;5=OFF", f"{name} carrier power/data", 5, 0.015, 0.05, 0.10, 22, 5, 4.0, 0.30, "shared 5V_SYS; OFF provides controlled disable", "separate from 24 V, relay, CAN/485; label both ends", "FROZEN_FOR_REVIEW", "Atlas carrier nominal current; allowance includes isolation/startup margin")
    add("HARN-TEMP", "Backplane J_TEMP", "digital temperature interface", "22-01-3047/08-50-0032 to 22-23-2041", "1=3V3;2=GND;3=DATA;4=AUX", "digital temperature", 3.3, 0.01, 0.03, 0.05, 24, 4, 4.0, 0.50, "3V3 source current-limited on MCU module", "twist DATA with GND for long route; away from relays", "FROZEN_FOR_REVIEW", "Endpoint must meet the 50 mA interface ceiling")
    add("HARN-CAN", "Backplane J_CAN", "isolated CAN daughtercard", "22-01-3067/08-50-0032 to 22-23-2061", "1=5V;2=GND;3=TX;4=RX;5=CAN_H;6=CAN_L", "CAN module power and bus", 5, 0.08, 0.15, 0.20, 22, 6, 4.0, 0.30, "daughtercard input branch protection", "CAN_H/L 120 ohm twisted pair; termination only at bus ends", "FROZEN_FOR_REVIEW", "Daughtercard isolation/ESD schematic is a separate approval object")
    add("HARN-485", "Backplane J_485", "isolated RS-485 daughtercard", "22-01-3077/08-50-0032 to 22-23-2071", "1=5V;2=GND;3=TX;4=RX;5=DE;6=A;7=B", "RS-485 module power and bus", 5, 0.08, 0.15, 0.20, 22, 7, 4.0, 0.30, "daughtercard input branch protection", "A/B 120 ohm twisted pair; controlled bias/termination", "FROZEN_FOR_REVIEW", "Daughtercard isolation/ESD schematic is a separate approval object")
    add("HARN-AO", "Backplane J_AO", "0-10 V daughtercard", "43025-0400/43030-0007 to 43045-0400", "1=24V;2=GND;3=RS485_A;4=RS485_B", "module power and Modbus", 24, 0.12, 0.20, 0.25, 22, 4, 7.0, 0.35, "0.35 A daughtercard branch protection", "A/B twisted; separate 0-10 V outputs from switching harnesses", "FROZEN_FOR_REVIEW", "External analog loads must be >=10 kohm/channel")
    add("HARN-PWRMOD", "Backplane J_PWRMOD", "external power-module electronics", "43025-0800/43030-0007 to 43045-0800", "1=24V;2/8=GND;3/4=CAN;5/6=485;7=SAFE", "module power/bus/safety", 24, 0.25, 0.40, 0.50, 20, 8, 7.0, 0.35, "0.75 A branch fuse/eFuse", "power pair separate within bundle; twisted bus pairs", "FROZEN_FOR_REVIEW", "Switched loads require separate fused supply and are excluded")
    add("HARN-SAFE", "Backplane J_SAFE", "safety relay driver", "22-01-3047/08-50-0032 to 22-23-2041", "1=ENABLE;2/4=GND;3=24V", "safe-state relay driver", 24, 0.04, 0.08, 0.10, 22, 4, 4.0, 0.30, "0.20 A protected branch; flyback at driver", "separate from raw analog; de-energize-to-safe", "FROZEN_FOR_REVIEW", "Relay/driver daughtercard schematic is a separate approval object")
    add("HARN-SVC", "Backplane J_SVC", "service fixture", "22-01-3087/08-50-0032 to 22-23-2081", "3V3/GND/SWD/UART", "fixture-only debug", 3.3, 0.0, 0.03, 0.05, 26, 8, 4.0, 0.20, "3V3 limited to 100 mA at source; no target backfeed", "disconnect during normal operation", "FROZEN_FOR_REVIEW", "Fixture must not source power")
    add("HARN-05", "CM5 RF connector", "enclosure antenna position", "official Raspberry Pi approved CM5 antenna assembly", "50 ohm RF", "Wi-Fi/Bluetooth", 0, 0, 0, 0, None, "50 ohm micro-coax assembly", "signal only", 0.20, "not applicable", "respect antenna keepout; no pinch; manufacturer bend radius", "PROCUREMENT_SELECTION_FOR_REVIEW", "Exact approved antenna SKU and enclosure RF validation remain build-record items")
    return rows


def netlist_rows(pinout: list[dict]) -> list[dict]:
    nets = defaultdict(list)
    for row in pinout:
        nets[row["Net"]].append(f'{row["Connector"]}.{row["Pin"]}')
    domain = {
        "24V_IN": "SELV power", "12V_SYS": "SELV power", "5V_SYS": "SELV power",
        "3V3_SYS": "logic power", "GND": "common reference",
        "CAN_H": "field differential", "CAN_L": "field differential",
        "RS485_A": "field differential", "RS485_B": "field differential",
    }
    rows = []
    for net, endpoints in sorted(nets.items()):
        rows.append(dict(Net=net, Electrical_domain=domain.get(net, "3.3 V logic"),
                         Endpoint_count=len(endpoints), Endpoints=" | ".join(endpoints),
                         Review_note="GND connects through L2/L5 planes" if net == "GND" else "Reconcile to PCB IPC-D-356 and pinout"))
    return rows


def build_markdown(pinout: list[dict], harnesses: list[dict]) -> None:
    cm5 = [r for r in pinout if r["Connector"] == "J_CM5"]
    text = f"""# BRMC Consumer v1.0 CM5 carrier, harness, and load schedule

Document ID: BRMC-ELEC-EVT-020
Revision: {REV}
Date: {DATE}
Status: **{STATUS}**

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
"""
    j8 = {1:6,2:9,3:5,4:3,5:8,6:10,7:11,8:13,9:23,10:21,11:19,12:24,13:15,14:16,15:20,16:25}
    bcm = {3:"GPIO3/SCL1",4:"GPIO2/SDA1",5:"GPIO14/TXD",6:"GPIO15/RXD",7:"GPIO17",8:"GPIO27",9:"GPIO11/SCLK",10:"GPIO9/MISO",11:"GPIO10/MOSI",12:"GPIO8/CE0",13:"GPIO22",14:"GPIO23"}
    for row in cm5:
        p = int(row["Pin"])
        text += f'| {p} | {row["Net"]} | {j8[p]} | {bcm.get(p, "GND")} |\n'
    text += """

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
"""
    (ROOT / "BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.md").write_text(text, encoding="utf-8")


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="CoverTitle", parent=s["Title"], fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=colors.HexColor("#17365D"), alignment=TA_CENTER, spaceAfter=14))
    s.add(ParagraphStyle(name="Status", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.HexColor("#9B1C1C"), alignment=TA_CENTER, spaceAfter=12))
    s.add(ParagraphStyle(name="H1x", parent=s["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=colors.HexColor("#17365D"), spaceBefore=6, spaceAfter=8))
    s.add(ParagraphStyle(name="H2x", parent=s["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=colors.HexColor("#285F8F"), spaceBefore=5, spaceAfter=5))
    s.add(ParagraphStyle(name="Bodyx", parent=s["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11, spaceAfter=5))
    s.add(ParagraphStyle(name="Smallx", parent=s["BodyText"], fontName="Helvetica", fontSize=6.5, leading=8))
    return s


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#AAB7C4")); canvas.line(16*mm, 11*mm, doc.pagesize[0]-16*mm, 11*mm)
    canvas.setFont("Helvetica", 6.5); canvas.setFillColor(colors.HexColor("#4B5563"))
    canvas.drawString(16*mm, 7*mm, f"BRMC Consumer EVT review package | Rev {REV} | {STATUS}")
    canvas.drawRightString(doc.pagesize[0]-16*mm, 7*mm, f"Page {doc.page}")
    canvas.restoreState()


def p(text, style):
    return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def make_table(rows, widths, small, header=True):
    cooked = [[p(cell, small) for cell in row] for row in rows]
    t = Table(cooked, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#AAB7C4")),
        ("LEFTPADDING", (0,0), (-1,-1), 3), ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]
    if header:
        commands += [("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DCE6F1")), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")]
    for i in range(1 if header else 0, len(rows)):
        if i % 2 == 0:
            commands.append(("BACKGROUND", (0,i), (-1,i), colors.HexColor("#F6F8FA")))
    t.setStyle(TableStyle(commands)); return t


def build_interconnect_pdf(pinout: list[dict], nets: list[dict]) -> None:
    target = ROOT / "BRMC_Consumer_EVT_Backplane_v1.0_Interconnect_Schematic.pdf"
    st = styles(); story = []
    story += [Spacer(1, 20*mm), p("BRMC Consumer EVT v1.0", st["CoverTitle"]), p("Controlled passive-backplane interconnect drawing", st["CoverTitle"]), p(STATUS, st["Status"]), Spacer(1, 8*mm), p("Drawing BRMC-ELEC-EVT-021 | Revision C | Units: mm where dimensional | Date: 2026-09-03", st["Bodyx"]), p("This drawing is the schematic-equivalent connectivity record for the board-only passive backplane. It is generated from the same connector table as the KiCad PCB and is reconciled to the exported IPC-D-356 netlist. KiCad ERC is not applicable because there is no component-level schematic in this artifact.", st["Bodyx"]), PageBreak()]
    story += [p("System interface boundary", st["H1x"])]
    blocks = [
        ["OFF-BOARD SOURCE", "INTERFACE", "BACKPLANE", "ENDPOINT MODULES"],
        ["Mean Well 24 V / 2.5 A", "PSM-01 protection + 5/12 V conversion", "J_PWR; passive copper; L2/L5 GND", "MCU, sensors, buses, AO, safety"],
        ["Official 27 W USB-C PSU", "CM5IO rev2 J11", "J_CM5 signal only", "CM5 GPIO at CM5IO J8"],
        ["Display 5 V branch", "HARN-04 + DSI FFC", "No display power through J_CM5", "Waveshare 10.1inch DSI LCD (C)"],
    ]
    story += [make_table(blocks, [60*mm,70*mm,70*mm,75*mm], st["Smallx"]), Spacer(1,5*mm), p("Power ownership: J_PWR is the only source for 24V_IN, 5V_SYS and 12V_SYS. J_MCU is the sole source for the limited 3V3_SYS interface. CM5IO power remains isolated from all backplane rails.", st["Bodyx"]), PageBreak()]
    grouped = defaultdict(list)
    for row in pinout: grouped[row["Connector"]].append(row)
    for group in (["J_CM5","J_MCU"], ["J_PH","J_ORP","J_EC","J_TEMP"], ["J_PWR","J_CAN","J_485"], ["J_AO","J_PWRMOD","J_SAFE","J_SVC"]):
        story.append(p("Connector pin definition", st["H1x"]))
        for ref in group:
            conn = next(c for c in CONNECTORS if c["Ref"] == ref)
            story.append(p(f'{ref} — {conn["Interface"]} — {conn["Board_MPN"]}', st["H2x"]))
            data = [["Pin","Net","Function"]] + [[r["Pin"],r["Net"],r["Function"]] for r in grouped[ref]]
            story.append(KeepTogether(make_table(data, [16*mm,45*mm,115*mm], st["Smallx"])))
            story.append(Spacer(1,3*mm))
        story.append(PageBreak())
    story.append(p("Net reconciliation", st["H1x"]))
    data = [["Net","Domain","Count","Endpoints"]] + [[r["Net"],r["Electrical_domain"],r["Endpoint_count"],r["Endpoints"]] for r in nets]
    story.append(make_table(data, [35*mm,35*mm,15*mm,190*mm], st["Smallx"]))
    doc = SimpleDocTemplate(str(target), pagesize=landscape(A3), leftMargin=15*mm, rightMargin=15*mm, topMargin=14*mm, bottomMargin=15*mm, title="BRMC Consumer EVT Backplane Interconnect Schematic", author="BattleReef")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_review_pdf(pinout: list[dict], harnesses: list[dict], nets: list[dict]) -> None:
    target = ROOT / "BRMC_Consumer_v1.0_Electrical_Engineering_Review_Package.pdf"
    st = styles(); story = []
    story += [Spacer(1, 22*mm), p("BattleReef BRMC Consumer v1.0", st["CoverTitle"]), p("Prototype electrical engineering review package", st["CoverTitle"]), p(STATUS, st["Status"]), Spacer(1, 10*mm), p("Document BRMC-ELEC-EVT-030 | Revision C | 2026-09-03", st["Bodyx"]), p("Review object: 220 x 78 mm, six-layer modular passive backplane; official CM5 IO Board rev2 prototype endpoint; controlled harness and enclosure-base interface evidence.", st["Bodyx"]), Spacer(1, 10*mm), p("Release statement", st["H2x"]), p("This package is complete for independent engineering review of the stated backplane scope. It is not a fabrication authorization and does not approve absent daughtercard or PSM-01 schematics. Fabricator DFM, first-article checks, measured EVT evidence, and signed qualified review remain mandatory gates.", st["Bodyx"]), PageBreak()]
    story += [p("1. Configuration and evidence", st["H1x"]), p("The deterministic PCB generator, generated KiCad board, rules, pinout, connector schedule, interconnect drawing, power budget, mechanical base candidate, and fail-closed validator are the controlled source. Accept manufacturing outputs only from a successful KiCad 9 CI run for the exact reviewed commit. The prior exact-source baseline passed KiCad 9.0.9 with zero DRC violations, zero unconnected pads and zero footprint errors; the production-connector ECO in this package requires a new successful run before review disposition.", st["Bodyx"])]
    evidence = [["Evidence","Purpose"], ["BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb","reviewed PCB source"], ["BRMC_Consumer_EVT_Backplane_v1.0.kicad_dru","controlled rules"], ["BRMC_Consumer_EVT_Backplane_v1.0_Interconnect_Schematic.pdf","schematic-equivalent connectivity"], ["BRMC_Consumer_EVT_Backplane_v1.0_Netlist.csv","machine-readable net/endpoints"], ["BRMC_Consumer_v1.0_Power_Budget.csv","load ceilings and margins"], ["BRMC_Consumer_v1.0_Connector_and_Harness_Schedule.csv","wire/contact/drop/protection schedule"], ["BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE.step","base CAD candidate"], ["..._Drawing.pdf / dimensions.csv / interference.csv","boss dimensions and nominal CAD evidence"], ["independent-review-checklist.csv","review return record"]]
    story += [make_table(evidence,[92*mm,175*mm],st["Smallx"]), PageBreak()]
    story += [p("2. Architecture decisions", st["H1x"]), p("EVT uses the official Raspberry Pi CM5 IO Board revision 2 outside the enclosure, independently powered at J11 by an official 27 W USB-C supply. J_CM5 carries GPIO and four returns only. A custom integrated carrier is deferred to a new revision. The current KiCad board is a passive modular backplane; it does not contain the integrated v0.9 power, safety, bus, analog or rear-I/O circuitry. Those circuits remain separate module approval objects.", st["Bodyx"])]
    arch = [["Boundary","Controlled decision","Reviewer focus"], ["CM5","external CM5IO rev2; independent 5 V / 5 A envelope","GPIO voltage, boot strapping, no rail backfeed"], ["Power","24 V / 2.5 A source; PSM-01 converts/protects; interface ceilings below","fault coordination and missing PSM schematic"], ["Backplane","passive connectors/tracks/planes only","pin map, copper/vias, returns, connector footprints"], ["Enclosure","CNC 6061 base Rev B candidate with six M3 bosses","clearance/tolerance evidence and approval boundary"]]
    story += [make_table(arch,[38*mm,115*mm,114*mm],st["Smallx"]), PageBreak()]
    story += [p("3. Worst-case power budget", st["H1x"]), p("Values labeled design allowance are mandatory interface ceilings. They are conservative allocations, not fabricated measurements. The 24 V source calculation uses 88% conversion efficiency for 5 V and 12 V branches and a 25% startup/transient multiplier.", st["Bodyx"])]
    pdata = [["Rail","Endpoint","V","Expected A","Worst A","Allowance A","Protection/status"]] + [[r["Rail"],r["Endpoint"],r["Nominal_V"],r["Expected_A"],r["Calculated_Worst_A"],r["Design_Allowance_A"],r["Protection"]] for r in POWER]
    story += [make_table(pdata,[24*mm,74*mm,13*mm,22*mm,20*mm,23*mm,91*mm],st["Smallx"]), Spacer(1,5*mm), p("Calculated 24 V envelope: direct 24 V loads 0.85 A + (5 V backplane 1.00 A / 88%)×5/24 + (display 1.00 A / 88%)×5/24 + (12 V 0.25 A / 88%)×12/24 = 1.47 A continuous. With 25% margin: 1.83 A. Adapter headroom: 0.67 A to the 2.5 A ceiling.", st["Bodyx"]), PageBreak()]
    story += [p("4. Harness schedule", st["H1x"])]
    hdata = [["ID","Source → destination","Function","V / allowance","Conductor / max length","Drop","Protection","Status"]]
    for r in harnesses:
        hdata.append([r["Record"],f'{r["Source"]} → {r["Destination"]}',r["Function"],f'{r["Nominal_voltage_V"]} V / {r["Design_derated_allowance_A"]} A',f'{r["Proposed_conductor"]}; {r["Max_one_way_length_m"]} m',f'{r["Warm_voltage_drop_V"]} V ({r["Voltage_drop_percent"]}%)',r["Fuse_eFuse_relationship"],r["Status"]])
    story += [make_table(hdata,[20*mm,58*mm,35*mm,27*mm,56*mm,25*mm,60*mm,45*mm],st["Smallx"]), PageBreak()]
    story += [p("5. Production connector implementation", st["H1x"])]
    cdata = [["Ref","Board MPN","Circuit / pitch","Orientation","Mate/contact","Rating","Status"]] + [[c["Ref"],c["Board_MPN"],f'{c["Circuits"]}; {c["Pitch_mm"]} mm',c["Orientation"],c["Mating"],c["Rating"],c["Status"]] for c in CONNECTORS]
    story += [make_table(cdata,[18*mm,37*mm,33*mm,43*mm,91*mm,53*mm,47*mm],st["Smallx"]), Spacer(1,4*mm), p("Footprint ECO: J_PWR/J_AO/J_PWRMOD now use the correct 3.00 mm dual-row Micro-Fit pattern with manufacturer locator holes. Signal connectors use controlled C-Grid III or KK 254 geometry. The independent reviewer must compare pad/drill/body/courtyard/pin-1 details with the listed manufacturer drawings and verify first-article mating orientation.", st["Bodyx"]), PageBreak()]
    story += [p("6. Layout and signal-integrity review points", st["H1x"])]
    checks = [["Topic","Controlled design / required review"], ["Ground","L2 and L5 continuous GND zones; every GND PTH connects directly; verify antipads and return continuity in filled Gerbers."], ["Fan-out","Top/bottom connector classes use separated copper layers; through-via slots are clearance checked by the deterministic router."], ["Power copper","24 V B.Cu trunk 1.50 mm; 5 V B.Cu trunk 2.00 mm with 0.80 mm fan-outs and 0.40 mm drills; review against allowed currents and fabricator copper."], ["Field buses","This board is a low-speed interconnect, not a controlled-impedance CAN/RS-485 trunk. Enforce short internal stubs and twisted external pairs."], ["I2C","Multiple module stubs require one pull-up owner and measured bus capacitance/rise time at assembled length."], ["Safety","SAFETY_ENABLE is an interface signal only; independent hardware de-energize-to-safe behavior belongs on reviewed MCU/safety daughtercard."], ["ERC","Not applicable to the board-only passive artifact; connectivity is controlled by the generated interconnect drawing/netlist and IPC-D-356 reconciliation."]]
    story += [make_table(checks,[42*mm,225*mm],st["Smallx"]), PageBreak()]
    story += [p("7. Mechanical evidence and limits", st["H1x"]), p("The enclosure base is CNC-machined 6061-T6 with six integral OD 10.00 ±0.10 mm bosses, support plane Z=8.00 ±0.05 mm, M3x0.5-6H blind threads and the controlled H1-H6 axes. The hash-controlled v0.8 assembly nominal check reports zero positive-volume intersections across 114 boss-to-nonbase-solid comparisons. The supplied assembly lacks populated daughtercard, harness, thermal and service-tool solids; therefore the independent mechanical approval and tolerance-aware first-article fit check remain required.", st["Bodyx"])]
    mech = [["Hole","PCB-centered X,Y mm","Enclosure X,Y mm","PCB hole","Boss/thread"], ["H1","-103,-32","-103,25.5","3.20 NPTH","OD10; M3x0.5"], ["H2","0,-32","0,25.5","3.20 NPTH","OD10; M3x0.5"], ["H3","+103,-32","+103,25.5","3.20 NPTH","OD10; M3x0.5"], ["H4","-103,+32","-103,89.5","3.20 NPTH","OD10; M3x0.5"], ["H5","0,+32","0,89.5","3.20 NPTH","OD10; M3x0.5"], ["H6","+103,+32","+103,89.5","3.20 NPTH","OD10; M3x0.5"]]
    story += [make_table(mech,[22*mm,55*mm,55*mm,35*mm,55*mm],st["Smallx"]), PageBreak()]
    story += [p("8. Review action register", st["H1x"])]
    actions = [
        ["ID","Owner","Required evidence","Blocks"],
        ["EE-01","Qualified electrical/layout engineer","signed checklist; approved or approved-with-closed-actions","backplane fabrication release"],
        ["EE-02","Electrical engineer","PSM-01 and every daughtercard schematic/BOM/layout reviewed as separate objects","complete product release"],
        ["ME-01","Mechanical engineer","signed base drawing/CAD and tolerance-aware populated fit review","Item 1 closure"],
        ["FAB-01","PCB fabricator","returned stackup and DFM report tied to exact commit/artifact","fabrication release"],
        ["FA-01","Build owner + reviewer","connector keying/pin-1/mating access and unshrouded CM5IO J8 first-article record","Item 2/connector closure"],
        ["EVT-01","Test engineer","startup, steady, peak and fault-current captures; rail droop; fuse/eFuse trip evidence","Item 2/system validation"],
        ["EVT-02","Test engineer","thermal, EMC/ESD and ingress evidence under controlled configurations","product qualification"],
    ]
    story += [make_table(actions,[20*mm,48*mm,150*mm,49*mm],st["Smallx"]), PageBreak()]
    story += [p("9. Independent review disposition", st["H1x"]), p("Reviewer name / organization: ______________________________________________", st["Bodyx"]), p("Qualifications and relevant experience: __________________________________________", st["Bodyx"]), Spacer(1,4*mm), p("Reviewed git commit: ______________________________  CI run/artifact: ______________________________", st["Bodyx"]), Spacer(1,4*mm), p("Disposition (select one):  APPROVED FOR BACKPLANE EVT FABRICATION  /  APPROVED WITH CLOSED ACTIONS  /  REJECTED", st["Bodyx"]), Spacer(1,8*mm), p("Open findings or attached report reference: __________________________________________________________", st["Bodyx"]), Spacer(1,12*mm), p("Signature: ______________________________________    Date: __________________", st["Bodyx"]), Spacer(1,8*mm), p("Approval applies only to the passive-backplane scope and exact reviewed configuration. It does not approve absent daughtercard/power-module designs or commercial production.", st["Status"])]
    doc = SimpleDocTemplate(str(target), pagesize=landscape(A4), leftMargin=14*mm, rightMargin=14*mm, topMargin=13*mm, bottomMargin=15*mm, title="BRMC Consumer v1.0 Electrical Engineering Review Package", author="BattleReef")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def build_index() -> None:
    files = [
        "BRMC_Consumer_v1.0_Electrical_Engineering_Review_Package.pdf",
        "BRMC_Consumer_EVT_Backplane_v1.0_Interconnect_Schematic.pdf",
        "BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb",
        "BRMC_Consumer_EVT_Backplane_v1.0.kicad_pro",
        "BRMC_Consumer_EVT_Backplane_v1.0.kicad_dru",
        "generate_brmc_evt.py",
        "generate_engineering_review_package.py",
        "validate_brmc_evt.py",
        "BRMC_Consumer_EVT_Backplane_v1.0_Pinout.csv",
        "BRMC_Consumer_EVT_Backplane_v1.0_Netlist.csv",
        "BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.md",
        "BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.csv",
        "BRMC_Consumer_v1.0_Power_Budget.csv",
        "BRMC_Consumer_v1.0_Connector_and_Harness_Schedule.csv",
        "connector-production-verification.csv",
        "independent-review-checklist.csv",
        "BRMC_Consumer_v1.0_Enclosure_Base_Mounting_Verification.md",
        "BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE.step",
        "BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_Drawing.pdf",
        "BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_dimensions.csv",
        "BRMC_Consumer_v1.0_Enclosure_Base_6Boss_CNC6061_RELEASE_CANDIDATE_interference.csv",
        "release-status.json", "release-gate-evidence.json", "EXTERNAL_GATE_HANDOFF.md",
    ]
    lines = ["# BRMC Consumer v1.0 independent engineering review index", "", f"Revision: {REV}", f"Date: {DATE}", f"Status: **{STATUS}**", "", "This set is complete for review of the modular passive backplane scope. It is not a complete integrated-product design package because PSM-01 and daughtercard implementation schematics/layouts do not exist in the controlled repository.", "", "## Review order", "", "1. Read the electrical engineering review package PDF.", "2. Review the interconnect schematic, pinout and netlist together.", "3. Review the KiCad PCB/rules and the exact successful CI manufacturing artifact.", "4. Review power/connector/harness schedules and mechanical base evidence.", "5. Record findings in the checklist and sign the disposition page only after actions close.", "", "## Controlled files", ""]
    for name in files: lines.append(f"- `{name}`")
    lines += ["", "## Configuration control", "", "Use the `SHA256SUMS` manifest in the successful CI manufacturing artifact for byte-level configuration hashes. The source index intentionally does not pre-compute hashes because text checkout normalization and the PDF runtime can vary by platform."]
    (ROOT / "BRMC_Consumer_v1.0_Engineer_Review_Index.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def main() -> None:
    with (ROOT / "BRMC_Consumer_EVT_Backplane_v1.0_Pinout.csv").open(newline="", encoding="utf-8") as handle:
        pinout = list(csv.DictReader(handle))
    harnesses = harness_rows()
    nets = netlist_rows(pinout)
    write_csv("BRMC_Consumer_v1.0_Power_Budget.csv", list(POWER[0]), POWER)
    write_csv("BRMC_Consumer_v1.0_Connector_and_Harness_Schedule.csv", list(harnesses[0]), harnesses)
    write_csv("BRMC_Consumer_EVT_Backplane_v1.0_Netlist.csv", list(nets[0]), nets)
    write_csv("BRMC_Consumer_v1.0_CM5_Carrier_Harness_and_Load_Schedule.csv", list(harnesses[0]), harnesses)
    write_csv("connector-production-verification.csv", list(CONNECTORS[0]), CONNECTORS)
    build_markdown(pinout, harnesses)
    build_interconnect_pdf(pinout, nets)
    build_review_pdf(pinout, harnesses, nets)
    build_index()


if __name__ == "__main__":
    main()
