# 🖨️ GC9A01 1.28″ Round Display & ESP32-C3 SuperMini Cyberdeck Enclosure

3D printable enclosure files, slicer settings, hardware BOM, and assembly instructions for the **Tiny AI Limits Round Cyberdeck Desk Console** (reengineered directly from the concept 3D renders [`gc9a01_3d_enclosure_render.jpg`](../assets/gc9a01_3d_enclosure_render.jpg) and [`gc9a01_enclosure_rear_view.jpg`](../assets/gc9a01_enclosure_rear_view.jpg)).

> [!IMPORTANT]
> **Bottom DuPont Wire Drop Trench + Slim 26mm Depth:**
> * **Bottom Wire Drop Trench ($20\text{mm} \times 12\text{mm}$):** Positioned directly beneath the GC9A01 7-pin header ($Y = -24.74\text{mm}$), allowing DuPont connectors to plug in and drop directly into the desk stand's $20\text{mm}$ cable channel with zero vertical pinch.
> * **Direct Screen Bolting:** 2 $\times$ M2 threaded pilot holes on the front bezel matching the GC9A01 bottom tab mounting holes ($19.26\text{mm}$ pitch).
> * **Self-Locking Pin Standoffs:** 16 pin-registration blind holes ($2.54\text{mm}$ pitch) + rear thrust stop to lock the ESP32-C3 against insertion force.
> * **Sculpted Two-Tier Pedestal Stand:** $22^\circ$ ergonomic V-saddle cradle with tapered body, $20\text{mm}$ rear cable channel, and optional standalone accent base plate.

---

## 📁 Included CAD & STL Files

All models are located in [`round 240x240/enclosure/`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/):

| File | Description | Outer Dims ($W \times D \times H$) | Print Time (est.) |
| **[`gc9a01_springlatch_enclosure_flat.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_springlatch_enclosure_flat.stl)** | **Springlatch 100% Print-in-Place Enclosure** with Clockspring-style compliant wavy spring latch, push-button locking tabs, GC9A01 viewing window, ESP32-C3 snap cradle, and kickstand pads (Flat 180° unfolded) | $56 \times 116 \times 20.0\text{mm}$ | ~60 mins |
| **[`gc9a01_springlatch_base.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_springlatch_base.stl)** | Springlatch Lower Base Housing with $18^\circ$ kickstand pads, 4x rubber feet pockets, USB-C port, and ESP32-C3 cradle | $56 \times 58 \times 20.0\text{mm}$ | ~40 mins |
| **[`gc9a01_springlatch_lid.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_springlatch_lid.stl)** | Springlatch Upper Hinged Lid with conical anti-shadow bezel, screen pocket, and compliant serpentine spring latch | $56 \times 58 \times 9.5\text{mm}$ | ~25 mins |
| **[`gc9a01_springlatch_enclosure.scad`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_springlatch_enclosure.scad)** | Parametric OpenSCAD source for Springlatch Edition (Parts 0–3: Flat PiP, Base, Lid, Closed preview) | — | — |
| **[`generate_springlatch_stl.py`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/generate_springlatch_stl.py)** | High-performance Python Manifold generator for watertight Springlatch STLs | — | — |
| **[`gc9a01_front_bezel.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_front_bezel.stl)** | Front bezel plate with $60^\circ$ male interlocking tongue, $\varnothing 33.0\text{mm}$ conical anti-shadow window, $\varnothing 39.4\text{mm}$ screen pocket, 2 blind M2 pilot holes, and 4 M3 counterbored corner pockets | $54.4 \times 54.4 \times 11.0\text{mm}$ | ~25 mins |
| **[`gc9a01_main_housing.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_main_housing.stl)** | Support-free $27.5\text{mm}$ deep **V2.1 Lightened Main Housing** with $60^\circ$ self-centering female receiving socket (0.20mm tolerance), 4x self-supporting conical corner coring pockets, slimmed $1.0\text{mm}$ cradle guide walls, $1.2\text{mm}$ flat USB-C wall, zero ceiling overhang, precision $18.5\text{mm}$ carriage, inside floor debossed "V2.1", rear corner stops with center wire gap, and dual DuPont trenches | $54.4 \times 54.4 \times 27.5\text{mm}$ | ~38 mins |
| **[`gc9a01_main_housing_legacy.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_main_housing_legacy.stl)** | Legacy $27.5\text{mm}$ deep main housing with single bottom DuPont wire trench (preserved for rollback) | $54.4 \times 54.4 \times 27.5\text{mm}$ | ~45 mins |
| **[`gc9a01_minimalist_stand.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_minimalist_stand.stl)** | Minimalist open A-frame cradle desk stand with $22^\circ$ tilt, front retaining lip, open triangular side window, and cable slot | $48 \times 62 \times 44.0\text{mm}$ | ~30 mins |
| **[`gc9a01_desk_stand.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_desk_stand.stl)** | Sculpted two-tier pedestal cradle stand with $22^\circ$ V-saddle & slide-in pod channel | $64 \times 68 \times 29.0\text{mm}$ | ~45 mins |
| **[`gc9a01_stand_tier1_base.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_stand_tier1_base.stl)** | Standalone Tier-1 bottom plate with 4 alignment pillars for wood PLA or dual-material printing | $64 \times 68 \times 8.5\text{mm}$ | ~20 mins |
| **[`gc9a01_stand_tier2_trunk.stl`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_stand_tier2_trunk.stl)** | Tier-2 cradle trunk with alignment sockets and $22^\circ$ V-saddle | $62 \times 66 \times 24.0\text{mm}$ | ~40 mins |
| **[`gc9a01_cyberdeck_enclosure.scad`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_cyberdeck_enclosure.scad)** | Fully parametric OpenSCAD source file (part 0 to 7) | — | — |
| **[`generate_stl.py`](file:///Users/alessandrolongoni/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/generate_stl.py)** | Standalone Boolean CSG mesh generator script generating 100% watertight binary STLs | — | — |

---

## 🔩 Hardware Bill of Materials (BOM)

| Item | Quantity | Purpose |
| :--- | :---: | :--- |
| **GC9A01 1.28″ Round IPS SPI Display** | 1 | Circular $240\times 240$ color screen module |
| **ESP32-C3 SuperMini** | 1 | Microcontroller board (pin headers soldered facing up) |
| **Female-to-Female DuPont Jumpers (10cm)** | 7 | Standard jumper wires for SPI wiring harness |
| **M3 $\times$ 35mm Socket Head Cap Screws** | 4 | Fastens Front Bezel $\to$ Mid Clamp $\to$ Main Housing |
| **M3 Brass Heat-Set Inserts / Direct Tap** | 4 | Main housing corner posts |
| **8mm $\times$ 1.5mm Adhesive Rubber Feet** | 4 | Fitted into stand base recesses for non-slip desk grip |
| **USB-C Cable (Braided or Right-Angle)** | 1 | Power delivery & firmware flashing |

---

## ⚙️ Slicer Print Settings (Cura / PrusaSlicer / Bambu Studio / OrcaSlicer)

* **Material:** Matte Charcoal Black PLA / PETG for the housing & bezel, Accent color (e.g. Orange / Cyan / White) for the Mid Clamp, Wood PLA or Walnut Brown for the stand base.
* **Layer Height:** `0.16mm` or `0.20mm`.
* **Perimeters / Walls:** `3` walls (for solid screw hole threading and spring flexures).
* **Top/Bottom Solid Layers:** `4` top, `4` bottom.
* **Infill:** `20% Gyroid` or `Grid`.
* **Supports:** **NO SUPPORTS NEEDED** when oriented properly:
  * **Springlatch Full PiP Assembly (`gc9a01_springlatch_enclosure_flat.stl`):** Print flat unfolded on build plate ($180^\circ$ orientation). The self-supporting $45^\circ$ conical hinge pins and compliant spring air slits print completely support-free.
  * **Front Bezel:** Print face-down on build plate (flat side down).
  * **Mid Clamp:** Print flat on build plate (compression lip facing up).
  * **Main Housing:** Print with rear face on build plate (open front cavity facing up).
  * **Desk Stand:** Print flat on base bottom (angled V-saddle cradle facing up).

---

## 🪗 Springlatch Edition: Zero-Hardware Tool-less Operation

The **Springlatch Edition** (`gc9a01_springlatch_enclosure_flat.stl`) allows 100% screwless, tool-less assembly:

1. **Print in One Piece:** Print the entire assembly unfolded flat on your 3D printer bed in ~60 minutes.
2. **First Flex (Break-In):** Gently wiggle the hinge to break free the $0.38\text{mm}$ print-in-place clearance cones until it swings smoothly through $180^\circ$.
3. **Mount Electronics:**
   * Snap the **ESP32-C3 SuperMini** into the lower tub cradle (held securely by the compliant snap arm).
   * Insert the **GC9A01 1.28″ Round Display** into the upper lid's rear pocket.
   * Connect the 7-wire SPI harness between the board and display.
4. **Push-to-Close Auto Latch:** Swing the lid closed. The dual front locking hooks ride up the base's $45^\circ$ lead-in ramps, flexing the serpentine spring back until snapping securely into the undercut catches.
5. **Desk Operation:** The integrated rear kickstand pads keep the console resting at an ergonomic $18^\circ$ viewing angle on your desk. Press the center tactile thumb button to flex the spring and pop open the lid anytime.

---

## 🪛 Assembly Step-by-Step

1. **Insert Screen into Front Bezel:** Drop the GC9A01 display face-down into the rear pocket of the front bezel.
2. **Position Mid Clamp:** Place the **Mid Clamp** behind the screen so the circular compression collar rests against the rear fiberglass rim of the PCB.
3. **Mount ESP32-C3 & Wire Harness:** Drop the ESP32-C3 SuperMini into the main housing standoffs and connect the 7 SPI jumper wires between the **GC9A01** and **ESP32-C3 SuperMini**:
   * `SCL` $\to$ `GPIO 4`
   * `SDA` $\to$ `GPIO 6`
   * `CS` $\to$ `GPIO 5`
   * `DC` $\to$ `GPIO 7`
   * `RST` $\to$ `GPIO 1`
   * `BLK` $\to$ `3V3` or `GPIO 0`
   * `VCC` $\to$ `3V3` / `GND` $\to$ `GND`
4. **Fasten 3-Piece Sandwich:** Mate Front Bezel $\to$ Mid Clamp $\to$ Main Housing and secure with 4 $\times$ M3 corner screws. Tightening the corner screws compresses the mid clamp against the screen PCB, locking it rigidly against the front window.
5. **Slot into Stand:** Slide the assembled pod into the sculpted $22^\circ$ V-saddle desk cradle and connect your USB-C cable through the chamfered port opening.
