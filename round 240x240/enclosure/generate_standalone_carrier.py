#!/usr/bin/env python3
"""
Standalone ESP32-S3 / C3 SuperMini Cyberdeck Carrier Cradle (Option 1 Concept)
100% Support-Free FDM 3D Printable Modular Hardware Bracket

Features:
- Chunky Multi-Faceted Industrial Cyberdeck Geometry matching the Option 1 Concept Art
- Dual Rear Sculpted Corner Buttresses (9.5mm height) with compound 45° chamfers to absorb 100% of USB-C insertion load
- Wide 10.0mm Open Center Notch for unobstructed 2.4GHz Wi-Fi / BLE ceramic antenna radiation
- Open-Front Entry Flare (15.0mm width) for wide USB-C cable overmolds
- Precision Stepped Internal Shelf (2.4mm height) with 45° snap-fit retention clips
- 2x Recessed Counterbored M3 Screw Mounting Sockets in the mid-waist
"""

import os
import manifold3d as m3d
import trimesh
import numpy as np

def make_snap_clip(length=4.5, width=0.50, height=1.0, side='+Y'):
    hw_x = length / 2.0
    hz = height / 2.0
    if side == '+Y':
        v_base = [[-hw_x, 0.05, -hz], [hw_x, 0.05, -hz], [hw_x, 0.05, hz], [-hw_x, 0.05, hz]]
        v_apex = [[-hw_x + 0.5, -width, 0.0], [hw_x - 0.5, -width, 0.0]]
    else:
        v_base = [[-hw_x, -0.05, -hz], [hw_x, -0.05, -hz], [hw_x, -0.05, hz], [-hw_x, -0.05, hz]]
        v_apex = [[-hw_x + 0.5, width, 0.0], [hw_x - 0.5, width, 0.0]]
    pts = v_base + v_apex
    combined = m3d.Manifold()
    for p in pts:
        combined = combined + m3d.Manifold.cube([0.01, 0.01, 0.01]).translate(p)
    return combined.hull()

def generate_standalone_carrier():
    board_l = 23.5 # ESP32-S3 PCB length
    board_w = 18.4 # ESP32-S3 PCB width
    pcb_t = 1.2
    shelf_z = 2.4
    
    total_l = 30.0 # X from -15.0 to +15.0
    total_w = 36.0 # Y from -18.0 to +18.0
    max_h = 9.5
    floor_t = 2.0
    
    # 1. Solid Monolithic Chassis Block:
    raw_block = m3d.Manifold.cube([total_l, total_w, max_h], center=True).translate([0, 0, max_h / 2.0])
    
    # 2. Central PCB Recess (width 18.8mm, length 23.9mm, depth down to shelf_z)
    pcb_pocket = m3d.Manifold.cube([board_l + 0.4, board_w + 0.4, max_h + 1.0], center=True).translate([
        0, 0, shelf_z + (max_h + 1.0) / 2.0
    ])
    
    # 3. Rear Antenna Gap (width 10.0mm, through floor)
    antenna_gap = m3d.Manifold.cube([12.0, 10.0, max_h + 2.0], center=True).translate([
        10.0, 0, max_h / 2.0
    ])
    
    # 4. Front USB-C Open Channel (width 15.0mm, through floor)
    usbc_channel = m3d.Manifold.cube([10.0, 15.0, max_h + 2.0], center=True).translate([
        -11.0, 0, max_h / 2.0
    ])
    
    # 5. Center Under-PCB Ventilation Window
    center_vent = m3d.Manifold.cube([12.0, 12.0, floor_t + 2.0], center=True).translate([
        0, 0, floor_t / 2.0
    ])
    
    # 6. Sculpted Waist Cutout (lowering side walls to 5.0mm at mid-section)
    waist_cut = m3d.Manifold.cube([12.0, total_w + 2.0, max_h], center=True).translate([
        0, 0, 5.0 + max_h / 2.0
    ])
    ramp_rear = m3d.Manifold.cube([6.0, total_w + 2.0, 8.0], center=True).rotate([0, 35, 0]).translate([
        7.5, 0, 8.0
    ])
    ramp_front = m3d.Manifold.cube([6.0, total_w + 2.0, 8.0], center=True).rotate([0, -35, 0]).translate([
        -7.5, 0, 8.0
    ])
    
    # 7. Multi-Faceted Outer Chamfers (matching Option 1 Concept Art):
    rear_top_ch = m3d.Manifold.cube([8.0, total_w + 2.0, 8.0], center=True).rotate([0, 40, 0]).translate([
        15.0, 0, max_h + 1.0
    ])
    front_top_ch = m3d.Manifold.cube([8.0, total_w + 2.0, 8.0], center=True).rotate([0, -40, 0]).translate([
        -15.0, 0, max_h + 1.0
    ])
    
    c_sw = m3d.Manifold.cube([5.0, 5.0, max_h + 2.0], center=True).rotate([0, 0, 45]).translate([-15.0, -18.0, max_h/2.0])
    c_nw = m3d.Manifold.cube([5.0, 5.0, max_h + 2.0], center=True).rotate([0, 0, 45]).translate([-15.0,  18.0, max_h/2.0])
    c_se = m3d.Manifold.cube([5.0, 5.0, max_h + 2.0], center=True).rotate([0, 0, 45]).translate([ 15.0, -18.0, max_h/2.0])
    c_ne = m3d.Manifold.cube([5.0, 5.0, max_h + 2.0], center=True).rotate([0, 0, 45]).translate([ 15.0,  18.0, max_h/2.0])
    outer_corners = c_sw + c_nw + c_se + c_ne
    
    side_bevel_top = m3d.Manifold.cube([total_l + 2.0, 5.0, 5.0], center=True).rotate([45, 0, 0]).translate([
        0, 18.0, max_h
    ])
    side_bevel_bot = m3d.Manifold.cube([total_l + 2.0, 5.0, 5.0], center=True).rotate([45, 0, 0]).translate([
        0, -18.0, max_h
    ])
    
    # 8. Counterbored M3 Mounting Holes on Side Flanges (X = 0, Y = +/- 14.5mm):
    m3_mounts = m3d.Manifold()
    for sy in [-14.5, 14.5]:
        hole = m3d.Manifold.cylinder(max_h + 2.0, 1.7, 1.7, 32).translate([0, sy, -1.0])
        cb = m3d.Manifold.cylinder(max_h, 3.2, 3.2, 32).translate([0, sy, 3.0])
        m3_mounts = m3_mounts + hole + cb
        
    cuts = (pcb_pocket + antenna_gap + usbc_channel + center_vent +
            waist_cut + ramp_rear + ramp_front + rear_top_ch + front_top_ch +
            outer_corners + side_bevel_top + side_bevel_bot + m3_mounts)
            
    carrier = raw_block - cuts
    
    # 9. Snap retention clips:
    clip_z = shelf_z + pcb_t + 0.3
    c_top = make_snap_clip(4.5, 0.50, 1.0, '+Y').translate([0, board_w / 2.0 + 0.2, clip_z])
    c_bot = make_snap_clip(4.5, 0.50, 1.0, '-Y').translate([0, -(board_w / 2.0 + 0.2), clip_z])
    
    return carrier + c_top + c_bot

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
    print(f"[Standalone ESP32-S3 Option 1 Carrier] Exported: {out_stl}")
    print(f"   -> Triangles: {len(tri_mesh.faces)}, Watertight: {tri_mesh.is_watertight}, Volume: {tri_mesh.volume / 1000.0:.2f} cm3")

if __name__ == "__main__":
    main()
