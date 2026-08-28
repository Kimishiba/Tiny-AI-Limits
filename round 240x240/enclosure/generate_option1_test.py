#!/usr/bin/env python3
import sys
import os
import manifold3d as m3d
import trimesh
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_stl import (
    make_chamfered_octagonal_base,
    make_text_emboss,
    make_snap_clip,
    export_stl
)

def make_rounded_pillar(w, d, h, r_top=2.0):
    b1 = m3d.Manifold.cube([d - r_top, w, h], center=False)
    b2 = m3d.Manifold.cube([d, w, h - r_top], center=False)
    cyl = m3d.Manifold.cylinder(w, r_top, r_top, 32).rotate([90, 0, 0]).translate([d - r_top, 0, h - r_top])
    return (b1 + b2 + cyl).hull()

def generate_main_housing_option1():
    w = 54.0
    c = 6.0
    depth = 27.5
    floor_t = 2.0

    cavity_depth = depth - floor_t
    screw_dist = 20.50
    chamfer_outer = 1.2
    
    # 1. Main outer solid chassis
    chassis = make_chamfered_octagonal_base(w, depth, c, chamfer_outer=chamfer_outer, chamfer_top=False)
    
    # 2. Main Internal Chamfered Cavity
    cw = 48.0
    cc = 12.0
    hcw = cw / 2.0
    pts_cavity = [
        [-hcw + cc, -hcw], [hcw - cc, -hcw],
        [hcw, -hcw + cc],  [hcw, hcw - cc],
        [hcw - cc, hcw],   [-hcw + cc, hcw],
        [-hcw, hcw - cc],  [-hcw, -hcw + cc]
    ]
    poly_cavity = m3d.CrossSection([pts_cavity])
    cavity_obj = m3d.Manifold.extrude(poly_cavity, cavity_depth + 0.1).translate([0, 0, floor_t])
    
    # 3. Extra-Wide High-Clearance USB-C Port
    usbc_z = 9.50
    y_span = 4.0
    r_inner = 3.25
    r_outer = 4.75
    
    c1 = m3d.Manifold.cylinder(18.0, r_inner, r_inner, 32).rotate([0, 90, 0]).translate([-32.0, -y_span, usbc_z])
    c2 = m3d.Manifold.cylinder(18.0, r_inner, r_inner, 32).rotate([0, 90, 0]).translate([-32.0, y_span, usbc_z])
    usbc_tunnel = (c1 + c2).hull()
    
    cone1 = m3d.Manifold.cylinder(4.0, r_outer, r_inner, 32).rotate([0, 90, 0]).translate([-29.5, -y_span, usbc_z])
    cone2 = m3d.Manifold.cylinder(4.0, r_outer, r_inner, 32).rotate([0, 90, 0]).translate([-29.5, y_span, usbc_z])
    usbc_flare = (cone1 + cone2).hull()
    usbc_port = usbc_tunnel + usbc_flare
    
    # 4. DuPont Clearance Trench
    dupont_trench = m3d.Manifold.cube([26.0, 5.0, cavity_depth + 0.1], center=False).translate([-13.0, -26.0, floor_t])
    
    # 5. 4 Corner M3 Screw Pilot Holes with Entry Chamfers
    screw_pilot_cuts = m3d.Manifold()
    for sx in [-screw_dist, screw_dist]:
        for sy in [-screw_dist, screw_dist]:
            pilot_m3 = m3d.Manifold.cylinder(15.2, 1.4, 1.4, 32).translate([sx, sy, depth - 15.0])
            cone_m3 = m3d.Manifold.cylinder(1.0, 1.4, 2.4, 32).translate([sx, sy, depth - 0.99])
            screw_pilot_cuts = screw_pilot_cuts + pilot_m3 + cone_m3
            
    # 6. Sleek Contour Aeration Slits
    vent_cuts = m3d.Manifold()
    top_rows = [
        (10.5, 9.0, -11.0, 7.5, 0.0, 9.0, 11.0),
        (12.7, 9.0, -11.0, 7.5, 0.0, 9.0, 11.0),
        (14.9, 9.0, -11.0, 7.5, 0.0, 9.0, 11.0),
        (17.1, 8.0, -10.5, 7.5, 0.0, 8.0, 10.5),
        (19.3, 7.0, -10.0, 7.5, 0.0, 7.0, 10.0),
        (21.5, 5.0, -9.0,  7.5, 0.0, 5.0, 9.0),
    ]
    slot_h = 1.05
    for (ry, lw, lcx, cw_v, ccx, rw, rcx) in top_rows:
        s_l = m3d.Manifold.cube([lw, slot_h, floor_t + 2.0], center=True).translate([lcx, ry, floor_t / 2.0])
        s_c = m3d.Manifold.cube([cw_v, slot_h, floor_t + 2.0], center=True).translate([ccx, ry, floor_t / 2.0])
        s_r = m3d.Manifold.cube([rw, slot_h, floor_t + 2.0], center=True).translate([rcx, ry, floor_t / 2.0])
        vent_cuts = vent_cuts + s_l + s_c + s_r

    for (ry, lw, lcx, cw_v, ccx, rw, rcx) in top_rows:
        s_l = m3d.Manifold.cube([lw, slot_h, floor_t + 2.0], center=True).translate([lcx, -ry, floor_t / 2.0])
        s_c = m3d.Manifold.cube([cw_v, slot_h, floor_t + 2.0], center=True).translate([ccx, -ry, floor_t / 2.0])
        s_r = m3d.Manifold.cube([rw, slot_h, floor_t + 2.0], center=True).translate([rcx, -ry, floor_t / 2.0])
        vent_cuts = vent_cuts + s_l + s_c + s_r
        
    pts_slot_ccw = [[-0.6, 11.0], [0.6, 11.0], [0.6, 18.4], [0.0, 19.0], [-0.6, 18.4]]
    poly_slot = m3d.CrossSection([pts_slot_ccw])
    for vx in [-12.0, -8.0, -4.0, 0.0, 4.0, 8.0, 12.0]:
        slot_solid = m3d.Manifold.extrude(poly_slot, 10.0).rotate([90, 0, 0]).scale([1, -1, 1]).translate([vx, 20.0, 0])
        vent_cuts = vent_cuts + slot_solid

    # 7. Embossed/Debossed Product Name ("TINY AI LIMITS / SENTINEL MK-1")
    text_deboss = make_text_emboss("TINY AI LIMITS", "SENTINEL MK-1", depth=0.50).translate([0, 0, -0.05])

    cuts = cavity_obj + dupont_trench + screw_pilot_cuts + vent_cuts + text_deboss
    housing_hollow = chassis - cuts
    
    # 8. Open-Front Minimalist U-Cradle with SMOOTH ROUNDED DUAL BUTTRESSES & ANTENNA GAP
    esp_l = 23.0
    esp_w = 18.4
    esp_center_x = -10.0
    rail_h = 3.2
    
    x_front = esp_center_x - esp_l / 2.0  # -21.5 (USB-C port end)
    x_rear = esp_center_x + esp_l / 2.0   # +1.5  (Opposite end behind antenna)
    side_thick = 1.6
    side_wall_h = 6.2   # Z = 2.0 to 8.2
    pillar_w = 5.2      # Width of each corner pillar along Y
    pillar_thick = 3.2  # Thickness along X
    pillar_h = 6.2      # Pillar height matching side walls (Z = 2.0 to 8.2)
    
    # Smoothly rounded corner thrust buttresses
    p_shape = make_rounded_pillar(pillar_w, pillar_thick, pillar_h, r_top=2.0)
    p_top = p_shape.translate([x_rear, esp_w / 2.0 + side_thick - pillar_w, floor_t])
    p_bot = p_shape.translate([x_rear, -(esp_w / 2.0 + side_thick), floor_t])
    buttresses = p_top + p_bot
    
    # Straight Vertical Side Guide Walls:
    side_wall_top = m3d.Manifold.cube([esp_l, side_thick, side_wall_h], center=False).translate([
        x_front, esp_w / 2.0, floor_t
    ])
    side_wall_bot = m3d.Manifold.cube([esp_l, side_thick, side_wall_h], center=False).translate([
        x_front, -(esp_w / 2.0 + side_thick), floor_t
    ])

    # 1.0mm side edge support steps:
    edge_step_top = m3d.Manifold.cube([esp_l, 1.0, rail_h], center=False).translate([
        x_front, esp_w / 2.0 - 1.0, floor_t
    ])
    edge_step_bot = m3d.Manifold.cube([esp_l, 1.0, rail_h], center=False).translate([
        x_front, -esp_w / 2.0, floor_t
    ])
    
    # Discrete 45-Degree Self-Supporting Snap Clips
    snap_z = floor_t + rail_h + 1.2 + 0.3 # 6.7mm
    clip_top = make_snap_clip(5.0, 0.55, 1.2, '+Y').translate([esp_center_x, esp_w / 2.0, snap_z])
    clip_bot = make_snap_clip(5.0, 0.55, 1.2, '-Y').translate([esp_center_x, -esp_w / 2.0, snap_z])
    
    carrier_solid = buttresses + side_wall_top + side_wall_bot + edge_step_top + edge_step_bot + clip_top + clip_bot

    return (housing_hollow + carrier_solid) - usbc_port

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_stl = os.path.join(out_dir, "gc9a01_main_housing_option1_test.stl")
    opt1_housing = generate_main_housing_option1()
    export_stl(opt1_housing, out_stl, "Main Housing Pod (Option 1 Test - Rounded Pillars)")
