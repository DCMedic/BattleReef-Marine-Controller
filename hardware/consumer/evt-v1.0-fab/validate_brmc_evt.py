#!/usr/bin/env python3
"""Fail closed on BRMC Consumer EVT source and fabrication-package drift."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STEM = "BRMC_Consumer_EVT_Backplane_v1.0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required file: {path}")
    require(path.stat().st_size > 0, f"empty required file: {path}")
    return path.read_text(encoding="utf-8", errors="strict")


def validate_source() -> None:
    pcb_path = ROOT / f"{STEM}.kicad_pcb"
    pcb = read(pcb_path)
    read(ROOT / f"{STEM}.kicad_pro")
    rules = read(ROOT / f"{STEM}.kicad_dru")

    required_layers = {"F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"}
    declared_layers = set(re.findall(r'^\s*\(\d+ "([^"]+\.Cu)"', pcb, re.MULTILINE))
    require(declared_layers == required_layers, f"unexpected copper layers: {sorted(declared_layers)}")
    require('(gr_rect (start 0 0) (end 220 78)' in pcb, "board outline is not 220 x 78 mm")
    require("MODULAR PROTOTYPE BACKPLANE - NOT FOR SALE" in pcb, "mandatory EVT marking missing")
    require(pcb.count("np_thru_hole circle") == 6, "expected six M3 mounting holes")
    require(pcb.count("(size 3.200 3.200) (drill 3.200)") == 6, "unexpected mounting-hole diameter")

    nets = {int(code): name for code, name in re.findall(r'^\s*\(net (\d+) "([^"]*)"\)', pcb, re.MULTILINE)}
    segment_pattern = re.compile(
        r'^\s*\(segment \(start [^)]+\) \(end [^)]+\) \(width ([0-9.]+)\) '
        r'\(layer "([^"]+)"\) \(net (\d+)\)',
        re.MULTILINE,
    )
    segments = [(float(width), layer, nets[int(code)]) for width, layer, code in segment_pattern.findall(pcb)]
    require(segments, "no routed segments found")
    require(not any(layer in {"In1.Cu", "In4.Cu"} for _, layer, _ in segments),
            "tracks found on reserved L2/L5 ground-reference layers")

    gnd_code = next((code for code, name in nets.items() if name == "GND"), None)
    require(gnd_code is not None, "GND net is missing")
    for layer in ("In1.Cu", "In4.Cu"):
        marker = f'(zone (net {gnd_code}) (net_name "GND") (layer "{layer}")'
        require(pcb.count(marker) == 1, f"expected one GND zone on {layer}")
    require(pcb.count('(fill yes (thermal_gap 0.30) (thermal_bridge_width 0.40))') == 2,
            "L2/L5 GND zones are not configured for fill")
    require(pcb.count('(xy 0.5 0.5) (xy 219.5 0.5) (xy 219.5 77.5) (xy 0.5 77.5)') == 2,
            "L2/L5 GND-zone boundaries do not cover the board")

    for width, layer, net in segments:
        minimum = 0.20
        if net in {"CAN_H", "CAN_L", "CAN_TX", "CAN_RX", "RS485_A", "RS485_B", "RS485_TX", "RS485_RX", "RS485_DE"}:
            minimum = 0.25
        if net == "3V3_SYS" and layer == "B.Cu":
            minimum = 0.50
        if net == "24V_IN":
            minimum = 1.50 if layer == "B.Cu" else 0.20
        if net in {"5V_SYS", "GND"}:
            minimum = 2.00 if layer == "B.Cu" else 0.20
        require(width + 1e-9 >= minimum, f"{net} width {width} mm below {minimum} mm on {layer}")

    require("No tracks on L2 ground reference" in rules, "L2 routing prohibition missing")
    require("No tracks on L5 ground reference" in rules, "L5 routing prohibition missing")

    with (ROOT / f"{STEM}_Pinout.csv").open(newline="", encoding="utf-8") as handle:
        pinout = list(csv.DictReader(handle))
    require(len(pinout) == 102, f"expected 102 connector pins, found {len(pinout)}")
    connector_refs = {row["Connector"] for row in pinout}
    require(len(connector_refs) == 13, f"expected 13 connector references, found {len(connector_refs)}")
    pcb_refs = set(re.findall(r'\(property "Reference" "([JH][^"]+)"', pcb))
    require(connector_refs <= pcb_refs, "pinout connector missing from PCB source")


def validate_checksums(fab: Path) -> None:
    manifest = fab / "SHA256SUMS"
    lines = read(manifest).splitlines()
    listed: set[str] = set()
    for line in lines:
        digest, relative = line.split("  ", 1)
        relative = relative.removeprefix("./")
        target = fab / relative
        require(target.is_file(), f"checksum target missing: {relative}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        require(actual == digest, f"checksum mismatch: {relative}")
        listed.add(relative)
    expected = {str(path.relative_to(fab)) for path in fab.rglob("*") if path.is_file() and path.name != "SHA256SUMS"}
    require(listed == expected, f"checksum manifest drift: missing={sorted(expected-listed)}, extra={sorted(listed-expected)}")


def validate_fabrication(fab: Path) -> None:
    required = [
        f"{STEM}.kicad_pcb",
        f"{STEM}.kicad_pro",
        f"{STEM}.kicad_dru",
        f"{STEM}_Pinout.csv",
        f"{STEM}_positions.csv",
        f"{STEM}_DRC.rpt",
        f"{STEM}.ipc",
        f"{STEM}.step",
        "release-status.json",
        "README.md",
        f"drill/{STEM}-PTH.drl",
        f"drill/{STEM}-NPTH.drl",
        f"gerbers/{STEM}-job.gbrjob",
    ]
    for relative in required:
        read(fab / relative)

    drc = read(fab / f"{STEM}_DRC.rpt")
    require("Found 0 DRC violations" in drc, "DRC violations are not zero")
    require("Found 0 unconnected pads" in drc, "unconnected pads are not zero")
    require("Found 0 Footprint errors" in drc, "footprint errors are not zero")

    job = json.loads(read(fab / "gerbers" / f"{STEM}-job.gbrjob"))
    specs = job["GeneralSpecs"]
    require(specs["LayerNumber"] == 6, "Gerber job is not six-layer")
    require(abs(float(specs["BoardThickness"]) - 1.6) < 1e-9, "board thickness is not 1.6 mm")
    copper = [entry for entry in job["FilesAttributes"] if entry["FileFunction"].startswith("Copper,")]
    require(len(copper) == 6, f"expected six copper Gerbers, found {len(copper)}")
    for entry in job["FilesAttributes"]:
        read(fab / "gerbers" / entry["Path"])

    for filename in (f"{STEM}-In1_Cu.g1", f"{STEM}-In4_Cu.g4"):
        plane = read(fab / "gerbers" / filename)
        require("G36*" in plane and "%TO.N,GND*%" in plane,
                f"continuous GND plane geometry missing from {filename}")

    pth = read(fab / "drill" / f"{STEM}-PTH.drl")
    npth = read(fab / "drill" / f"{STEM}-NPTH.drl")
    require(len(re.findall(r'^X[-0-9.]+' , pth, re.MULTILINE)) >= 102, "PTH drill hit count is unexpectedly low")
    require(len(re.findall(r'^X[-0-9.]+' , npth, re.MULTILINE)) == 6, "expected six NPTH mounting-hole hits")
    require("C3.200" in npth, "3.2 mm M3 drill tool missing")

    with (fab / f"{STEM}_positions.csv").open(newline="", encoding="utf-8") as handle:
        positions = list(csv.DictReader(handle))
    required_connectors = {"J_CM5", "J_MCU", "J_PH", "J_ORP", "J_EC", "J_TEMP", "J_PWR", "J_CAN", "J_485", "J_AO", "J_PWRMOD", "J_SAFE", "J_SVC"}
    require(required_connectors <= {row["Ref"] for row in positions}, "connector missing from position output")

    ipc = read(fab / f"{STEM}.ipc")
    for net in ("24V_IN", "5V_SYS", "3V3_SYS", "GND", "CAN_H", "CAN_L", "RS485_A", "RS485_B"):
        require(net in ipc, f"critical net missing from IPC-D-356 output: {net}")
    require((fab / f"{STEM}.step").stat().st_size > 1_000_000, "STEP model is unexpectedly small")
    status = json.loads(read(fab / "release-status.json"))
    require(status["commercial_production_authorized"] is False, "EVT package must not authorize commercial production")
    validate_checksums(fab)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fab", type=Path, help="validate an exported fabrication directory")
    args = parser.parse_args()
    try:
        validate_source()
        if args.fab:
            validate_fabrication(args.fab.resolve())
    except (AssertionError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"BRMC EVT validation FAILED: {exc}", file=sys.stderr)
        return 1
    print("BRMC EVT validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
