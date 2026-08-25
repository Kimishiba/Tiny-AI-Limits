// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model (Replicating the Cyberdeck Unit 01 Desk Concept)
// 100% Support-Free FDM 3D Printable Architecture (Exact Render Geometry)
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PARAMETERS ---
part = 0; // 0 = Assembly Preview, 1 = Front Bezel, 2 = Main Housing, 3 = Stand Tier 1 Base, 4 = Stand Tier 2 Trunk, 5 = Monolithic Stand

// Outer Dimensions
enclosure_width  = 54.0; // Outer width & height (mm)
housing_depth    = 27.5; // Open-tub housing depth (+3mm extra wire/DuPont clearance) (mm)

bezel_thickness  = 5.5;  // Display carrier front bezel plate thickness (mm)
chamfer_size     = 6.0;  // Cyberdeck corner chamfers (mm)
outer_chamfer    = 1.2;  // Standard perimeter 45-degree outer edge chamfer (mm)

// Display Pocket Dimensions (from Engineering Blueprint + generous 3D print clearance)
display_active_dia = 33.0; // Active LCD A.A clearing diameter at glass plane (+0.1mm clearance) (mm)
display_funnel_top = 38.6; // Wide front opening diameter (36.4° conical anti-shadow slope) (mm)
display_glass_dia  = 36.4; // Glass / Backlight step (35.6mm blueprint + 0.8mm clearance [+0.1mm extra])
display_pcb_dia    = 39.0; // Circular PCB body (38.0mm blueprint + 1.0mm clearance [+0.1mm extra])
display_tab_w      = 24.0; // Bottom connector tab width (22.92mm blueprint + 1.08mm clearance)
display_tab_h      = 26.6; // Tab height from center (45.6mm total height)
display_top_tab_w  = 18.0; // Top clearance notch width for screen protrusion / ribbon / extra material (mm)
display_top_tab_h  = 23.0; // Top notch height from center (mm)
display_pcb_depth  = 3.3;  // Bezel rear pocket depth (+0.1mm depth clearance) (mm)


// Direct Screen Bolting Blind Pilot Holes (1.75mm dia for M2 plastic thread grip)
screen_bolt_x      = 9.63;  // Half of 19.26mm hole-to-hole pitch (x = +/-9.63mm)
screen_bolt_y      = -18.91; // Y distance from screen center (mm)
screen_bolt_dia    = 1.75;  // 1.75mm blind pilot holes (does NOT punch through front face)
screen_bolt_depth  = 3.2;   // Blind depth from rear pocket (leaving solid front face)

// Bezel Corner Screws (M3 Socket Cap Screws)
screw_bolt_circle  = 39.0; // 39mm center-to-center square (x=+/-19.50, y=+/-19.50)
screw_hole_dia     = 3.4;  // M3 clearance through-hole (mm)
screw_head_dia     = 6.2;  // M3 socket cap head counterbore (mm)
screw_head_depth   = 3.2;  // Counterbore pocket depth (mm)
screw_pilot_dia    = 2.8;  // M3 pilot / self-tapping / heat-set insert hole (mm)

// Internal Cavity & ESP32-C3 SuperMini Mounting (Lowered)
cavity_w           = 46.0; // 46mm wide internal bay (mm)
cavity_chamfer     = 13.0; // 13.0mm corner chamfers leaving massive corner screw pillars (mm)
floor_t            = 2.5;  // Rear wall thickness (mm)
esp_l              = 23.0; // ESP32-C3 PCB length along X (mm)
esp_w              = 18.4; // ESP32-C3 SuperMini PCB width along Y (mm)
esp_standoff_h     = 2.5;  // ESP32 standoff rail height (mm)
usbc_center_z      = 8.25; // Elevated USB-C port centerline with ample clearance (mm)


// Stand Parameters (Exact Concept Render Proportions)
stand_base_w       = 64.0; // Tier 1 base width (mm)
stand_base_d       = 68.0; // Tier 1 base depth (mm)
stand_base_h       = 5.0;  // Tier 1 base height (mm)
stand_trunk_h      = 24.0; // Tier 2 cradle trunk height (mm) (total 29.0mm stand height)
stand_tilt_deg     = 22.0; // Backward tilt angle from vertical (degrees)
pin_dist_x         = 20.0; // Alignment pillar X distance from center (mm)
pin_dist_y         = 21.0; // Alignment pillar Y distance from center (mm)
pin_dia            = 5.0;  // Alignment pillar diameter (mm)
pin_h              = 3.5;  // Alignment pillar height (mm)

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

// Chamfered Octagonal Base with Perimeter Chamfer
module chamfered_octagonal_base(w, h, c, ch, chamfer_top=true) {
    hw1 = w / 2;
    hw2 = (w - 2 * ch) / 2;
    c2 = c - ch * 0.414;
    
    if (chamfer_top) {
        hull() {
            linear_extrude(height = h - ch) {
                polygon([
                    [-hw1 + c, -hw1], [hw1 - c, -hw1],
                    [hw1, -hw1 + c],  [hw1, hw1 - c],
                    [hw1 - c, hw1],   [-hw1 + c, hw1],
                    [-hw1, hw1 - c],  [-hw1, -hw1 + c]
                ]);
            }
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
    } else {
        hull() {
            linear_extrude(height = 0.01) {
                polygon([
                    [-hw2 + c2, -hw2], [hw2 - c2, -hw2],
                    [hw2, -hw2 + c2],  [hw2, hw2 - c2],
                    [hw2 - c2, hw2],   [-hw2 + c2, hw2],
                    [-hw2, hw2 - c2],  [-hw2, -hw2 + c2]
                ]);
            }
            translate([0, 0, ch]) {
                linear_extrude(height = h - ch) {
                    polygon([
                        [-hw1 + c, -hw1], [hw1 - c, -hw1],
                        [hw1, -hw1 + c],  [hw1, hw1 - c],
                        [hw1 - c, hw1],   [-hw1 + c, hw1],
                        [-hw1, hw1 - c],  [-hw1, -hw1 + c]
                    ]);
                }
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

// Composite GC9A01 Blueprint PCB Pocket with Top Relief Notch
module gc9a01_blueprint_pocket(h) {
    union() {
        cylinder(d = display_pcb_dia, h = h);
        // Bottom connector tab
        translate([-display_tab_w / 2, -display_tab_h, 0])
            cube([display_tab_w, display_tab_h, h]);
        // Top extra material relief notch
        translate([-display_top_tab_w / 2, 0, 0])
            cube([display_top_tab_w, display_top_tab_h, h]);
    }
}

// Internal Blind Snap Detent Bead (Molded directly into inside wall of pocket at Z = 3.3mm)
module internal_snap_detent(angle) {
    rotate([0, 0, angle]) translate([0, display_pcb_dia / 2 - 0.25, display_pcb_depth]) {
        // Smooth rounded detent bead with gradual lead-in ramp
        rotate([90, 0, 0])
            cylinder(r = 0.5, h = 1.0, center = true);
    }
}

// Lowered Precision Oval USB-C Cutter with Accentuated Lead-In Chamfer
module usbc_stadium_cutter() {
    hull() {
        translate([-32.0, -3.0, usbc_center_z]) rotate([0, 90, 0]) cylinder(r = 2.75, h = 16.0);
        translate([-32.0, 3.0, usbc_center_z])  rotate([0, 90, 0]) cylinder(r = 2.75, h = 16.0);
    }
    hull() {
        translate([-29.0, -3.0, usbc_center_z]) rotate([0, 90, 0]) cylinder(r1 = 4.5, r2 = 2.75, h = 3.5);
        translate([-29.0, 3.0, usbc_center_z])  rotate([0, 90, 0]) cylinder(r1 = 4.5, r2 = 2.75, h = 3.5);
    }
}

// 1. FRONT BEZEL RING PLATE (100% Solid Front Face, Internal Blind Snap Detents)
module front_bezel() {
    oal_t = bezel_thickness + 1.5;
    
    difference() {
        union() {
            chamfered_octagonal_base(enclosure_width, bezel_thickness, chamfer_size, outer_chamfer, chamfer_top=true);
            translate([0, 0, bezel_thickness])
                cylinder(d1 = 44.0, d2 = 41.0, h = 1.5);
            
            // Internal Blind Retention Detents (100% inside pocket, zero front cuts)
            internal_snap_detent(40);
            internal_snap_detent(-40);
            internal_snap_detent(130);
            internal_snap_detent(-130);
        }
        
        // 1. Wide Sloping Conical Anti-Shadow Aperture
        translate([0, 0, -1])
            cylinder(d1 = display_active_dia - 2.0, d2 = display_funnel_top + 1.0, h = oal_t + 2.0);
            
        // 2. Glass Retention Lip
        translate([0, 0, -0.1])
            cylinder(d = display_glass_dia, h = 1.8);
            
        // 3. PCB Retention Pocket with Top & Bottom Relief (100% Blind Pocket, Zero Through Cuts)
        translate([0, 0, -0.1])
            gc9a01_blueprint_pocket(display_pcb_depth + 0.1);
            
        // 4. 4 Corner M3 Screw Holes with Recessed Counterbores
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, -1])
                    cylinder(d = screw_hole_dia, h = bezel_thickness + 3.0);
                translate([sx, sy, oal_t - screw_head_depth])
                    cylinder(d = screw_head_dia, h = screw_head_depth + 0.1);
            }
        }
        
        // 5. 2 Blind 1.75mm M2 Screen Pilot Holes
        for (sx = [-screen_bolt_x, screen_bolt_x]) {
            translate([sx, screen_bolt_y, -0.1])
                cylinder(d = screen_bolt_dia, h = screen_bolt_depth);
        }
    }
}

// 2. MAIN HOUSING POD (Lowered USB-C with Accentuated Chamfer, 1.2mm Bottom Chamfer)

module main_housing() {
    cavity_depth = housing_depth - floor_t;
    esp_center_x = -10.0;
    
    difference() {
        union() {
            chamfered_octagonal_base(enclosure_width, housing_depth, chamfer_size, outer_chamfer, chamfer_top=false);
        }
        
        // 1. Chamfered Open Tub Cavity
        translate([0, 0, floor_t])
            octagonal_prism(cavity_w, cavity_depth + 0.1, cavity_chamfer);
            
        // 2. Lowered Precision Chamfered Oval/Stadium USB-C Port Cutout
        usbc_stadium_cutter();
            
        // 3. DuPont Connector & Wire Clearance Trench (26.0mm wide x 5.0mm deep, Z = floor_t to top)
        translate([-13.0, -26.0, floor_t])
            cube([26.0, 5.0, cavity_depth + 0.1]);
            
        // 4. 4 Corner M3 Screw Pilot Holes

        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, housing_depth - 15.0])
                    cylinder(d = screw_pilot_dia, h = 15.1);
            }
        }
    }
    
    // Internal ESP32-C3 SuperMini Lowered Standoff Rails (1.4mm)
    difference() {
        union() {
            translate([esp_center_x, 0, floor_t]) {
                translate([-esp_l/2, 7.62 - 1.7, 0])
                    cube([esp_l, 3.4, esp_standoff_h]);
                translate([-esp_l/2, -7.62 - 1.7, 0])
                    cube([esp_l, 3.4, esp_standoff_h]);
                translate([esp_l/2, -esp_w/2, 0])
                    cube([2.5, esp_w, esp_standoff_h + 3.0]);
            }
        }
        
        for (k = [0:7]) {
            px = -18.3 + k * 2.54;
            translate([px, 7.62, floor_t + esp_standoff_h - 2.0])
                cylinder(d = 1.5, h = 2.1);
            translate([px, -7.62, floor_t + esp_standoff_h - 2.0])
                cylinder(d = 1.5, h = 2.1);
        }
    }
}

// 3. STAND TIER 1 BASE PLATE (with 4 Protruding Alignment Pillars)
module stand_tier1_base() {
    difference() {
        union() {
            rounded_rect_prism(stand_base_w, stand_base_d, stand_base_h, 6.0);
            
            for (px = [-pin_dist_x, pin_dist_x]) {
                for (py = [-pin_dist_y, pin_dist_y]) {
                    translate([px, py, stand_base_h])
                        cylinder(d1 = pin_dia, d2 = pin_dia - 1.0, h = pin_h);
                }
            }
        }
        
        for (fx = [-stand_base_w/2 + 10, stand_base_w/2 - 10]) {
            for (fy = [-stand_base_d/2 + 10, stand_base_d/2 - 10]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.2, h = 1.5);
            }
        }
    }
}

// 4. STAND TIER 2 MONOLITHIC PEDESTAL TRUNK (Deep V-Saddle Cradle)
module stand_tier2_trunk() {
    difference() {
        hull() {
            translate([0, 0, stand_base_h])
                rounded_rect_prism(62.0, 66.0, 0.01, 5.0);
            translate([0, 0, stand_base_h + stand_trunk_h - 0.01])
                rounded_rect_prism(54.0, 58.0, 0.01, 3.5);
        }
        
        // 4 Mating Slide Sockets on Bottom Face
        for (px = [-pin_dist_x, pin_dist_x]) {
            for (py = [-pin_dist_y, pin_dist_y]) {
                translate([px, py, stand_base_h - 0.1])
                    cylinder(d = pin_dia + 0.4, h = pin_h + 0.6);
            }
        }
        
        // Deep Negative Cradle Slot for Full 33.0mm Assembled Pod (34.2mm depth with slide clearance)
        translate([0, -4.0, 42.40])
            rotate([90.0 - stand_tilt_deg, 0, 180.0])
            octagonal_prism(enclosure_width + 0.8, 34.2, 6.0);
    }
}

// --- PART DISPATCH ---
if (part == 1) {
    front_bezel();
} else if (part == 2) {
    main_housing();
} else if (part == 3) {
    stand_tier1_base();
} else if (part == 4) {
    stand_tier2_trunk();
} else {
    // Complete Multi-Part Assembly Preview (22° Ergonomic Desktop Stance)
    translate([0, -4.0, 42.40])
        rotate([90.0 - stand_tilt_deg, 0, 180.0]) {
            translate([0, 0, 27.5]) color("#22252B") front_bezel();
            color("#181A1F") main_housing();
        }
    color("#5c4033") stand_tier1_base();
    color("#2E3440") stand_tier2_trunk();
}

