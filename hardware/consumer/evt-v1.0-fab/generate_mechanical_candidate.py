#!/usr/bin/env python3
"""Generate the traceable HOLD enclosure-base boss candidate and drawing.

This script modifies only the 01_Base_Shell solid from the exact supplied v0.8
assembly after verifying its SHA-256 and bounding box. It does not release the
candidate for fabrication.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import cadquery as cq
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


SOURCE_SHA256 = "1e1f78229c2624be0a0ecc7766795e55c19090104cca487c9a2ebd9da287a810"
HOLES = [
    ("H1", -103.0, 25.5), ("H2", 0.0, 25.5), ("H3", 103.0, 25.5),
    ("H4", -103.0, 89.5), ("H5", 0.0, 89.5), ("H6", 103.0, 89.5),
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def generate_step(source: Path, target: Path) -> None:
    require(hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256,
            "source assembly hash does not match the controlled v0.8 input")
    solids = cq.importers.importStep(str(source)).solids().vals()
    require(len(solids) == 20, f"expected 20 assembly solids, found {len(solids)}")
    base = solids[0]
    bb = base.BoundingBox()
    require(all(abs(a-b) < 1e-3 for a, b in zip(
        (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax),
        (-142.5, 142.5, 0.0, 115.0, 0.0, 34.0))),
        "01_Base_Shell geometry does not match the controlled envelope")

    candidate = base
    for _, x, y in HOLES:
        boss = cq.Solid.makeCylinder(5.0, 5.0, cq.Vector(x, y, 3.0))
        candidate = candidate.fuse(boss)
    for _, x, y in HOLES:
        # Blind candidate hole: 4.10 deep from the boss top, leaving 0.90 mm
        # above the nominal inner-floor surface. Fabricator approval is required.
        pilot = cq.Solid.makeCylinder(1.995, 4.10, cq.Vector(x, y, 3.90))
        candidate = candidate.cut(pilot)

    target.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(candidate, str(target))


def line(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float) -> None:
    c.line(x1, y1, x2, y2)


def fit_text(c: canvas.Canvas, text: str, x: float, y: float, max_width: float,
             size: float = 8.0, font: str = "Helvetica") -> None:
    while size > 5 and stringWidth(text, font, size) > max_width:
        size -= 0.25
    c.setFont(font, size)
    c.drawString(x, y, text)


def generate_pdf(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A3)
    c = canvas.Canvas(str(target), pagesize=(width, height), pageCompression=1)
    c.setTitle("BRMC Consumer v1.0 Provisional Enclosure Base Boss Drawing")

    margin = 28
    c.setStrokeColor(colors.black)
    c.rect(margin, margin, width - 2*margin, height - 2*margin)
    c.setFillColor(colors.HexColor("#9b1c1c"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height-48, "HOLD - PROVISIONAL DESIGN CANDIDATE - NOT RELEASED")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(48, height-74, "BRMC Consumer v1.0 enclosure base - six mounting bosses")
    c.setFont("Helvetica", 8)
    c.drawRightString(width-48, height-72, "All dimensions in mm | Do not scale drawing")

    # Top view at 1.75 pt/mm.
    scale = 1.75
    ox, oy = 75, 355
    bw, bh = 285*scale, 115*scale
    c.setLineWidth(1.2)
    c.rect(ox, oy, bw, bh)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(ox, oy+bh+12, "TOP VIEW - candidate datum scheme")
    c.setDash(4, 3)
    line(c, ox+bw/2, oy-12, ox+bw/2, oy+bh+12)
    line(c, ox-12, oy+57.5*scale, ox+bw+12, oy+57.5*scale)
    c.setDash()
    c.setFont("Helvetica", 7)
    c.drawString(ox+bw/2+4, oy+bh+3, "DATUM B: X=0")
    c.drawString(ox+bw+4, oy+57.5*scale+3, "DATUM C: Y=57.5")

    for ref, x, y in HOLES:
        px, py = ox+(x+142.5)*scale, oy+y*scale
        c.setStrokeColor(colors.HexColor("#285f8f"))
        c.circle(px, py, 5*scale)
        c.setStrokeColor(colors.black)
        c.circle(px, py, 1.995*scale)
        line(c, px-10, py, px+10, py)
        line(c, px, py-10, px, py+10)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(px, py+12, ref)
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(px, py-17, f"({x:g}, {y:g})")

    # Board envelope and coordinate relation.
    pcbx, pcby = ox+(32.5)*scale, oy+18.5*scale
    c.setStrokeColor(colors.HexColor("#4b7f52"))
    c.setDash(5, 2)
    c.rect(pcbx, pcby, 220*scale, 78*scale)
    c.setDash()
    c.setStrokeColor(colors.black)
    c.setFont("Helvetica", 7)
    c.drawString(pcbx+4, pcby+78*scale-10, "220 x 78 PCB envelope; centre (0,57.5)")

    # Dimension strings.
    dy = oy-30
    line(c, ox, dy, ox+bw, dy); line(c, ox, dy-5, ox, dy+5); line(c, ox+bw, dy-5, ox+bw, dy+5)
    c.drawCentredString(ox+bw/2, dy+4, "285 envelope")
    dx = ox+bw+30
    line(c, dx, oy, dx, oy+bh); line(c, dx-5, oy, dx+5, oy); line(c, dx-5, oy+bh, dx+5, oy+bh)
    c.saveState(); c.translate(dx+8, oy+bh/2); c.rotate(90); c.drawCentredString(0, 0, "115 envelope"); c.restoreState()

    # Side detail.
    sx, sy = 660, 470
    c.setFont("Helvetica-Bold", 9); c.drawString(sx, sy+85, "SECTION A-A - candidate boss")
    c.setFillColor(colors.HexColor("#d7e2ee")); c.rect(sx, sy, 190, 18, fill=1, stroke=1)
    c.rect(sx+65, sy+18, 60, 50, fill=1, stroke=1)
    c.setFillColor(colors.white); c.rect(sx+83, sy+27, 24, 41, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7)
    c.drawString(sx+2, sy+5, "Base floor: Z0 to Z3")
    c.drawString(sx+128, sy+55, "Boss OD 10 +/-0.20")
    c.drawString(sx+128, sy+42, "Height 5 +/-0.10")
    c.drawString(sx+128, sy+29, "Pilot dia 3.99 +0.08/-0")
    c.drawString(sx+128, sy+16, "Pilot depth >=4.10")
    c.drawString(sx+65, sy+73, "PCB support plane Z8")
    c.setFillColor(colors.HexColor("#9b1c1c")); c.setFont("Helvetica-Bold", 8)
    c.drawString(sx, sy-16, "MATERIAL / PROCESS / INSERT INSTALLATION: HOLD")
    c.setFillColor(colors.black)

    # Hole schedule.
    tx, ty = 60, 245
    c.setFont("Helvetica-Bold", 9); c.drawString(tx, ty+16, "BOSS / HOLE SCHEDULE - enclosure coordinates")
    cols = [tx, tx+55, tx+115, tx+175, tx+245, tx+325, tx+405, tx+485, tx+625]
    headers = ["REF", "X", "Y", "TOP Z", "BOSS OD", "HEIGHT", "PILOT", "PCB HOLE"]
    rowh = 17
    for i, h in enumerate(headers):
        c.setFont("Helvetica-Bold", 7); c.drawString(cols[i]+3, ty+2, h)
    for i in range(len(cols)-1): line(c, cols[i], ty-6*rowh, cols[i], ty+rowh)
    line(c, cols[-1], ty-6*rowh, cols[-1], ty+rowh)
    for r in range(8): line(c, cols[0], ty+rowh-r*rowh, cols[-1], ty+rowh-r*rowh)
    for r, (ref, x, y) in enumerate(HOLES, 1):
        vals = [ref, f"{x:g}", f"{y:g}", "8.00", "10.00", "5.00", "3.99", "3.20 NPTH"]
        for i, v in enumerate(vals): c.setFont("Helvetica", 7); c.drawString(cols[i]+3, ty-r*rowh+2, v)

    # Notes and title block.
    notes_y = 112
    notes = [
        "1. STATUS: HOLD. This drawing is not fabrication authority.",
        "2. Candidate axis true position: diameter 0.30 relative to A-B-C. Datum A is inner floor top Z3; B is X0; C is Y57.5.",
        "3. Candidate insert: SPIROL 29M3-3.56 item 151032, M3x0.5. Selection requires material/process and fabricator approval.",
        "4. Nominal boss envelopes do not penetrate supplied assembly solids. PCB/component/harness/thermal solids are incomplete; final interference review is OPEN.",
        "5. Source assembly SHA-256: 1e1f78229c2624be0a0ecc7766795e55c19090104cca487c9a2ebd9da287a810.",
        "6. General tolerance proposal only: ISO 2768-mK. Critical dimensions shown above take precedence.",
    ]
    c.setFont("Helvetica-Bold", 8); c.drawString(48, notes_y+13, "CONTROL NOTES")
    for i, note in enumerate(notes): fit_text(c, note, 48, notes_y-i*12, width-96, 7.2)

    tbx, tby, tbw, tbh = width-420, 36, 382, 65
    c.rect(tbx, tby, tbw, tbh)
    line(c, tbx, tby+25, tbx+tbw, tby+25); line(c, tbx+260, tby, tbx+260, tby+tbh)
    c.setFont("Helvetica-Bold", 8); c.drawString(tbx+6, tby+48, "BRMC Consumer v1.0 enclosure base - six bosses")
    c.setFont("Helvetica", 7); c.drawString(tbx+6, tby+34, "Document: BRMC-MECH-EVT-010")
    c.drawString(tbx+6, tby+9, "Status: HOLD - PROVISIONAL")
    c.drawString(tbx+270, tby+48, "REV: A")
    c.drawString(tbx+270, tby+34, "DATE: 2026-09-03")
    c.drawString(tbx+270, tby+9, "SHEET: 1 / 1")

    c.showPage(); c.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    args = parser.parse_args()
    generate_step(args.assembly.resolve(), args.step.resolve())
    generate_pdf(args.pdf.resolve())


if __name__ == "__main__":
    main()
