// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model (Replicating the Cyberdeck Unit 01 Desk Concept)
// 100% Support-Free FDM 3D Printable Architecture
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PARAMETERS ---
part = 0; // 0 = All Assembly Preview, 1 = Front Bezel, 2 = Main Housing, 3 = Sculpted Desk Stand, 4 = Accent Base

// Outer Dimensions
enclosure_width  = 54.0; // Outer width & height (mm)
housing_depth    = 24.5; // Open-tub housing depth (mm)
bezel_thickness  = 5.5;  // Display carrier front bezel plate thickness (mm)
chamfer_size     = 6.0;  // Cyberdeck corner chamfers (mm)
outer_chamfer    = 1.2;  // Front perimeter 45-degree outer edge chamfer (mm)

// Display Pocket Dimensions (from Engineering Blueprint)
display_active_dia = 32.6; // Active LCD A.A window (32.40mm blueprint + 0.2mm clearance)
display_glass_dia  = 36.0; // Glass / Backlight step (35.6mm blueprint + 0.4mm clearance)
display_pcb_dia    = 38.6; // Circular PCB body (38.0mm blueprint + 0.6mm clearance)
display_tab_w      = 23.6; // Bottom connector tab width (22.92mm blueprint + 0.68mm clearance)
display_tab_h      = 26.5; // Tab height from center (45.5mm total height)
display_pcb_depth  = 3.2;  // Bezel rear pocket depth (mm)

// Direct Screen Bolting Blind Pilot Holes (1.75mm dia for M2 plastic thread grip)
screen_bolt_x      = 9.63;  // Half of 19.26mm hole-to-hole pitch (x = +/-9.63mm)
screen_bolt_y      = -18.91; // Y distance from screen center (mm)
screen_bolt_dia    = 1.75;  // 1.75mm blind pilot holes (does NOT punch through front face)
screen_bolt_depth  = 3.2;   // Blind depth from rear pocket (leaving solid front face)

// Bezel Corner Screws (M2 Socket Cap or Self-Tapping)
screw_bolt_circle  = 42.0; // 42mm center-to-center square (x=+/-21, y=+/-21)
screw_hole_dia     = 2.6;  // M2 / M2.5 clearance through-hole (mm)
screw_head_dia     = 4.8;  // M2 socket cap head counterbore (mm)
screw_head_depth   = 2.2;  // Counterbore pocket depth (mm)
screw_pilot_dia    = 2.0;  // M2 pilot / heat-set insert hole (mm)

// Internal Cavity & ESP32-C3 SuperMini Mounting
cavity_w           = 46.0; // 46mm wide internal bay (mm)
cavity_chamfer     = 11.5; // 11.5mm corner chamfers to preserve massive solid corner pillars (mm)
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

// Chamfered Octagonal Prism
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

// Chamfered Octagonal Base with Front Perimeter Chamfer
module chamfered_octagonal_base(w, h, c, ch) {
    hw1 = w / 2;
    hw2 = (w - 2 * ch) / 2;
    c2 = c - ch * 0.414;
    
    hull() {
        // Lower vertical section
        linear_extrude(height = h - ch) {
            polygon([
                [-hw1 + c, -hw1], [hw1 - c, -hw1],
                [hw1, -hw1 + c],  [hw1, hw1 - c],
                [hw1 - c, hw1],   [-hw1 + c, hw1],
                [-hw1, hw1 - c],  [-hw1, -hw1 + c]
            ]);
        }
        // Upper chamfered section
        translate([0, 0, h - 0.01]) {
            linear_extrude(height = 0.01) {
                polygon([
                    [-hw2 + c2, -hw2], [hw2 - c2, -hw2],
                    [hw2, -hw2 + c2],  [hw2, hw2 - c2],
                    [hw2 - c2, hw2],   [-hw2 + c2, hw2],
                    [-hw2, hw2 - c2],  [-hw2, -hw2 + c2]
                ]);
            }
        }
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

// 1. FRONT BEZEL RING PLATE (Chamfered Outer Edges & Chamfered Bezel Trim Ring)
module front_bezel() {
    difference() {
        union() {
            // Main chamfered bezel plate with 45-deg outer edge chamfers
            chamfered_octagonal_base(enclosure_width, bezel_thickness, chamfer_size, outer_chamfer);
            // Raised decorative cyberdeck bezel trim ring with 45-deg outer chamfer (dia 44mm to dia 41mm)
            translate([0, 0, bezel_thickness])
                cylinder(d1 = 44.0, d2 = 41.0, h = 1.5);
        }
        
        // 1. Center Screen Active View Window (32.6mm through-hole with 45-deg inner chamfer)
        translate([0, 0, -1])
            cylinder(d1 = display_active_dia + 2.4, d2 = display_active_dia, h = bezel_thickness + 3.0);
            
        // 2. Glass Retention Lip (36.0mm dia x 1.6mm deep)
        translate([0, 0, -0.1])
            cylinder(d = display_glass_dia, h = 1.7);
            
        // 3. PCB Retention Lip (Upper circle + bottom tab, depth 3.2mm into bezel)
        translate([0, 0, -0.1])
            gc9a01_blueprint_pocket(display_pcb_depth + 0.1);
            
        // 4. 4 Corner M2 Screw Holes with Recessed Counterbores
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, -1])
                    cylinder(d = screw_hole_dia, h = bezel_thickness + 3.0);
                translate([sx, sy, bezel_thickness + 1.6 - screw_head_depth])
                    cylinder(d = screw_head_dia, h = screw_head_depth + 0.1);
            }
        }
        
        // 5. 2 Blind 1.75mm M2 Thread-Gripping Pilot Holes (from back z = -0.1 to z = 3.2)
        for (sx = [-screen_bolt_x, screen_bolt_x]) {
            translate([sx, screen_bolt_y, -0.1])
                cylinder(d = screen_bolt_dia, h = screen_bolt_depth);
        }
    }
}

// 2. MAIN HOUSING POD (Open Tub, Massive Corner Pillars, 4 Open M2 Screw Holes)
module main_housing() {
    cavity_depth = housing_depth - floor_t; // 22.0mm continuous vertical cavity
    esp_center_x = -10.0;
    
    difference() {
        union() {
            // Outer Solid Chassis
            octagonal_prism(enclosure_width, housing_depth, chamfer_size);
        }
        
        // 1. Chamfered Open Tub Cavity (width = 46mm, corner chamfer = 11.5mm leaving solid corner pillars)
        translate([0, 0, floor_t])
            octagonal_prism(cavity_w, cavity_depth + 0.1, cavity_chamfer);
            
        // 2. Left-Side USB-C Port Cutout
        translate([-enclosure_width/2 - 1, -6.5, floor_t + esp_standoff_h])
            cube([12.0, 13.0, 8.0]);
            
        // 3. 4 Corner M2 Screw Pilot Holes (14mm deep at +/-21mm)
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, housing_depth - 14.0])
                    cylinder(d = screw_pilot_dia, h = 14.1);
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
            
        // 2. Rear USB-C Cable Relief Channel (16mm wide)
        translate([-8.0, -stand_base_d/2 - 1, -0.1])
            cube([16.0, stand_base_d + 2, 14.0]);
            
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
    translate([0, 0, 24.5])
        color("#22252B") front_bezel();
    color("#181A1F") main_housing();
    translate([0, -16.0, -26.0])
        color("#2E3440") desk_stand();
}
