// =========================================================================
// GC9A01 1.28" Circular IPS Display & ESP32-C3 SuperMini
// Springlatch Edition - 100% Print-in-Place (PiP) Clamshell Enclosure
// Inspired by Clockspring 3D Compliant Springlatch Mechanisms
// 100% Support-Free FDM 3D Printable Architecture
// =========================================================================

$fn = 64; // High resolution curves for 3D printing

// --- PART SELECTOR ---
// 0 = Full Print-in-Place Assembly (Flat 180° Unfolded for 3D Printing)
// 1 = Main Lower Housing (Base Only)
// 2 = Upper Hinged Bezel (Lid Only)
// 3 = Closed Enclosure Assembly Preview (Desk Operating Mode)
part = 0;

// --- GLOBAL DIMENSIONS ---
box_w         = 56.0;  // Enclosure width (X, mm)
box_d         = 58.0;  // Enclosure depth (Y, mm from hinge center to front)
base_h        = 20.0;  // Base lower tub height (Z, mm)
lid_h         = 9.5;   // Upper lid thickness (Z, mm)
wall_t        = 2.8;   // Outer perimeter wall thickness (mm)
floor_t       = 2.0;   // Base floor thickness (mm)
chamfer_c     = 5.0;   // Front corner 45-degree chamfers (mm)
outer_ch      = 1.2;   // Perimeter edge chamfer (mm)

// --- HINGE PARAMETERS ---
hinge_z       = 14.0;  // Hinge axis height above print bed (mm)
hinge_rad_out = 4.2;   // Outer knuckle radius (mm)
hinge_pin_rad = 2.2;   // Axle pin radius (mm)
hinge_clear   = 0.38;  // Radial print-in-place clearance gap (mm)
hinge_gap_x   = 0.40;  // Axial knuckle separation gap (mm)

// Knuckle spans along X:
knuckle_mid_w = 15.2;
knuckle_out_w = 15.5;
knuckle_out_x = 15.75;

// --- SPRINGLATCH PARAMETERS ---
spring_beam_t = 0.95;  // Thickness of compliant serpentine spring ribbon (mm)
spring_slit_w = 1.25;  // Air clearance gap between spring waves (mm)
spring_h      = 5.0;   // Height of spring flexure in Z (mm)
latch_tab_w   = 14.0;  // Center push-button tab width (mm)
latch_hook_w  = 5.0;   // Left/right latch locking hooks width (mm)
latch_hook_x  = 16.5;  // Offset distance of locking hooks from center (mm)
latch_lip_dep = 1.20;  // Depth of locking undercut hook (mm)
cam_ramp_ang  = 45.0;  // Auto-camming lead-in ramp angle (degrees)

// --- DISPLAY POCKET PARAMETERS (LID) ---
disp_center_y = 28.0;  // Screen center Y offset from hinge (mm)
disp_active_d = 33.0;  // Active display viewing opening (mm)
disp_funnel_d = 38.6;  // Conical anti-shadow viewing bezel opening (mm)
disp_glass_d  = 36.6;  // Glass step diameter (mm)
disp_pcb_d    = 39.4;  // PCB circular body pocket (mm)
disp_depth    = 3.4;   // Internal pocket depth (mm)

// --- ESP32-C3 SUPERMINI MOUNTING (BASE) ---
esp_l         = 23.6;  // Length (+0.6mm clearance)
esp_w         = 18.9;  // Width (+0.5mm clearance)
esp_rail_h    = 1.8;   // Support ledge height (mm)
esp_cx        = -9.0;  // Center X offset (mm)
esp_cy        = -28.0; // Center Y offset from hinge (mm)
usbc_z        = 7.0;   // USB-C port centerline height (mm)

// --- KICKSTAND PADS PARAMETERS ---
kickstand_h   = 4.5;   // Height of rear kickstand elevation wedges (mm)
feet_pocket_d = 8.2;   // Non-slip rubber bumper pocket diameter (mm)
feet_pocket_h = 1.4;   // Bumper pocket depth (mm)


// =========================================================================
// 2D PROFILE HELPERS (CCW WINDING)
// =========================================================================

module box_perimeter_2d(w, d, c) {
    hw = w / 2.0;
    polygon(points=[
        [-hw, 0],
        [-hw, -d + c],
        [-hw + c, -d],
        [hw - c, -d],
        [hw, -d + c],
        [hw, 0]
    ]);
}

module lid_perimeter_2d(w, d, c) {
    hw = w / 2.0;
    polygon(points=[
        [-hw, 0],
        [hw, 0],
        [hw, d - c],
        [hw - c, d],
        [-hw + c, d],
        [-hw, d - c]
    ]);
}


// =========================================================================
// MODULE: BASE HOUSING (LOWER TUB WITH KICKSTAND & ESP32 CRADLE)
// =========================================================================

module base_housing() {
    difference() {
        union() {
            // 1. Main outer tub solid
            linear_extrude(base_h)
                box_perimeter_2d(box_w, box_d, chamfer_c);

            // 2. Base Hinge Knuckles (Left and Right)
            for (sx = [-1, 1]) {
                translate([sx * knuckle_out_x, 0, hinge_z])
                    rotate([0, 90, 0])
                        cylinder(r=hinge_rad_out, h=knuckle_out_w, center=true);
                
                translate([sx * knuckle_out_x, -2.0, hinge_z / 2.0])
                    cube([knuckle_out_w, 4.0, hinge_z], center=true);
            }

            // 3. Integrated Angled Desk Kickstand Pads (Rear elevation wedges)
            translate([-box_w/2 + 7.0, -8.0, -kickstand_h/2])
                cube([10.0, 12.0, kickstand_h], center=true);
            translate([box_w/2 - 7.0, -8.0, -kickstand_h/2])
                cube([10.0, 12.0, kickstand_h], center=true);
            translate([-box_w/2 + 7.0, -box_d + 10.0, -1.0/2])
                cube([10.0, 12.0, 1.0], center=true);
            translate([box_w/2 - 7.0, -box_d + 10.0, -1.0/2])
                cube([10.0, 12.0, 1.0], center=true);
        }

        // --- CUTOUTS ---

        // 1. Main Internal Electronics Cavity
        translate([0, 0, floor_t])
            linear_extrude(base_h + 1.0)
                offset(r=-wall_t)
                    box_perimeter_2d(box_w, box_d, chamfer_c);

        // 2. Hinge Pin Clearance Bores (Outer Knuckles)
        for (sx = [-1, 1]) {
            translate([sx * knuckle_out_x, 0, hinge_z])
                rotate([0, 90, 0])
                    cylinder(r=hinge_pin_rad + hinge_clear, h=knuckle_out_w + 2.0, center=true);
        }

        // 3. Center Knuckle Clearance Pocket for Lid
        translate([0, 0, hinge_z])
            cube([knuckle_mid_w + 2 * hinge_gap_x, 2 * hinge_rad_out + 2.0, 2 * hinge_rad_out + 4.0], center=true);

        // 4. USB-C Port Cutout on Left Wall (X = -box_w/2)
        translate([-box_w/2 - 1.0, esp_cy, usbc_z])
            rotate([0, 90, 0])
                hull() {
                    translate([0, -4.0, 0]) cylinder(r=3.25, h=wall_t + 3.0);
                    translate([0, 4.0, 0]) cylinder(r=3.25, h=wall_t + 3.0);
                }

        // 5. Front Latch Catches & 45° Auto-Camming Lead-in Ramps (Y = -box_d)
        for (sx = [-latch_hook_x, latch_hook_x]) {
            translate([sx, -box_d + wall_t - 0.2, base_h - 4.5])
                cube([latch_hook_w + 1.0, latch_lip_dep + 0.8, 3.2], center=true);
            
            translate([sx, -box_d + wall_t/2.0, base_h - 1.5])
                rotate([cam_ramp_ang, 0, 0])
                    cube([latch_hook_w + 1.0, 4.0, 4.0], center=true);
        }

        // 6. Central Thumb Push Recess
        translate([0, -box_d + wall_t/2.0, base_h - 3.0])
            cube([latch_tab_w + 4.0, wall_t + 1.0, 8.0], center=true);

        // 7. Passive Aeration Slots on Bottom Floor
        for (y_slot = [-16, -22, -28, -34, -40, -46]) {
            translate([8.0, y_slot, -kickstand_h - 0.1])
                cube([16.0, 1.4, kickstand_h + floor_t + 1.0], center=true);
        }

        // 8. Rubber Bumper Feet Recess Pockets
        translate([-box_w/2 + 7.0, -8.0, -kickstand_h - 0.1])
            cylinder(r=feet_pocket_d/2.0, h=feet_pocket_h + 0.1);
        translate([box_w/2 - 7.0, -8.0, -kickstand_h - 0.1])
            cylinder(r=feet_pocket_d/2.0, h=feet_pocket_h + 0.1);
        translate([-box_w/2 + 7.0, -box_d + 10.0, -1.0 - 0.1])
            cylinder(r=feet_pocket_d/2.0, h=feet_pocket_h + 0.1);
        translate([box_w/2 - 7.0, -box_d + 10.0, -1.0 - 0.1])
            cylinder(r=feet_pocket_d/2.0, h=feet_pocket_h + 0.1);
    }

    // --- INTERNAL ESP32-C3 SUPERMINI CRADLE ---
    translate([esp_cx, esp_cy, floor_t])
        esp32_cradle();
}


// =========================================================================
// MODULE: ESP32-C3 SNAP-FIT CRADLE
// =========================================================================

module esp32_cradle() {
    hw = esp_w / 2.0;
    hl = esp_l / 2.0;
    
    // Side Guide Rails with PCB resting ledge
    difference() {
        union() {
            translate([-hl - 1.5, -hw - 1.4, 0])
                cube([esp_l + 3.0, 1.4, 5.0]);
            translate([-hl - 1.5, hw, 0])
                cube([esp_l + 3.0, 1.4, 5.0]);
            translate([-hl, -hw, 0])
                cube([esp_l, 1.0, esp_rail_h]);
            translate([-hl, hw - 1.0, 0])
                cube([esp_l, 1.0, esp_rail_h]);
        }
    }

    // Rear Compliant Cantilever Snap Arm (X = +hl)
    translate([hl, -3.0, 0]) {
        cube([1.6, 6.0, 7.2]);
        translate([-0.55, 0, 5.2])
            rotate([0, 30, 0])
                cube([0.8, 6.0, 1.6]);
    }
}


// =========================================================================
// MODULE: UPPER HINGED BEZEL (LID WITH DISPLAY MOUNT & COMPLIANT LATCH)
// =========================================================================

module hinged_lid() {
    difference() {
        union() {
            // 1. Main Lid Solid Perimeter (extends Y = 0 to Y = +box_d)
            linear_extrude(lid_h)
                lid_perimeter_2d(box_w, box_d, chamfer_c);

            // 2. Lid Center Hinge Knuckle with Integral Pins
            translate([0, 0, hinge_z]) {
                rotate([0, 90, 0])
                    cylinder(r=hinge_rad_out, h=knuckle_mid_w, center=true);

                for (sx = [-1, 1]) {
                    translate([sx * (knuckle_mid_w/2.0), 0, 0])
                        rotate([0, sx * 90, 0])
                            cylinder(r1=hinge_pin_rad, r2=hinge_pin_rad, h=knuckle_out_w/2.0 + 2.0);
                }
            }

            translate([0, 2.0, hinge_z / 2.0])
                cube([knuckle_mid_w, 4.0, hinge_z], center=true);
        }

        // --- CUTOUTS ---

        // 1. GC9A01 Conical Anti-Shadow Front Viewing Aperture (Z = 0)
        translate([0, disp_center_y, -0.1])
            cylinder(r1=disp_funnel_d/2.0, r2=disp_active_d/2.0, h=lid_h - disp_depth + 0.1);

        // 2. GC9A01 Circular PCB Seating Pocket
        translate([0, disp_center_y, lid_h - disp_depth])
            cylinder(r=disp_pcb_d/2.0, h=disp_depth + 1.0);

        // 3. Screen Cable Routing Trench (towards hinge)
        translate([-12.0, 0, lid_h - disp_depth])
            cube([24.0, disp_center_y, disp_depth + 1.0]);

        // 4. Outer Knuckle Clearance Pockets for Base Knuckles
        for (sx = [-1, 1]) {
            translate([sx * knuckle_out_x, 0, hinge_z])
                cube([knuckle_out_w + 2 * hinge_gap_x, 2 * hinge_rad_out + 2.0, 2 * hinge_rad_out + 4.0], center=true);
        }

        // 5. Compliant Serpentine Spring Slits
        slit_z = lid_h - spring_h/2.0;
        translate([0, box_d - 4.5, slit_z])
            cube([box_w - 5.6, spring_slit_w, spring_h + 1.0], center=true);
        translate([0, box_d - 7.0, slit_z])
            cube([box_w - 13.6, spring_slit_w, spring_h + 1.0], center=true);
        for (sx = [-latch_hook_x - 3.5, latch_hook_x + 3.5]) {
            translate([sx, box_d - 5.75, slit_z])
                cube([spring_slit_w, 4.0, spring_h + 1.0], center=true);
        }
    }

    // --- INTEGRATED CLOCKSPRING-STYLE SPRINGLATCH MECHANISM ---
    slit_z = lid_h - spring_h/2.0;
    
    // Center push-button tab
    translate([0, box_d - 2.0, slit_z]) {
        cube([latch_tab_w, 2.8, spring_h], center=true);
        for (gx = [-4.0, 0.0, 4.0]) {
            translate([gx, 1.4, 0])
                cylinder(r=0.6, h=spring_h, center=true);
        }
    }

    // Compliant serpentine spring waves
    for (sx = [-1, 1]) {
        translate([sx * 10.0, box_d - 3.25, slit_z])
            cube([10.0, spring_beam_t, spring_h], center=true);
        translate([sx * 15.0, box_d - 4.5, slit_z - spring_h/2.0])
            cylinder(r=1.25, h=spring_h);
        translate([sx * 19.5, box_d - 5.75, slit_z])
            cube([9.0, spring_beam_t, spring_h], center=true);
        translate([sx * 24.5, box_d - 4.7, slit_z])
            cube([3.0, 3.2, spring_h], center=true);

        translate([sx * latch_hook_x, box_d - 2.0, slit_z]) {
            cube([latch_hook_w, 2.8, spring_h], center=true);
            translate([0, 1.4 + latch_lip_dep/2.0, -spring_h/2.0 + 1.5])
                cube([latch_hook_w, latch_lip_dep, 3.0], center=true);
            translate([0, 1.4 + latch_lip_dep, -spring_h/2.0 + 0.8])
                rotate([45, 0, 0])
                    cube([latch_hook_w, 1.5, 1.5], center=true);
        }
    }
}


// =========================================================================
// RENDER DISPATCHER
// =========================================================================

if (part == 0) {
    base_housing();
    hinged_lid();
} else if (part == 1) {
    base_housing();
} else if (part == 2) {
    hinged_lid();
} else if (part == 3) {
    base_housing();
    translate([0, 0, hinge_z])
        rotate([180, 0, 0])
            translate([0, 0, -hinge_z])
                hinged_lid();
}
