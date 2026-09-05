// =========================================================================
// GC9B72 2.1" Round TFT (360x360) Cyberdeck Desk Console Enclosure
// Parametric OpenSCAD Master Model
// Form Factor: 100% Symmetrical Square Housing Pod (84.0mm x 84.0mm)
// Re-engineered directly from the 240x240 Unit 01 Heritage Architecture:
// - 45° outer bottom chassis chamfer (1.2mm x 45°) + 45° corner chamfers (7.0mm)
// - Precision flush-edge ESP32 cradle (board 1.2mm from outer edge, x_front = -40.8mm)
// - Shaved-depth USB-C port with 45° conical lead-in flare
// - 45° peaked-roof top vertical exhaust vents + horizontal rear aeration rows
// - Elevated DuPont clearance trench with 45° bottom ramp
// - M2.3 socket head screws for Top Bezel with 100% direct plastic tapping
// =========================================================================

$fn = 72; // Smooth curves for 3D printing

// --- SELECT PART TO RENDER ---
// 0 = Full Assembly Exploded/Closed Preview
// 1 = Circular Top Bezel Ring (M2.3 4-Screw Screen Clamp)
// 2 = Front Face Carrier Plate (84x84mm Square + Ø1.90mm Direct Tap Pilot Holes)
// 3 = Main Housing Pod (84x84mm Square + Flush ESP32 Cradle + Left USB-C Port)
// 4 = Stand Tier 1 Base Accent Plate (Wood/Walnut Base)
// 5 = Stand Tier 2 Cradle Trunk (22° V-Saddle for 84mm Pod)
// 6 = Monolithic Combined Desk Stand
part = is_undef(part) ? 0 : part;

// =========================================================================
// PARAMETERS (All in millimeters)
// =========================================================================

// --- Screen Blueprint Dimensions (GoldenMorning GC9B72) ---
screen_pcb_w        = 59.24; // Screen PCB width
screen_pcb_h        = 67.47; // Screen PCB total height
screen_lcm_w        = 55.92; // Outer display module width
screen_lcm_h        = 57.58; // Outer display module height
screen_glass_w      = 55.52; // Outer glass width
screen_glass_h      = 57.18; // Outer glass height
screen_active_dia   = 52.92; // Active circular display diameter
screen_thickness    = 2.40;  // Total glass + PCB thickness
screen_circle_cy    = 0.0;   // Origin is aligned with the center of the active circle

// Top of PCB: +29.62mm, Bottom of PCB: -37.85mm
screen_pcb_top      = 29.62;
screen_pcb_bottom   = -37.85;
screen_tab_half_w   = 15.24; // Official blueprint dimension: (10 - 1)*2.54/2 + 3.81 = 15.24mm (30.48mm width)
screen_tab_w        = 30.48; // Official blueprint tab width
screen_pocket_depth = 2.00;  // Recess depth in front face carrier plate
screen_tolerance    = 0.36;  // Printing tolerance (pocket width = 31.20mm)

// --- Enclosure Outer Footprint (100% Symmetrical Square Pod) ---
housing_w           = 84.0;  // Pod outer width (84mm square)
housing_h           = 84.0;  // Pod outer height (84mm square)
housing_depth       = 28.0;  // Main housing depth
front_face_thick    = 7.0;   // Front face carrier plate thickness
bezel_thick         = 4.5;   // Top bezel ring total thickness
chamfer_outer       = 7.0;   // Cyberdeck 45° corner chamfer size
edge_chamfer        = 1.2;   // Outer perimeter 45° edge bevel
floor_thick         = 2.0;   // Rear housing floor thickness
cavity_depth        = housing_depth - floor_thick;

// --- Option 2: Rear-Loading Architecture Parameters ---
rear_pocket_depth   = 2.40;  // Recessed cavity depth on rear of Front Face
integrated_bezel_h  = 2.80;  // Raised circular bezel rim height on front (increased from 1.60mm)
integrated_bezel_od = 72.00; // Raised circular bezel outer diameter (increased from 66.40mm)
screen_aperture_dia = 54.00; // Central circular viewing aperture at screen retaining lip
screen_aperture_top = 60.00; // Continuous conical viewing funnel top diameter at ring summit

// --- Rear Clamp Plate Parameters (Sandwich Architecture) ---
clamp_thick         = 1.60;  // Slim 1.6mm intermediate sandwich clamp plate (8 layers at 0.2mm)

// --- Legacy Circular Top Bezel Parameters (Retained for reference) ---
bezel_inner_dia     = 53.60;
bezel_funnel_top    = 58.00;
bezel_ring_dia      = 66.40;
bezel_retaining_dia = 56.80;
bezel_retaining_depth = 0.80;

// --- Legacy M2.3 Fasteners ---
bezel_screw_x       = 26.00;
bezel_screw_y       = 32.50;
m2_3_clearance      = 2.55;
m2_3_cb_dia         = 5.00;
m2_3_cb_depth       = 2.40;
m2_3_pilot_dia      = 1.90;
m2_3_pilot_depth    = 5.20;

// --- Symmetrical Square Housing Corner Fasteners (Direct Plastic Tapping) ---
corner_screw_x      = 34.00; // Symmetrical square pattern (+/-34mm)
corner_screw_y      = 34.00; // Symmetrical square pattern (+/-34mm)
m3_clearance        = 3.40;  // Front face clearance through-hole
m3_cb_dia           = 6.20;  // M3 socket head counterbore diameter
m3_cb_depth         = 3.50;  // M3 counterbore depth
m3_pilot_dia        = 2.50;  // Direct plastic tap pilot hole in housing corner posts
m3_pilot_depth      = 14.00; // Deep thread engagement in corner posts

// --- ESP32 SuperMini Tolerance-Based Press Fit Cradle (G0 Rev 2 Approved) ---
esp_w               = 18.60; // Baseline channel width (+0.30mm per side against nominal 18.0mm)
esp_l               = 23.20; // ESP32 SuperMini length
rail_h              = 1.80;  // Rail height (PCB bottom at Z = 3.8mm)
side_thick          = 1.20;  // Rigid side guide walls
cradle_h            = 3.60;  // Side wall height (Z = 5.6mm)
x_front             = -40.8; // Board front seating datum (shaved wall relief)
x_rear              = -17.6; // Rear mechanical thrust corner shoulders
hw_in               = esp_w / 2.0;        // 9.30mm
hw_out              = hw_in + side_thick; // 10.50mm
center_gap_half_w   = 5.0;   // 10.0mm open center corridor for 2.4GHz ceramic antenna
crush_rib_protrusion= 0.35;  // 0.35mm crush rib protrusion (effective width 17.90mm)

// Left Flank Snug Oval USB-C Port
usbc_z              = 6.60;  // USB-C metal shell centerline
y_span              = 3.40;  // Port horizontal slot half-width
r_port              = 1.95;  // 3.90mm snug height matching standard USB-C shell (clean straight cut)

// --- Sculpted Two-Tier Stand (Sized for 84mm square pod) ---
stand_tilt_deg      = 22.0;  // Ergonomic backward tilt
stand_base_w        = 94.0;  // Stand base width
stand_base_d        = 88.0;  // Stand base depth
stand_base_h        = 6.0;   // Tier 1 base accent plate height
stand_trunk_h       = 26.0;  // Tier 2 cradle trunk height

// =========================================================================
// 2D HELPER PROFILES
// =========================================================================

module octagonal_profile_2d(w, h, c) {
    hw = w / 2.0;
    hh = h / 2.0;
    polygon([
        [-hw + c, -hh], [hw - c, -hh],
        [hw, -hh + c],  [hw, hh - c],
        [hw - c, hh],   [-hw + c, hh],
        [-hw, hh - c],  [-hw, -hh + c]
    ]);
}

module octagonal_prism(w, h, c, z_height) {
    linear_extrude(height = z_height) {
        octagonal_profile_2d(w, h, c);
    }
}

// =========================================================================
// PART 1: INTERNAL REAR CLAMP BRACKET (OPTION 2 M2.5 RETENTION)
// =========================================================================
module rear_clamp() {
    clamp_thick  = 1.6;
    tab_cutout_w = 32.00;
    hw_tab_cut   = tab_cutout_w / 2.0; // 16.00mm
    bot_y_cut    = screen_pcb_bottom - screen_tolerance - 0.5; // -38.71mm

    difference() {
        // Exact 84x84mm Octagonal Base Profile matching Front Face & Main Housing
        octagonal_prism(housing_w, housing_h, chamfer_outer, clamp_thick);

        // 1. Exact Rectangular Screen PCB Tab Cutout (32.00mm wide x Y = -38.71 to 0.0mm)
        // Leaving continuous 3.29mm solid structural bottom bridge (Y = -42 to -38.71mm)
        translate([-hw_tab_cut, bot_y_cut, -1.0])
            cube([tab_cutout_w, -bot_y_cut + 1.0, clamp_thick + 2.0]);

        // 2. Central aeration / weight reduction opening (Ø38.0mm)
        translate([0, 0, -1.0])
            cylinder(d = 38.0, h = clamp_thick + 2.0);

        // 3. 4x M3 Corner Screw Clearance Holes (+/-34.0mm, +/-34.0mm)
        // Matching Front Face and Main Housing corner chassis bolts
        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * corner_screw_x, sy * corner_screw_y, -1.0])
                    cylinder(d = m3_clearance, h = clamp_thick + 2.0);
            }
        }
    }
}

// Legacy Bezel module (Retained for reference)
module circular_top_bezel() {
    theta = atan2(bezel_screw_y, bezel_screw_x);
    r_anchor = 28.5;
    x_anchor = r_anchor * cos(theta);
    y_anchor = r_anchor * sin(theta);

    difference() {
        union() {
            cylinder(d = bezel_ring_dia, h = bezel_thick);
            for (sx = [-1, 1]) {
                for (sy = [-1, 1]) {
                    hull() {
                        translate([sx * x_anchor, sy * y_anchor, 0])
                            cylinder(d = 10.4, h = bezel_thick);
                        translate([sx * bezel_screw_x, sy * bezel_screw_y, 0])
                            cylinder(d = 10.4, h = bezel_thick);
                    }
                }
            }
        }

        translate([0, 0, -0.1])
            cylinder(d = bezel_inner_dia, h = bezel_thick + 0.2);
        
        translate([0, 0, bezel_thick - 1.8])
            cylinder(d1 = bezel_inner_dia, d2 = bezel_funnel_top, h = 1.81);

        translate([0, 0, -0.05])
            cylinder(d = 56.50, h = 1.60 + 0.05);

        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * bezel_screw_x, sy * bezel_screw_y, -0.5]) {
                    cylinder(d = m2_3_clearance, h = bezel_thick + 1.0);
                    translate([0, 0, bezel_thick - m2_3_cb_depth + 0.5])
                        cylinder(d = m2_3_cb_dia, h = m2_3_cb_depth + 1.0);
                }
            }
        }

        translate([0, 0, bezel_thick - 0.8])
            difference() {
                cylinder(d = bezel_ring_dia + 30, h = 1.0);
                cylinder(d1 = bezel_ring_dia, d2 = bezel_ring_dia - 1.6, h = 1.0);
            }
    }
}

// =========================================================================
// PART 2: MONOLITHIC FRONT FACE (OPTION 2: REAR-LOADING SCREEN)
// =========================================================================
module front_face_plate() {
    clr       = screen_tolerance;
    r_pocket  = (screen_pcb_w / 2.0) + clr;
    hw_tab    = screen_tab_half_w + clr;
    bot_y_tab = screen_pcb_bottom - clr;

    difference() {
        union() {
            // 1. Base 84x84mm plate with 45° outer perimeter edge chamfer
            hull() {
                octagonal_prism(housing_w, housing_h, chamfer_outer, front_face_thick - edge_chamfer);
                translate([0, 0, front_face_thick - 0.001])
                    octagonal_prism(housing_w - 2 * edge_chamfer, housing_h - 2 * edge_chamfer, chamfer_outer - edge_chamfer * 0.414, 0.001);
            }

            // 2. Integrated Raised Bezel Rim on Front (Z = 7.0 to 8.6mm)
            translate([0, 0, front_face_thick])
                cylinder(d1 = integrated_bezel_od, d2 = integrated_bezel_od - 2.4, h = integrated_bezel_h);
        }

        // 3. Continuous Conical Anti-Shadow Viewing Funnel connecting screen shelf to top of ring
        translate([0, 0, -1.0])
            cylinder(d = screen_aperture_dia, h = rear_pocket_depth + 1.0);
        translate([0, 0, rear_pocket_depth - 0.01])
            cylinder(d1 = screen_aperture_dia, d2 = screen_aperture_top, h = front_face_thick + integrated_bezel_h - rear_pocket_depth + 0.02);

        // 4. Exact Screen Contour Cavity RECESSED INTO REAR FACE (Z = 0 to rear_pocket_depth)
        translate([0, 0, -0.01]) {
            cylinder(r = r_pocket, h = rear_pocket_depth + 0.02);
            translate([-hw_tab, bot_y_tab, 0])
                cube([2 * hw_tab, -bot_y_tab, rear_pocket_depth + 0.02]);
        }

        // 5. 4x Symmetrical Outer M3 Mounting Screws (+/-34mm, +/-34mm)
        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * corner_screw_x, sy * corner_screw_y, -0.5]) {
                    cylinder(d = m3_clearance, h = front_face_thick + integrated_bezel_h + 1.0);
                    translate([0, 0, front_face_thick - m3_cb_depth + 0.5])
                        cylinder(d = m3_cb_dia, h = m3_cb_depth + 1.0);
                }
            }
        }
    }
}

// =========================================================================
// PART 3: MAIN HOUSING POD (84mm SQUARE, 240 HERITAGE RE-ENGINEERED)
// =========================================================================
module main_housing_pod() {
    difference() {
        // 1. Outer Chassis with 45° bottom chamfer (z = 0 to 28mm)
        hull() {
            octagonal_prism(housing_w - 2 * edge_chamfer, housing_h - 2 * edge_chamfer, chamfer_outer - edge_chamfer * 0.414, 0.001);
            translate([0, 0, edge_chamfer])
                octagonal_prism(housing_w, housing_h, chamfer_outer, housing_depth - edge_chamfer);
        }

        // 2. Internal Electronics Bay Cavity
        translate([0, 0, floor_thick])
            octagonal_prism(76.0, 76.0, 14.0, cavity_depth + 1.0);

        // 3. Shaved-depth USB-C Port with Conical Flare
        // Shaves inner wall down to 1.2mm outer wall thickness
        translate([-40.8, -11.0, floor_thick])
            cube([2.8, 22.0, cavity_depth + 0.2]);

        // Snug Oval Tunnel (clean straight cut without outer chamfer)
        translate([-45.0, 0, usbc_z]) {
            rotate([0, 90, 0])
                hull() {
                    translate([-r_port, -y_span, 0]) cylinder(d = 2 * r_port, h = 10.0);
                    translate([-r_port,  y_span, 0]) cylinder(d = 2 * r_port, h = 10.0);
                }
        }

        // 4. Elevated DuPont Clearance Trenches (starts at Z = 6.0mm with 45° bottom ramp)
        // 4a. Bottom Wall DuPont Trench (Y = -40.0 to -38.0mm, width 32.0mm)
        hull() {
            translate([-16.0, -40.0, 6.0]) cube([32.0, 6.0, housing_depth - 5.9]);
            translate([-16.0, -38.0, 4.0]) cube([32.0, 4.0, housing_depth - 3.9]);
        }

        // 4b. Right Wall DuPont Trench (opposite USB-C on Left Wall: X = 38.0 to 40.0mm, length 32.0mm)
        hull() {
            translate([34.0, -16.0, 6.0]) cube([6.0, 32.0, housing_depth - 5.9]);
            translate([34.0, -16.0, 4.0]) cube([4.0, 32.0, housing_depth - 3.9]);
        }

        // 5. 4x Symmetrical Corner M3 Pilot Holes with 45° Entry Lead-In Chamfers
        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * corner_screw_x, sy * corner_screw_y, housing_depth - m3_pilot_depth]) {
                    cylinder(d = m3_pilot_dia, h = m3_pilot_depth + 0.1);
                    translate([0, 0, m3_pilot_depth - 1.2])
                        cylinder(d1 = m3_pilot_dia, d2 = 4.8, h = 1.21);
                }
            }
        }

        // 6. High-Airflow Aeration Slits in Outer Zones (|Y| >= 16.5mm)
        for (sy = [-1, 1]) {
            for (row = [22.0, 26.0]) {
                for (cx = [-18.0, 0.0, 18.0]) {
                    translate([cx, sy * row, -0.5])
                        cube([10.0, 1.20, floor_thick + 1.0], center = true);
                }
            }
        }

        // Safe Under-ESP32 Aeration Grille
        for (y_pos = [-3.6, -1.2, 1.2, 3.6]) {
            translate([-33.0, y_pos, floor_thick / 2.0]) cube([6.0, 1.35, floor_thick + 1.0], center = true);
            translate([-24.0, y_pos, floor_thick / 2.0]) cube([6.0, 1.35, floor_thick + 1.0], center = true);
        }

        // 45° Peaked Roof Top Vertical Aeration Exhaust Slits (7 slots along top wall at Y = +42mm)
        // Centered vertically at Z = 9.0 to 19.0mm (leaving balanced 9mm solid base and 9mm solid top rim)
        // Extrusion height 16.0mm from Y = 46.0mm cleanly punches through the 4.0mm wall into cavity (Y = 30 to 46mm)
        for (vx = [-18.0, -12.0, -6.0, 0.0, 6.0, 12.0, 18.0]) {
            translate([vx, 46.0, 0]) {
                rotate([90, 0, 0])
                    linear_extrude(height = 16.0)
                        polygon([
                            [-1.0, 9.0],
                            [ 1.0, 9.0],
                            [ 1.0, 18.0],
                            [ 0.0, 19.0],
                            [-1.0, 18.0]
                        ]);
            }
        }
    }

    // 7. ESP32 SuperMini Precision Tolerance-Based Press Fit Cradle (G0 Rev 2 Approved)
    translate([0, 0, floor_thick]) {
        // Top and Bottom Guide Rails with Rear Corner Stops
        linear_extrude(height = cradle_h) {
            polygon([[x_front, hw_in], [x_rear, hw_in], [x_rear, center_gap_half_w], [x_rear + 1.6, center_gap_half_w], [x_rear + 1.6, hw_out], [x_front, hw_out]]);
            polygon([[x_front, -hw_out], [x_rear + 1.6, -hw_out], [x_rear + 1.6, -center_gap_half_w], [x_rear, -center_gap_half_w], [x_rear, -hw_in], [x_front, -hw_in]]);
        }

        // Outer Edge Support Ledges (0.80mm step outside pins)
        linear_extrude(height = rail_h) {
            polygon([[x_front, hw_in - 0.80], [x_rear, hw_in - 0.80], [x_rear, hw_in], [x_front, hw_in]]);
            polygon([[x_front, -hw_in], [x_rear, -hw_in], [x_rear, -(hw_in - 0.80)], [x_front, -(hw_in - 0.80)]]);
        }

        // 4x Vertical Micro-Crush Ribs (0.35mm protrusion)
        for (rx = [-32.0, -22.0]) {
            translate([rx - 0.7, hw_in - crush_rib_protrusion, 0])
                cube([1.4, crush_rib_protrusion, cradle_h - 0.4]);
            translate([rx - 0.7, -hw_in, 0])
                cube([1.4, crush_rib_protrusion, cradle_h - 0.4]);
        }
    }
}

// =========================================================================
// PART 4 & 5: TWO-TIER DESK PEDESTAL STAND (FOR 84mm SQUARE POD)
// =========================================================================
module stand_tier1_base() {
    difference() {
        hull() {
            for (sx = [-1, 1]) {
                for (sy = [-1, 1]) {
                    translate([sx * (stand_base_w / 2 - 6), sy * (stand_base_d / 2 - 6), 0])
                        cylinder(r = 6.0, h = stand_base_h);
                }
            }
        }

        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * (stand_base_w / 2 - 12), sy * (stand_base_d / 2 - 12), -0.1])
                    cylinder(d = 8.5, h = 1.6);
            }
        }

        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * 28.0, sy * 26.0, stand_base_h - 3.0])
                    cylinder(d = 5.2, h = 3.2);
            }
        }
    }
}

module stand_tier2_trunk() {
    cradle_tilt = stand_tilt_deg;
    
    difference() {
        hull() {
            translate([0, 0, 0])
                octagonal_prism(stand_base_w - 4, stand_base_d - 4, 8.0, 2.0);
            translate([0, 2.0, stand_trunk_h - 2.0])
                octagonal_prism(housing_w + 2.0, housing_w - 2.0, 8.0, 2.0);
        }

        translate([0, 8.0, stand_trunk_h + 12.0]) {
            rotate([cradle_tilt, 0, 0]) {
                translate([0, 0, -housing_depth / 2])
                    octagonal_prism(housing_w + 0.8, housing_h + 0.8, chamfer_outer, housing_depth + 40.0);
            }
        }

        translate([-13.0, -stand_base_d / 2 - 1.0, -0.5])
            cube([26.0, stand_base_d + 2.0, stand_trunk_h + 1.0]);

        for (sx = [-1, 1]) {
            for (sy = [-1, 1]) {
                translate([sx * 28.0, sy * 26.0, -3.0])
                    cylinder(d = 4.8, h = 3.0);
            }
        }
    }
}

module monolithic_stand() {
    stand_tier1_base();
    translate([0, 0, stand_base_h])
        stand_tier2_trunk();
}

// =========================================================================
// ASSEMBLY PREVIEW
// =========================================================================
if (part == 0) {
    color("#4A3728")
        stand_tier1_base();
    translate([0, 0, stand_base_h])
        color("#222426")
            stand_tier2_trunk();

    translate([0, 8.0, stand_base_h + stand_trunk_h + 12.0]) {
        rotate([stand_tilt_deg, 0, 0]) {
            color("#1E2022")
                main_housing_pod();

            // Internal Rear Clamp Bracket (Option 2)
            translate([0, 0, housing_depth - 3.0])
                color("#E67E22")
                    rear_clamp();

            // Screen Module (Seated in rear cavity)
            translate([0, 0, housing_depth]) {
                color("#00E5FF")
                    translate([0, 0, 1.2])
                        cylinder(d = screen_active_dia, h = 0.5);
                color("#0A0A0A")
                    cylinder(d = screen_lcm_w, h = 1.0);
            }

            // Monolithic Front Face with Integrated Raised Bezel
            translate([0, 0, housing_depth])
                color("#2B2D30")
                    front_face_plate();

            // Corner M3 Screws
            for (sx = [-1, 1]) {
                for (sy = [-1, 1]) {
                    translate([sx * corner_screw_x, sy * corner_screw_y, housing_depth + front_face_thick - 1.5])
                        color("#D4AF37")
                            cylinder(d = 5.5, h = 2.5);
                }
            }
        }
    }
} else if (part == 1) {
    rear_clamp();
} else if (part == 11) {
    circular_top_bezel();
} else if (part == 2) {
    front_face_plate();
} else if (part == 3) {
    main_housing_pod();
} else if (part == 4) {
    stand_tier1_base();
} else if (part == 5) {
    stand_tier2_trunk();
} else if (part == 6) {
    monolithic_stand();
}
