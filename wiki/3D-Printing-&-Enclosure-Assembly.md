# 🖨️ 3D Printing & Enclosure Assembly

All enclosure CAD models for **Tiny AI Limits** are **100% support-free FDM 3D printable**, engineered with tight tolerances, anti-shadow conical bevels, and integrated cable strain reliefs.

---

## 📦 STL Model Files (`round 240x240/enclosure/`)

| File Name | Component | Function |
| :--- | :--- | :--- |
| `gc9a01_front_bezel.stl` | **Front Bezel Display Carrier** | Holds the 1.28" LCD with an anti-shadow conical aperture and M3 counterbores. |
| `gc9a01_main_housing.stl` | **Main Housing Bucket** | Encloses the ESP32-C3 SuperMini with a lowered USB-C port and M3 pilot holes. |
| `gc9a01_stand_tier1_base.stl` | **Tier 1 Base Plate** | Weighted desk footprint with 4 alignment pillars and rubber feet recesses (ideal for Wood PLA). |
| `gc9a01_stand_tier2_trunk.stl` | **Tier 2 Pedestal Trunk** | Sculpted monolithic trunk with 4 slide sockets and an $18^\circ$ ergonomic viewing V-saddle. |
| `gc9a01_desk_stand.stl` | **Unified Desk Stand** | Single-piece monolithic alternative to the two-tier pedestal. |
| `gc9a01_cyberdeck_enclosure.scad` | **Parametric OpenSCAD Source** | Full parametric source code allowing customizable dimensions and tolerances. |

---

## 🖨️ Recommended Slicer Settings

| Slicer Parameter | Recommended Value | Notes |
| :--- | :--- | :--- |
| **Material** | PLA, PETG, or Wood-filled PLA | PETG for heat resistance; Wood PLA for the base tier. |
| **Layer Height** | `0.16 mm` – `0.20 mm` | `0.16 mm` recommended for smooth conical bezel curves. |
| **Wall Loops / Perimeters** | `3` or `4` walls | Ensures strong M3 screw threading without cracking. |
| **Infill Density & Pattern** | `20%` Gyroid or Grid | Gives optimal mechanical rigidity and weight. |
| **Supports** | **NONE (Disabled)** | All overhangs and bridges are designed at $\le 45^\circ$. |
| **Brim** | Optional | Recommended for small footprint parts if bed adhesion is weak. |

---

## 🔧 Step-by-Step Mechanical Assembly

```
     [ FRONT BEZEL ]       [ GC9A01 LCD ]     [ MAIN HOUSING ]        [ 4x M3 SCREWS ]
       ┌─────────┐           ┌─────────┐        ┌─────────┐             ══════>
       │ ╭─────╮ │  <──────  │ ╭─────╮ │ <────  │ ╭─────╮ │  <────────  ══════>
       │ │ LCD │ │           │ │     │ │        │ │ ESP │ │             ══════>
       │ ╰─────╯ │           │ ╰─────╯ │        │ ╰─────╯ │             ══════>
       └─────────┘           └─────────┘        └─────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ TIER 2 PEDESTAL      │
                                          │ ($18^\circ$ V-Saddle)│
                                          └──────────┬───────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ TIER 1 BASE (Wood)   │
                                          │ + Non-slip Feet      │
                                          └──────────────────────┘
```

### 1. Mount the Display into the Front Bezel
* Gently press the GC9A01 circular display into the front bezel carrier.
* Ensure the anti-shadow conical bevel frames the active display area without obstruction.

### 2. Route Wiring into Main Housing
* Pass the soldered silicone wires and ESP32-C3 SuperMini into the main housing bucket.
* Align the USB-C port with the rear cutout in the bucket.

### 3. Fasten the Enclosure
* Mate the front bezel to the main housing.
* Secure the sandwich using four **M3 × 6mm** or **M3 × 8mm** socket head screws into the corner pilot holes. Do not overtighten.

### 4. Assemble the Two-Tier Desk Pedestal
* Insert the 4 alignment pillars of the **Tier 1 Base Plate** into the matching sockets of the **Tier 2 Pedestal Trunk**. (Use a drop of cyanoacrylate CA glue for permanent bonding if desired).
* Attach four small self-adhesive silicone/rubber bumper feet into the bottom recesses of the base plate.
* Seat the assembled display module into the $18^\circ$ tilted V-saddle cradle notch.
