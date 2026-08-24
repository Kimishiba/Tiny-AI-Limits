// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model (Redesigned for DuPont Cable & Upward Pin Clearances)
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PARAMETERS ---
part = 0; // 0 = All Assembly Preview, 1 = Front Bezel, 2 = Main Housing, 3 = Modular Desk Stand

// Outer Dimensions
enclosure_width  = 54.0; // Outer width & height (mm)
enclosure_depth  = 36.0; // Deepened pod for upward DuPont clearance (mm)
bezel_thickness  = 4.5;  // Front bezel plate thickness (mm)
chamfer_size     = 6.0;  // Cyberdeck corner chamfers (mm)

// Display Pocket
display_active_dia = 32.8; // 1.28" visible active area window
display_pcb_dia    = 37.2; // GC9A01 PCB outer diameter + tolerance (mm)
display_recess_lip = 1.8;  // Front bezel retention step depth (mm)
display_pcb_depth  = 4.0;  // Housing front pocket depth (mm)

// Screw Mounting (M2 Socket Cap or Self-Tapping)
screw_bolt_circle  = 42.0; // 42mm center-to-center square (x=+/-21, y=+/-21)
screw_hole_dia     = 2.6;  // M2 / M2.5 clearance through-hole (mm)
screw_head_dia     = 4.8;  // M2 socket cap head counterbore (mm)
screw_head_depth   = 2.2;  // Counterbore pocket depth (mm)
screw_pilot_dia    = 2.0;  // M2 pilot / heat-set insert hole (mm)

// Internal Cavity & ESP32-C3 SuperMini Mounting
cavity_w           = 44.0; // Generous internal width for DuPont wire loops (mm)
cavity_h           = 44.0; // Internal height (mm)
floor_t            = 2.5;  // Rear wall thickness (mm)
esp_w              = 18.4; // ESP32-C3 SuperMini PCB width + tolerance (mm)
esp_l              = 23.0; // ESP32-C3 PCB length (mm)
esp_standoff_h     = 2.5;  // Height above floor for bottom solder joint clearance (mm)

// Stand Parameters
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
            // Main chamfered bezel plate
            octagonal_prism(enclosure_width, bezel_thickness, chamfer_size);
            // Raised decorative cyberdeck bezel trim ring
            translate([0, 0, bezel_thickness])
                cylinder(d = 44.0, h = 1.5);
        }
        
        // 1. Center Screen Active View Window (Through-hole with 45-deg inner chamfer)
        translate([0, 0, -1])
            cylinder(d1 = display_active_dia + 2.0, d2 = display_active_dia, h = bezel_thickness + 3.0);
            
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

// 2. MAIN HOUSING POD (36mm Deep, DuPont Cable Loop Channels & ESP32 Seat)
module main_housing() {
    cavity_depth = enclosure_depth - floor_t - display_pcb_depth; // 29.5mm internal clearance
    
    difference() {
        union() {
            // Outer Solid Chassis
            octagonal_prism(enclosure_width, enclosure_depth, chamfer_size);
        }
        
        // 1. Front Display PCB Pocket (Recessed from front face)
        translate([0, 0, enclosure_depth - display_pcb_depth])
            cylinder(d = display_pcb_dia, h = display_pcb_depth + 0.1);
            
        // 2. Main DuPont & Electronics Cavity
        translate([-cavity_w/2, -cavity_h/2, floor_t])
            cube([cavity_w, cavity_h, cavity_depth + 0.1]);
            
        // 3. Left-Side USB-C Port Cutout (13mm x 8mm with generous overmold clearance)
        translate([-enclosure_width/2 - 1, -6.5, floor_t + esp_standoff_h])
            cube([12.0, 13.0, 8.0]);
            
        // 4. 4 Corner M2 Screw Pilot Holes (14mm deep into solid corner posts)
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, enclosure_depth - 14.0])
                    cylinder(d = screw_pilot_dia, h = 14.1);
            }
        }
    }
    
    // Internal ESP32-C3 SuperMini Mounting Standoff Rails
    translate([-esp_w/2, -esp_l/2, floor_t]) {
        // Left guide rail
        difference() {
            cube([2.0, esp_l, esp_standoff_h + 3.0]);
            translate([-0.1, 4.0, esp_standoff_h])
                cube([2.2, 15.0, 4.0]); // Cutout for side pins
        }
        // Right guide rail
        translate([esp_w - 2.0, 0, 0])
        difference() {
            cube([2.0, esp_l, esp_standoff_h + 3.0]);
            translate([-0.1, 4.0, esp_standoff_h])
                cube([2.2, 15.0, 4.0]); // Cutout for side pins
        }
        // Bottom support pads
        cube([esp_w, 3.0, esp_standoff_h]);
        translate([0, esp_l - 3.0, 0])
            cube([esp_w, 3.0, esp_standoff_h]);
    }
}

// 3. MODULAR 20-DEGREE ANGLED DESK STAND CRADLE
module desk_stand() {
    base_w = 62.0;
    base_d = 68.0;
    base_h = 10.0;
    cradle_h = 30.0;
    
    difference() {
        union() {
            // Weighted Base Plate with Top Chamfers
            translate([-base_w/2, -base_d/2, 0])
                cube([base_w, base_d, base_h]);
                
            // Upright Angled Support Wedge
            translate([0, 8.0, base_h])
                rotate([tilt_angle, 0, 0])
                translate([-enclosure_width/2 - 3.0, -10.0, 0])
                cube([enclosure_width + 6.0, 20.0, cradle_h]);
        }
        
        // 1. Angled Mating Pocket for Deepened Main Housing Pod (0.4mm clearance)
        translate([0, 8.0, base_h])
            rotate([tilt_angle, 0, 0])
            translate([-enclosure_width/2 - 0.4, -10.1, 5.0])
            cube([enclosure_width + 0.8, 20.5, cradle_h + 10.0]);
            
        // 2. Rear USB-C Cable Relief Channel (16mm wide)
        translate([-8.0, -base_d/2 - 1, -0.1])
            cube([16.0, base_d + 2, 14.0]);
            
        // 3. 4 Corner Anti-Slip Rubber Foot Recesses (8.2mm dia, 1.3mm deep)
        for (fx = [-base_w/2 + 9, base_w/2 - 9]) {
            for (fy = [-base_d/2 + 9, base_d/2 - 9]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.2, h = 1.4);
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
    // Assembly Preview Mode
    color("#22252B") front_bezel();
    translate([0, 0, -enclosure_depth])
        color("#181A1F") main_housing();
    translate([0, -22.0, -enclosure_depth - 15.0])
        color("#2E3440") desk_stand();
}
