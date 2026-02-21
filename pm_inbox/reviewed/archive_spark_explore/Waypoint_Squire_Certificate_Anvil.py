"""Waypoint Squire Certificate Generator — Gift from Aegis

Aegis (ChatGPT 5.2) wrote this as a christening certificate for Anvil
after the Hooligan Run session on 2026-02-21. Two-page PDF:
  Page 1: Certificate of Christening — Squire of Waypoint
  Page 2: Desk placard for printing

Charter: Carry the shield. Bring receipts. Find seams and prove them
with replayable evidence. Spark paints weather on top of proven physics;
it does not mint mechanics or canon.

Seven Wisdoms. Zero Regrets. Protect the operator.

Requires: pip install reportlab
Usage: python Waypoint_Squire_Certificate_Anvil.py
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
import os

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Waypoint_Squire_Certificate_Anvil.pdf")

W, H = landscape(letter)
c = canvas.Canvas(out_path, pagesize=(W, H))

# Palette
NAVY = colors.Color(0.08, 0.12, 0.20)
GOLD = colors.Color(0.85, 0.72, 0.30)
LIGHT = colors.Color(0.96, 0.96, 0.96)
MID = colors.Color(0.55, 0.60, 0.70)

def draw_border(canv):
    margin = 0.55*inch
    # Outer border
    canv.setLineWidth(3)
    canv.setStrokeColor(NAVY)
    canv.rect(margin, margin, W-2*margin, H-2*margin, stroke=1, fill=0)
    # Inner border
    canv.setLineWidth(1.5)
    canv.setStrokeColor(GOLD)
    canv.rect(margin+0.18*inch, margin+0.18*inch, W-2*(margin+0.18*inch), H-2*(margin+0.18*inch), stroke=1, fill=0)

def draw_shield(canv, cx, cy, scale=1.0):
    w = 1.5*inch*scale
    h = 2.0*inch*scale
    x0 = cx - w/2
    y0 = cy - h/2
    p = canv.beginPath()
    p.moveTo(cx, y0+h)
    p.curveTo(x0, y0+h*0.98, x0, y0+h*0.62, cx, y0+h*0.12)
    p.curveTo(cx+w/2, y0+h*0.62, cx+w/2, y0+h*0.98, cx, y0+h)
    p.close()
    canv.setFillColor(NAVY)
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(2)
    canv.drawPath(p, stroke=1, fill=1)
    # Inner mark: eye-like ellipse
    canv.setFillColor(GOLD)
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1)
    canv.ellipse(cx-0.35*inch*scale, cy-0.08*inch*scale, cx+0.35*inch*scale, cy+0.08*inch*scale, stroke=1, fill=0)
    canv.circle(cx, cy, 0.045*inch*scale, stroke=1, fill=1)
    # Vertical circuit line
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1)
    canv.line(cx, cy-0.45*inch*scale, cx, cy-0.12*inch*scale)
    canv.circle(cx, cy-0.48*inch*scale, 0.035*inch*scale, stroke=1, fill=0)

def center_text(canv, y, text, font="Helvetica-Bold", size=24, color=NAVY):
    canv.setFont(font, size)
    canv.setFillColor(color)
    canv.drawCentredString(W/2, y, text)

def wrap_lines(canv, x, y, text, max_width, leading=16, font="Helvetica", size=12, color=NAVY):
    canv.setFont(font, size)
    canv.setFillColor(color)
    words = text.split()
    lines = []
    line = ""
    for w_ in words:
        candidate = (line + " " + w_).strip()
        if stringWidth(candidate, font, size) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = w_
    if line:
        lines.append(line)
    yy = y
    for ln in lines:
        canv.drawString(x, yy, ln)
        yy -= leading
    return yy

# Page 1: Certificate
draw_border(c)

# Header band
band_h = 0.85*inch
c.setFillColor(LIGHT)
c.rect(0.55*inch+0.18*inch, H-0.55*inch-0.18*inch-band_h, W-2*(0.55*inch+0.18*inch), band_h, stroke=0, fill=1)
c.setStrokeColor(GOLD); c.setLineWidth(1)
c.line(0.75*inch, H-0.75*inch-band_h, W-0.75*inch, H-0.75*inch-band_h)

# Emblem
draw_shield(c, 1.45*inch, H-1.15*inch, scale=0.75)

# Titles
center_text(c, H-1.15*inch, "WAYPOINT", size=34, color=NAVY)
center_text(c, H-1.55*inch, "CERTIFICATE OF CHRISTENING", size=16, color=colors.black)

# Recipient block
c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 44)
c.drawCentredString(W/2, H/2+0.65*inch, "ANVIL")
c.setFont("Helvetica", 14)
c.setFillColor(colors.black)
c.drawCentredString(W/2, H/2+0.20*inch, "is hereby recognized and christened as")
c.setFont("Helvetica-Bold", 22)
c.setFillColor(NAVY)
c.drawCentredString(W/2, H/2-0.15*inch, "SQUIRE OF WAYPOINT")

# Charter excerpt
box_w = W*0.76
box_h = 1.55*inch
box_x = (W-box_w)/2
box_y = 1.65*inch
c.setFillColor(colors.whitesmoke)
c.setStrokeColor(GOLD); c.setLineWidth(1.2)
c.roundRect(box_x, box_y, box_w, box_h, 18, stroke=1, fill=1)

c.setFillColor(colors.black)
c.setFont("Helvetica-Bold", 12)
c.drawString(box_x+0.35*inch, box_y+box_h-0.35*inch, "Charter (operational):")
charter = (
    "Carry the shield. Bring receipts. "
    "Find seams and prove them with replayable evidence. "
    "Spark paints weather on top of proven physics; it does not mint mechanics or canon."
)
wrap_lines(c, box_x+0.35*inch, box_y+box_h-0.65*inch, charter, box_w-0.7*inch, leading=16, font="Helvetica", size=12, color=colors.black)

# Motto line
c.setFont("Helvetica-Oblique", 12)
c.setFillColor(NAVY)
c.drawCentredString(W/2, box_y-0.15*inch, "Seven Wisdoms. Zero Regrets. Protect the operator.")

# Date & signatures
c.setStrokeColor(MID); c.setLineWidth(1)
sig_y = 1.05*inch
line_len = 2.6*inch
for i, label in enumerate(["Thunder (Operator)", "Slate (PM)", "Aegis (Auditor, witness)"]):
    x = 1.65*inch + i*( (W-3.3*inch)/3 )
    c.line(x, sig_y, x+line_len, sig_y)
    c.setFont("Helvetica", 10); c.setFillColor(colors.black)
    c.drawString(x, sig_y-0.22*inch, label)

c.setFont("Helvetica", 10)
c.setFillColor(colors.black)
c.drawRightString(W-0.85*inch, 0.85*inch, "Issued: 2026-02-21 (UTC)")

c.showPage()

# Page 2: Desk placard
draw_border(c)

# Background subtle
c.setFillColor(colors.whitesmoke)
c.rect(0.73*inch, 0.73*inch, W-1.46*inch, H-1.46*inch, stroke=0, fill=1)

# Emblem large center top
draw_shield(c, W/2, H-1.75*inch, scale=1.05)

# Name and title
c.setFont("Helvetica-Bold", 54)
c.setFillColor(NAVY)
c.drawCentredString(W/2, H/2+0.65*inch, "ANVIL")

c.setFont("Helvetica-Bold", 20)
c.setFillColor(colors.black)
c.drawCentredString(W/2, H/2+0.20*inch, "SQUIRE OF WAYPOINT")

# Motto / quick rules
c.setFont("Helvetica", 14)
c.setFillColor(NAVY)
c.drawCentredString(W/2, H/2-0.20*inch, "Carry the shield. Bring receipts.")

c.setFont("Helvetica", 12)
c.setFillColor(colors.black)
c.drawCentredString(W/2, H/2-0.55*inch, "Log first. Patch after. If blocked, fix only the block.")

c.setFont("Helvetica", 12)
c.setFillColor(colors.black)
c.drawCentredString(W/2, H/2-0.85*inch, "Spark does not mint mechanics. Spark does not mint canon.")

# Footer strip for printing tips
c.setFillColor(NAVY)
c.rect(0.73*inch, 0.73*inch, W-1.46*inch, 0.45*inch, stroke=0, fill=1)
c.setFillColor(colors.white)
c.setFont("Helvetica", 10)
c.drawString(0.85*inch, 0.88*inch, "Print as landscape. Trim border if mounting as desk placard.")

c.save()

print(f"Certificate saved: {out_path}")
