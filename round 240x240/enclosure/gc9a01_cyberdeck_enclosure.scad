// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model (Replicating the Cyberdeck Unit 01 Desk Concept)
// Verified directly against GC9A01 1.28" TFT Module Engineering Blueprint
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PARAMETERS ---
part = 0; // 0 = All Assembly Preview, 1 = Front Bezel, 2 = Main Housing, 3 = Sculpted Desk Stand, 4 = Accent Base

// Outer Dimensions (Slim 26mm depth for concept-accurate proportions)
enclosure_width  = 54.0; // Outer width & height (mm)
enclosure_depth  = 26.0; // Slim, sleek pod depth matching concept render (mm)
bezel_thickness  = 4.5;  // Front bezel plate thickness (mm)
chamfer_size     = 6.0;  // Cyberdeck corner chamfers (mm)

// Display Pocket Dimensions (from Engineering Blueprint)
display_active_dia = 32.6; // Active LCD A.A window (32.40mm blueprint + 0.2mm clearance)
display_glass_dia  = 36.0; // Glass / Backlight step (35.6mm blueprint + 0.4mm clearance)
display_pcb_dia    = 38.6; // Circular PCB body (38.0mm blueprint + 0.6mm clearance)
display_tab_w      = 23.6; // Bottom connector tab width (22.92mm blueprint + 0.68mm clearance)
display_tab_h      = 27.0; // Tab height from center (45.5mm total height)
display_pcb_depth  = 4.0;  // Housing front pocket depth (mm)

// Direct Screen Bolting Holes on Bezel (from Engineering Blueprint)
screen_bolt_x      = 9.63;  // Half of 19.26mm hole-to-hole pitch (x = +/-9.63mm)
screen_bolt_y      = -18.91; // Y distance from screen center (mm)
screen_bolt_dia    = 1.8;   // M2 self-tapping pilot or M2 heat-set insert hole (mm)

// Bezel Corner Screws (M2 Socket Cap or Self-Tapping)
screw_bolt_circle  = 42.0; // 42mm center-to-center square (x=+/-21, y=+/-21)
screw_hole_dia     = 2.6;  // M2 / M2.5 clearance through-hole (mm)
screw_head_dia     = 4.8;  // M2 socket cap head counterbore (mm)
screw_head_depth   = 2.2;  // Counterbore pocket depth (mm)
screw_pilot_dia    = 2.0;  // M2 pilot / heat-set insert hole (mm)

// Internal Cavity & ESP32-C3 SuperMini Mounting
cavity_w           = 44.0; // Generous internal width for DuPont wire loops (mm)
cavity_h           = 44.0; // Internal height (mm)
floor_t            = 2.5;  // Rear wall thickness (mm)
esp_l              = 23.0; // ESP32-C3 PCB length along X (mm)
esp_w              = 18.4; // ESP32-C3 SuperMini PCB width along Y (mm)
esp_standoff_h     = 2.5;  // Height above floor for bottom solder joint clearance (mm)

// Stand Parameters
stand_base_w       = 64.0; // Stand base width (mm)
stand_base_d       = 68.0; // Stand base depth (mm)
stand_base_h       = 6.0;  // Tier 1 base plate height (mm)
stand_trunk_h      = 28.0; // Tier 2 pyramidal trunk height (mm)
tilt_angle         = 22.0; // Ergonomic viewing angle (degrees)

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

// Rounded Rectangle Prism
module rounded_rect_prism(w, d, h, r) {
    linear_extrude(height = h) {
        hull() {
            translate([w/2 - r, d/2 - r]) circle(r = r);
            translate([-w/2 + r, d/2 - r]) circle(r = r);
            translate([-w/2 + r, -d/2 + r]) circle(r = r);
            translate([w/2 - r, -d/2 + r]) circle(r = r);
        }
    }
}

// Composite GC9A01 Blueprint PCB Pocket
module gc9a01_blueprint_pocket(h) {
    union() {
        cylinder(d = display_pcb_dia, h = h);
        translate([-display_tab_w / 2, -display_tab_h, 0])
            cube([display_tab_w, display_tab_h, h]);
    }
}

// 1. FRONT BEZEL RING PLATE (with 2 Direct Screen Bolting Holes)
module front_bezel() {
    difference() {
        union() {
            // Main chamfered bezel plate
            octagonal_prism(enclosure_width, bezel_thickness, chamfer_size);
            // Raised decorative cyberdeck bezel trim ring
            translate([0, 0, bezel_thickness])
                cylinder(d = 44.0, h = 1.5);
        }
        
        // 1. Center Screen Active View Window (32.6mm through-hole with 45-deg inner chamfer)
        translate([0, 0, -1])
            cylinder(d1 = display_active_dia + 2.0, d2 = display_active_dia, h = bezel_thickness + 3.0);
            
        // 2. Glass Retention Lip (36.0mm dia x 1.6mm deep)
        translate([0, 0, -0.1])
            cylinder(d = display_glass_dia, h = 1.7);
            
        // 3. PCB Retention Lip (Upper circle + bottom tab)
        translate([0, 0, -0.1])
            gc9a01_blueprint_pocket(1.9);
            
        // 4. 4 Corner M2 Screw Holes with Recessed Counterbores
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, -1])
                    cylinder(d = screw_hole_dia, h = bezel_thickness + 3.0);
                translate([sx, sy, bezel_thickness + 1.6 - screw_head_depth])
                    cylinder(d = screw_head_dia, h = screw_head_depth + 0.1);
            }
        }
        
        // 5. 2 Direct Screen-Retaining Pilot Holes (X = +/-9.63mm, Y = -18.91mm)
        for (sx = [-screen_bolt_x, screen_bolt_x]) {
            translate([sx, screen_bolt_y, 1.8])
                cylinder(d = screen_bolt_dia, h = 3.2);
        }
    }
}

// 2. MAIN HOUSING POD (Slim 26mm Depth, Bottom Wire Drop Trench, Pin-Locking Standoffs)
module main_housing() {
    cavity_depth = enclosure_depth - floor_t - display_pcb_depth; // 19.5mm internal clearance
    esp_center_x = -10.0;
    
    difference() {
        union() {
            // Outer Solid Chassis
            octagonal_prism(enclosure_width, enclosure_depth, chamfer_size);
        }
        
        // 1. Front GC9A01 Display PCB Pocket (Exact Blueprint Outline)
        translate([0, 0, enclosure_depth - display_pcb_depth])
            gc9a01_blueprint_pocket(display_pcb_depth + 0.1);
            
        // 2. Main DuPont & Electronics Cavity (44x44x19.5mm)
        translate([-cavity_w/2, -cavity_h/2, floor_t])
            cube([cavity_w, cavity_h, cavity_depth + 0.1]);
            
        // 3. Bottom DuPont Wire Drop Trench (Direct wire drop under 7-pin header into stand channel)
        translate([-10.0, -29.5, -0.1])
            cube([20.0, 12.0, enclosure_depth + 0.2]);
            
        // 4. Left-Side USB-C Port Cutout
        translate([-enclosure_width/2 - 1, -6.5, floor_t + esp_standoff_h])
            cube([12.0, 13.0, 8.0]);
            
        // 5. 4 Corner M2 Screw Pilot Holes (12mm deep)
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, enclosure_depth - 12.0])
                    cylinder(d = screw_pilot_dia, h = 12.1);
            }
        }
    }
    
    // Internal ESP32-C3 SuperMini Mounting Standoff Rails with 16 Pin-Locking Holes
    difference() {
        union() {
            translate([esp_center_x, 0, floor_t]) {
                // Top standoff rail along Y = +7.62mm (pin row)
                translate([-esp_l/2, 7.62 - 1.7, 0])
                    cube([esp_l, 3.4, esp_standoff_h]);
                    
                // Bottom standoff rail along Y = -7.62mm (pin row)
                translate([-esp_l/2, -7.62 - 1.7, 0])
                    cube([esp_l, 3.4, esp_standoff_h]);
                    
                // Rear thrust stop block (+X end)
                translate([esp_l/2, -esp_w/2, 0])
                    cube([2.5, esp_w, esp_standoff_h + 3.0]);
            }
        }
        
        // 16 Pin Locking Holes (2 rows of 8 holes at 2.54mm pitch)
        for (k = [0:7]) {
            px = -18.3 + k * 2.54;
            translate([px, 7.62, floor_t + esp_standoff_h - 2.0])
                cylinder(d = 1.5, h = 2.1);
            translate([px, -7.62, floor_t + esp_standoff_h - 2.0])
                cylinder(d = 1.5, h = 2.1);
        }
    }
}

// 3. SCULPTED CONCEPT DESK STAND CRADLE (Two-Tier Pedestal with 22° V-Saddle & Cable Channel)
module desk_stand() {
    difference() {
        union() {
            // Tier 1: Rounded Base Plate (Wood/Accent Tier)
            rounded_rect_prism(stand_base_w, stand_base_d, stand_base_h, 6.0);
            
            // Tier 2: Tapered Pyramidal Trunk
            translate([0, 0, stand_base_h])
                linear_extrude(height = stand_trunk_h, scale = [0.92, 0.90])
                polygon([
                    [-27.0, -29.0], [27.0, -29.0],
                    [29.0, -27.0],  [29.0, 27.0],
                    [27.0, 29.0],   [-27.0, 29.0],
                    [-29.0, 27.0],  [-29.0, -27.0]
                ]);
        }
        
        // 1. 22-Degree Angled V-Saddle Cradle Pocket
        translate([0, 6.0, stand_base_h + 10.0])
            rotate([tilt_angle, 0, 0])
            octagonal_prism(enclosure_width + 0.8, 35.0, 6.2);
            
        // 2. Rear & Bottom USB-C & DuPont Cable Relief Channel (20mm wide)
        translate([-10.0, -stand_base_d/2 - 1, -0.1])
            cube([20.0, stand_base_d + 2, 14.0]);
            
        // 3. 4 Bottom Rubber Foot Recesses (8.2mm dia, 1.4mm deep)
        for (fx = [-stand_base_w/2 + 10, stand_base_w/2 - 10]) {
            for (fy = [-stand_base_d/2 + 10, stand_base_d/2 - 10]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.2, h = 1.5);
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
    // Assembly Preview Mode matching render
    translate([0, 0, 26.0])
        color("#22252B") front_bezel();
    color("#181A1F") main_housing();
    translate([0, -16.0, -26.0])
        color("#2E3440") desk_stand();
}
