// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model
// =========================================================================

$fn = 60; // High resolution curves for 3D printing

// --- PARAMETERS ---
enclosure_width  = 48.0; // Outer width & height (mm)
enclosure_depth  = 22.0; // Main pod depth (mm)
bezel_thickness  = 4.0;  // Front bezel plate thickness (mm)
chamfer_size     = 4.0;  // Corner 45-degree chamfers (mm)

display_active_dia = 32.6; // 1.28" visible active area window
display_pcb_dia    = 36.8; // GC9A01 PCB outer diameter + tolerance
display_recess_lip = 1.5;  // Front bezel retention step depth

screw_bolt_circle  = 36.0; // 36mm center-to-center square (x=+/-18, y=+/-18)
screw_hole_dia     = 2.6;  // M2.5 clearance through-hole
screw_head_dia     = 4.8;  // M2 socket cap head counterbore
screw_pilot_dia    = 1.9;  // M2 self-tapping pilot or M2 heat-set insert hole

tilt_angle         = 20.0; // Ergonomic desk viewing angle (degrees)

// --- MODULES ---

// Chamfered Cyberdeck Octagonal Prism
module octagonal_prism(w, h, c) {
    hw = w / 2;
    linear_extrude(height = h) {
        polygon([
            [-hw + c, -hw], [hw - c, -hw],
            [hw, -hw + c],  [hw, hw - c],
            [hw - c, hw],   [-hw + c, hw],
            [-hw, hw - c],  [-hw, -hw + c]
        ]);
    }
}

// 1. FRONT BEZEL RING PLATE
module front_bezel() {
    difference() {
        union() {
            // Base plate
            octagonal_prism(enclosure_width, bezel_thickness, chamfer_size);
            // Raised decorative bezel ring
            translate([0, 0, bezel_thickness])
                cylinder(d = 40.0, h = 1.5);
        }
        
        // Display view window
        translate([0, 0, -1])
            cylinder(d = display_active_dia, h = bezel_thickness + 4);
            
        // Rear retention lip for display glass
        translate([0, 0, -0.1])
            cylinder(d = display_pcb_dia, h = display_recess_lip + 0.1);
            
        // 4 Corner Screw Holes with Counterbore
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                // Through hole
                translate([sx, sy, -1])
                    cylinder(d = screw_hole_dia, h = bezel_thickness + 4);
                // Counterbore socket head pocket
                translate([sx, sy, 2.0])
                    cylinder(d = screw_head_dia, h = bezel_thickness);
            }
        }
    }
}

// 2. MAIN HOUSING POD
module main_housing() {
    difference() {
        // Outer body
        octagonal_prism(enclosure_width, enclosure_depth, chamfer_size);
        
        // Front PCB Pocket
        translate([0, 0, enclosure_depth - 4.5])
            cylinder(d = display_pcb_dia, h = 5.0);
            
        // Internal electronics cavity for ESP32 SuperMini & wiring
        translate([0, 0, 2.5])
            cube([28.0, 34.0, enclosure_depth - 6.0], center = true);
            
        // Left Side USB-C port cutout
        translate([-enclosure_width/2 - 1, 0, 8.5])
            cube([14.0, 11.0, 6.5], center = true);
            
        // 4 Corner Screw Pilot Holes / Heat-Set Insert Pockets
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, enclosure_depth - 10.0])
                    cylinder(d = screw_pilot_dia, h = 11.0);
            }
        }
    }
}

// 3. 20-DEGREE ANGLED DESK STAND
module desk_stand() {
    base_w = 54.0;
    base_d = 56.0;
    base_h = 10.0;
    
    difference() {
        union() {
            // Weighted base plate
            translate([0, 0, base_h/2])
                cube([base_w, base_d, base_h], center = true);
                
            // Angled support cradle
            translate([0, 0, base_h])
                rotate([tilt_angle, 0, 0])
                difference() {
                    cube([48.0, 16.0, 22.0], center = true);
                    // Mating slot for housing body
                    translate([0, 0, 2])
                        cube([48.4, 16.4, 20.0], center = true);
                }
        }
        
        // Rear USB-C Cable relief channel
        translate([0, 0, 0])
            cube([14.0, base_d + 4, 12.0], center = true);
            
        // 4 Bottom Anti-slip rubber foot recesses (8mm diameter, 1.2mm deep)
        for (fx = [-base_w/2 + 8, base_w/2 - 8]) {
            for (fy = [-base_d/2 + 8, base_d/2 - 8]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.0, h = 1.3);
            }
        }
    }
}

// --- RENDER SELECTION ---
// Uncomment the part you wish to preview/export:
// front_bezel();
// main_housing();
desk_stand();
