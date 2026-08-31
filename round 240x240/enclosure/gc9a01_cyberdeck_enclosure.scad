// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini Cyberdeck Enclosure
// Parametric OpenSCAD Source Model (Replicating the Cyberdeck Unit 01 Desk Concept)
// 100% Support-Free FDM 3D Printable Architecture
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PARAMETERS ---
part = is_undef(part) ? 2 : part; // 0 = Assembly Preview, 1 = Front Bezel, 2 = Main Housing (V2.0), 3 = Mid Clamp, 4 = Stand Tier 1 Base, 5 = Stand Tier 2 Trunk, 6 = Monolithic Pedestal Stand, 7 = Minimalist Cradle Stand

// Outer Dimensions
enclosure_width  = 54.4; // Outer width & height (mm) — 54.4mm yields exact 1.2mm (3x 0.4mm perimeters) thin walls
housing_depth    = 27.5; // Open-tub housing depth (mm)
bezel_thickness  = 5.5;  // Display carrier front bezel plate thickness (mm)
chamfer_size     = 6.0;  // Cyberdeck corner chamfers (mm)
outer_chamfer    = 1.2;  // Standard perimeter 45-degree outer edge chamfer (mm)

// Display Pocket Dimensions
display_active_dia = 33.0; // Active LCD A.A clearing diameter at glass plane (mm)
display_funnel_top = 38.8; // Wide front opening diameter (36.4° conical anti-shadow slope) (mm)
display_glass_dia  = 36.6; // Glass / Backlight step (mm)
display_pcb_dia    = 39.4; // Circular PCB body (38.0mm blueprint + 1.4mm clearance) (mm)
display_tab_w      = 24.0; // Bottom connector tab width (mm)
display_tab_h      = 26.6; // Tab height from center (mm)
display_top_tab_w  = 24.0; // Top clearance notch width (mm)
display_top_tab_h  = 26.0; // Top notch height from center (mm)
display_pcb_depth  = 3.4;  // Bezel rear pocket depth (mm)

// Mid Clamp Sandwich Plate Parameters
mid_clamp_thickness = 2.0;  // Mid clamp sandwich plate thickness (mm)
mid_clamp_lip_h     = 0.6;  // Forward circular compression collar protrusion (mm)
mid_clamp_inner_dia = 34.0; // Central component clearance opening (mm)
mid_clamp_outer_dia = 38.6; // Outer compression rim diameter (mm)

// Direct Screen Bolting Blind Pilot Holes
screen_bolt_x      = 9.63;  // Half of 19.26mm hole-to-hole pitch (mm)
screen_bolt_y      = -18.91; // Y distance from screen center (mm)
screen_bolt_dia    = 1.75;  // Blind pilot holes (mm)
screen_bolt_depth  = 3.2;   // Blind depth from rear pocket (mm)

// Bezel Corner Screws (M3 Socket Cap Screws)
screw_bolt_circle  = 41.0; // 41mm center-to-center square (x=+/-20.50, y=+/-20.50)
screw_hole_dia     = 3.4;  // M3 clearance through-hole (mm)
screw_head_dia     = 6.2;  // M3 socket cap head counterbore (mm)
screw_head_depth   = 3.2;  // Counterbore pocket depth (mm)
screw_pilot_dia    = 2.8;  // M3 pilot / self-tapping hole (mm)

// Internal Cavity & ESP32-C3 SuperMini Mounting
cavity_w           = 48.0; // 48mm wide internal bay (3.0mm slim perimeter walls) (mm)
cavity_chamfer     = 12.0; // 12.0mm corner chamfers (mm)
floor_t            = 2.0;  // Rear wall floor thickness (mm)
esp_l              = 23.0; // ESP32-C3 PCB length along X (mm)
esp_w              = 18.4; // ESP32-C3 SuperMini PCB width along Y (mm)
esp_standoff_h     = 3.2;  // ESP32 standoff rail height (mm)
esp_center_x       = -10.0;// Center offset along X (mm)
usbc_center_z      = 9.50; // USB-C port centerline (mm)

// Stand Parameters
stand_base_w       = 64.0; // Tier 1 base width (mm)
stand_base_d       = 68.0; // Tier 1 base depth (mm)
stand_base_h       = 5.0;  // Tier 1 base height (mm)
stand_trunk_h      = 24.0; // Tier 2 cradle trunk height (mm)
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
            translate([0, 0, h - 0.001])
            linear_extrude(height = 0.001) {
                polygon([
                    [-hw2 + c2, -hw2], [hw2 - c2, -hw2],
                    [hw2, -hw2 + c2],  [hw2, hw2 - c2],
                    [hw2 - c2, hw2],   [-hw2 + c2, hw2],
                    [-hw2, hw2 - c2],  [-hw2, -hw2 + c2]
                ]);
            }
        }
    } else {
        hull() {
            linear_extrude(height = 0.001) {
                polygon([
                    [-hw2 + c2, -hw2], [hw2 - c2, -hw2],
                    [hw2, -hw2 + c2],  [hw2, hw2 - c2],
                    [hw2 - c2, hw2],   [-hw2 + c2, hw2],
                    [-hw2, hw2 - c2],  [-hw2, -hw2 + c2]
                ]);
            }
            translate([0, 0, ch])
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

// Rounded Rectangular Prism
module rounded_rect_prism(w, d, h, r) {
    hw = w / 2 - r;
    hd = d / 2 - r;
    linear_extrude(height = h) {
        hull() {
            translate([hw, hd]) circle(r = r);
            translate([-hw, hd]) circle(r = r);
            translate([-hw, -hd]) circle(r = r);
            translate([hw, -hd]) circle(r = r);
        }
    }
}

// Precision Oval/Stadium USB-C Cutter with Accentuated Lead-in Chamfer
module usbc_stadium_cutter() {
    // Outer to inner through-wall tunnel (stops at flat recessed wall X = -26.0)
    translate([-32.0, 0, usbc_center_z]) {
        rotate([0, 90, 0]) {
            hull() {
                translate([0, -3.0, 0]) cylinder(r = 2.75, h = 6.2);
                translate([0, 3.0, 0])  cylinder(r = 2.75, h = 6.2);
            }
        }
    }
    // External lead-in entry chamfer on outside wall (X = -27.2 to -26.0)
    translate([-29.2, 0, usbc_center_z]) {
        rotate([0, 90, 0]) {
            hull() {
                translate([0, -3.0, 0]) cylinder(r1 = 4.25, r2 = 2.75, h = 2.0);
                translate([0, 3.0, 0])  cylinder(r1 = 4.25, r2 = 2.75, h = 2.0);
            }
        }
    }
}

// 1. FRONT BEZEL PLATE
module front_bezel() {
    difference() {
        union() {
            chamfered_octagonal_base(enclosure_width, bezel_thickness, chamfer_size, outer_chamfer, chamfer_top=true);
            translate([0, 0, bezel_thickness])
                cylinder(r1 = 22.0, r2 = 20.5, h = 1.5);
        }
        
        translate([0, 0, -1.0])
            cylinder(r1 = display_active_dia/2, r2 = display_funnel_top/2, h = bezel_thickness + 1.5 + 2.0);
            
        translate([0, 0, -0.1])
            cylinder(d = display_pcb_dia, h = display_pcb_depth + 0.1);
        translate([-display_tab_w/2, -display_tab_h, -0.1])
            cube([display_tab_w, display_tab_h, display_pcb_depth + 0.1]);
        translate([-display_top_tab_w/2, 0, -0.1])
            cube([display_top_tab_w, display_top_tab_h, display_pcb_depth + 0.1]);
            
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, -1.0])
                    cylinder(d = screw_hole_dia, h = bezel_thickness + 4.0);
                translate([sx, sy, bezel_thickness + 1.5 - screw_head_depth])
                    cylinder(d = screw_head_dia, h = screw_head_depth + 0.1);
            }
        }
        
        for (sx = [-screen_bolt_x, screen_bolt_x]) {
            translate([sx, screen_bolt_y, -0.1])
                cylinder(d = screen_bolt_dia, h = screen_bolt_depth + 0.1);
        }
    }
}

// 2. MID CLAMP SANDWICH BRACKET
module mid_clamp() {
    difference() {
        union() {
            difference() {
                octagonal_prism(enclosure_width, mid_clamp_thickness, chamfer_size);
                translate([0, 0, -0.1])
                    octagonal_prism(cavity_w, mid_clamp_thickness + 0.2, cavity_chamfer);
            }
            intersection() {
                octagonal_prism(enclosure_width, mid_clamp_thickness, chamfer_size);
                union() {
                    rotate([0, 0, 45]) cube([7.0, 80.0, mid_clamp_thickness], center=true);
                    rotate([0, 0, -45]) cube([7.0, 80.0, mid_clamp_thickness], center=true);
                }
            }
            intersection() {
                cylinder(d = mid_clamp_outer_dia, h = mid_clamp_thickness + mid_clamp_lip_h);
                union() {
                    rotate([0, 0, 45]) cube([7.0, 80.0, mid_clamp_thickness + mid_clamp_lip_h], center=true);
                    rotate([0, 0, -45]) cube([7.0, 80.0, mid_clamp_thickness + mid_clamp_lip_h], center=true);
                }
            }
        }
        
        translate([0, 0, -1.0])
            cylinder(d = 14.0, h = mid_clamp_thickness + mid_clamp_lip_h + 2.0);
            
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, -1.0])
                    cylinder(d = screw_hole_dia, h = mid_clamp_thickness + mid_clamp_lip_h + 2.0);
            }
        }
    }
}

// 3. MAIN HOUSING POD (Support-Free V2.0: Recessed Flat USB-C, Wide Cradle, Dual DuPont Trenches, Debossed V2.0)
module main_housing() {
    cavity_depth = housing_depth - floor_t;
    
    difference() {
        chamfered_octagonal_base(enclosure_width, housing_depth, chamfer_size, outer_chamfer, chamfer_top=false);
        
        // 1. Chamfered Open Tub Cavity
        translate([0, 0, floor_t])
            octagonal_prism(cavity_w, cavity_depth + 0.1, cavity_chamfer);
            
        // 2. Precision USB-C Port Cutout (Flat Inside Wall at X = -26.0mm)
        usbc_stadium_cutter();
        
        // 2b. Inner Wall Relief Pocket at USB-C Port with 45-degree self-supporting overhangs & chamfers
        hull() {
            translate([-26.1, -10.5, floor_t])
                cube([0.1, 21.0, 9.5]);
            translate([-23.9, -12.6, floor_t])
                cube([0.1, 25.2, 11.6]);
        }
            
        // 3. DuPont Connector & Wire Clearance Trench (Bottom Wall: Y = -26.0 to -21.0)
        translate([-13.0, -26.0, floor_t])
            cube([26.0, 5.0, cavity_depth + 0.1]);
            
        // 3b. DuPont Connector & Wire Clearance Trench (Right Wall opposite USB-C: X = 21.0 to 26.0)
        translate([21.0, -13.0, floor_t])
            cube([5.0, 26.0, cavity_depth + 0.1]);
            
        // 4. 4 Corner M3 Screw Pilot Holes with 45-degree Entry Lead-In Chamfers (Z = 27.5mm)
        for (sx = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
            for (sy = [-screw_bolt_circle/2, screw_bolt_circle/2]) {
                translate([sx, sy, housing_depth - 15.0])
                    cylinder(d = screw_pilot_dia, h = 15.1);
                translate([sx, sy, housing_depth - 0.99])
                    cylinder(d1 = screw_pilot_dia, d2 = screw_pilot_dia + 2.0, h = 1.0);
            }
        }
        
        // 5. Contour-Following Rear Aeration Slits
        // Top 6 rows
        translate([-11.0,  10.5, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,    10.5, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([11.0,   10.5, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);

        translate([-11.0,  12.7, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,    12.7, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([11.0,   12.7, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);

        translate([-11.0,  14.9, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,    14.9, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([11.0,   14.9, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);

        translate([-10.5,  17.1, -1.0]) cube([8.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,    17.1, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([10.5,   17.1, -1.0]) cube([8.0, 1.05, floor_t + 2.0], center=true);

        translate([-10.0,  19.3, -1.0]) cube([7.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,    19.3, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([10.0,   19.3, -1.0]) cube([7.0, 1.05, floor_t + 2.0], center=true);

        translate([-9.0,   21.5, -1.0]) cube([5.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,    21.5, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([9.0,    21.5, -1.0]) cube([5.0, 1.05, floor_t + 2.0], center=true);

        // Bottom 6 rows
        translate([-11.0, -10.5, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,   -10.5, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([11.0,  -10.5, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);

        translate([-11.0, -12.7, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,   -12.7, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([11.0,  -12.7, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);

        translate([-11.0, -14.9, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,   -14.9, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([11.0,  -14.9, -1.0]) cube([9.0, 1.05, floor_t + 2.0], center=true);

        translate([-10.5, -17.1, -1.0]) cube([8.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,   -17.1, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([10.5,  -17.1, -1.0]) cube([8.0, 1.05, floor_t + 2.0], center=true);

        translate([-10.0, -19.3, -1.0]) cube([7.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,   -19.3, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([10.0,  -19.3, -1.0]) cube([7.0, 1.05, floor_t + 2.0], center=true);

        translate([-9.0,  -21.5, -1.0]) cube([5.0, 1.05, floor_t + 2.0], center=true);
        translate([0.0,   -21.5, -1.0]) cube([7.5, 1.05, floor_t + 2.0], center=true);
        translate([9.0,   -21.5, -1.0]) cube([5.0, 1.05, floor_t + 2.0], center=true);
        
        // 6. Top Edge Perimeter Vertical Exhaust Slits with 45-degree peaked roofs
        for (vx = [-12.0, -8.0, -4.0, 0.0, 4.0, 8.0, 12.0]) {
            translate([vx, 25.0, 0])
                rotate([90, 0, 0])
                    linear_extrude(height = 10.0, center = true)
                        polygon(points = [
                            [-0.6, 11.0], [0.6, 11.0],
                            [0.6, 18.4], [0.0, 19.0], [-0.6, 18.4]
                        ]);
        }
        
        // 7. Embossed/Debossed Product Name on Underside Backplate (Z = 0)
        translate([0, 2.0, -0.05])
            linear_extrude(height = 0.45)
                text("CYBER-DECK", size = 3.2, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
        translate([0, -2.0, -0.05])
            linear_extrude(height = 0.45)
                text("UNIT 01", size = 2.5, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");

        // 8. Inside Floor Debossed "V2.0" (0.4mm deep into inside floor)
        translate([8.5, 0, floor_t - 0.40])
            linear_extrude(height = 0.45)
                text("V2.0", size = 3.6, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
    
    // Fused Internal ESP32-C3 SuperMini Minimalist U-Cradle (Open Front, Recessed Seating at X = -26.0mm)
    wall_thick  = 3.0;
    side_thick  = 1.6;
    tall_wall_h = 12.0; // Solid vertical back thrust wall opposite USB-C
    side_wall_h = 6.2;  // Clean vertical side guide wall height
    
    cur_esp_w   = 19.9; // Expanded width (+0.5mm on each lateral side for easy board seating)
    cur_esp_l   = 23.6;
    x_front     = -26.0;
    x_rear      = -2.4;
    cur_esp_cx  = (x_front + x_rear) / 2;
    snap_z      = floor_t + esp_standoff_h + 1.2 + 0.3; // 6.7mm

    union() {
        // 1. Straight Solid Rear Thrust Wall (shifted with board)
        translate([x_rear, -(cur_esp_w / 2 + side_thick), floor_t])
            cube([wall_thick, cur_esp_w + 2 * side_thick, tall_wall_h]);

        // 2. Straight Vertical Side Guide Walls (solid all the way to floor)
        translate([x_front, cur_esp_w / 2, floor_t])
            cube([cur_esp_l, side_thick, side_wall_h]);
        translate([x_front, -(cur_esp_w / 2 + side_thick), floor_t])
            cube([cur_esp_l, side_thick, side_wall_h]);

        // 3. Integrated 1.0mm Side Edge Support Steps (Z = 2.0 to 5.2)
        translate([x_front, cur_esp_w / 2 - 1.0, floor_t])
            cube([cur_esp_l, 1.0, esp_standoff_h]);
        translate([x_front, -cur_esp_w / 2, floor_t])
            cube([cur_esp_l, 1.0, esp_standoff_h]);

        // 4. Discrete 45-Degree Self-Supporting Snap Retention Clips
        // Top clip
        translate([cur_esp_cx, cur_esp_w / 2, snap_z])
            hull() {
                translate([-2.5, 0.05, -0.6]) cube([0.01, 0.01, 1.2]);
                translate([ 2.5, 0.05, -0.6]) cube([0.01, 0.01, 1.2]);
                translate([-1.95, -0.55, 0.0]) cube([0.01, 0.01, 0.01]);
                translate([ 1.95, -0.55, 0.0]) cube([0.01, 0.01, 0.01]);
            }
        
        // Bottom clip
        translate([cur_esp_cx, -cur_esp_w / 2, snap_z])
            hull() {
                translate([-2.5, -0.05, -0.6]) cube([0.01, 0.01, 1.2]);
                translate([ 2.5, -0.05, -0.6]) cube([0.01, 0.01, 1.2]);
                translate([-1.95, 0.55, 0.0]) cube([0.01, 0.01, 0.01]);
                translate([ 1.95, 0.55, 0.0]) cube([0.01, 0.01, 0.01]);
            }
    }
}

// 4. STAND TIER 1 BASE PLATE
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

// 5. STAND TIER 2 MONOLITHIC PEDESTAL TRUNK (Deep V-Saddle Cradle)
module stand_tier2_trunk() {
    difference() {
        hull() {
            translate([0, 0, stand_base_h])
                rounded_rect_prism(62.0, 66.0, 0.01, 5.0);
            translate([0, 0, stand_base_h + stand_trunk_h - 0.01])
                rounded_rect_prism(54.0, 58.0, 0.01, 3.5);
        }
        for (px = [-pin_dist_x, pin_dist_x]) {
            for (py = [-pin_dist_y, pin_dist_y]) {
                translate([px, py, stand_base_h - 0.1])
                    cylinder(d = pin_dia + 0.4, h = pin_h + 0.6);
            }
        }
        translate([0, -4.0, 42.40])
            rotate([90.0 - stand_tilt_deg, 0, 180.0])
            octagonal_prism(enclosure_width + 0.8, 36.5, 6.0);
    }
}

// 6. UNIFIED MONOLITHIC PEDESTAL DESK STAND
module desk_stand() {
    difference() {
        union() {
            rounded_rect_prism(stand_base_w, stand_base_d, stand_base_h, 6.0);
            hull() {
                translate([0, 0, stand_base_h])
                    rounded_rect_prism(62.0, 66.0, 0.01, 5.0);
                translate([0, 0, stand_base_h + stand_trunk_h - 0.01])
                    rounded_rect_prism(54.0, 58.0, 0.01, 3.5);
            }
        }
        for (fx = [-stand_base_w/2 + 10, stand_base_w/2 - 10]) {
            for (fy = [-stand_base_d/2 + 10, stand_base_d/2 - 10]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.2, h = 1.5);
            }
        }
        translate([0, -4.0, 42.40])
            rotate([90.0 - stand_tilt_deg, 0, 180.0])
            octagonal_prism(enclosure_width + 0.8, 36.5, 6.0);
    }
}

// 7. MINIMALIST ANGLED CRADLE DESK STAND (Open Triangular A-Frame)
module minimalist_stand() {
    m_stand_w = 54.0;
    m_base_l  = 56.0;
    m_base_t  = 6.0;
    m_beam_t  = 5.5;
    m_back_h  = 36.0;
    m_cr_rear = 40.0;
    m_tilt    = stand_tilt_deg; // 22.0 deg

    s_t = sin(m_tilt);
    c_t = cos(m_tilt);

    difference() {
        union() {
            // Base plate
            translate([-m_stand_w/2, 0, 0])
                cube([m_stand_w, m_base_l, m_base_t]);

            // Angled front retaining lip
            translate([0, 5.0, m_base_t])
                rotate([-m_tilt, 0, 0])
                    translate([-m_stand_w/2, 0, 0])
                        cube([m_stand_w, 4.5, 5.5]);

            // Slanted backrest spine
            translate([0, m_cr_rear, m_base_t])
                rotate([-m_tilt, 0, 0])
                    translate([-m_stand_w/2, 0, 0])
                        cube([m_stand_w, m_beam_t, m_back_h]);

            // Rear triangular gussets
            translate([-m_stand_w/2, 0, 0])
                rotate([0, 90, 0])
                    linear_extrude(height = m_stand_w)
                        polygon(points = [
                            [m_base_t, m_cr_rear + m_beam_t - 0.5],
                            [m_base_t, m_base_l - 2.0],
                            [m_base_t + c_t*(m_back_h - 3.0), m_cr_rear + s_t*(m_back_h - 3.0)]
                        ]);
        }

        // Front 45° chamfer cutter
        translate([0, 0, m_base_t + 1.5])
            rotate([45, 0, 0])
                cube([m_stand_w + 10.0, 5.0, 5.0], center = true);

        // Open Triangular Side Window Cutout
        translate([-(m_stand_w + 20)/2, 0, 0])
            rotate([0, 90, 0])
                linear_extrude(height = m_stand_w + 20)
                    polygon(points = [
                        [m_base_t + 2.0, 10.0],
                        [m_base_t + 2.0, m_base_l - 8.0],
                        [m_base_t + c_t*(m_back_h - 8.0) - 3.0, m_cr_rear + s_t*(m_back_h - 8.0) + 1.0]
                    ]);

        // Rear Cable Routing Slot
        translate([0, m_cr_rear + s_t * 16.0 + 3.0, m_base_t + c_t * 16.0])
            rotate([-m_tilt, 0, 0])
                cube([26.0, 40.0, 24.0], center = true);

        // 4x Rubber Feet Recesses (dia 8.0mm x 1.5mm deep)
        for (fx = [-m_stand_w/2 + 8.5, m_stand_w/2 - 8.5]) {
            for (fy = [6.5, m_base_l - 6.5]) {
                translate([fx, fy, -0.1])
                    cylinder(d = 8.0, h = 1.6);
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
    mid_clamp();
} else if (part == 4) {
    stand_tier1_base();
} else if (part == 5) {
    stand_tier2_trunk();
} else if (part == 6) {
    desk_stand();
} else if (part == 7) {
    minimalist_stand();
} else {
    // Complete Multi-Part Assembly Preview (22° Ergonomic Desktop Stance on Minimalist Stand)
    translate([0, 40.0 + sin(stand_tilt_deg)*27.0, 6.0 + cos(stand_tilt_deg)*27.0])
        rotate([-stand_tilt_deg, 0, 0]) {
            translate([0, 0, housing_depth + mid_clamp_thickness]) color("#22252B") front_bezel();
            translate([0, 0, housing_depth]) color("#D08770") mid_clamp();
            color("#181A1F") main_housing();
        }
    color("#1E2127") minimalist_stand();
}
