#!/usr/bin/env python3
"""
GC9A01 Cyberdeck Enclosure - Engineering Blueprint & Technical Drawing Generator
Generates publication-quality 300 DPI dimensioned mechanical engineering drawing sheets
for 100% Support-Free FDM 3D Printable Architecture with Chamfered Bezel Trim Ring.
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
    x0, y0, w, h = 250, 10, 160, 35
    rect = Rectangle((x0, y0), w, h, fill=True, facecolor='#0d1b2a', edgecolor='#415a77', linewidth=1.5)
    ax.add_patch(rect)
    
    ax.plot([x0, x0 + w], [y0 + 20, y0 + 20], color='#415a77', linewidth=1)
    ax.plot([x0 + 100, x0 + 100], [y0, y0 + 20], color='#415a77', linewidth=1)
    
    ax.text(x0 + 5, y0 + 26, "TINY AI LIMITS CYBERDECK 01", color='#e0e1dd', fontsize=9, fontweight='bold', family='monospace')
    ax.text(x0 + 5, y0 + 8, f"PART: {sheet_title}", color='#00e5ff', fontsize=8, fontweight='bold', family='monospace')
    ax.text(x0 + 105, y0 + 8, f"SHEET {sheet_num}/{total_sheets}\nSCALE 1:1 [mm]", color='#a9d6e5', fontsize=7, family='monospace')

def setup_blueprint_canvas(figsize=(14, 10), title="ENGINEERING DRAWING"):
    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    fig.patch.set_facecolor('#0b0f19')
    ax.set_facecolor('#0b0f19')
    
    border = Rectangle((5, 5), 410, 287, fill=False, edgecolor='#1b2a4a', linewidth=2)
    inner_border = Rectangle((8, 8), 404, 281, fill=False, edgecolor='#2a3d66', linewidth=1)
    ax.add_patch(border)
    ax.add_patch(inner_border)
    
    for x in range(20, 410, 20):
        ax.axvline(x, color='#141c2e', linewidth=0.5, linestyle=':')
    for y in range(20, 290, 20):
        ax.axhline(y, color='#141c2e', linewidth=0.5, linestyle=':')
        
    ax.set_xlim(0, 420)
    ax.set_ylim(0, 297)
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.text(20, 275, title, color='#ffffff', fontsize=14, fontweight='bold', family='monospace')
    ax.text(20, 267, "PRECISION MECHANICAL SPECIFICATION | ALL UNITS IN MILLIMETERS [MM]", color='#778da9', fontsize=8, family='monospace')
    
    return fig, ax

def add_dim_line(ax, p1, p2, text, offset=6, text_offset=2, is_vertical=False, color='#ff7a00'):
    x1, y1 = p1
    x2, y2 = p2
    
    if is_vertical:
        ax.plot([x1, x1 + offset], [y1, y1], color='#415a77', linewidth=0.8, linestyle='--')
        ax.plot([x2, x2 + offset], [y2, y2], color='#415a77', linewidth=0.8, linestyle='--')
        dim_x = x1 + offset
        ax.annotate('', xy=(dim_x, y1), xytext=(dim_x, y2),
                    arrowprops=dict(arrowstyle='<->', color=color, lw=1.0, mutation_scale=10))
        ax.text(dim_x + text_offset, (y1 + y2)/2, text, color=color, fontsize=8,
                va='center', ha='left', family='monospace', fontweight='bold')
    else:
        ax.plot([x1, x1], [y1, y1 + offset], color='#415a77', linewidth=0.8, linestyle='--')
        ax.plot([x2, x2], [y2, y2 + offset], color='#415a77', linewidth=0.8, linestyle='--')
        dim_y = y1 + offset
        ax.annotate('', xy=(x1, dim_y), xytext=(x2, dim_y),
                    arrowprops=dict(arrowstyle='<->', color=color, lw=1.0, mutation_scale=10))
        ax.text((x1 + x2)/2, dim_y + text_offset, text, color=color, fontsize=8,
                va='bottom', ha='center', family='monospace', fontweight='bold')

def generate_sheet_1_front_bezel(output_path):
    fig, ax = setup_blueprint_canvas(title="PART 1: FRONT BEZEL DISPLAY CARRIER (CHAMFERED TRIM RING)")
    draw_title_block(ax, "FRONT BEZEL CARRIER", 1)
    
    cx, cy = 110, 150
    ax.text(cx, cy - 45, "VIEW A: FRONT EXTERIOR (CHAMFERED RING)", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    hw, c = 27.0, 6.0
    oct_pts = np.array([
        [-hw + c, -hw], [hw - c, -hw],
        [hw, -hw + c],  [hw, hw - c],
        [hw - c, hw],   [-hw + c, hw],
        [-hw, hw - c],  [-hw, -hw + c]
    ]) + [cx, cy]
    ax.add_patch(Polygon(oct_pts, fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.5))
    
    # 45° Chamfered raised decorative bezel ring (Outer dia 44mm base, 41mm top)
    ax.add_patch(Circle((cx, cy), 22.0, fill=False, edgecolor='#4cc9f0', linewidth=0.8, linestyle=':'))
    ax.add_patch(Circle((cx, cy), 20.5, fill=False, edgecolor='#4cc9f0', linewidth=1.2, linestyle='-'))
    
    # Active Screen Aperture
    ax.add_patch(Circle((cx, cy), 16.3, fill=True, facecolor='#060a12', edgecolor='#00e5ff', linewidth=1.5))
    ax.add_patch(Circle((cx, cy), 15.3, fill=False, edgecolor='#5c677d', linewidth=0.8, linestyle=':'))
    
    ax.plot([cx - 32, cx + 32], [cy, cy], color='#5c677d', linewidth=0.6, linestyle='-.')
    ax.plot([cx, cx], [cy - 32, cy + 32], color='#5c677d', linewidth=0.6, linestyle='-.')
    
    for sx in [-21.0, 21.0]:
        for sy in [-21.0, 21.0]:
            ax.add_patch(Circle((cx + sx, cy + sy), 2.4, fill=False, edgecolor='#f72585', linewidth=1.0))
            ax.add_patch(Circle((cx + sx, cy + sy), 1.3, fill=True, facecolor='#060a12', edgecolor='#f72585', linewidth=1.0))
            
    add_dim_line(ax, (cx - 27, cy + 27), (cx + 27, cy + 27), "54.00", offset=10)
    add_dim_line(ax, (cx + 27, cy - 27), (cx + 27, cy + 27), "54.00", offset=10, is_vertical=True)
    add_dim_line(ax, (cx - 21, cy + 21), (cx + 21, cy + 21), "42.00 B.C.", offset=4)
    
    ax.annotate("45° CHAMFERED TRIM RING\nØ44.00 BASE -> Ø41.00 TOP\n(MATCHES CONCEPT RENDER)", xy=(cx + 20.5, cy), xytext=(cx + 35, cy + 12),
                arrowprops=dict(arrowstyle='->', color='#4cc9f0', lw=1.0),
                color='#4cc9f0', fontsize=7.5, family='monospace', fontweight='bold')
    
    ax.annotate("4x M2 COUNTERBORE\nØ4.80 x 2.20 DP\nØ2.60 THRU", xy=(cx + 21, cy + 21), xytext=(cx + 35, cy + 30),
                arrowprops=dict(arrowstyle='->', color='#f72585', lw=1.0),
                color='#f72585', fontsize=7.5, family='monospace', fontweight='bold')

    rx, ry = 240, 150
    ax.text(rx, ry - 45, "VIEW B: REAR DISPLAY CARRIER POCKET", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    ax.add_patch(Polygon(np.array(oct_pts) - [cx, cy] + [rx, ry], fill=True, facecolor='#162032', edgecolor='#415a77', linewidth=1.2))
    ax.add_patch(Circle((rx, ry), 18.1, fill=False, edgecolor='#4cc9f0', linewidth=1.0, linestyle='--'))
    ax.add_patch(Circle((rx, ry), 19.4, fill=True, facecolor='#0f172a', edgecolor='#ffd166', linewidth=1.2))
    ax.add_patch(Rectangle((rx - 11.9, ry - 26.6), 23.8, 26.6, fill=True, facecolor='#0f172a', edgecolor='#ffd166', linewidth=1.2))
    ax.add_patch(Circle((rx, ry), 16.3, fill=True, facecolor='#060a12', edgecolor='#00e5ff', linewidth=1.0))
    
    sh_x, sh_y = 9.63, -18.91
    ax.add_patch(Circle((rx - sh_x, ry + sh_y), 1.75/2, fill=True, facecolor='#ff006e', edgecolor='#ffbe0b', linewidth=1.2))
    ax.add_patch(Circle((rx + sh_x, ry + sh_y), 1.75/2, fill=True, facecolor='#ff006e', edgecolor='#ffbe0b', linewidth=1.2))
    
    add_dim_line(ax, (rx - 11.9, ry - 26.6), (rx + 11.9, ry - 26.6), "23.80 TAB", offset=-8)
    add_dim_line(ax, (rx - sh_x, ry + sh_y), (rx + sh_x, ry + sh_y), "19.26 PITCH", offset=6, color='#ffbe0b')
    
    ax.annotate("2x SCREEN BOLTING HOLES\nØ1.75 BLIND x 3.30 DP\n(NO FRONT THRU-HOLE)", xy=(rx + sh_x, ry + sh_y), xytext=(rx + 25, ry + sh_y - 8),
                arrowprops=dict(arrowstyle='->', color='#ffbe0b', lw=1.0),
                color='#ffbe0b', fontsize=7.5, family='monospace', fontweight='bold')
    
    sx, sy = 355, 150
    ax.text(sx + 5, sy - 45, "SECTION A-A", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')

    
    sec_poly = [
        [sx, sy - 27], [sx + 5.5, sy - 27], [sx + 5.5, sy - 22],
        [sx + 7.0, sy - 20.5], [sx + 7.0, sy + 20.5], [sx + 5.5, sy + 22],
        [sx + 5.5, sy + 27], [sx, sy + 27],
        [sx, sy + 19.3], [sx + 3.2, sy + 19.3], [sx + 3.2, sy + 18.0],
        [sx + 4.4, sy + 18.0], [sx + 4.4, sy + 16.3], [sx + 7.0, sy + 15.3],
        [sx + 7.0, sy - 15.3], [sx + 4.4, sy - 16.3], [sx + 4.4, sy - 18.0],
        [sx + 3.2, sy - 18.0], [sx + 3.2, sy - 26.5], [sx, sy - 26.5]
    ]
    ax.add_patch(Polygon(sec_poly, fill=True, facecolor='#1b2a4a', edgecolor='#00e5ff', linewidth=1.2, hatch='//'))
    
    add_dim_line(ax, (sx, sy + 27), (sx + 5.5, sy + 27), "5.50", offset=8)
    add_dim_line(ax, (sx, sy - 27), (sx + 7.0, sy - 27), "7.00 OAL", offset=-10)
    add_dim_line(ax, (sx, sy + 19.3), (sx + 3.2, sy + 19.3), "3.20 DP", offset=3, color='#ffd166')
    
    ax.text(20, 45, "MANUFACTURING NOTES:\n1. MATERIAL: MATTE BLACK PETG / PLA (0.16mm LAYER HEIGHT, 3 PERIMETERS).\n2. 45° SCULPTED TRIM RING MATCHES ORIGINAL 3D CYBERDECK CONCEPT RENDER.\n3. 100% SUPPORT-FREE: PRINT FLAT ON FRONT FACE (Z=7.0 ON BED). ALL POCKETS STEP OUTWARD.\n4. 2x M2 SCREEN HOLES: 1.75mm BLIND PILOT ACCEPTS M2 SELF-TAPPING SCREWS DIRECTLY.",
            color='#8ecae6', fontsize=7.5, family='monospace', va='top')
            
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 1 Generated]: {output_path}")

def generate_sheet_2_main_housing(output_path):
    fig, ax = setup_blueprint_canvas(title="PART 2: OPEN-TUB MAIN HOUSING (4 SOLID CORNER PILLARS)")
    draw_title_block(ax, "MAIN HOUSING TUB", 2)
    
    cx, cy = 110, 160
    ax.text(cx, cy - 45, "VIEW A: FRONT OPEN TUB & CORNER PILLARS", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    hw, c = 27.0, 6.0
    oct_pts = np.array([
        [-hw + c, -hw], [hw - c, -hw],
        [hw, -hw + c],  [hw, hw - c],
        [hw - c, hw],   [-hw + c, hw],
        [-hw, hw - c],  [-hw, -hw + c]
    ]) + [cx, cy]
    ax.add_patch(Polygon(oct_pts, fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.5))
    
    # Chamfered Cavity (46mm wide, 11.5mm corner chamfers)
    hcw, cc = 23.0, 11.5
    cav_pts = np.array([
        [-hcw + cc, -hcw], [hcw - cc, -hcw],
        [hcw, -hcw + cc],  [hcw, hcw - cc],
        [hcw - cc, hcw],   [-hcw + cc, hcw],
        [-hcw, hcw - cc],  [-hcw, -hcw + cc]
    ]) + [cx, cy]
    ax.add_patch(Polygon(cav_pts, fill=True, facecolor='#0b111e', edgecolor='#4cc9f0', linewidth=1.2))
    
    # DuPont Connector Wire Trench (26mm wide x 5mm deep, Y=-21 to Y=-26)
    ax.add_patch(Rectangle((cx - 13.0, cy - 26.0), 26.0, 5.0, fill=True, facecolor='#0b111e', edgecolor='#ff7b00', linewidth=1.2, linestyle='--'))
    add_dim_line(ax, (cx - 13.0, cy - 26.0), (cx + 13.0, cy - 26.0), "26.00 DUPONT TRENCH", offset=-8, color='#ff7b00')
    
    # Left USB-C Port Cutout
    ax.add_patch(Rectangle((cx - 27.5, cy - 6.5), 6.5, 13, fill=True, facecolor='#060a12', edgecolor='#38b000', linewidth=1.2))
    
    # 4 Corner Screw Pilot Holes (M3 @ +/-19.50mm)
    for sx in [-19.50, 19.50]:
        for sy in [-19.50, 19.50]:
            ax.add_patch(Circle((cx + sx, cy + sy), 1.4, fill=True, facecolor='#060a12', edgecolor='#f72585', linewidth=1.2))
            
    # ESP32-C3 Standoffs
    ax.add_patch(Rectangle((cx - 21.5, cy + 7.62 - 1.7), 23, 3.4, fill=True, facecolor='#1e293b', edgecolor='#a2d2ff', linewidth=1.0))
    ax.add_patch(Rectangle((cx - 21.5, cy - 7.62 - 1.7), 23, 3.4, fill=True, facecolor='#1e293b', edgecolor='#a2d2ff', linewidth=1.0))
    ax.add_patch(Rectangle((cx + 1.5, cy - 9.2), 2.5, 18.4, fill=True, facecolor='#334155', edgecolor='#a2d2ff', linewidth=1.0))
    
    for k in range(8):
        px = cx - 18.3 + k * 2.54
        ax.add_patch(Circle((px, cy + 7.62), 0.75, fill=True, facecolor='#060a12', edgecolor='#ffbe0b', linewidth=0.8))
        ax.add_patch(Circle((px, cy - 7.62), 0.75, fill=True, facecolor='#060a12', edgecolor='#ffbe0b', linewidth=0.8))
        
    add_dim_line(ax, (cx - 23, cy + 23), (cx + 23, cy + 23), "46.00 BAY", offset=4, color='#4cc9f0')
    add_dim_line(ax, (cx - 19.50, cy + 19.50), (cx + 19.50, cy + 19.50), "39.00 B.C.", offset=-6, color='#f72585')
    
    ax.annotate("4x SOLID CORNER PILLARS\nØ2.80 PILOT x 15.0mm DP\n(M3 SOCKET HEAD CAP BOLTS)", xy=(cx + 19.50, cy + 19.50), xytext=(cx + 35, cy + 30),
                arrowprops=dict(arrowstyle='->', color='#f72585', lw=1.0),
                color='#f72585', fontsize=7.5, family='monospace', fontweight='bold')
                
    ax.annotate("ELEVATED USB-C PORT\nZ = 8.25mm CENTERLINE", xy=(cx - 27, cy), xytext=(cx - 48, cy + 18),
                arrowprops=dict(arrowstyle='->', color='#38b000', lw=1.0),
                color='#38b000', fontsize=7.5, family='monospace', fontweight='bold')

    sx, sy = 265, 160
    ax.text(sx + 15, sy - 45, "VIEW B: SECTION B-B (Z-DEPTH PROFILE)", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    sec_housing = [
        [sx, sy - 27], [sx + 27.5, sy - 27], [sx + 27.5, sy - 21],
        [sx + 2.5, sy - 21],
        [sx + 2.5, sy - 9.3], [sx + 5.0, sy - 9.3], [sx + 5.0, sy - 6.0], [sx + 2.5, sy - 6.0],
        [sx + 2.5, sy + 6.0], [sx + 5.0, sy + 6.0], [sx + 5.0, sy + 9.3], [sx + 2.5, sy + 9.3],
        [sx + 2.5, sy + 21], [sx + 27.5, sy + 21], [sx + 27.5, sy + 27], [sx, sy + 27]
    ]
    ax.add_patch(Polygon(sec_housing, fill=True, facecolor='#1b2a4a', edgecolor='#00e5ff', linewidth=1.2, hatch='//'))
    
    add_dim_line(ax, (sx, sy + 27), (sx + 27.5, sy + 27), "27.50 DEPTH", offset=10)
    add_dim_line(ax, (sx, sy - 21), (sx + 2.5, sy - 21), "2.50", offset=-6)
    add_dim_line(ax, (sx + 2.5, sy - 21), (sx + 27.5, sy - 21), "25.00 VERTICAL CAVITY", offset=-6, color='#4cc9f0')
    
    ax.annotate("ESP32-C3 STANDOFFS (2.5mm H)\n16x Ø1.50 PIN REGISTRATION\nREAR THRUST STOP BLOCK", xy=(sx + 5, sy + 7.62), xytext=(sx + 35, sy + 15),
                arrowprops=dict(arrowstyle='->', color='#a2d2ff', lw=1.0),
                color='#a2d2ff', fontsize=7.5, family='monospace', fontweight='bold')
                
    ax.text(20, 45, "MANUFACTURING NOTES:\n1. 100% SUPPORT-FREE FDM ARCHITECTURE: PRINT REAR BACKPLATE FLAT ON BED (Z=0).\n2. 4 MASSIVE SOLID CORNER PILLARS RUN CONTINUOUSLY FROM FLOOR TO TOP RIM.\n3. 4x M3 PILOT HOLES (Ø2.8mm x 15mm DP) AT (+/-19.5, +/-19.5) FOR M3 BOLTS OR HEAT-SET INSERTS.\n4. DUPONT TRENCH (26.0 x 25.0mm) PROVIDES 100% UNOBSTRUCTED CONNECTOR & WIRE ROUTING CLEARANCE.",
            color='#8ecae6', fontsize=7.5, family='monospace', va='top')

            
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 2 Generated]: {output_path}")

def generate_sheet_3_desk_stand(output_path):
    fig, ax = setup_blueprint_canvas(title="PART 3: SCULPTED TWO-TIER DESK STAND (GC9A01-STAND-01)")
    draw_title_block(ax, "DESK STAND CRADLE", 3)
    
    cx, cy = 110, 160
    ax.text(cx, cy - 45, "VIEW A: TOP CRADLE FOOTPRINT", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    base_box = FancyBboxPatch((cx - 32, cy - 34), 64, 68, boxstyle="round,pad=0,rounding_size=6",
                               fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.5)
    ax.add_patch(base_box)
    
    # Stand trunk top profile (54x58)
    ax.add_patch(FancyBboxPatch((cx - 27, cy - 29), 54, 58, boxstyle="round,pad=0,rounding_size=3.5",
                                fill=True, facecolor='#1f2d42', edgecolor='#4cc9f0', linewidth=1.0))
    # Deep V-saddle cradle slot (54.8mm wide x 34.2mm depth)
    ax.add_patch(Rectangle((cx - 27.4, cy - 17.1), 54.8, 34.2, fill=True, facecolor='#0b111e', edgecolor='#ffd166', linewidth=1.5))
    
    for fx in [-22, 22]:
        for fy in [-24, 24]:
            ax.add_patch(Circle((cx + fx, cy + fy), 4.1, fill=False, edgecolor='#a2d2ff', linewidth=0.8, linestyle='--'))
            
    add_dim_line(ax, (cx - 32, cy + 34), (cx + 32, cy + 34), "64.00 BASE WIDTH", offset=8)
    add_dim_line(ax, (cx + 32, cy - 34), (cx + 32, cy + 34), "68.00 BASE DEPTH", offset=8, is_vertical=True)
    add_dim_line(ax, (cx - 27.4, cy - 17.1), (cx + 27.4, cy - 17.1), "54.80 SLOT W", offset=-8, color='#ffd166')
    add_dim_line(ax, (cx + 27.4, cy - 17.1), (cx + 27.4, cy + 17.1), "34.20 SLOT D", offset=4, is_vertical=True, color='#ffd166')

    sx, sy = 275, 160
    ax.text(sx, sy - 45, "VIEW B: SIDE ELEVATION & 22° CRADLE", color='#00e5ff', fontsize=10, fontweight='bold', ha='center', family='monospace')
    
    ax.add_patch(Rectangle((sx - 34, sy - 15), 68, 5, fill=True, facecolor='#162032', edgecolor='#00e5ff', linewidth=1.2))
    
    stand_side_pts = [
        [sx - 31, sy - 10], [sx + 31, sy - 10],
        [sx + 27, sy + 14],
        [sx + 7, sy + 14],
        [sx - 15, sy + 2],
        [sx - 22, sy + 9],
        [sx - 27, sy - 10]
    ]
    ax.add_patch(Polygon(stand_side_pts, fill=True, facecolor='#1f2d42', edgecolor='#4cc9f0', linewidth=1.5))
    
    ax.annotate("22.0° ERGONOMIC TILT\n54.8 x 34.2mm SLIDING CRADLE\n12.0mm SEATING POCKET", xy=(sx - 6, sy + 6), xytext=(sx + 8, sy + 25),
                arrowprops=dict(arrowstyle='->', color='#ffd166', lw=1.2),
                color='#ffd166', fontsize=7.5, family='monospace', fontweight='bold')
                
    add_dim_line(ax, (sx + 34, sy - 15), (sx + 34, sy + 14), "29.00 TOTAL H", offset=10, is_vertical=True)
    add_dim_line(ax, (sx - 34, sy - 15), (sx - 34, sy - 10), "5.00 TIER 1", offset=-8, is_vertical=True)
    add_dim_line(ax, (sx - 34, sy - 10), (sx - 34, sy + 14), "24.00 TRUNK H", offset=-8, is_vertical=True, color='#4cc9f0')
    
    ax.text(20, 45, "MANUFACTURING NOTES:\n1. 22° V-SADDLE CRADLE OFFERS OPTIMAL DESKTOP VIEWING ANGLE WITH ZERO WOBBLE.\n2. 54.8 x 34.2mm CRADLE SLOT ACCOMMODATES FULL ASSEMBLED 33.0mm POD (BEZEL + BODY) WITH 1.2mm CLEARANCE.\n3. TIER 1 BASE (5mm) CAN BE PRINTED IN DUAL MATERIAL / WOOD PLA AS A SEPARATE ACCENT PLATE.\n4. 4x UNDERSIDE RECESSES (Ø8.2mm x 1.5mm DP) FIT STANDARD ADHESIVE SILICONE FEET.",
            color='#8ecae6', fontsize=7.5, family='monospace', va='top')
            
    fig.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[Sheet 3 Generated]: {output_path}")

def generate_sheet_4_full_assembly(output_path):
    fig, ax = setup_blueprint_canvas(title="PART 4: COMPLETE EXPLODED ASSEMBLY & HARDWARE STACKUP")
    draw_title_block(ax, "EXPLODED ASSEMBLY", 4)
    
    ax.text(200, 245, "EXPLODED MECHANICAL STACKUP DIAGRAM", color='#00e5ff', fontsize=11, fontweight='bold', ha='center', family='monospace')
    
    x1, y1 = 70, 160
    ax.add_patch(Rectangle((x1 - 15, y1 - 25), 7, 50, fill=True, facecolor='#1b2a4a', edgecolor='#00e5ff', linewidth=1.2))
    ax.text(x1 - 12, y1 + 32, "1. FRONT BEZEL\nCARRIER (5.5mm)", color='#00e5ff', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    
    x2, y2 = 135, 160
    ax.add_patch(Rectangle((x2 - 3, y2 - 20), 3.1, 40, fill=True, facecolor='#ffd166', edgecolor='#ffbe0b', linewidth=1.2))
    ax.text(x2, y2 + 32, "2. GC9A01 1.28\"\nSCREEN MODULE", color='#ffd166', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    
    x3, y3 = 215, 160
    ax.add_patch(Rectangle((x3 - 15, y3 - 25), 27.5, 50, fill=True, facecolor='#162032', edgecolor='#4cc9f0', linewidth=1.2))
    ax.add_patch(Rectangle((x3 - 5, y3 - 8), 12, 16, fill=True, facecolor='#38b000', edgecolor='#55a630', linewidth=1.0))
    ax.text(x3 - 2, y3 + 32, "3. MAIN HOUSING\nOPEN TUB (27.5mm)", color='#4cc9f0', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    ax.text(x3 + 1, y3 - 2, "ESP32-C3\nSUPERMINI", color='#ffffff', fontsize=6, fontweight='bold', ha='center', family='monospace')

    
    x4, y4 = 320, 125
    ax.add_patch(Polygon([[x4 - 25, y4 - 15], [x4 + 25, y4 - 15], [x4 + 20, y4 + 15], [x4 - 20, y4 + 15]],
                         fill=True, facecolor='#1f2d42', edgecolor='#f72585', linewidth=1.2))
    ax.text(x4, y4 + 25, "4. SCULPTED DESK\nSTAND (22° CRADLE)", color='#f72585', fontsize=7.5, fontweight='bold', ha='center', family='monospace')
    
    for xa in [x1 + 3, x2 + 8, x3 + 20]:
        ax.annotate('', xy=(xa + 25, 160), xytext=(xa + 5, 160),
                    arrowprops=dict(arrowstyle='->', color='#ffffff', lw=1.2, mutation_scale=12, linestyle='--'))
                    
    ax.annotate('', xy=(x4 - 10, y4 + 10), xytext=(x3 + 10, 140),
                arrowprops=dict(arrowstyle='->', color='#f72585', lw=1.2, mutation_scale=12, linestyle='--'))
                
    ax.text(20, 95, "HARDWARE BILL OF MATERIALS (BOM):", color='#00e5ff', fontsize=8.5, fontweight='bold', family='monospace')
    bom_text = """
+----+------------------------------------+-----+-------------------------------------------------------------+
| ID | COMPONENT / PART NAME              | QTY | SPECIFICATION & PURPOSE                                     |
+----+------------------------------------+-----+-------------------------------------------------------------+
| 01 | Front Bezel Display Carrier Plate  |  1  | 3D Print (Matte Black PETG) | 45° Chamfered Trim Ring       |
| 02 | GC9A01 1.28" Round IPS Module      |  1  | 240x240 Circular Display with 7-Pin SPI Header Bottom Tab  |
| 03 | Main Housing Pod (Open Tub Bucket) |  1  | 3D Print | 4 Solid Corner Pillars & 4x M2 Pilot Holes       |
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
    
    print("Generating 100% Support-Free 300 DPI Engineering Blueprint Technical Drawings...\n")
    
    s1 = os.path.join(enclosure_dir, "technical_drawings_front_bezel.png")
    generate_sheet_1_front_bezel(s1)
    
    s2 = os.path.join(enclosure_dir, "technical_drawings_main_housing.png")
    generate_sheet_2_main_housing(s2)
    
    s3 = os.path.join(enclosure_dir, "technical_drawings_desk_stand.png")
    generate_sheet_3_desk_stand(s3)
    
    s4 = os.path.join(enclosure_dir, "technical_drawings_full_assembly.png")
    generate_sheet_4_full_assembly(s4)
    
    print("\n[ALL 4 SHEETS COMPLETE] Technical drawings exported successfully at 300 DPI!")

if __name__ == "__main__":
    main()
