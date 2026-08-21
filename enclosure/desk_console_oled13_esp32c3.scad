// ==============================================================================
// 3D Printable Angled Desk Macropad & Monitor Console
// Hardware: 1.3" I2C OLED + ESP32-C3 SuperMini + 3x MX Switches + 1x EC11 Encoder
// Designed for Easy FDM 3D Printing (No Supports Required if printed flat)
// ==============================================================================

$fn = 40;

// --- CONFIGURATION / SELECT PART TO RENDER ---
// Options: "assembly", "top_case", "bottom_base", "oled_bracket"
RENDER_PART = "assembly"; 

// --- OVERALL CONSOLE DIMENSIONS ---
case_width       = 92.0;   // Left-to-right width
case_depth       = 72.0;   // Front-to-back depth
front_height     = 14.0;   // Front edge height
rear_height      = 32.0;   // Rear edge height (creates ~15-20° viewing angle)
wall_thickness   = 2.4;    // Outer shell thickness
plate_thickness  = 1.5;    // Standard Cherry MX plate snap-in thickness

// --- 1.3" OLED SCREEN SPECS (SH1106 / SSD1306) ---
oled_pcb_w       = 35.5;   // OLED PCB width
oled_pcb_h       = 33.5;   // OLED PCB height
oled_window_w    = 31.5;   // Visible display window width
oled_window_h    = 17.0;   // Visible display window height
oled_mount_pitch_x = 30.5; // Mounting hole spacing X
oled_mount_pitch_y = 29.0; // Mounting hole spacing Y

// --- MECHANICAL SWITCH (CHERRY / GATERON MX) SPECS ---
mx_cutout_size   = 14.0;   // Standard 14x14mm square cutout
mx_pitch         = 19.05;  // Standard 0.75" mechanical switch spacing

// --- EC11 ROTARY ENCODER SPECS ---
encoder_hole_dia = 7.5;    // M7 shaft mounting hole

// --- ESP32-C3 SUPER MINI CRADLE SPECS ---
esp_w            = 18.2;   // Board width
esp_l            = 22.8;   // Board length
usbc_w           = 10.5;   // USB-C port cutout width
usbc_h           = 5.0;    // USB-C port cutout height

// --- SCREW POST SPECS (M3 Self-tapping or Heat-set Inserts) ---
screw_hole_dia   = 2.8;    // Pilot hole for M3 screw
post_outer_dia   = 6.5;

// ==============================================================================
// MODULES
// ==============================================================================

module rounded_box_2d(w, d, r=4) {
    hull() {
        translate([r, r]) circle(r=r);
        translate([w-r, r]) circle(r=r);
        translate([w-r, d-r]) circle(r=r);
        translate([r, d-r]) circle(r=r);
    }
}

// Wedge prism for angled body
module angled_body(w, d, h_front, h_rear, r=4) {
    polyhedron(
        points=[
            // Bottom 4 vertices
            [r, r, 0], [w-r, r, 0], [w-r, d-r, 0], [r, d-r, 0],
            // Top 4 vertices
            [r, r, h_front], [w-r, r, h_front], [w-r, d-r, h_rear], [r, d-r, h_rear]
        ],
        faces=[
            [0, 1, 2, 3], // Bottom
            [4, 7, 6, 5], // Top
            [0, 4, 5, 1], // Front
            [2, 6, 7, 3], // Back
            [0, 3, 7, 4], // Left
            [1, 5, 6, 2]  // Right
        ]
    );
}

// Smooth angled solid
module solid_angled_case(w, d, h_f, h_r, r=4) {
    hull() {
        translate([r, r, 0]) cylinder(r=r, h=h_f);
        translate([w-r, r, 0]) cylinder(r=r, h=h_f);
        translate([w-r, d-r, 0]) cylinder(r=r, h=h_r);
        translate([r, d-r, 0]) cylinder(r=r, h=h_r);
    }
}

// ------------------------------------------------------------------------------
// TOP CONTROL PANEL / SHELL
// ------------------------------------------------------------------------------
module top_case() {
    angle = atan2(rear_height - front_height, case_depth);
    
    difference() {
        // Outer Main Body
        solid_angled_case(case_width, case_depth, front_height, rear_height, 4);

        // Hollow interior (leaving 2.4mm walls and perimeter lip)
        translate([wall_thickness, wall_thickness, -1])
            solid_angled_case(case_width - 2*wall_thickness, case_depth - 2*wall_thickness, 
                              front_height - wall_thickness + 1, rear_height - wall_thickness + 1, 3);

        // Bottom opening for baseplate
        translate([-5, -5, -10])
            cube([case_width + 10, case_depth + 10, 10]);

        // ==========================================
        // TOP FACE CUTOUTS (Transformed onto angled plane)
        // ==========================================
        translate([0, 0, front_height])
        rotate([angle, 0, 0]) {
            
            // 1. OLED Screen Window (Top Half)
            translate([case_width/2 - oled_window_w/2, 42.0, -10]) {
                cube([oled_window_w, oled_window_h, 20]);
                
                // Recess inside for glass bezel
                translate([-1.5, -2, -1.0])
                    cube([oled_window_w + 3.0, oled_window_h + 4.0, 3.0]);
            }

            // 2. Three Mechanical Switch Cutouts (Bottom Row)
            // Centered nicely across the width
            for (i = [0:2]) {
                translate([16.0 + i*mx_pitch, 12.0, -10]) {
                    // MX standard 14x14mm square cutout
                    cube([mx_cutout_size, mx_cutout_size, 20]);
                }
            }

            // 3. EC11 Rotary Encoder Cutout (Top Left or Right)
            translate([16.0 + 3*mx_pitch - 1, 48.0, -10]) {
                cylinder(d=encoder_hole_dia, h=20);
                // Anti-rotation notch
                translate([0, 4.2, 0])
                    cylinder(d=2.2, h=20);
            }
        }

        // Rear USB-C Pass-through / ESP32 Port Cutout
        translate([case_width/2 - usbc_w/2, case_depth - wall_thickness - 2, 2.5])
            cube([usbc_w, 8.0, usbc_h]);
    }

    // --- INTERNAL MOUNTING BOSSES & BRACKETS ---
    // 4x Corner Screw Posts for Baseplate
    corner_posts();
    
    // Internal OLED Mounting Standoffs
    translate([0, 0, front_height])
    rotate([atan2(rear_height - front_height, case_depth), 0, 0]) {
        translate([case_width/2, 42.0 + oled_window_h/2, 0]) {
            for (dx = [-oled_mount_pitch_x/2, oled_mount_pitch_x/2]) {
                for (dy = [-oled_mount_pitch_y/2, oled_mount_pitch_y/2]) {
                    translate([dx, dy, -4.5])
                    difference() {
                        cylinder(d=4.5, h=4.5);
                        cylinder(d=1.8, h=6); // M2 pilot hole
                    }
                }
            }
        }
    }
}

module corner_posts() {
    positions = [
        [wall_thickness + 3.5, wall_thickness + 3.5],
        [case_width - wall_thickness - 3.5, wall_thickness + 3.5],
        [case_width - wall_thickness - 3.5, case_depth - wall_thickness - 3.5],
        [wall_thickness + 3.5, case_depth - wall_thickness - 3.5]
    ];
    
    for (pos = positions) {
        translate([pos[0], pos[1], 0]) {
            difference() {
                cylinder(d=post_outer_dia, h=front_height - 2);
                cylinder(d=screw_hole_dia, h=front_height);
            }
        }
    }
}

// ------------------------------------------------------------------------------
// BOTTOM BASE PLATE WITH ESP32-C3 SUPERMINI MOUNTING CRADLE
// ------------------------------------------------------------------------------
module bottom_base() {
    base_t = 2.4;
    
    difference() {
        union() {
            // Main floor plate
            linear_extrude(base_t)
                rounded_box_2d(case_width - 0.4, case_depth - 0.4, 3.8);
            
            // Raised alignment inner rim
            translate([wall_thickness, wall_thickness, base_t])
                difference() {
                    linear_extrude(2.0)
                        rounded_box_2d(case_width - 0.4 - 2*wall_thickness, case_depth - 0.4 - 2*wall_thickness, 2.5);
                    translate([1.2, 1.2, -0.5])
                        linear_extrude(3.0)
                            rounded_box_2d(case_width - 0.4 - 2*wall_thickness - 2.4, case_depth - 0.4 - 2*wall_thickness - 2.4, 2.0);
                }

            // ESP32-C3 SuperMini Alignment Bracket / Cradle
            translate([case_width/2 - esp_w/2 - 1.2, case_depth - esp_l - wall_thickness - 2.0, base_t]) {
                // Left & Right retention walls
                cube([1.2, esp_l, 4.0]);
                translate([esp_w + 1.2, 0, 0]) cube([1.2, esp_l, 4.0]);
                // Front stop
                cube([esp_w + 2.4, 1.2, 4.0]);
            }
            
            // 4x Rubber Foot Cavities on bottom
        }

        // 4x Screw Counter-bore Holes
        positions = [
            [wall_thickness + 3.5, wall_thickness + 3.5],
            [case_width - wall_thickness - 3.5, wall_thickness + 3.5],
            [case_width - wall_thickness - 3.5, case_depth - wall_thickness - 3.5],
            [wall_thickness + 3.5, case_depth - wall_thickness - 3.5]
        ];
        
        for (pos = positions) {
            translate([pos[0], pos[1], -1]) {
                cylinder(d=3.4, h=base_t + 2);     // Screw pass-through
                cylinder(d=6.0, h=1.5);           // Countersink for M3 screw head
            }
        }
        
        // Cable tie / ventilation slots
        for (i = [-1, 1]) {
            translate([case_width/2 + i*20 - 10, 20, -1])
                cube([20, 2.5, 10]);
        }
    }
}

// ==============================================================================
// RENDER CONTROLLER
// ==============================================================================
if (RENDER_PART == "assembly") {
    // Top Case
    color("DimGray", 0.9) top_case();
    
    // Bottom Plate (shown exploded or in place)
    translate([0, 0, -5])
        color("SteelBlue", 0.95) bottom_base();

} else if (RENDER_PART == "top_case") {
    // Print upside down on build plate for zero supports!
    rotate([180, 0, 0])
        top_case();

} else if (RENDER_PART == "bottom_base") {
    bottom_base();
}
