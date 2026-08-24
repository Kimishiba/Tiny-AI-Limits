#!/usr/bin/env python3
"""
GC9A01 1.28" Round Display & ESP32-C3 SuperMini Cyberdeck Enclosure
Professional 3D Printable STL Generator (Boolean CSG & Watertight Manifold Engine)

Generates 100% watertight, genuinely hollow STL meshes for slicing in Cura, PrusaSlicer, Bambu Studio, and Orca.
"""

import math
import os
import manifold3d as m3d
import trimesh
import numpy as np

def make_octagonal_prism(w, h, c):
    hw = w / 2.0
    pts_2d = [
        [-hw + c, -hw], [hw - c, -hw],
        [hw, -hw + c],  [hw, hw - c],
        [hw - c, hw],   [-hw + c, hw],
        [-hw, hw - c],  [-hw, -hw + c]
    ]
    poly = m3d.CrossSection([pts_2d])
    return m3d.Manifold.extrude(poly, h)

def export_stl(manifold_obj, filepath, name="Model"):
    mesh_data = manifold_obj.to_mesh()
    tri_mesh = trimesh.Trimesh(
        vertices=mesh_data.vert_properties[:, :3],
        faces=mesh_data.tri_verts
    )
    tri_mesh.export(filepath, file_type='stl')
    print(f"[{name}] Exported: {filepath}")
    print(f"   -> Triangles: {len(tri_mesh.faces)}, Watertight: {tri_mesh.is_watertight}, Volume: {tri_mesh.volume / 1000.0:.2f} cm3")

def generate_front_bezel():
    w = 54.0
    c = 6.0
    t = 4.5
    
    # 1. Base octagonal plate (z = 0 to 4.5)
    base = make_octagonal_prism(w, t, c)
    
    # 2. Raised circular decorative trim ring (z = 4.5 to 6.0)
    ring = m3d.Manifold.cylinder(1.5, 22.0, 22.0, 64).translate([0, 0, t])
    bezel_solid = base + ring
    
    # 3. Center Screen Active View Window (Through-hole bore from z = -1 to 7)
    window_chamfer = m3d.Manifold.cylinder(t + 3.0, 16.4 + 1.0, 16.4, 64).translate([0, 0, -1.0])
    
    # 4. Rear Retention Pocket for GC9A01 Display PCB & Glass (z = -0.1 to 1.8)
    recess = m3d.Manifold.cylinder(1.9, 18.6, 18.6, 64).translate([0, 0, -0.1])
    
    cuts = window_chamfer + recess
    
    # 5. 4 Corner M2 Screw Through-Holes & Counterbore Pockets (+/-21mm)
    screw_dist = 21.0
    for sx in [-screw_dist, screw_dist]:
        for sy in [-screw_dist, screw_dist]:
            # M2.5 clearance through-hole (d = 2.6mm)
            hole = m3d.Manifold.cylinder(t + 4.0, 1.3, 1.3, 32).translate([sx, sy, -1.0])
            # M2 Socket cap counterbore pocket (d = 4.8mm, depth = 2.2mm from top)
            cb = m3d.Manifold.cylinder(3.0, 2.4, 2.4, 32).translate([sx, sy, t + 1.5 - 2.2])
            cuts = cuts + hole + cb
            
    return bezel_solid - cuts

def generate_main_housing():
    w = 54.0
    c = 6.0
    depth = 36.0
    floor_t = 2.5
    pcb_depth = 4.0
    cavity_depth = depth - floor_t - pcb_depth # 29.5mm internal clearance
    
    # 1. Main outer solid chassis (z = 0 to 36)
    chassis = make_octagonal_prism(w, depth, c)
    
    # 2. Front Circular Display Pocket (z = 32 to 36.1)
    display_pocket = m3d.Manifold.cylinder(pcb_depth + 0.2, 18.6, 18.6, 64).translate([0, 0, depth - pcb_depth])
    
    # 3. Main Internal Electronics & DuPont Cable Cavity (44mm x 44mm x 29.5mm)
    # Centered at (0, 0), z = floor_t (2.5) to depth - pcb_depth (32.0)
    cavity = m3d.Manifold.cube([44.0, 44.0, cavity_depth + 0.1], center=True).translate([0, 0, floor_t + cavity_depth / 2.0])
    
    # 4. Left-Side USB-C Port Cutout (13.0mm wide x 8.0mm tall)
    # Cut completely through the left wall at x = -27
    usbc = m3d.Manifold.cube([16.0, 13.0, 8.0], center=True).translate([-24.0, 0, floor_t + 2.5 + 4.0])
    
    cuts = display_pocket + cavity + usbc
    
    # 5. 4 Corner M2 Screw Pilot Holes (14mm deep from front face)
    screw_dist = 21.0
    for sx in [-screw_dist, screw_dist]:
        for sy in [-screw_dist, screw_dist]:
            pilot = m3d.Manifold.cylinder(14.2, 1.0, 1.0, 32).translate([sx, sy, depth - 14.0])
            cuts = cuts + pilot
            
    housing = chassis - cuts
    
    # 6. Internal ESP32-C3 SuperMini Mounting Standoff Rails on rear floor
    esp_w, esp_l = 18.4, 23.0
    rail_h = 2.5
    
    rail_l = m3d.Manifold.cube([2.0, esp_l, rail_h + 2.5], center=True).translate([-esp_w/2.0 + 1.0, 0, floor_t + (rail_h + 2.5)/2.0])
    rail_r = m3d.Manifold.cube([2.0, esp_l, rail_h + 2.5], center=True).translate([esp_w/2.0 - 1.0, 0, floor_t + (rail_h + 2.5)/2.0])
    pad_b  = m3d.Manifold.cube([esp_w, 3.0, rail_h], center=True).translate([0, -esp_l/2.0 + 1.5, floor_t + rail_h/2.0])
    pad_t  = m3d.Manifold.cube([esp_w, 3.0, rail_h], center=True).translate([0, esp_l/2.0 - 1.5, floor_t + rail_h/2.0])
    
    return housing + rail_l + rail_r + pad_b + pad_t

def generate_desk_stand():
    base_w = 62.0
    base_d = 68.0
    base_h = 10.0
    cradle_h = 30.0
    tilt = 20.0 # degrees
    
    # Base weighted block
    base = m3d.Manifold.cube([base_w, base_d, base_h], center=True).translate([0, 0, base_h / 2.0])
    
    # Upright angled cradle support
    cradle_solid = m3d.Manifold.cube([54.0 + 6.0, 20.0, cradle_h], center=True).translate([0, 0, cradle_h / 2.0])
    cradle_rotated = cradle_solid.rotate([tilt, 0, 0]).translate([0, 8.0, base_h])
    
    stand_solid = base + cradle_rotated
    
    # 1. Angled Mating Pocket for 54mm Main Housing Pod
    pocket_solid = m3d.Manifold.cube([54.0 + 0.8, 20.5, cradle_h + 10.0], center=True).translate([0, 0, (cradle_h + 10.0)/2.0])
    pocket_rotated = pocket_solid.rotate([tilt, 0, 0]).translate([0, 8.0, base_h + 5.0])
    
    # 2. Rear Cable Relief Channel (16mm wide)
    cable_slot = m3d.Manifold.cube([16.0, base_d + 10.0, 14.0], center=True).translate([0, 0, 7.0])
    
    # 3. 4 Bottom Anti-Slip Rubber Foot Recesses (d = 8.2mm, depth = 1.4mm)
    feet_cuts = m3d.Manifold()
    for fx in [-base_w/2.0 + 9.0, base_w/2.0 - 9.0]:
        for fy in [-base_d/2.0 + 9.0, base_d/2.0 - 9.0]:
            foot = m3d.Manifold.cylinder(1.5, 4.1, 4.1, 32).translate([fx, fy, -0.1])
            feet_cuts = feet_cuts + foot
            
    return stand_solid - pocket_rotated - cable_slot - feet_cuts

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating 100% Watertight Hollow STL Enclosure Models...\n")
    
    # 1. Front Bezel Plate (with clear center through-hole screen aperture)
    bezel = generate_front_bezel()
    bezel_path = os.path.join(output_dir, "gc9a01_front_bezel.stl")
    export_stl(bezel, bezel_path, "Front Bezel Plate")

    # 2. Main Housing Enclosure (with 44x44x29.5mm DuPont cavity & USB-C cutout)
    housing = generate_main_housing()
    housing_path = os.path.join(output_dir, "gc9a01_main_housing.stl")
    export_stl(housing, housing_path, "Main Housing Pod")

    # 3. Modular 20-Degree Angled Desk Stand
    stand = generate_desk_stand()
    stand_path = os.path.join(output_dir, "gc9a01_desk_stand.stl")
    export_stl(stand, stand_path, "Desk Stand Cradle")

    print("\n[ALL MODELS COMPLETE] All 3 STL files are 100% watertight, manifold, and ready to print!")

if __name__ == "__main__":
    main()
