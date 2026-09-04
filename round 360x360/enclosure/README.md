# 🖨️ GC9B72 2.1″ Round Display (360×360) Cyberdeck Enclosure (Heritage Edition)

3D printable enclosure files, slicer settings, hardware BOM, and assembly instructions for the **2.1-Inch GC9B72 Cyberdeck Desk Console**, engineered directly following the **240×240 Unit 01 Heritage Architecture** with the **Option 2 Rear-Loading Screen Architecture**:
* **100% Symmetrical 84mm Square Chassis ($84.0\text{mm} \times 84.0\text{mm}$)**
* **Option 2 Rear-Loading Screen Architecture:**
  * **100% Seamless Monolithic Front Face:** Clean solid front plate with an integrated raised circular bezel rim ($\varnothing 66.4\text{mm}$) and $\varnothing 54.0\text{mm}$ viewing aperture.
  * **Zero Front Screws & Zero Exposed Cutouts:** The rectangular PCB tab, solder joints, flex ribbon, and 10-pin header are completely concealed inside the enclosure.
  * **Solid Front Retaining Lip:** $2.62\text{mm}$ continuous circular flange prevents display glass from ever pushing out the front.
  * **Internal Rear Clamp Bracket:** Rigid internal frame fastens with 4x M2.5 direct-tap screws, trapping the PCB forward while keeping the 10-pin header 100% open for DuPont jumpers.
* **Chamfering & Edge Bevels:** $45^\circ$ outer bottom perimeter chamfer ($1.2\text{mm} \times 45^\circ$) + $7.0\text{mm} \times 45^\circ$ corner chamfers
* **Flush-Edge Microcontroller Mounting:** ESP32-S3/C3 SuperMini mounted **only $1.2\text{mm}$ from the outer left flank** for flush USB-C cable seating
* **Shaved-Depth USB-C Port:** Precision oval/stadium cutout ($r_{inner}=1.95\text{mm}$) with $45^\circ$ conical lead-in entry flare
* **High-Airflow Cooling System:**
  * 7 $\times$ vertical exhaust vents with $45^\circ$ peaked roof along top wall ($Y = +42\text{mm}$)
  * Contour-following horizontal rear aeration rows in outer zones ($|Y| \ge 16.5\text{mm}$)
  * Safe under-ESP32 cooling grille
* **Precision Board Retention Cradle:**
  * Dual L-shaped guide rails with rear mechanical thrust stop wall ($X = -16.0\text{mm}$)
  * $0.7\text{mm}$ outer edge support ledges (supporting PCB edges outside pin headers; bottom components completely unobstructed)
  * Dual discrete side retention snap clips ($0.28\text{mm}$ lip overhang at $Z = 5.2\text{mm}$)
* **Dual Elevated DuPont Clearance Trenches:** Starts at $Z = 6.0\text{mm}$ with $45^\circ$ self-supporting bottom ramps along both the bottom wall (for screen 10-pin DuPont headers) and opposite right wall (for internal jumper bundle routing and side accessories).
* **Fasteners:**
  * 4x M2.5 $\times$ 6mm Socket Head Cap Screws for internal Rear Clamp retention ($\varnothing 2.05\text{mm}$ direct-tap pilot holes in Front Face)
  * 4x M3 $\times$ 16mm Socket Head Cap Screws for Chassis Corners ($\varnothing 2.50\text{mm}$ direct-tap pilot posts)

---

## 📁 Included CAD & STL Files

All models are located in [`round 360x360/enclosure/`](./):

| File | Description | Outer Dims ($W \times D \times H$) | Print Time (est.) |
| :--- | :--- | :---: | :---: |
| **`gc9b72_front_face.stl`** | Monolithic Symmetrical 84mm Square Front Plate with integrated raised circular bezel rim, rear exact-contour cavity, and 4x M3 corner countersunk holes | **$84.0 \times 84.0 \times 8.6\text{ mm}$** | ~40 mins |
| **`gc9b72_rear_clamp.stl`** | Slim Full-Footprint 84mm Sandwich Clamp Plate with 4x M3 corner clearance holes, center ventilation port, and enclosed DuPont pass-through window | **$84.0 \times 84.0 \times 1.6\text{ mm}$** | ~12 mins |
| **`gc9b72_main_housing.stl`** | Symmetrical 84mm Square Housing Pod with flush-edge ESP32 cradle, shaved USB-C port, peaked roof vents, and 4x direct tap corner posts | **$84.0 \times 84.0 \times 28.0\text{ mm}$** | ~55 mins |
| **`gc9b72_stand_tier1_base.stl`** | Stand Tier 1 Accent Base Plate with 4x rubber feet pockets and alignment sockets | $94.0 \times 88.0 \times 6.0\text{ mm}$ | ~25 mins |
| **`gc9b72_stand_tier2_trunk.stl`** | Stand Tier 2 Cradle Trunk with $22^\circ$ V-saddle for 84mm pod and $26\text{mm}$ rear cable channel | $90.0 \times 85.0 \times 29.0\text{ mm}$ | ~50 mins |
| **`gc9b72_monolithic_stand.stl`** | Single-piece combined desk stand for 84mm square pod | $94.0 \times 88.0 \times 32.0\text{ mm}$ | ~70 mins |
| **`gc9b72_top_bezel.stl`** | *(Legacy / Optional)* External Circular Top Bezel Ring for front-clamping configurations | $74.6 \times 66.8 \times 4.5\text{ mm}$ | ~20 mins |
| **`gc9b72_cyberdeck_enclosure.scad`**| Fully parametric OpenSCAD master source model (Parts 0–6) | — | — |
| **`generate_stl.py`** | High-performance Python Manifold generator for watertight binary STLs | — | — |

---

## 🔩 Hardware Bill of Materials (BOM)

| Item | Quantity | Purpose | Notes |
| :--- | :---: | :--- | :--- |
| **GC9B72 2.1″ Round IPS TFT Display ($360\times 360$)** | 1 | Circular color display module | GoldenMorning / EstarDyn 10-pin SPI |
| **ESP32-S3 SuperMini / Zero (or C3 SuperMini)** | 1 | Microcontroller board | Snaps into flush-edge L-rails |
| **M3 $\times$ 16mm Socket Head Cap Screws** | 4 | Fastens entire sandwich: Front Face $\to$ Rear Clamp $\to$ Main Housing Pod | Direct taps into $\varnothing 2.50\text{mm}$ corner posts |
| **8mm $\times$ 1.5mm Adhesive Rubber Feet** | 4 | Fitted into stand base recesses for non-slip desk grip | Optional |
| **USB-C Cable (Braided or Standard)** | 1 | Power & data connection through left port | Plugs into flush ESP32 port |

---

## 🛠️ Step-by-Step Assembly Sequence

1. **Install the Display Module:**
   * Place the `gc9b72_front_face` face-down on a soft surface.
   * Drop the GC9B72 display module into the rear pocket cavity from behind. The round glass seats against the internal $2.62\text{mm}$ retaining lip.
2. **Place the Rear Clamp Plate:**
   * Lay the slim $1.6\text{mm}$ `gc9b72_rear_clamp` plate directly over the back of the front plate. Its 4 corner M3 holes align with the front plate holes, and the enclosed window fits over the 10-pin header.
3. **Wire the Display:**
   * Plug female DuPont jumpers directly through the enclosed $28 \times 10\text{mm}$ wiring window onto the 10-pin header.
4. **Install Microcontroller & Housing:**
   * Snap the ESP32 into the cradle rails inside `gc9b72_main_housing`.
   * Connect the DuPont jumpers to the corresponding SPI pins on the ESP32.
5. **Close the Console:**
   * Mate the Main Housing Pod onto the back of the sandwich.
   * Thread the 4x M3 $\times$ 16mm screws into the corner counterbored holes from the front and tighten until snug. Zero extra fasteners required!

---

## ⚙️ Slicer Print Settings (Bambu Studio / PrusaSlicer / OrcaSlicer)

* **Material:** 
  * Main Housing & Rear Clamp: Matte Charcoal Black PLA / PETG.
  * Front Face Plate: Matte Charcoal Black with optional accent color ring or single color.
  * Stand Base: Wood PLA or Walnut Brown PLA.
* **Perimeters / Walls:** **`4` walls minimum** (ensures 100% solid plastic around the $\varnothing 2.05\text{mm}$ and $\varnothing 2.50\text{mm}$ pilot holes and cradle retaining clips).
* **Layer Height:** `0.16mm` or `0.20mm`.
* **Top / Bottom Solid Layers:** `4` top, `4` bottom.
* **Infill:** `20% Gyroid` or `Grid`.
* **Supports:** **NONE NEEDED** when oriented properly:
  * **Front Face:** Print flat front face-up (or face-down on a textured PEI sheet).
  * **Rear Clamp:** Print flat on build plate.
  * **Main Housing:** Print with rear backplate on build plate (cavity opening facing up).
  * **Desk Stand:** Print flat on bottom surface.
