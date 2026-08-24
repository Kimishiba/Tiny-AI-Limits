#!/usr/bin/env python3
"""
GC9A01 Cyberdeck Enclosure - Engineering Blueprint & Technical Drawing Generator
Generates publication-quality 300 DPI dimensioned mechanical engineering drawing sheets
for CAD modeling, CNC machining, and 3D printing verification.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, Arc
import numpy as np

def draw_title_block(ax, sheet_title, sheet_num, total_sheets=4):
    """Draws standard engineering blueprint title block."""
    # Title box in lower right corner
    x0, y0, w, h = 250, 10, 160, 35
    rect = Rectangle((x0, y0), w, h, fill=True, facecolor='#0d1b2a', edgecolor='#415a77', linewidth=1.5)
    ax.add_patch(rect)
    
    # Grid lines inside title block
    ax.plot([x0, x0 + w], [y0 + 20, y0 + 20], color='#415a77', linewidth=1)
    ax.plot([x0 + 100, x0 + 100], [y0, y0 + 20], color='#415a77', linewidth=1)
    
    ax.text(x0 + 5, y0 + 26, "TINY AI LIMITS CYBERDECK 01", color='#e0e1dd', fontsize=9, fontweight='bold', family='monospace')
    ax.text(x0 + 5, y0 + 8, f"PART: {sheet_title}", color='#00e5ff', fontsize=8, fontweight='bold', family='monospace')
    ax.text(x0 + 105, y0 + 8, f"SHEET {sheet_num}/{total_sheets}\nSCALE 1:1 [mm]", color='#a9d6e5', fontsize=7, family='monospace')

def setup_blueprint_canvas(figsize=(14, 10), title="ENGINEERING DRAWING"):
    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    fig.patch.set_facecolor('#0b0f19') # Blueprint dark slate blue
    ax.set_facecolor('#0b0f19')
    
    # Outer blueprint frame
    border = Rectangle((5, 5), 410, 287, fill=False, edgecolor='#1b2a4a', linewidth=2)
    inner_border = Rectangle((8, 8), 404, 281, fill=False, edgecolor='#2a3d66', linewidth=1)
    ax.add_patch(border)
    ax.add_patch(inner_border)
    
    # Subtle background grid
    for x in range(20, 410, 20):
        ax.axvline(x, color='#141c2e', linewidth=0.5, linestyle=':')
    for y in range(20, 290, 20):
        ax.axhline(y, color='#141c2e', linewidth=0.5, linestyle=':')
        
    ax.set_xlim(0, 420)
    ax.set_ylim(0, 297)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Main Header
    ax.text(20, 275, title, color='#ffffff', fontsize=14, fontweight='bold', family='monospace')
    ax.text(20, 267, "PRECISION MECHANICAL SPECIFICATION | ALL UNITS IN MILLIMETERS [MM]", color='#778da9', fontsize=8, family='monospace')
    
    return fig, ax

def add_dim_line(ax, p1, p2, text, offset=6, text_offset=2, is_vertical=False, color='#ff7a00'):
    """Draws an engineering dimension line with arrows and dimension text."""
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vertical:
        # Extension lines
        ax.plot([x1, x1 + offset], [y1, y1], color='#415a77', linewidth=0.8, linestyle='--')
        ax.plot([x2, x2 + offset], [y2, y2], color='#415a77', linewidth=0.8, linestyle='--')
        # Dimension line
        dim_x = x1 + offset
        ax.annotate('', xy=(dim_x, y1), xytext=(dim_x, y2),
                    arrowprops=dict(arrowstyle='<->', color=color, lw=1.0, mutation_scale=10))
        ax.text(dim_x + text_offset, (y1 + y2)/2, text, color=color, fontsize=8,
                va='center', ha='left', family='monospace', fontweight='bold')
    else:
        # Extension lines
        ax.plot([x1, x1], [y1, y1 + offset], color='#415a77', linewidth=0.8, linestyle='--')
        ax.plot([x2, x2], [y2, y2 + offset], color='#415a77', linewidth=0.8, linestyle='--')
        # Dimension line
        dim_y = y1 + offset
        ax.annotate('', xy=(x1, dim_y), xytext=(x2, dim_y),
                    arrowprops=dict(arrowstyle='<->', color=color, lw=1.0, mutation_scale=10))
        ax.text((x1 + x2)/2, dim_y + text_offset, text, color=color, fontsize=8,
                va='bottom', ha='center', family='monospace', fontweight='bold')

def generate_sheet_1_front_bezel(output_path):
    """Sheet 1: Front Bezel Plate Engineering Drawing."""
    fig, ax = setup_blueprint_canvas(title="PART 1: FRONT BEZEL RING PLATE (GC9A01-BEZEL-01)")
    draw_title_block(ax, "FRONT BEZEL PLATE", 1)
    
    # ---------------- VIEW A: FRONT EXTERIOR VIEW (Center: 110, 150) ----------------
    cx, cy = 110, 150
    ax.text(cx, cy - 45, "VIEW A: FRONT EXTERIOR", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Octagonal outer perimeter (54x54 with 6mm chamfers)
    hw, c = 27.0, 6.0
    oct_pts = np.array([
        [-hw + c, -hw], [hw - c, -hw],
        [hw, -hw + c],  [hw, hw - c],
        [hw - c, hw],   [-hw + c, hw],
        [-hw, hw - c],  [-hw, -hw + c]
    ]) + [cx, cy]
    ax.add_patch(Polygon(oct_pts, fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.5))
    
    # Raised circular bezel ring (dia 44mm)
    ax.add_patch(Circle((cx, cy), 22.0, fill=False, edgecolor='#4cc9f0', linewidth=1.2, linestyle='-'))
    
    # Active Screen Aperture (dia 32.6mm with 45° chamfer inner dia 30.6mm)
    ax.add_patch(Circle((cx, cy), 16.3, fill=True, facecolor='#060a12', edgecolor='#00e5ff', linewidth=1.5))
    ax.add_patch(Circle((cx, cy), 15.3, fill=False, edgecolor='#5c677d', linewidth=0.8, linestyle=':'))
    
    # Center crosshairs
    ax.plot([cx - 32, cx + 32], [cy, cy], color='#5c677d', linewidth=0.6, linestyle='-.')
    ax.plot([cx, cx], [cy - 32, cy + 32], color='#5c677d', linewidth=0.6, linestyle='-.')
    
    # 4 Corner M2 Screw Holes (+/-21mm) with counterbores (dia 4.8mm outer, 2.6mm inner)
    for sx in [-21.0, 21.0]:
        for sy in [-21.0, 21.0]:
            ax.add_patch(Circle((cx + sx, cy + sy), 2.4, fill=False, edgecolor='#f72585', linewidth=1.0))
            ax.add_patch(Circle((cx + sx, cy + sy), 1.3, fill=True, facecolor='#060a12', edgecolor='#f72585', linewidth=1.0))
            
    # Dimensions for View A
    add_dim_line(ax, (cx - 27, cy + 27), (cx + 27, cy + 27), "54.00", offset=10)
    add_dim_line(ax, (cx + 27, cy - 27), (cx + 27, cy + 27), "54.00", offset=10, is_vertical=True)
    add_dim_line(ax, (cx - 21, cy + 21), (cx + 21, cy + 21), "42.00 B.C.", offset=4)
    
    # Leader line for screen aperture
    ax.annotate("ACTIVE VIEWPORT\nØ32.60 THRU (45° BEVEL)", xy=(cx + 11.5, cy + 11.5), xytext=(cx + 35, cy + 35),
                arrowprops=dict(arrowstyle='->', color='#00e5ff', lw=1.0),
                color='#00e5ff', fontsize=7.5, family='monospace', fontweight='bold')
    
    # Leader line for corner screws
    ax.annotate("4x M2 COUNTERBORE\nØ4.80 x 2.20 DP\nØ2.60 THRU", xy=(cx + 21, cy + 21), xytext=(cx + 35, cy + 18),
                arrowprops=dict(arrowstyle='->', color='#f72585', lw=1.0),
                color='#f72585', fontsize=7.5, family='monospace', fontweight='bold')

    # ---------------- VIEW B: REAR RETENTION POCKET VIEW (Center: 240, 150) ----------------
    rx, ry = 240, 150
    ax.text(rx, ry - 45, "VIEW B: REAR RETENTION POCKET", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Octagonal outer perimeter
    ax.add_patch(Polygon(np.array(oct_pts) - [cx, cy] + [rx, ry], fill=True, facecolor='#162032', edgecolor='#415a77', linewidth=1.2))
    
    # Glass retention step (dia 36.0mm x 1.6mm deep)
    ax.add_patch(Circle((rx, ry), 18.0, fill=False, edgecolor='#4cc9f0', linewidth=1.0, linestyle='--'))
    
    # PCB Outline Pocket (dia 38.6mm circular top + 23.6mm bottom tab down to y=-26.8mm)
    # Circle
    ax.add_patch(Circle((rx, ry), 19.3, fill=True, facecolor='#0f172a', edgecolor='#ffd166', linewidth=1.2))
    # Tab
    ax.add_patch(Rectangle((rx - 11.8, ry - 26.8), 23.6, 26.8, fill=True, facecolor='#0f172a', edgecolor='#ffd166', linewidth=1.2))
    
    # Active window through-hole (center)
    ax.add_patch(Circle((rx, ry), 16.3, fill=True, facecolor='#060a12', edgecolor='#00e5ff', linewidth=1.0))
    
    # 2 Blind M2 Thread-Gripping Pilot Holes (X = +/-9.63, Y = -18.91, dia = 1.75mm, depth = 3.4mm)
    sh_x, sh_y = 9.63, -18.91
    ax.add_patch(Circle((rx - sh_x, ry + sh_y), 1.75/2, fill=True, facecolor='#ff006e', edgecolor='#ffbe0b', linewidth=1.2))
    ax.add_patch(Circle((rx + sh_x, ry + sh_y), 1.75/2, fill=True, facecolor='#ff006e', edgecolor='#ffbe0b', linewidth=1.2))
    
    # Dimensions for View B
    add_dim_line(ax, (rx - 11.8, ry - 26.8), (rx + 11.8, ry - 26.8), "23.60 TAB", offset=-8)
    add_dim_line(ax, (rx - sh_x, ry + sh_y), (rx + sh_x, ry + sh_y), "19.26 PITCH", offset=6, color='#ffbe0b')
    
    # Leader for blind pilot holes
    ax.annotate("2x SCREEN BOLTING HOLES\nØ1.75 BLIND x 3.40 DP\n(NO FRONT THRU-HOLE)", xy=(rx + sh_x, ry + sh_y), xytext=(rx + 25, ry + sh_y - 8),
                arrowprops=dict(arrowstyle='->', color='#ffbe0b', lw=1.0),
                color='#ffbe0b', fontsize=7.5, family='monospace', fontweight='bold')
    
    # ---------------- VIEW C: SECTION A-A CROSS SECTION (Center: 350, 150) ----------------
    sx, sy = 355, 150
    ax.text(sx + 5, sy - 45, "SECTION A-A", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Section profile (Z axis horizontal, Y axis vertical)
    # Total thickness: 4.5mm base + 1.5mm ring = 6.0mm
    # Base: z=0 to 4.5, y=-27 to +27
    sec_poly = [
        [sx, sy - 27], [sx + 4.5, sy - 27], [sx + 4.5, sy - 22],
        [sx + 6.0, sy - 22], [sx + 6.0, sy + 22], [sx + 4.5, sy + 22],
        [sx + 4.5, sy + 27], [sx, sy + 27],
        [sx, sy + 19.3], [sx + 1.8, sy + 19.3], [sx + 1.8, sy + 18.0],
        [sx + 3.4, sy + 18.0], [sx + 3.4, sy + 16.3], [sx + 6.0, sy + 15.3],
        [sx + 6.0, sy - 15.3], [sx + 3.4, sy - 16.3], [sx + 3.4, sy - 18.0],
        [sx + 1.8, sy - 18.0], [sx + 1.8, sy - 26.8], [sx, sy - 26.8]
    ]
    ax.add_patch(Polygon(sec_poly, fill=True, facecolor='#1b2a4a', edgecolor='#00e5ff', linewidth=1.2, hatch='//'))
    
    # Section Dimensions
    add_dim_line(ax, (sx, sy + 27), (sx + 4.5, sy + 27), "4.50", offset=8)
    add_dim_line(ax, (sx, sy - 27), (sx + 6.0, sy - 27), "6.00 OAL", offset=-10)
    add_dim_line(ax, (sx, sy + 19.3), (sx + 1.8, sy + 19.3), "1.80 DP", offset=3, color='#ffd166')
    
    # Notes block
    ax.text(20, 45, "MANUFACTURING NOTES:\n1. MATERIAL: MATTE BLACK PETG / PLA (0.16mm LAYER HEIGHT, 3 PERIMETERS).\n2. TOLERANCE: GENERAL +/- 0.15mm | PCB POCKET CLEARS BLUEPRINT OUTLINE (+0.6mm).\n3. 2x M2 SCREEN HOLES: 1.75mm PILOT ACCEPTS M2 SELF-TAPPING SCREWS DIRECTLY.\n4. PRINT ORIENTATION: FLAT FACE DOWN (Z=6.0 ON BUILD PLATE). ZERO SUPPORTS REQUIRED.",
            color='#8ecae6', fontsize=7.5, family='monospace', va='top')
            
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 1 Generated]: {output_path}")

def generate_sheet_2_main_housing(output_path):
    """Sheet 2: Main Housing Pod (26mm) Engineering Drawing."""
    fig, ax = setup_blueprint_canvas(title="PART 2: MAIN HOUSING POD 26MM (GC9A01-BODY-26)")
    draw_title_block(ax, "MAIN HOUSING POD", 2)
    
    # ---------------- VIEW A: FRONT OPENING VIEW (Center: 110, 160) ----------------
    cx, cy = 110, 160
    ax.text(cx, cy - 45, "VIEW A: FRONT INTERIOR & CAVITY", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Octagonal outer perimeter
    hw, c = 27.0, 6.0
    oct_pts = np.array([
        [-hw + c, -hw], [hw - c, -hw],
        [hw, -hw + c],  [hw, hw - c],
        [hw - c, hw],   [-hw + c, hw],
        [-hw, hw - c],  [-hw, -hw + c]
    ]) + [cx, cy]
    ax.add_patch(Polygon(oct_pts, fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.5))
    
    # 44x44mm Internal Electronics Cavity
    ax.add_patch(Rectangle((cx - 22, cy - 22), 44, 44, fill=True, facecolor='#0b111e', edgecolor='#4cc9f0', linewidth=1.2))
    
    # GC9A01 Front PCB Pocket Rim (dia 38.6mm + 23.6mm tab down to y=-27)
    ax.add_patch(Circle((cx, cy), 19.3, fill=False, edgecolor='#ffd166', linewidth=1.0, linestyle='--'))
    ax.add_patch(Rectangle((cx - 11.8, cy - 27), 23.6, 27, fill=False, edgecolor='#ffd166', linewidth=1.0, linestyle='--'))
    
    # Bottom DuPont Wire Drop Trench (20mm wide x 12mm deep at bottom wall)
    ax.add_patch(Rectangle((cx - 10, cy - 27.5), 20, 8, fill=True, facecolor='#060a12', edgecolor='#ff006e', linewidth=1.5, hatch='\\\\'))
    
    # Left USB-C Port Cutout (13mm wide x 8mm tall through left wall at x = -27)
    ax.add_patch(Rectangle((cx - 27.5, cy - 6.5), 6.5, 13, fill=True, facecolor='#060a12', edgecolor='#38b000', linewidth=1.2))
    
    # ESP32-C3 Pin-Locking Standoffs (X = -10, Y = +/-7.62, Length = 23mm, 16 blind holes)
    ax.add_patch(Rectangle((cx - 21.5, cy + 7.62 - 1.7), 23, 3.4, fill=True, facecolor='#1e293b', edgecolor='#a2d2ff', linewidth=1.0))
    ax.add_patch(Rectangle((cx - 21.5, cy - 7.62 - 1.7), 23, 3.4, fill=True, facecolor='#1e293b', edgecolor='#a2d2ff', linewidth=1.0))
    ax.add_patch(Rectangle((cx + 1.5, cy - 9.2), 2.5, 18.4, fill=True, facecolor='#334155', edgecolor='#a2d2ff', linewidth=1.0))
    
    # 16 Pin-Locking Registration Holes (dia = 1.5mm at 2.54mm pitch)
    for k in range(8):
        px = cx - 18.3 + k * 2.54
        ax.add_patch(Circle((px, cy + 7.62), 0.75, fill=True, facecolor='#060a12', edgecolor='#ffbe0b', linewidth=0.8))
        ax.add_patch(Circle((px, cy - 7.62), 0.75, fill=True, facecolor='#060a12', edgecolor='#ffbe0b', linewidth=0.8))
        
    # 4 Corner M2 Screw Pilot Holes (dia 2.0mm, 12mm deep)
    for sx in [-21.0, 21.0]:
        for sy in [-21.0, 21.0]:
            ax.add_patch(Circle((cx + sx, cy + sy), 1.0, fill=True, facecolor='#060a12', edgecolor='#f72585', linewidth=1.0))
            
    # Dimensions View A
    add_dim_line(ax, (cx - 22, cy + 22), (cx + 22, cy + 22), "44.00 CAVITY", offset=4, color='#4cc9f0')
    add_dim_line(ax, (cx - 10, cy - 27.5), (cx + 10, cy - 27.5), "20.00 WIRE TRENCH", offset=-8, color='#ff006e')
    
    # Leader for DuPont Wire Drop Trench
    ax.annotate("BOTTOM WIRE DROP TRENCH\n20.00 x 12.00 CUTOUT\n(UNRESTRICTED DUPONT DROP)", xy=(cx, cy - 25), xytext=(cx + 25, cy - 36),
                arrowprops=dict(arrowstyle='->', color='#ff006e', lw=1.0),
                color='#ff006e', fontsize=7.5, family='monospace', fontweight='bold')
                
    # Leader for USB-C Port
    ax.annotate("USB-C WINDOW\n13.00 x 8.00mm", xy=(cx - 27, cy), xytext=(cx - 48, cy + 18),
                arrowprops=dict(arrowstyle='->', color='#38b000', lw=1.0),
                color='#38b000', fontsize=7.5, family='monospace', fontweight='bold')

    # ---------------- VIEW B: SIDE PROFILE & SECTION B-B (Center: 270, 160) ----------------
    sx, sy = 265, 160
    ax.text(sx + 15, sy - 45, "VIEW B: SECTION B-B (Z-DEPTH PROFILE)", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Total depth: 26.0mm (z=0 rear floor to z=26.0 front rim)
    # Floor thickness: 2.5mm
    # Usable cavity depth: 19.5mm
    # PCB pocket depth: 4.0mm
    # Standoff height: 2.5mm
    sec_housing = [
        [sx, sy - 27], [sx + 26, sy - 27], [sx + 26, sy - 22],
        [sx + 22, sy - 22], [sx + 22, sy - 22], [sx + 2.5, sy - 22],
        [sx + 2.5, sy - 9.3], [sx + 5.0, sy - 9.3], [sx + 5.0, sy - 6.0], [sx + 2.5, sy - 6.0], # Standoff rail
        [sx + 2.5, sy + 6.0], [sx + 5.0, sy + 6.0], [sx + 5.0, sy + 9.3], [sx + 2.5, sy + 9.3], # Standoff rail
        [sx + 2.5, sy + 22], [sx + 22, sy + 22], [sx + 26, sy + 22], [sx + 26, sy + 27], [sx, sy + 27]
    ]
    ax.add_patch(Polygon(sec_housing, fill=True, facecolor='#1b2a4a', edgecolor='#00e5ff', linewidth=1.2, hatch='//'))
    
    # Depth Dimensions
    add_dim_line(ax, (sx, sy + 27), (sx + 26, sy + 27), "26.00 TOTAL DEPTH", offset=10)
    add_dim_line(ax, (sx, sy - 22), (sx + 2.5, sy - 22), "2.50", offset=-6)
    add_dim_line(ax, (sx + 2.5, sy - 22), (sx + 22, sy - 22), "19.50 USABLE CAVITY", offset=-6, color='#4cc9f0')
    add_dim_line(ax, (sx + 22, sy - 22), (sx + 26, sy - 22), "4.00 PCB", offset=-6, color='#ffd166')
    
    # Leader for Standoffs
    ax.annotate("ESP32-C3 STANDOFFS (2.5mm H)\n16x Ø1.50 PIN REGISTRATION\nREAR THRUST STOP BLOCK", xy=(sx + 5, sy + 7.62), xytext=(sx + 35, sy + 15),
                arrowprops=dict(arrowstyle='->', color='#a2d2ff', lw=1.0),
                color='#a2d2ff', fontsize=7.5, family='monospace', fontweight='bold')
                
    # Notes block
    ax.text(20, 45, "MANUFACTURING NOTES:\n1. 26.0mm SLIM POD PROFILE PRESERVES ORIGINAL CONCEPT CYBERDECK PROPORTIONS.\n2. 44x44x19.5mm USABLE CAVITY EASILY FITS DUPONT CABLES AND UPWARD PIN HEADERS.\n3. BOTTOM TRENCH DIRECTLY CONNECTS TO DESK STAND TO PREVENT WIRE PINCHING.\n4. 4x CORNER PILOT HOLES (Ø2.0mm x 12mm DP) FOR M2 SCREWS OR HEAT-SET INSERTS.",
            color='#8ecae6', fontsize=7.5, family='monospace', va='top')
            
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 2 Generated]: {output_path}")

def generate_sheet_3_desk_stand(output_path):
    """Sheet 3: Sculpted Desk Stand Cradle Engineering Drawing."""
    fig, ax = setup_blueprint_canvas(title="PART 3: SCULPTED TWO-TIER DESK STAND (GC9A01-STAND-01)")
    draw_title_block(ax, "DESK STAND CRADLE", 3)
    
    # ---------------- VIEW A: TOP CRADLE VIEW (Center: 110, 160) ----------------
    cx, cy = 110, 160
    ax.text(cx, cy - 45, "VIEW A: TOP CRADLE FOOTPRINT", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Tier 1 Rounded Base (64x68mm, r=6mm)
    base_box = FancyBboxPatch((cx - 32, cy - 34), 64, 68, boxstyle="round,pad=0,rounding_size=6",
                               fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.5)
    ax.add_patch(base_box)
    
    # Tier 2 Tapered Pyramidal Trunk Profile (58x58 with corner chamfers)
    ax.add_patch(Rectangle((cx - 27, cy - 27), 54, 54, fill=True, facecolor='#1f2d42', edgecolor='#4cc9f0', linewidth=1.0))
    
    # 22-Degree Angled V-Saddle Octagonal Cradle Pocket (54.8mm wide)
    ax.add_patch(Rectangle((cx - 27.4, cy - 14), 54.8, 35, fill=True, facecolor='#0b111e', edgecolor='#ffd166', linewidth=1.5))
    
    # 20mm Rear Cable Relief Channel (20mm wide x straight through rear)
    ax.add_patch(Rectangle((cx - 10, cy - 34), 20, 68, fill=True, facecolor='#060a12', edgecolor='#ff006e', linewidth=1.2, hatch='//'))
    
    # 4 Bottom Rubber Feet Recesses (Ø8.2mm, 1.4mm deep)
    for fx in [-22, 22]:
        for fy in [-24, 24]:
            ax.add_patch(Circle((cx + fx, cy + fy), 4.1, fill=False, edgecolor='#a2d2ff', linewidth=0.8, linestyle='--'))
            
    # Dimensions View A
    add_dim_line(ax, (cx - 32, cy + 34), (cx + 32, cy + 34), "64.00 BASE WIDTH", offset=8)
    add_dim_line(ax, (cx + 32, cy - 34), (cx + 32, cy + 34), "68.00 BASE DEPTH", offset=8, is_vertical=True)
    add_dim_line(ax, (cx - 10, cy - 34), (cx + 10, cy - 34), "20.00 CABLE SLOT", offset=-8, color='#ff006e')

    # ---------------- VIEW B: SIDE VIEW & 22° TILT CRADLE (Center: 275, 160) ----------------
    sx, sy = 275, 160
    ax.text(sx, sy - 45, "VIEW B: SIDE ELEVATION & 22° CRADLE", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    # Tier 1 Base: 6mm thick (y = -34 to +34, z = 0 to 6)
    ax.add_patch(Rectangle((sx - 34, sy - 15), 68, 6, fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.2))
    
    # Tier 2 Tapered Pyramidal Trunk with 22° V-Saddle Cutout
    stand_side_pts = [
        [sx - 29, sy - 9], [sx + 29, sy - 9],
        [sx + 25, sy + 19], # Rear top peak
        [sx + 6, sy + 19],  # Saddle rear wall
        [sx - 18, sy + 3],  # 22 deg saddle floor
        [sx - 24, sy + 12], # Saddle front lip
        [sx - 27, sy - 9]
    ]
    ax.add_patch(Polygon(stand_side_pts, fill=True, facecolor='#1f2d42', edgecolor='#4cc9f0', linewidth=1.5))
    
    # Cable Channel through-cut
    ax.add_patch(Rectangle((sx - 34, sy - 15), 68, 14, fill=False, edgecolor='#ff006e', linewidth=1.0, linestyle=':'))
    
    # Cradle angle annotation
    ax.annotate("22.0° ERGONOMIC TILT", xy=(sx - 6, sy + 11), xytext=(sx + 10, sy + 28),
                arrowprops=dict(arrowstyle='->', color='#ffd166', lw=1.2),
                color='#ffd166', fontsize=8, family='monospace', fontweight='bold')
                
    # Total Height Dimension
    add_dim_line(ax, (sx + 34, sy - 15), (sx + 34, sy + 19), "34.00 TOTAL H", offset=10, is_vertical=True)
    add_dim_line(ax, (sx - 34, sy - 15), (sx - 34, sy - 9), "6.00 TIER 1", offset=-8, is_vertical=True)
    
    # Notes block
    ax.text(20, 45, "MANUFACTURING NOTES:\n1. 22° V-SADDLE CRADLE OFFERS OPTIMAL DESKTOP VIEWING ANGLE WITH ZERO WOBBLE.\n2. TIER 1 BASE CAN BE PRINTED IN DUAL MATERIAL / WOOD PLA AS A SEPARATE ACCENT PLATE.\n3. 20mm PASS-THROUGH WIRE CHANNEL ALLOWS ROUTING BOTH USB-C CABLE AND DUPONT BUNDLES.\n4. 4x UNDERSIDE RECESSES (Ø8.2mm x 1.4mm DP) FIT STANDARD ADHESIVE SILICONE FEET.",
            color='#8ecae6', fontsize=7.5, family='monospace', va='top')
            
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 3 Generated]: {output_path}")

def generate_sheet_4_full_assembly(output_path):
    """Sheet 4: Full Exploded Assembly & Stackup Overview."""
    fig, ax = setup_blueprint_canvas(title="PART 4: COMPLETE EXPLODED ASSEMBLY & HARDWARE STACKUP")
    draw_title_block(ax, "EXPLODED ASSEMBLY", 4)
    
    # Assembly Diagram Layout
    # Center X = 200, Y = 165
    ax.text(200, 245, "EXPLODED MECHANICAL STACKUP DIAGRAM", color='#00e5ff', fontsize=11, fontweight='bold', ha='center', family='monospace')
    
    # Component 1: Front Bezel (Left / Top)
    x1, y1 = 70, 160
    ax.add_patch(Rectangle((x1 - 15, y1 - 25), 6, 50, fill=True, facecolor='#1b2a4a', edgecolor='#00e5ff', linewidth=1.2))
    ax.text(x1 - 12, y1 + 32, "1. FRONT BEZEL\nPLATE (4.5mm)", color='#00e5ff', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    
    # Component 2: GC9A01 Screen Module
    x2, y2 = 135, 160
    ax.add_patch(Rectangle((x2 - 3, y2 - 20), 3.1, 40, fill=True, facecolor='#ffd166', edgecolor='#ffbe0b', linewidth=1.2))
    ax.text(x2, y2 + 32, "2. GC9A01 1.28\"\nSCREEN MODULE", color='#ffd166', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    
    # Component 3: Main Housing Pod (26mm)
    x3, y3 = 215, 160
    ax.add_patch(Rectangle((x3 - 15, y3 - 25), 26, 50, fill=True, facecolor='#162032', edgecolor='#4cc9f0', linewidth=1.2))
    # Internal ESP32-C3
    ax.add_patch(Rectangle((x3 - 5, y3 - 8), 12, 16, fill=True, facecolor='#38b000', edgecolor='#55a630', linewidth=1.0))
    ax.text(x3 - 2, y3 + 32, "3. MAIN HOUSING\nPOD (26mm)", color='#4cc9f0', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    ax.text(x3 + 1, y3 - 2, "ESP32-C3\nSUPERMINI", color='#ffffff', fontsize=6, fontweight='bold', ha='center', family='monospace')
    
    # Component 4: Sculpted Desk Stand
    x4, y4 = 320, 125
    ax.add_patch(Polygon([[x4 - 25, y4 - 15], [x4 + 25, y4 - 15], [x4 + 20, y4 + 15], [x4 - 20, y4 + 15]],
                         fill=True, facecolor='#1f2d42', edgecolor='#f72585', linewidth=1.2))
    ax.text(x4, y4 + 25, "4. SCULPTED DESK\nSTAND (22° CRADLE)", color='#f72585', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    
    # Assembly alignment arrows
    for xa in [x1 + 3, x2 + 8, x3 + 20]:
        ax.annotate('', xy=(xa + 25, 160), xytext=(xa + 5, 160),
                    arrowprops=dict(arrowstyle='->', color='#ffffff', lw=1.2, mutation_scale=12, linestyle='--'))
                    
    ax.annotate('', xy=(x4 - 10, y4 + 10), xytext=(x3 + 10, 140),
                arrowprops=dict(arrowstyle='->', color='#f72585', lw=1.2, mutation_scale=12, linestyle='--'))
                
    # Bill of Materials Table (BOM)
    ax.text(20, 95, "HARDWARE BILL OF MATERIALS (BOM):", color='#00e5ff', fontsize=8.5, fontweight='bold', family='monospace')
    bom_text = """
+----+------------------------------------+-----+-------------------------------------------------------------+
| ID | COMPONENT / PART NAME              | QTY | SPECIFICATION & PURPOSE                                     |
+----+------------------------------------+-----+-------------------------------------------------------------+
| 01 | Front Bezel Ring Plate             |  1  | 3D Print (Matte Black PETG) | Ø32.6mm Viewport & Trim Ring  |
| 02 | GC9A01 1.28" Round IPS Module      |  1  | 240x240 Circular Display with 7-Pin SPI Header Bottom Tab  |
| 03 | Main Housing Pod (26mm Depth)      |  1  | 3D Print | DuPont Trench, Pin-Lock Standoffs & USB-C Window |
| 04 | ESP32-C3 SuperMini MCU Board       |  1  | Pin Headers facing UP | Solder pins lock into standoffs     |
| 05 | Sculpted Two-Tier Desk Stand       |  1  | 3D Print (Charcoal / Walnut) | 22° V-Saddle & Cable Channel |
| 06 | Screen Fasteners (M2 x 4mm/6mm)    |  2  | Self-tapping screws into bezel rear blind 1.75mm pilot holes|
| 07 | Enclosure Corner Screws (M2 x 12mm)|  4  | Brass / Black Oxide Socket Head Cap Screws (42mm Bolt Circle|
| 08 | Female-to-Female DuPont Jumpers    |  7  | 10cm SPI Harness (SCL, SDA, CS, DC, RST, BLK, VCC/GND)      |
| 09 | Anti-Slip Silicone Rubber Feet     |  4  | Ø8.0mm x 1.5mm Adhesive Pads for Stand Base Recesses        |
+----+------------------------------------+-----+-------------------------------------------------------------+
"""
    ax.text(20, 22, bom_text, color='#e0e1dd', fontsize=6.2, family='monospace')
    
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 4 Generated]: {output_path}")

def main():
    enclosure_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Generating Professional 300 DPI Engineering Blueprint Technical Drawings...\n")
    
    # Sheet 1: Front Bezel Plate
    s1 = os.path.join(enclosure_dir, "technical_drawings_front_bezel.png")
    generate_sheet_1_front_bezel(s1)
    
    # Sheet 2: Main Housing Pod
    s2 = os.path.join(enclosure_dir, "technical_drawings_main_housing.png")
    generate_sheet_2_main_housing(s2)
    
    # Sheet 3: Sculpted Desk Stand
    s3 = os.path.join(enclosure_dir, "technical_drawings_desk_stand.png")
    generate_sheet_3_desk_stand(s3)
    
    # Sheet 4: Exploded Assembly & BOM
    s4 = os.path.join(enclosure_dir, "technical_drawings_full_assembly.png")
    generate_sheet_4_full_assembly(s4)
    
    print("\n[ALL 4 SHEETS COMPLETE] Technical drawings exported successfully at 300 DPI!")

if __name__ == "__main__":
    main()
