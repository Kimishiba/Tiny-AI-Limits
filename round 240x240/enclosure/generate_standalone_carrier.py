#!/usr/bin/env python3
"""
Standalone ESP32-S3 / C3 SuperMini Minimalist Snap-In Carrier Cradle
100% Support-Free FDM 3D Printable Modular Hardware Bracket

Features:
- Dual Angled Corner Buttresses at the rear to absorb 100% of USB-C insertion load
- Wide 10.0mm Open Center Gap for unobstructed 2.4GHz Wi-Fi / BLE ceramic antenna radiation
- Open-Front entry for full USB-C cable and plug overmold clearance
- Continuous 1.0mm side edge support ledges (Z = 2.0 to 5.2mm)
- 45° Self-Supporting Snap-Fit retention clips (Z = 6.7mm)
- Integrated base plate with 2x M3 mounting eyelets for chassis integration
"""

import os
import math
import manifold3d as m3d
import trimesh
import numpy as np

def make_snap_clip(length=5.0, width=0.55, height=1.2, side='+Y'):
    hw_x = length / 2.0
    hz = height / 2.0
    if side == '+Y':
        v_base = [[-hw_x, 0.05, -hz], [hw_x, 0.05, -hz], [hw_x, 0.05, hz], [-hw_x, 0.05, hz]]
        v_apex = [[-hw_x + 0.55, -width, 0.0], [hw_x - 0.55, -width, 0.0]]
    else:
        v_base = [[-hw_x, -0.05, -hz], [hw_x, -0.05, -hz], [hw_x, -0.05, hz], [-hw_x, -0.05, hz]]
        v_apex = [[-hw_x + 0.55, width, 0.0], [hw_x - 0.55, width, 0.0]]
    pts = v_base + v_apex
    combined = m3d.Manifold()
    for p in pts:
        combined = combined + m3d.Manifold.cube([0.01, 0.01, 0.01]).translate(p)
    return combined.hull()

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

def make_rounded_rect_prism(w, d, h, r, fn=32):
    pts = make_rounded_rect_2d(w, d, r, fn)
    poly = m3d.CrossSection([pts])
    return m3d.Manifold.extrude(poly, h)

def generate_standalone_carrier():
    # ESP32-S3 / C3 SuperMini Dimensions:
    board_l = 23.5 # Length along X
    board_w = 18.4 # Width along Y
    floor_t = 2.0  # Base plate thickness
    rail_h = 3.2   # PCB support ledge height above floor (Z = 2.0 to 5.2)
    side_wall_h = 6.2 # Overall wall height above floor (Z = 2.0 to 8.2)
    side_thick = 1.8
    
    # Cradle Bounds along X:
    x_front = -board_l / 2.0 # -11.75
    x_rear  =  board_l / 2.0 # +11.75
    
    # 1. Base Mounting Plate (flanged with rounded corners)
    flange_w = board_w + 2 * side_thick + 12.0 # 34.0mm
    flange_l = board_l + 6.0 # 29.5mm
    base_plate = make_rounded_rect_prism(flange_l, flange_w, floor_t, 3.0)
    
    # 2. Side Guide Walls & 1.0mm Edge Support Steps:
    poly_wall_top = m3d.CrossSection.square([board_l, side_thick], center=False).translate([x_front, board_w / 2.0])
    poly_step_top = m3d.CrossSection.square([board_l, 1.0], center=False).translate([x_front, board_w / 2.0 - 1.0])

    poly_wall_bot = m3d.CrossSection.square([board_l, side_thick], center=False).translate([x_front, -(board_w / 2.0 + side_thick)])
    poly_step_bot = m3d.CrossSection.square([board_l, 1.0], center=False).translate([x_front, -board_w / 2.0])

    wall_top = m3d.Manifold.extrude(poly_wall_top, side_wall_h).translate([0, 0, floor_t])
    step_top = m3d.Manifold.extrude(poly_step_top, rail_h).translate([0, 0, floor_t])

    wall_bot = m3d.Manifold.extrude(poly_wall_bot, side_wall_h).translate([0, 0, floor_t])
    step_bot = m3d.Manifold.extrude(poly_step_bot, rail_h).translate([0, 0, floor_t])
    
    # 3. Dual Angled Corner Buttresses at the Rear (+X end) with 45° sloped shoulders:
    pillar_w = 4.8
    pillar_thick = 3.2
    pillar_h = 8.2 # Z = 2.0 to 10.2
    
    p_top = m3d.Manifold.cube([pillar_thick, pillar_w, pillar_h], center=False).translate([
        x_rear, board_w / 2.0 + side_thick - pillar_w, floor_t
    ])
    p_bot = m3d.Manifold.cube([pillar_thick, pillar_w, pillar_h], center=False).translate([
        x_rear, -(board_w / 2.0 + side_thick), floor_t
    ])
    
    # 45° chamfers on rear top edges:
    ch_top = m3d.Manifold.cube([5.0, pillar_w + 1.0, 5.0], center=True).rotate([0, 45, 0]).translate([
        x_rear + pillar_thick, board_w / 2.0 + side_thick - pillar_w / 2.0, floor_t + pillar_h
    ])
    ch_bot = m3d.Manifold.cube([5.0, pillar_w + 1.0, 5.0], center=True).rotate([0, 45, 0]).translate([
        x_rear + pillar_thick, -(board_w / 2.0 + side_thick - pillar_w / 2.0), floor_t + pillar_h
    ])
    buttresses = (p_top + p_bot) - ch_top - ch_bot
    
    # 4. Discrete 45° Self-Supporting Snap Retention Clips:
    snap_z = floor_t + rail_h + 1.2 + 0.3 # 6.7mm
    clip_top = make_snap_clip(5.0, 0.55, 1.2, '+Y').translate([0.0, board_w / 2.0, snap_z])
    clip_bot = make_snap_clip(5.0, 0.55, 1.2, '-Y').translate([0.0, -board_w / 2.0, snap_z])
    
    solid = base_plate + wall_top + step_top + wall_bot + step_bot + buttresses + clip_top + clip_bot
    
    # 5. Mounting Screw Holes (2x M3 holes on side flanges, spacing = 28.0mm along Y)
    hole_m3_top = m3d.Manifold.cylinder(floor_t + 2.0, 1.7, 1.7, 32).translate([0.0, 13.5, -1.0])
    hole_m3_bot = m3d.Manifold.cylinder(floor_t + 2.0, 1.7, 1.7, 32).translate([0.0, -13.5, -1.0])
    
    # Central Aeration / Weight-Reduction Window in the floor:
    floor_window = m3d.Manifold.cube([14.0, 12.0, floor_t + 2.0], center=True).translate([0.0, 0.0, floor_t / 2.0])
    
    return solid - hole_m3_top - hole_m3_bot - floor_window

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    out_stl = os.path.join(output_dir, "esp32_s3_supermini_carrier.stl")
    carrier = generate_standalone_carrier()
    
    mesh_data = carrier.to_mesh()
    tri_mesh = trimesh.Trimesh(
        vertices=mesh_data.vert_properties[:, :3],
        faces=mesh_data.tri_verts
    )
    tri_mesh.export(out_stl, file_type='stl')
    print(f"[Standalone ESP32-S3 Carrier] Exported: {out_stl}")
    print(f"   -> Triangles: {len(tri_mesh.faces)}, Watertight: {tri_mesh.is_watertight}, Volume: {tri_mesh.volume / 1000.0:.2f} cm3")

if __name__ == "__main__":
    main()
