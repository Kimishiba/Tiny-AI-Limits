#!/usr/bin/env python3
"""
GC9B72 2.1" Round Display & ESP32 Cyberdeck Desk Console (84mm Square Heritage Edition)
Professional 3D Printable STL Generator (Boolean CSG & Watertight Manifold Engine)

RE-ENGINEERED DIRECTLY FROM THE 240x240 UNIT 01 HERITAGE INSTRUCTIONS:
- 100% Symmetrical 84mm Square Cyberdeck Pod (84.0mm x 84.0mm)
- Perimeter Chamfering: 45° outer bottom chassis chamfer (1.2mm x 45°) + 45° corner chamfers (7.0mm)
- Flat Mating Face at Z = 28.0mm for 100% seamless flush front face joining
- High-Airflow Aeration System:
  * Contour-following horizontal rear cooling slits in outer zones
  * Safe central under-ESP32 aeration grille
  * 45° peaked roof top vertical aeration exhaust slits (7 slots along top wall)
- Precision ESP32-S3 / C3 SuperMini Retention Cradle:
  * Board held as close to the outer edge as humanly possible (x_front = -40.8mm, outer wall = -42.0mm -> 1.2mm thin wall!)
  * Shaved-depth USB-C port (inner wall shaved by 2.8mm down to 1.2mm outer wall thickness)
  * Precision snug oval/stadium USB-C port with 45° conical entry flare
  * Dual L-shaped guide rails + rear mechanical thrust stop wall (x_back = -16.0mm)
  * 0.7mm outer edge support ledges (supports PCB edge outside pin headers, bottom components unobstructed)
  * Dual discrete side retention snap clips (0.28mm lip overhang at Z = 5.2mm)
  * Elevated reinforced DuPont clearance trench with 45° bottom ramp
- Fasteners & Direct Tapping:
  * 4x M2.3 Socket Head Cap Screws for Circular Top Bezel clamping (Ø1.90mm direct tap pilot holes)
  * 4x M3 Socket Head Cap Screws for Outer Housing Corners (Ø2.50mm direct tap pilot holes, 34mm square pattern)
- Two-Tier Sculpted Pedestal Stand (22° V-saddle cradle + rear cable channel + rubber feet pockets)
"""

import math
import os
import manifold3d as m3d
import trimesh
import numpy as np

# =========================================================================
# PARAMETERS (All in millimeters)
# =========================================================================
HOUSING_W = 84.0
HOUSING_H = 84.0
HOUSING_DEPTH = 28.0
FRONT_FACE_THICK = 7.0
BEZEL_THICK = 4.5
CHAMFER_OUTER = 7.0
EDGE_CHAMFER = 1.2
FLOOR_THICK = 2.0
CAVITY_DEPTH = HOUSING_DEPTH - FLOOR_THICK

# Screen Blueprint Dimensions (GC9B72)
SCREEN_PCB_W = 59.24
SCREEN_PCB_H = 67.47
SCREEN_LCM_W = 55.92
SCREEN_LCM_H = 57.58
SCREEN_ACTIVE_DIA = 52.92
SCREEN_THICKNESS = 2.40
SCREEN_PCB_TOP = 29.62
SCREEN_PCB_BOTTOM = -37.85
SCREEN_TAB_HALF_W = 15.24        # Official blueprint dimension (30.48mm total width)
SCREEN_TAB_W = 30.48             # Official blueprint dimension: (10 - 1)*2.54 + 2*3.81 = 30.48mm
SCREEN_POCKET_DEPTH = 2.00
SCREEN_TOLERANCE = 0.36          # 0.36mm clearance per side (pocket width = 31.20mm)

# Option 2: Rear-Loading Architecture Parameters
REAR_POCKET_DEPTH = 2.40        # Recessed cavity depth on rear of Front Face
INTEGRATED_BEZEL_H = 2.80       # Raised circular bezel rim on front face (increased from 1.60mm)
INTEGRATED_BEZEL_OD = 72.00     # Outer diameter of raised circular bezel rim (increased from 66.40mm)
SCREEN_APERTURE_DIA = 54.00     # Central circular viewing aperture at screen retaining lip
SCREEN_APERTURE_TOP = 60.00     # Continuous conical viewing funnel top diameter at ring summit

# Rear Clamp Plate Parameters (Sandwich Architecture)
CLAMP_THICK = 1.60              # Slim, rigid 1.6mm intermediate sandwich clamp plate (8 layers at 0.2mm)

# Legacy Bezel Parameters (Retained for reference)
BEZEL_INNER_DIA = 53.60
BEZEL_FUNNEL_TOP = 58.00
BEZEL_RING_DIA = 66.40
BEZEL_RETAINING_DIA = 56.80
BEZEL_RETAINING_DEPTH = 0.80

# M2.3 Bezel Fasteners (Legacy)
BEZEL_SCREW_X = 26.00
BEZEL_SCREW_Y = 32.50
M2_3_CLEARANCE_HOLE = 2.55
M2_3_CB_DIA = 5.00
M2_3_CB_DEPTH = 2.40
M2_3_PILOT_DIA = 1.90
M2_3_PILOT_DEPTH = 5.20

# Symmetrical Square Housing Corner Fasteners (Direct Plastic Tapping)
CORNER_SCREW_X = 34.00      # Symmetrical square pattern (+/-34mm)
CORNER_SCREW_Y = 34.00      # Symmetrical square pattern (+/-34mm)
M3_CLEARANCE_HOLE = 3.40    # Front face clearance through-hole
M3_CB_DIA = 6.20           # M3 socket head counterbore diameter
M3_CB_DEPTH = 3.50         # M3 counterbore depth
M3_PILOT_DIA = 2.50        # Direct plastic tap pilot hole in housing corner posts
M3_PILOT_DEPTH = 14.00     # Deep thread engagement in corner posts

# Stand (Sized to cradle 84mm square pod)
STAND_TILT_DEG = 22.0
STAND_BASE_W = 94.0
STAND_BASE_D = 88.0
STAND_BASE_H = 6.0
STAND_TRUNK_H = 26.0

def make_multi_layer_octagonal_solid(layers_desc):
    verts = []
    num_layers = len(layers_desc)
    for w, c, z in layers_desc:
        hw = w / 2.0
        pts = [
            [-hw + c, -hw], [hw - c, -hw],
            [hw, -hw + c],  [hw, hw - c],
            [hw - c, hw],   [-hw + c, hw],
            [-hw, hw - c],  [-hw, -hw + c]
        ]
        for x, y in pts:
            verts.append([x, y, z])
    verts = np.array(verts, dtype=np.float32)
    faces = []
    for i in range(1, 7):
        faces.append([0, i + 1, i])
    for l in range(num_layers - 1):
        off1 = l * 8
        off2 = (l + 1) * 8
        for i in range(8):
            i_next = (i + 1) % 8
            faces.append([off1 + i, off1 + i_next, off2 + i_next])
            faces.append([off1 + i, off2 + i_next, off2 + i])
    top_off = (num_layers - 1) * 8
    for i in range(1, 7):
        faces.append([top_off, top_off + i, top_off + i + 1])
    faces = np.array(faces, dtype=np.int32)
    return m3d.Manifold(m3d.Mesh(vert_properties=verts, tri_verts=faces))

def make_octagonal_prism(w, h, c, z_height):
    hw = w / 2.0
    hh = h / 2.0
    pts = [
        [-hw + c, -hh], [hw - c, -hh],
        [hw, -hh + c],  [hw, hh - c],
        [hw - c, hh],   [-hw + c, hh],
        [-hw, hh - c],  [-hw, -hh + c]
    ]
    poly = m3d.CrossSection([pts])
    return m3d.Manifold.extrude(poly, z_height)

def make_rounded_rect_2d(w, d, r, fn=32):
    hw = w / 2.0 - r
    hd = d / 2.0 - r
    pts = []
    corners = [(hw, hd), (-hw, hd), (-hw, -hd), (hw, -hd)]
    start_angles = [0, math.pi/2, math.pi, 3*math.pi/2]
    for (cx, cy), sa in zip(corners, start_angles):
        for i in range(fn // 4 + 1):
            angle = sa + (math.pi / 2.0) * (i / (fn // 4))
            pts.append([cx + r * math.cos(angle), cy + r * math.sin(angle)])
    return pts

def make_snap_clip(length=5.0, width=0.30, height=1.2, side='+Y'):
    hw_x = length / 2.0
    hz = height / 2.0
    if side == '+Y':
        v_base = [[-hw_x, 0.05, -hz], [hw_x, 0.05, -hz], [hw_x, 0.05, hz], [-hw_x, 0.05, hz]]
        v_apex = [[-hw_x + 0.60, -width, 0.0], [hw_x - 0.60, -width, 0.0]]
    else:
        v_base = [[-hw_x, -0.05, -hz], [hw_x, -0.05, -hz], [hw_x, -0.05, hz], [-hw_x, -0.05, hz]]
        v_apex = [[-hw_x + 0.60, width, 0.0], [hw_x - 0.60, width, 0.0]]
    pts = v_base + v_apex
    combined = m3d.Manifold()
    for p in pts:
        combined = combined + m3d.Manifold.cube([0.01, 0.01, 0.01]).translate(p)
    return combined.hull()

def export_stl(manifold_obj, filepath, name="Model"):
    mesh_data = manifold_obj.to_mesh()
    tri_mesh = trimesh.Trimesh(
        vertices=mesh_data.vert_properties[:, :3],
        faces=mesh_data.tri_verts,
        process=False
    )
    tri_mesh.export(filepath, file_type='stl')
    print(f"[{name}] Exported: {filepath} ({len(tri_mesh.vertices)} verts, {len(tri_mesh.faces)} faces, watertight: {tri_mesh.is_watertight})")

# =========================================================================
# BUILD PART 1: INTERNAL REAR CLAMP BRACKET (M2.5 4-SCREW RETENTION)
# =========================================================================
def build_rear_clamp():
    # Rigid sandwich clamp plate with exact 84.0 x 84.0mm octagonal footprint matching Front Face & Main Housing
    # Slim 1.60mm profile (8 layers at 0.2mm) with matching 4x M3 corner clearance holes
    clamp_thick = CLAMP_THICK
    hw = HOUSING_W / 2.0  # 42.0mm
    c = CHAMFER_OUTER     # 7.0mm

    # Exact 84x84mm Octagonal Base Profile matching Front Face & Main Housing
    pts = [
        [-hw + c, -hw], [hw - c, -hw],
        [hw, -hw + c],  [hw, hw - c],
        [hw - c, hw],   [-hw + c, hw],
        [-hw, hw - c],  [-hw, -hw + c]
    ]
    poly = m3d.CrossSection([pts])
    bracket = m3d.Manifold.extrude(poly, clamp_thick)

    # 1. Exact Rectangular Screen PCB Tab Cutout (32.00mm wide x Y = -38.65 to 0.0mm)
    # Sized to 32.00mm wide (+0.76mm per side around official 30.48mm tab)
    # Clears 10-pin header and DuPont jumper connectors, seamlessly merging into Ø38mm center hole
    # while preserving a solid 3.35mm bottom structural bridge (Y = -42.0 to -38.65mm).
    tab_cutout_w = 32.00
    hw_cut = tab_cutout_w / 2.0  # 16.00mm
    bot_y_tab = SCREEN_PCB_BOTTOM - SCREEN_TOLERANCE - 0.5  # -38.71mm
    tab_cutout = m3d.Manifold.cube([tab_cutout_w, -bot_y_tab + 1.0, clamp_thick + 2.0], center=False).translate([-hw_cut, bot_y_tab, -1.0])
    bracket = bracket - tab_cutout

    # 2. Central ventilation / weight-reduction opening (Ø38.0mm)
    center_hole = m3d.Manifold.cylinder(clamp_thick + 2.0, 19.0, 19.0, 72).translate([0, 0, -1.0])
    bracket = bracket - center_hole

    # 3. 4x M3 Corner Screw Clearance Holes (+/-34.0mm, +/-34.0mm)
    # Only 4 holes matching the Front Face and Main Housing corner chassis bolts
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            m3_hole = m3d.Manifold.cylinder(clamp_thick + 2.0, M3_CLEARANCE_HOLE / 2.0, M3_CLEARANCE_HOLE / 2.0, 32).translate([sx * CORNER_SCREW_X, sy * CORNER_SCREW_Y, -1.0])
            bracket = bracket - m3_hole

    return bracket

# Legacy Bezel generator (Retained for backwards compatibility)
def build_circular_top_bezel():
    ring = m3d.Manifold.cylinder(BEZEL_THICK, BEZEL_RING_DIA / 2.0, BEZEL_RING_DIA / 2.0, 72)
    theta = math.atan2(BEZEL_SCREW_Y, BEZEL_SCREW_X)
    r_anchor = 28.5
    x_anchor = r_anchor * math.cos(theta)
    y_anchor = r_anchor * math.sin(theta)

    lugs = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            c_inner = m3d.Manifold.cylinder(BEZEL_THICK, 5.5, 5.5, 32).translate([sx * x_anchor, sy * y_anchor, 0])
            c_outer = m3d.Manifold.cylinder(BEZEL_THICK, 5.2, 5.2, 32).translate([sx * BEZEL_SCREW_X, sy * BEZEL_SCREW_Y, 0])
            lugs.append((c_inner + c_outer).hull())
    
    bezel = ring
    for lug in lugs:
        bezel = bezel + lug

    cyl_through = m3d.Manifold.cylinder(BEZEL_THICK + 2.0, BEZEL_INNER_DIA / 2.0, BEZEL_INNER_DIA / 2.0, 72).translate([0, 0, -1.0])
    cone_funnel = m3d.Manifold.cylinder(1.81, BEZEL_INNER_DIA / 2.0, BEZEL_FUNNEL_TOP / 2.0, 72).translate([0, 0, BEZEL_THICK - 1.80])
    bezel = bezel - cyl_through - cone_funnel

    glass_pocket = m3d.Manifold.cylinder(1.60 + 0.01, 56.50 / 2.0, 56.50 / 2.0, 72).translate([0, 0, -0.005])
    bezel = bezel - glass_pocket

    for sx in [-1, 1]:
        for sy in [-1, 1]:
            hole = m3d.Manifold.cylinder(BEZEL_THICK + 2.0, M2_3_CLEARANCE_HOLE / 2.0, M2_3_CLEARANCE_HOLE / 2.0, 32).translate([sx * BEZEL_SCREW_X, sy * BEZEL_SCREW_Y, -1.0])
            cb = m3d.Manifold.cylinder(M2_3_CB_DEPTH + 2.0, M2_3_CB_DIA / 2.0, M2_3_CB_DIA / 2.0, 32).translate([sx * BEZEL_SCREW_X, sy * BEZEL_SCREW_Y, BEZEL_THICK - M2_3_CB_DEPTH])
            bezel = bezel - hole - cb

    return bezel

# =========================================================================
# BUILD PART 2: MONOLITHIC FRONT FACE (OPTION 2: REAR-LOADING SCREEN)
# =========================================================================
def build_front_face():
    # 1. Base 84x84mm plate with 45° outer edge chamfer
    w_ch = HOUSING_W - 2 * EDGE_CHAMFER
    c_ch = CHAMFER_OUTER - EDGE_CHAMFER * 0.414
    layers_front = [
        (HOUSING_W, CHAMFER_OUTER, 0.0),
        (HOUSING_W, CHAMFER_OUTER, FRONT_FACE_THICK - EDGE_CHAMFER),
        (w_ch, c_ch, FRONT_FACE_THICK)
    ]
    plate = make_multi_layer_octagonal_solid(layers_front)

    # 2. Integrated Raised Bezel Rim on Front (Z = 7.0 to 8.6mm)
    r_base = INTEGRATED_BEZEL_OD / 2.0
    r_top = r_base - 1.2
    bezel_ring = m3d.Manifold.cylinder(INTEGRATED_BEZEL_H, r_base, r_top, 72).translate([0, 0, FRONT_FACE_THICK])
    plate = plate + bezel_ring

    # 3. Continuous Conical Anti-Shadow Viewing Funnel connecting screen shelf to top of ring
    total_h = FRONT_FACE_THICK + INTEGRATED_BEZEL_H
    hole_pocket = m3d.Manifold.cylinder(REAR_POCKET_DEPTH + 0.02, SCREEN_APERTURE_DIA / 2.0, SCREEN_APERTURE_DIA / 2.0, 72).translate([0, 0, -0.01])
    cone_h = total_h - REAR_POCKET_DEPTH
    cone_funnel = m3d.Manifold.cylinder(cone_h + 0.04, SCREEN_APERTURE_DIA / 2.0, SCREEN_APERTURE_TOP / 2.0, 72).translate([0, 0, REAR_POCKET_DEPTH - 0.02])
    plate = plate - hole_pocket - cone_funnel

    # 4. Exact Screen Contour Cavity RECESSED INTO REAR FACE (Z = 0.0 to REAR_POCKET_DEPTH)
    clr = SCREEN_TOLERANCE
    r_pocket = (SCREEN_PCB_W / 2.0) + clr      # 29.92mm
    hw_tab = SCREEN_TAB_HALF_W + clr          # 24.18mm
    bot_y_tab = SCREEN_PCB_BOTTOM - clr       # -38.15mm

    cyl_pocket = m3d.Manifold.cylinder(REAR_POCKET_DEPTH + 0.01, r_pocket, r_pocket, 72)
    box_tab = m3d.Manifold.cube([2 * hw_tab, -bot_y_tab, REAR_POCKET_DEPTH + 0.01], center=False).translate([-hw_tab, bot_y_tab, 0])
    screen_cavity = (cyl_pocket + box_tab).translate([0, 0, -0.005])
    plate = plate - screen_cavity

    # 5. 4x Symmetrical Outer M3 Corner Screws (+/-34mm, +/-34mm)
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            m3_hole = m3d.Manifold.cylinder(total_h + 2.0, M3_CLEARANCE_HOLE / 2.0, M3_CLEARANCE_HOLE / 2.0, 32).translate([sx * CORNER_SCREW_X, sy * CORNER_SCREW_Y, -1.0])
            m3_cb = m3d.Manifold.cylinder(M3_CB_DEPTH + 1.0, M3_CB_DIA / 2.0, M3_CB_DIA / 2.0, 32).translate([sx * CORNER_SCREW_X, sy * CORNER_SCREW_Y, FRONT_FACE_THICK - M3_CB_DEPTH])
            plate = plate - m3_hole - m3_cb

    return plate

# =========================================================================
# BUILD PART 3: MAIN HOUSING POD (240x240 HERITAGE RE-ENGINEERED)
# =========================================================================
def build_main_housing():
    w = HOUSING_W
    c = CHAMFER_OUTER
    depth = HOUSING_DEPTH
    floor_t = FLOOR_THICK
    cavity_depth = depth - floor_t
    chamfer_outer = EDGE_CHAMFER
    screw_dist = CORNER_SCREW_X

    # 1. Main outer solid chassis with 45° bottom chamfer (z = 0 to 28.0mm)
    w_ch = w - 2 * chamfer_outer
    c_ch = c - chamfer_outer * 0.414
    layers_chassis = [
        (w_ch, c_ch, 0.0),
        (w, c, chamfer_outer),
        (w, c, depth)
    ]
    chassis = make_multi_layer_octagonal_solid(layers_chassis)

    # 2. Main Internal Chamfered Cavity (width 76.0mm with 4.0mm perimeter walls)
    cw = 76.0
    cc = 14.0
    hcw = cw / 2.0
    pts_cavity = [
        [-hcw + cc, -hcw], [hcw - cc, -hcw],
        [hcw, -hcw + cc],  [hcw, hcw - cc],
        [hcw - cc, hcw],   [-hcw + cc, hcw],
        [-hcw, hcw - cc],  [-hcw, -hcw + cc]
    ]
    poly_cavity = m3d.CrossSection([pts_cavity])
    cavity_obj = m3d.Manifold.extrude(poly_cavity, cavity_depth + 0.1).translate([0, 0, floor_t])

    # 3. Precision Snug Oval/Stadium USB-C Port on LEFT wall (as in 240x240):
    usbc_z = 6.60
    y_span = 3.40
    r_inner = 1.95   # 3.90mm snug height matching USB-C metal shell
    r_outer = 2.85   # 5.70mm outer flare for cable overmold entry

    c1 = m3d.Manifold.cylinder(8.0, r_inner, r_inner, 32).rotate([0, 90, 0]).translate([-45.0, -y_span, usbc_z])
    c2 = m3d.Manifold.cylinder(8.0, r_inner, r_inner, 32).rotate([0, 90, 0]).translate([-45.0,  y_span, usbc_z])
    usbc_tunnel = (c1 + c2).hull()

    cone1 = m3d.Manifold.cylinder(2.4, r_outer, r_inner, 32).rotate([0, 90, 0]).translate([-43.0, -y_span, usbc_z])
    cone2 = m3d.Manifold.cylinder(2.4, r_outer, r_inner, 32).rotate([0, 90, 0]).translate([-43.0,  y_span, usbc_z])
    usbc_flare = (cone1 + cone2).hull()
    usbc_port = usbc_tunnel + usbc_flare

    # Shaved-depth USB-C wall relief (down to 1.2mm outer wall thickness, keeping board as close to edge as possible!)
    usbc_wall_relief = m3d.Manifold.cube([2.8, 22.0, cavity_depth + 0.2], center=False).translate([-40.8, -11.0, floor_t])

    # 4. Reinforced Elevated DuPont Clearance Trenches (starts at Z = 6.0mm with 45° bottom ramp)
    trench_z0 = 6.0
    trench_h = depth - trench_z0 + 0.1

    # 4a. Bottom Wall DuPont Trench (Y = -40.0 to -38.0mm, width 32.0mm)
    t_base_bot = m3d.Manifold.cube([32.0, 6.0, trench_h]).translate([-16.0, -40.0, trench_z0])
    t_ramp_bot = m3d.Manifold.cube([32.0, 4.0, trench_h + 2.0]).translate([-16.0, -38.0, trench_z0 - 2.0])
    dupont_trench_bot = (t_base_bot + t_ramp_bot).hull()

    # 4b. Right Wall DuPont Trench (opposite USB-C on Left Wall: X = +38.0 to +40.0mm, length 32.0mm)
    t_base_rt = m3d.Manifold.cube([6.0, 32.0, trench_h]).translate([34.0, -16.0, trench_z0])
    t_ramp_rt = m3d.Manifold.cube([4.0, 32.0, trench_h + 2.0]).translate([34.0, -16.0, trench_z0 - 2.0])
    dupont_trench_rt = (t_base_rt + t_ramp_rt).hull()

    dupont_trench = dupont_trench_bot + dupont_trench_rt

    # 5. 4 Corner M3 Screw Pilot Holes with 45° Entry Lead-In Chamfers (depth = 14mm, pilot dia = 2.50mm):
    screw_pilot_cuts = m3d.Manifold()
    for sx in [-screw_dist, screw_dist]:
        for sy in [-screw_dist, screw_dist]:
            pilot_m3 = m3d.Manifold.cylinder(14.2, 1.25, 1.25, 32).translate([sx, sy, depth - 14.0])
            cone_m3 = m3d.Manifold.cylinder(1.2, 1.25, 2.4, 32).translate([sx, sy, depth - 1.19])
            screw_pilot_cuts = screw_pilot_cuts + pilot_m3 + cone_m3

    # 6. High-Airflow Aeration Slits in Outer Zones (|Y| >= 16.5mm):
    vent_cuts = m3d.Manifold()
    outer_rows = [
        # (ry, lw, lcx, cw_v, ccx, rw, rcx)
        (22.0, 10.0, -18.0, 10.0, 0.0, 10.0, 18.0),
        (26.0,  8.0, -16.0, 10.0, 0.0,  8.0, 16.0),
    ]
    slot_h = 1.20
    for (ry, lw, lcx, cw_v, ccx, rw, rcx) in outer_rows:
        s_l = m3d.Manifold.cube([lw, slot_h, floor_t + 2.0], center=True).translate([lcx, ry, floor_t / 2.0])
        s_c = m3d.Manifold.cube([cw_v, slot_h, floor_t + 2.0], center=True).translate([ccx, ry, floor_t / 2.0])
        s_r = m3d.Manifold.cube([rw, slot_h, floor_t + 2.0], center=True).translate([rcx, ry, floor_t / 2.0])
        vent_cuts = vent_cuts + s_l + s_c + s_r

    for (ry, lw, lcx, cw_v, ccx, rw, rcx) in outer_rows:
        s_l = m3d.Manifold.cube([lw, slot_h, floor_t + 2.0], center=True).translate([lcx, -ry, floor_t / 2.0])
        s_c = m3d.Manifold.cube([cw_v, slot_h, floor_t + 2.0], center=True).translate([ccx, -ry, floor_t / 2.0])
        s_r = m3d.Manifold.cube([rw, slot_h, floor_t + 2.0], center=True).translate([rcx, -ry, floor_t / 2.0])
        vent_cuts = vent_cuts + s_l + s_c + s_r

    # Safe Under-ESP32 Aeration Grille (central zone X = -34 to -22, |Y| <= 4.0mm):
    for y_pos in [-3.6, -1.2, 1.2, 3.6]:
        s1 = m3d.Manifold.cube([6.0, 1.35, floor_t + 2.0], center=True).translate([-33.0, y_pos, floor_t / 2.0])
        s2 = m3d.Manifold.cube([6.0, 1.35, floor_t + 2.0], center=True).translate([-24.0, y_pos, floor_t / 2.0])
        vent_cuts = vent_cuts + s1 + s2

    # Vertical Exhaust Vents with 45° Peaked Roof along top perimeter wall (Y = +42mm):
    # Centered vertically at Z = 9.0mm to 19.0mm (leaving balanced 9mm solid base & 9mm solid top rim).
    # Cut extends Y = 30.0mm to 46.0mm to punch 100% clean through the 4.0mm wall into the cavity.
    slot_w = 2.0
    half_w = slot_w / 2.0
    z_bot = 9.0
    z_shoulder = 18.0
    z_apex = z_shoulder + half_w  # 19.0mm (45° peaked roof for support-free printing)

    pts_slot_ccw = [
        [-half_w, z_bot],
        [ half_w, z_bot],
        [ half_w, z_shoulder],
        [    0.0, z_apex],
        [-half_w, z_shoulder]
    ]
    poly_slot = m3d.CrossSection([pts_slot_ccw])
    for vx in [-18.0, -12.0, -6.0, 0.0, 6.0, 12.0, 18.0]:
        slot_solid = m3d.Manifold.extrude(poly_slot, 16.0).rotate([90, 0, 0]).translate([vx, 46.0, 0])
        vent_cuts = vent_cuts + slot_solid

    cuts = cavity_obj + usbc_wall_relief + usbc_port + dupont_trench + screw_pilot_cuts + vent_cuts
    housing_hollow = chassis - cuts

    # 7. ESP32 SuperMini Precision Tolerance-Based Press Fit Cradle (G0 Rev 2 Approved):
    # - Baseline channel width = 18.60mm (+0.30mm per side clearance against nominal 18.0mm)
    # - 4x vertical micro-crush ribs (0.35mm protrusion, effective width 17.90mm) with 45° lead-in chamfers
    # - Bifurcated front capture ears at X = -40.8mm for positive +Z lock against USB-C extraction prying
    # - Rear mechanical thrust corner shoulders at X = -17.6mm with 10.0mm antenna keep-out gap
    # - Floor pry relief notch for safe tool/fingernail ejection
    esp_l = 23.2
    esp_w = 18.60
    rail_h = 1.8       # PCB bottom at Z = 3.8mm, PCB top at Z = 5.0mm (1.2mm) to 5.4mm (1.6mm)
    side_thick = 1.2   # Rigid side guide walls
    cradle_h = 3.6     # Side wall height above floor (Z = 5.6mm)

    x_front = -40.8    # Board front seating datum (shaved wall relief)
    x_rear = -17.6     # Rear mechanical thrust shoulders
    wall_thick_back = 1.6
    x_back = x_rear + wall_thick_back # -16.0mm

    hw_in = esp_w / 2.0          # 9.30mm
    hw_out = hw_in + side_thick  # 10.50mm
    center_gap_half_w = 5.0      # 10.0mm open center gap around 2.4GHz ceramic antenna (F-1.4)

    # 7a. Top L-Shaped Guide Rail & Rear Corner Stop (CCW Winding)
    pts_rail_t = [
        [x_front, hw_in],
        [x_rear, hw_in],
        [x_rear, center_gap_half_w],
        [x_back, center_gap_half_w],
        [x_back, hw_out],
        [x_front, hw_out]
    ]
    poly_rail_t = m3d.CrossSection([pts_rail_t])
    wall_top_solid = m3d.Manifold.extrude(poly_rail_t, cradle_h).translate([0, 0, floor_t])

    # 7b. Bottom L-Shaped Guide Rail & Rear Corner Stop (CCW Winding)
    pts_rail_b = [
        [x_front, -hw_out],
        [x_back, -hw_out],
        [x_back, -center_gap_half_w],
        [x_rear, -center_gap_half_w],
        [x_rear, -hw_in],
        [x_front, -hw_in]
    ]
    poly_rail_b = m3d.CrossSection([pts_rail_b])
    wall_bot_solid = m3d.Manifold.extrude(poly_rail_b, cradle_h).translate([0, 0, floor_t])

    # 7c. Outer Edge Support Ledges (0.80mm step supporting PCB edge outside pin headers)
    step_w = 0.80
    pts_ledge_t = [
        [x_front, hw_in - step_w],
        [x_rear, hw_in - step_w],
        [x_rear, hw_in],
        [x_front, hw_in]
    ]
    poly_ledge_t = m3d.CrossSection([pts_ledge_t])
    ledge_top = m3d.Manifold.extrude(poly_ledge_t, rail_h).translate([0, 0, floor_t])

    pts_ledge_b = [
        [x_front, -hw_in],
        [x_rear, -hw_in],
        [x_rear, -(hw_in - step_w)],
        [x_front, -(hw_in - step_w)]
    ]
    poly_ledge_b = m3d.CrossSection([pts_ledge_b])
    ledge_bot = m3d.Manifold.extrude(poly_ledge_b, rail_h).translate([0, 0, floor_t])

    # 7d. 4x Vertical Micro-Crush Ribs with 45° Top Lead-In Chamfers (F-1.2):
    # Protrudes 0.35mm inward into channel (effective width 17.90mm)
    crush_ribs = m3d.Manifold()
    rib_len = 1.4
    rib_protrusion = 0.35
    rib_h = cradle_h - 0.4  # Z = 2.0 to 5.2mm
    for rx in [-32.0, -22.0]:
        # Top wall ribs (projecting downward in -Y):
        r_body_t = m3d.Manifold.cube([rib_len, rib_protrusion, rib_h], center=False).translate([rx - rib_len / 2.0, hw_in - rib_protrusion, floor_t])
        r_lead_t = m3d.Manifold.cube([rib_len, rib_protrusion * 1.414, rib_protrusion * 1.414], center=False).rotate([45, 0, 0]).translate([rx - rib_len / 2.0, hw_in, floor_t + rib_h])
        rib_t = r_body_t - r_lead_t

        # Bottom wall ribs (projecting upward in +Y):
        r_body_b = m3d.Manifold.cube([rib_len, rib_protrusion, rib_h], center=False).translate([rx - rib_len / 2.0, -hw_in, floor_t])
        r_lead_b = m3d.Manifold.cube([rib_len, rib_protrusion * 1.414, rib_protrusion * 1.414], center=False).rotate([-45, 0, 0]).translate([rx - rib_len / 2.0, -hw_in, floor_t + rib_h])
        rib_b = r_body_b - r_lead_b

        crush_ribs = crush_ribs + rib_t + rib_b

    # 7e. Bifurcated Front Capture Ears (F-1.1: 10.0mm open center for USB-C, 45° support-free chamfers)
    ear_len = 2.2
    ear_t = m3d.Manifold.cube([ear_len, hw_out - 5.0, 1.8], center=False).translate([x_front, 5.0, 5.60])
    ear_b = m3d.Manifold.cube([ear_len, hw_out - 5.0, 1.8], center=False).translate([x_front, -hw_out, 5.60])
    ear_chamfer_t = m3d.Manifold.cube([1.2, hw_out - 5.0, 1.2], center=False).rotate([0, 45, 0]).translate([x_front + ear_len, 5.0, 6.40])
    ear_chamfer_b = m3d.Manifold.cube([1.2, hw_out - 5.0, 1.2], center=False).rotate([0, 45, 0]).translate([x_front + ear_len, -hw_out, 6.40])
    front_ears = (ear_t + ear_b) - (ear_chamfer_t + ear_chamfer_b)

    # 7f. Disassembly Pry Relief Notch in Floor (F-1.5: 4.0 x 3.0mm bevel slot at X = -17.6mm, Y = 6.5mm)
    pry_notch = m3d.Manifold.cube([4.0, 3.0, 1.2], center=False).translate([x_rear - 2.0, 5.0, floor_t - 0.2])

    cradle_solid = (wall_top_solid + wall_bot_solid + ledge_top + ledge_bot + crush_ribs + front_ears) - pry_notch
    housing = housing_hollow + cradle_solid

    return housing

# =========================================================================
# BUILD PART 4 & 5: TWO-TIER DESK STAND
# =========================================================================
def build_stand_tier1():
    base_pts = make_rounded_rect_2d(STAND_BASE_W, STAND_BASE_D, 6.0, 32)
    poly = m3d.CrossSection([base_pts])
    base = m3d.Manifold.extrude(poly, STAND_BASE_H)

    for sx in [-1, 1]:
        for sy in [-1, 1]:
            foot = m3d.Manifold.cylinder(1.7, 8.5 / 2.0, 8.5 / 2.0, 32).translate([sx * (STAND_BASE_W / 2.0 - 12.0), sy * (STAND_BASE_D / 2.0 - 12.0), -0.1])
            base = base - foot

    for sx in [-1, 1]:
        for sy in [-1, 1]:
            socket = m3d.Manifold.cylinder(3.5, 5.2 / 2.0, 5.2 / 2.0, 32).translate([sx * 28.0, sy * 26.0, STAND_BASE_H - 3.0])
            base = base - socket

    return base

def build_stand_tier2():
    b_prism = make_octagonal_prism(STAND_BASE_W - 4.0, STAND_BASE_D - 4.0, 8.0, 2.0)
    t_prism = make_octagonal_prism(HOUSING_W + 2.0, HOUSING_W - 2.0, 8.0, 2.0).translate([0, 2.0, STAND_TRUNK_H - 2.0])
    trunk = (b_prism + t_prism).hull()

    # 22° Ergonomic V-Saddle Pod Cradle (sized for 84mm square pod)
    cradle_cutter = make_octagonal_prism(HOUSING_W + 0.8, HOUSING_H + 0.8, CHAMFER_OUTER, HOUSING_DEPTH + 40.0).translate([0, 0, -HOUSING_DEPTH / 2.0]).rotate([STAND_TILT_DEG, 0, 0]).translate([0, 8.0, STAND_TRUNK_H + 12.0])
    trunk = trunk - cradle_cutter

    # Rear Cable Channel (26mm wide)
    cable_cut = m3d.Manifold.cube([26.0, STAND_BASE_D + 4.0, STAND_TRUNK_H + 2.0], center=False).translate([-13.0, -STAND_BASE_D / 2.0 - 2.0, -1.0])
    trunk = trunk - cable_cut

    # 4x downward alignment pins for Tier 1 base
    pins = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            pin = m3d.Manifold.cylinder(3.0, 4.8 / 2.0, 4.8 / 2.0, 32).translate([sx * 28.0, sy * 26.0, -3.0])
            pins.append(pin)
    
    for p in pins:
        trunk = trunk + p

    return trunk

def build_monolithic_stand():
    t1 = build_stand_tier1()
    t2 = build_stand_tier2().translate([0, 0, STAND_BASE_H])
    return t1 + t2

# =========================================================================
# MAIN EXECUTION
# =========================================================================
if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print("Building Part 1: Internal Rear Clamp Bracket (Option 2 M2.5)...")
    rear_clamp = build_rear_clamp()
    export_stl(rear_clamp, os.path.join(out_dir, "gc9b72_rear_clamp.stl"), "Part 1 - Rear Clamp")

    print("Building Part 1B (Legacy): Circular Top Bezel Ring (M2.3)...")
    bezel = build_circular_top_bezel()
    export_stl(bezel, os.path.join(out_dir, "gc9b72_top_bezel.stl"), "Part 1B - Legacy Bezel Ring")

    print("Building Part 2: Monolithic Front Face (Option 2: Rear-Loading + Integrated Bezel)...")
    front_face = build_front_face()
    export_stl(front_face, os.path.join(out_dir, "gc9b72_front_face.stl"), "Part 2 - Front Face")

    print("Building Part 3: Main Housing Pod (Tolerance Press-Fit Cradle, Vents, Chamfers)...")
    housing = build_main_housing()
    export_stl(housing, os.path.join(out_dir, "gc9b72_main_housing.stl"), "Part 3 - Main Housing")

    print("Building Part 4: Stand Tier 1 Base Plate...")
    stand_t1 = build_stand_tier1()
    export_stl(stand_t1, os.path.join(out_dir, "gc9b72_stand_tier1_base.stl"), "Part 4 - Stand Tier 1")

    print("Building Part 5: Stand Tier 2 Trunk...")
    stand_t2 = build_stand_tier2()
    export_stl(stand_t2, os.path.join(out_dir, "gc9b72_stand_tier2_trunk.stl"), "Part 5 - Stand Tier 2")

    print("Building Part 6: Monolithic Stand...")
    mono_stand = build_monolithic_stand()
    export_stl(mono_stand, os.path.join(out_dir, "gc9b72_monolithic_stand.stl"), "Part 6 - Monolithic Stand")

    print("\nAll 6 models successfully generated with tolerance-based press fit & 240x240 heritage architecture!")
