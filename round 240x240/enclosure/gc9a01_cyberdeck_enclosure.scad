// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PARAMETERS ---
part = 0; // 0 = All Assembly Preview, 1 = Front Bezel, 2 = Main Housing, 3 = Desk Stand

enclosure_width  = 48.0; // Outer width & height (mm)
enclosure_depth  = 22.0; // Main pod depth (mm)
bezel_thickness  = 4.5;  // Front bezel plate thickness (mm)
chamfer_size     = 4.5;  // Corner 45-degree chamfers (mm)

display_active_dia = 32.6; // 1.28" visible active area window
display_pcb_dia    = 36.8; // GC9A01 PCB outer diameter + tolerance (36.8mm)
display_recess_lip = 1.5;  // Front bezel retention step depth

screw_bolt_circle  = 36.0; // 36mm center-to-center square (x=+/-18, y=+/-18)
screw_hole_dia     = 2.6;  // M2 / M2.5 clearance through-hole
screw_head_dia     = 4.8;  // M2 socket cap head counterbore
screw_head_depth   = 2.2;  // Counterbore pocket depth
screw_pilot_dia    = 2.0;  // M2 self-tapping pilot or M2 heat-set insert hole (mm)

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

// 1. FRONT BEZEL RING PLATE (Truly Hollow with Display Window & Screw Counterbores)
module front_bezel() {
    difference() {
        union() {
            // Main chamfered bezel plate
            octagonal_prism(enclosure_width, bezel_thickness, chamfer_size);
            // Raised decorative cyberdeck bezel trim ring
            translate([0, 0, bezel_thickness])
                cylinder(d = 40.0, h = 1.5);
        }
        
        // 1. Center Screen Active View Window (Through-hole bore)
        translate([0, 0, -1])
            cylinder(d = display_active_dia, h = bezel_thickness + 3.0);
            
        // 2. Rear Retention Lip for Display Glass (Hollow step pocket)
        translate([0, 0, -0.1])
            cylinder(d = display_pcb_dia, h = display_recess_lip + 0.1);
            
        // 3. 4 Corner M2 Screw Holes with Recessed Counterbores
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                // Through hole
                translate([sx, sy, -1])
                    cylinder(d = screw_hole_dia, h = bezel_thickness + 3.0);
                // Counterbore pocket for socket cap head
                translate([sx, sy, bezel_thickness + 1.6 - screw_head_depth])
                    cylinder(d = screw_head_dia, h = screw_head_depth + 0.1);
            }
        }
    }
}

// 2. MAIN HOUSING POD (Truly Hollow with PCB Pocket, Electronics Cavity & USB-C Cutout)
module main_housing() {
    cavity_w = 34.0;
    cavity_h = 34.0;
    floor_t  = 2.5;
    pcb_depth = 4.0;
    
    difference() {
        // Outer Solid Chassis
        octagonal_prism(enclosure_width, enclosure_depth, chamfer_size);
        
        // 1. Front Display PCB Pocket (Recessed 4mm from front face)
        translate([0, 0, enclosure_depth - pcb_depth])
            cylinder(d = display_pcb_dia, h = pcb_depth + 0.1);
            
        // 2. Internal Main Electronics Cavity (Houses ESP32-C3 SuperMini & Wiring)
        translate([-cavity_w/2, -cavity_h/2, floor_t])
            cube([cavity_w, cavity_h, enclosure_depth - floor_t - pcb_depth + 0.1]);
            
        // 3. Left-Side USB-C Port Cutout (Direct access to ESP32-C3 port)
        translate([-enclosure_width/2 - 1, -6.0, floor_t + 3.0])
            cube([12.0, 12.0, 7.0]);
            
        // 4. 4 Corner M2 Screw Pilot Holes (10mm deep into corner posts)
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, enclosure_depth - 10.0])
                    cylinder(d = screw_pilot_dia, h = 10.1);
            }
        }
    }
}

// 3. 20-DEGREE ANGLED DESK STAND (Truly Hollow Mating Cradle)
module desk_stand() {
    base_w = 54.0;
    base_d = 58.0;
    base_h = 8.0;
    cradle_h = 24.0;
    
    difference() {
        union() {
            // Weighted Base Plate
            translate([-base_w/2, -base_d/2, 0])
                cube([base_w, base_d, base_h]);
                
            // Upright Angled Support Wedge
            translate([0, 6.0, base_h])
                rotate([tilt_angle, 0, 0])
                translate([-enclosure_width/2 - 2.5, -8.0, 0])
                cube([enclosure_width + 5.0, 16.0, cradle_h]);
        }
        
        // 1. Angled Mating Pocket for Main Housing Pod
        translate([0, 6.0, base_h])
            rotate([tilt_angle, 0, 0])
            translate([-enclosure_width/2 - 0.3, -8.1, 4.0])
            cube([enclosure_width + 0.6, 17.0, cradle_h + 5.0]);
            
        // 2. Rear USB-C Cable Relief Channel
        translate([-7.0, -base_d/2 - 1, -0.1])
            cube([14.0, base_d + 2, 12.0]);
            
        // 3. 4 Corner Anti-Slip Rubber Foot Recesses (8mm dia, 1.2mm deep)
        for (fx = [-base_w/2 + 8, base_w/2 - 8]) {
            for (fy = [-base_d/2 + 8, base_d/2 - 8]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.2, h = 1.3);
            }
        }
    }
}

// --- PART DISPATCH ---
if (part == 1) {
    front_bezel();
} else if (part == 2) {
    main_housing();
} else if (part == 3) {
    desk_stand();
} else {
    // Assembly layout preview
    front_bezel();
    translate([60, 0, 0]) main_housing();
    translate([0, 70, 0]) desk_stand();
}
