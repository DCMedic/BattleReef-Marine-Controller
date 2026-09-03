#!/usr/bin/env python3
"""Generate the approval-ready CNC 6061 enclosure-base release candidate.

The controlled v0.8 exact-display assembly is hash checked before use. Only
its base solid is modified. The STEP models the M3 tap drill; the drawing is
the authority for the thread definition. The output remains a release
candidate until the explicitly listed engineering approvals are recorded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import cadquery as cq
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


SOURCE_SHA256 = "1e1f78229c2624be0a0ecc7766795e55c19090104cca487c9a2ebd9da287a810"
HOLES = [
    ("H1", -103.0, 25.5, -103.0, -32.0),
    ("H2", 0.0, 25.5, 0.0, -32.0),
    ("H3", 103.0, 25.5, 103.0, -32.0),
    ("H4", -103.0, 89.5, -103.0, 32.0),
    ("H5", 0.0, 89.5, 0.0, 32.0),
    ("H6", 103.0, 89.5, 103.0, 32.0),
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_controlled_assembly(source: Path) -> list[cq.Shape]:
    require(hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256,
            "source assembly hash does not match controlled v0.8 input")
    solids = cq.importers.importStep(str(source)).solids().vals()
    require(len(solids) == 20, f"expected 20 assembly solids, found {len(solids)}")
    bb = solids[0].BoundingBox()
    require(all(abs(a - b) < 1e-3 for a, b in zip(
        (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax),
        (-142.5, 142.5, 0.0, 115.0, 0.0, 34.0))),
        "base geometry does not match controlled v0.8 envelope")
    return solids


def make_boss(x: float, y: float) -> cq.Shape:
    return cq.Solid.makeCylinder(5.0, 5.0, cq.Vector(x, y, 3.0))


def generate_step(solids: list[cq.Shape], target: Path) -> cq.Shape:
    candidate = solids[0]
    for _, x, y, _, _ in HOLES:
        candidate = candidate.fuse(make_boss(x, y))
    for _, x, y, _, _ in HOLES:
        # Drawing controls M3 x 0.5-6H. STEP represents the 2.50 mm tap drill.
        pilot = cq.Solid.makeCylinder(1.25, 5.30, cq.Vector(x, y, 2.70))
        candidate = candidate.cut(pilot)
    target.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(candidate, str(target))
    return candidate


def generate_dimensions(target: Path) -> None:
    fields = [
        "Reference", "Enclosure_X_mm", "Enclosure_Y_mm", "PCB_center_X_mm",
        "PCB_center_Y_mm", "Boss_OD_mm", "Boss_height_mm", "Support_Z_mm",
        "Thread", "Full_thread_depth_min_mm", "Tap_drill_diameter_mm",
        "Tap_drill_depth_mm", "PCB_hole_mm", "Axis_position_tolerance_mm",
        "Status",
    ]
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for ref, x, y, px, py in HOLES:
            writer.writerow({
                "Reference": ref, "Enclosure_X_mm": f"{x:.2f}",
                "Enclosure_Y_mm": f"{y:.2f}", "PCB_center_X_mm": f"{px:.2f}",
                "PCB_center_Y_mm": f"{py:.2f}", "Boss_OD_mm": "10.00 +/-0.10",
                "Boss_height_mm": "5.00 +/-0.05", "Support_Z_mm": "8.00 +/-0.05",
                "Thread": "M3x0.5-6H", "Full_thread_depth_min_mm": "4.30",
                "Tap_drill_diameter_mm": "2.50 +0.10/-0.00",
                "Tap_drill_depth_mm": "5.30 +/-0.20", "PCB_hole_mm": "3.20 NPTH",
                "Axis_position_tolerance_mm": "diameter 0.20 to A|B|C",
                "Status": "RELEASE_CANDIDATE_AWAITING_APPROVAL",
            })


def generate_interference_report(solids: list[cq.Shape], target: Path) -> None:
    fields = ["Reference", "Assembly_solid_index", "Intersection_volume_mm3",
              "Nominal_minimum_distance_mm", "Result", "Scope_note"]
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for ref, x, y, _, _ in HOLES:
            boss = make_boss(x, y)
            for index, solid in enumerate(solids[1:], start=2):
                common = boss.intersect(solid)
                volume = common.Volume()
                distance = boss.distance(solid)
                writer.writerow({
                    "Reference": ref,
                    "Assembly_solid_index": index,
                    "Intersection_volume_mm3": f"{volume:.6f}",
                    "Nominal_minimum_distance_mm": f"{distance:.6f}",
                    "Result": "PASS" if volume <= 1e-6 else "INTERFERENCE",
                    "Scope_note": "v0.8 supplied solids only; populated PCB/harness/thermal/service envelopes absent",
                })


def line(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float) -> None:
    c.line(x1, y1, x2, y2)


def fit_text(c: canvas.Canvas, value: str, x: float, y: float, max_width: float,
             size: float = 8.0, font: str = "Helvetica") -> None:
    while size > 5 and stringWidth(value, font, size) > max_width:
        size -= 0.25
    c.setFont(font, size)
    c.drawString(x, y, value)


def generate_pdf(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A3)
    c = canvas.Canvas(str(target), pagesize=(width, height), pageCompression=1)
    c.setTitle("BRMC Consumer v1.0 CNC 6061 Enclosure Base Release Candidate")

    margin = 28
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)
    c.setFillColor(colors.HexColor("#9b1c1c"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 46,
                        "RELEASE CANDIDATE - ENGINEERING APPROVAL REQUIRED - NOT FABRICATION AUTHORITY")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(48, height - 72, "BRMC Consumer v1.0 CNC 6061 enclosure base - six threaded bosses")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 48, height - 71, "UNITS: mm | SCALE: noted | DO NOT SCALE")

    scale = 1.75
    ox, oy = 75, 355
    bw, bh = 285 * scale, 115 * scale
    c.setLineWidth(1.2)
    c.rect(ox, oy, bw, bh)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ox, oy + bh + 12, "TOP VIEW - 1.75 pt/mm")
    c.setDash(4, 3)
    line(c, ox + bw / 2, oy - 12, ox + bw / 2, oy + bh + 12)
    line(c, ox - 12, oy + 57.5 * scale, ox + bw + 12, oy + 57.5 * scale)
    c.setDash()
    c.setFont("Helvetica", 7)
    c.drawString(ox + bw / 2 + 4, oy + bh + 3, "DATUM B: X=0")
    c.drawString(ox + bw + 4, oy + 57.5 * scale + 3, "DATUM C: Y=57.5")

    for ref, x, y, _, _ in HOLES:
        px, py = ox + (x + 142.5) * scale, oy + y * scale
        c.setStrokeColor(colors.HexColor("#285f8f")); c.circle(px, py, 5 * scale)
        c.setStrokeColor(colors.black); c.circle(px, py, 1.25 * scale)
        line(c, px - 10, py, px + 10, py); line(c, px, py - 10, px, py + 10)
        c.setFont("Helvetica-Bold", 7); c.drawCentredString(px, py + 12, ref)
        c.setFont("Helvetica", 6.5); c.drawCentredString(px, py - 17, f"({x:g}, {y:g})")

    pcbx, pcby = ox + 32.5 * scale, oy + 18.5 * scale
    c.setStrokeColor(colors.HexColor("#4b7f52")); c.setDash(5, 2)
    c.rect(pcbx, pcby, 220 * scale, 78 * scale)
    c.setDash(); c.setStrokeColor(colors.black)
    c.setFont("Helvetica", 7)
    c.drawCentredString(pcbx + 110 * scale, pcby + 39 * scale + 18,
                        "220 x 78 PCB envelope; centre (X0, Y57.5)")

    dy = oy - 30
    line(c, ox, dy, ox + bw, dy); line(c, ox, dy - 5, ox, dy + 5); line(c, ox + bw, dy - 5, ox + bw, dy + 5)
    c.drawCentredString(ox + bw / 2, dy + 4, "285 enclosure envelope")
    dx = ox + bw + 30
    line(c, dx, oy, dx, oy + bh); line(c, dx - 5, oy, dx + 5, oy); line(c, dx - 5, oy + bh, dx + 5, oy + bh)
    c.saveState(); c.translate(dx + 8, oy + bh / 2); c.rotate(90); c.drawCentredString(0, 0, "115 enclosure envelope"); c.restoreState()

    sx, sy = 650, 454
    c.setFont("Helvetica-Bold", 9); c.drawString(sx, sy + 105, "SECTION A-A - THREADED BOSS")
    c.setFillColor(colors.HexColor("#d7e2ee")); c.rect(sx, sy, 205, 18, fill=1, stroke=1)
    c.rect(sx + 66, sy + 18, 64, 50, fill=1, stroke=1)
    c.setFillColor(colors.white); c.rect(sx + 88, sy + 21, 20, 47, fill=1, stroke=1)
    c.setFillColor(colors.black); c.setFont("Helvetica", 7)
    details = [
        "A = exterior bottom, Z0", "Inner floor top Z3.00 nominal",
        "Boss OD 10.00 +/-0.10", "Height 5.00 +/-0.05",
        "Support plane Z8.00 +/-0.05 to A", "M3 x 0.5-6H blind",
        "Full thread depth 4.30 MIN", "Tap drill dia 2.50 +0.10/-0.00",
        "Tap drill depth 5.30 +/-0.20", "Residual exterior floor 2.70 nominal",
    ]
    for i, item in enumerate(details): c.drawString(sx + 215, sy + 92 - i * 11, item)

    tx, ty = 54, 250
    c.setFont("Helvetica-Bold", 9); c.drawString(tx, ty + 17, "BOSS / HOLE SCHEDULE - ENCLOSURE DATUM COORDINATES")
    cols = [tx, tx + 43, tx + 98, tx + 153, tx + 213, tx + 283, tx + 353, tx + 470, tx + 575, tx + 690]
    headers = ["REF", "X", "Y", "TOP Z", "BOSS OD", "HEIGHT", "THREAD", "FULL THREAD", "PCB HOLE"]
    rowh = 17
    for i, header in enumerate(headers):
        c.setFont("Helvetica-Bold", 6.8); c.drawString(cols[i] + 3, ty + 2, header)
    for x in cols: line(c, x, ty - 6 * rowh, x, ty + rowh)
    for r in range(8): line(c, cols[0], ty + rowh - r * rowh, cols[-1], ty + rowh - r * rowh)
    for r, (ref, x, y, _, _) in enumerate(HOLES, 1):
        values = [ref, f"{x:g}", f"{y:g}", "8.00 +/-0.05", "10.00 +/-0.10", "5.00 +/-0.05",
                  "M3x0.5-6H", "4.30 MIN", "dia 3.20 NPTH"]
        for i, value in enumerate(values):
            fit_text(c, value, cols[i] + 3, ty - r * rowh + 2, cols[i + 1] - cols[i] - 6, 6.8)

    notes_y = 117
    notes = [
        "1. MATERIAL: 6061-T6 aluminum to ASTM B209/B221. PROCESS: CNC mill from billet/plate; integral bosses; no inserts.",
        "2. FINISH: Type II Class 2 black anodize, sealed, 12-25 um per MIL-PRF-8625. Mask all threads, datum/interface and electrical bond surfaces as specified by assembly drawing.",
        "3. DATUM A: exterior bottom plane Z0. DATUM B: longitudinal center plane X0. DATUM C: transverse center plane Y57.5. Boss-axis true position dia 0.20 to A|B|C.",
        "4. Six boss tops coplanar within 0.10. Boss axes perpendicular to A within 0.10 over 5 mm. Break edges 0.2-0.5; remove burrs. Surface finish Ra 3.2 um unless noted.",
        "5. FASTENER: M3x6 ISO 7380-1 A4-70 button-head screw plus 0.5 mm PA66/PEEK washer. Nominal engagement 3.9 mm; verify no bottoming. Assembly torque 0.35 +/-0.05 N.m with marine-compatible anti-seize.",
        "6. GENERAL TOLERANCES: ISO 2768-mK. Critical dimensions and GD&T shown here take precedence. STEP models tap-drill geometry; this drawing controls the M3 thread.",
        "7. Nominal OD10 x 5 boss envelopes have zero positive-volume intersections with the 19 non-base solids in the hash-controlled v0.8 assembly. See interference CSV.",
        "8. RELEASE HOLD: populated PCB/component bodies, connector mates, routed harnesses, thermal hardware and service-tool envelopes are absent; tolerance-aware final assembly review and approvals remain mandatory.",
        "9. CONTROLLED SOURCE SHA-256: 1e1f78229c2624be0a0ecc7766795e55c19090104cca487c9a2ebd9da287a810.",
    ]
    c.setFont("Helvetica-Bold", 8); c.drawString(48, notes_y + 13, "MANUFACTURING / CONTROL NOTES")
    for i, note in enumerate(notes): fit_text(c, note, 48, notes_y - i * 10.5, width - 96, 6.9)

    tbx, tby, tbw, tbh = width - 430, 34, 390, 64
    c.rect(tbx, tby, tbw, tbh); line(c, tbx, tby + 25, tbx + tbw, tby + 25); line(c, tbx + 270, tby, tbx + 270, tby + tbh)
    c.setFont("Helvetica-Bold", 8); c.drawString(tbx + 6, tby + 48, "BRMC Consumer v1.0 CNC 6061 enclosure base")
    c.setFont("Helvetica", 7); c.drawString(tbx + 6, tby + 34, "DOC: BRMC-MECH-EVT-010 | DRAWING: 010-BASE-01")
    c.drawString(tbx + 6, tby + 9, "STATUS: RELEASE CANDIDATE - APPROVAL HOLD")
    c.drawString(tbx + 280, tby + 48, "REV: B")
    c.drawString(tbx + 280, tby + 34, "DATE: 2026-09-03")
    c.drawString(tbx + 280, tby + 9, "SHEET: 1 / 1")

    c.showPage(); c.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--dimensions", type=Path, required=True)
    parser.add_argument("--interference", type=Path, required=True)
    args = parser.parse_args()
    solids = load_controlled_assembly(args.assembly.resolve())
    generate_step(solids, args.step.resolve())
    generate_dimensions(args.dimensions.resolve())
    generate_interference_report(solids, args.interference.resolve())
    generate_pdf(args.pdf.resolve())


if __name__ == "__main__":
    main()
