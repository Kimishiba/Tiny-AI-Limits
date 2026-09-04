# 🖨️ GC9B72 2.1″ Round Display (360×360) Cyberdeck Enclosure (Heritage Edition)

3D printable enclosure files, slicer settings, hardware BOM, and assembly instructions for the **2.1-Inch GC9B72 Cyberdeck Desk Console**, engineered directly following the **240×240 Unit 01 Heritage Architecture** with the **Option 2 Rear-Loading Screen Architecture**:
* **100% Symmetrical 84mm Square Chassis ($84.0\text{mm} \times 84.0\text{mm}$)**
* **Option 2 Rear-Loading Screen Architecture:**
  * **100% Seamless Monolithic Front Face:** Clean solid front plate with a prominent raised circular bezel rim ($\varnothing 72.0\text{mm}$, $+2.8\text{mm}$ elevation) and a continuous anti-shadow conical viewing funnel expanding from $\varnothing 54.0\text{mm}$ at the screen shelf to $\varnothing 60.0\text{mm}$ at the ring summit.
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
* **Precision M.2-Style Screw Retention System (G0 Approved):**
  * **Bifurcated Front Capture Ears:** Left ($Y = -9.65\text{ to } -5.00\text{mm}$) and Right ($Y = +5.00\text{ to } +9.65\text{mm}$) ears with $45^\circ$ self-supporting lead-in chamfers trap front PCB shoulders against lift and pull-out, leaving central $10.0\text{mm}$ open for the USB-C metal shell.
  * **Expanded Clone Tolerances:** $19.30\text{mm}$ pocket width, $Z = 5.90\text{mm}$ ear height, $24.20\text{mm}$ longitudinal span swallows AliExpress board variations ($1.2 - 1.6\text{mm}$ thickness, $18.2 - 18.9\text{mm}$ width).
  * **Mechanical Thrust Stop Rib ($X = -17.0\text{mm}$):** Absorbs 100% of USB-C insertion forces directly into the chassis floor.
  * **Rear Standoff Post ($X = -11.5\text{mm}$):** $\varnothing 7.00\text{mm}$ post with thick $2.175\text{mm}$ solid plastic wall (5 perimeters) and $\varnothing 2.65\text{mm}$ pilot hole, eliminating hoop stress blowout. Positioned $> 5.5\text{mm}$ behind the ceramic antenna element to protect 2.4GHz Wi-Fi/BLE from RF detuning.
  * **Precision M3 Clamp Tab (`gc9b72_esp32_clamp_tab.stl`):** $11.50 \times 7.50 \times 4.00\text{mm}$ bridge tab with captive retention ring and 100% planar bed face for support-free printing in $\sim 2.5\text{ mins}$.
* **Dual Elevated DuPont Clearance Trenches:** Starts at $Z = 6.0\text{mm}$ with $45^\circ$ self-supporting bottom ramps along both the bottom wall (for screen 10-pin DuPont headers) and opposite right wall (for internal jumper bundle routing and side accessories).
* **Fasteners:**
  * 4x M2.5 $\times$ 6mm Socket Head Cap Screws for internal Rear Clamp retention ($\varnothing 2.05\text{mm}$ direct-tap pilot holes in Front Face)
  * 4x M3 $\times$ 16mm Socket Head Cap Screws for Chassis Corners ($\varnothing 2.50\text{mm}$ direct-tap pilot posts)
  * 1x M3 $\times$ 6mm or 8mm Socket Head or Button Head Cap Screw for ESP32 Hold-Down Tab

---

## 📁 Included CAD & STL Files

All models are located in [`round 360x360/enclosure/`](./):

| File | Description | Outer Dims ($W \times D \times H$) | Print Time (est.) |
| :--- | :--- | :---: | :---: |
| **`gc9b72_front_face.stl`** | Monolithic Symmetrical 84mm Square Front Plate with prominent raised circular bezel rim, continuous conical viewing funnel, precision 31.2mm rear screen pocket, and 4x M3 corner countersunk holes | **$84.0 \times 84.0 \times 9.8\text{ mm}$** | ~45 mins |
| **`gc9b72_rear_clamp.stl`** | Slim Full-Footprint 84mm Sandwich Clamp Plate with 4x M3 corner clearance holes, center ventilation port, and precision 32.0mm screen PCB tab window | **$84.0 \times 84.0 \times 1.6\text{ mm}$** | ~12 mins |
| **`gc9b72_main_housing.stl`** | Symmetrical 84mm Square Housing Pod with tolerance-based press fit cradle, micro-crush ribs, front capture ears, shaved USB-C port, peaked roof vents, and 4x direct tap corner posts | **$84.0 \times 84.0 \times 28.0\text{ mm}$** | ~55 mins |
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
| **ESP32-S3 SuperMini / Zero (or C3 SuperMini)** | 1 | Microcontroller board | Press-fit into integrated cradle with crush ribs |
| **M3 $\times$ 16mm Socket Head Cap Screws** | 4 | Fastens entire sandwich: Front Face $\to$ Rear Clamp $\to$ Main Housing Pod | Direct taps into $\varnothing 2.50\text{mm}$ corner posts |
| **8mm $\times$ 1.5mm Adhesive Rubber Feet** | 4 | Fitted into stand base recesses for non-slip desk grip | Optional |
| **USB-C Cable (Braided or Standard)** | 1 | Power & data connection through left port | Plugs into flush ESP32 port |

---

## 🛠️ Step-by-Step Assembly Sequence

1. **Install the Display Module:**
   * Place the `gc9b72_front_face` face-down on a soft surface.
   * Drop the GC9B72 display module into the rear pocket cavity from behind. The round glass seats against the internal $2.62\text{mm}$ retaining lip.
2. **Place the Rear Clamp Plate:**
   * Lay the slim $1.6\text{mm}$ `gc9b72_rear_clamp` plate directly over the back of the front plate. Its 4 corner M3 holes align with the front plate holes, and the precision $32.0\text{mm}$ cutout fits over the 10-pin header.
3. **Wire the Display:**
   * Plug female DuPont jumpers directly through the cutout onto the 10-pin header.
4. **Install the Microcontroller (Tool-Free Press Fit):**
   * Slide the front nose of the ESP32 forward under the bifurcated front capture ears so the USB-C connector seats into the left wall port.
   * Press the rear of the board down firmly into the channel. The 4x vertical micro-crush ribs yield slightly to lock the board with positive friction against the dual rear thrust corner shoulders ($X = -17.6\text{mm}$).
   * Connect the DuPont jumpers to the corresponding SPI pins on the ESP32.
   * *(To remove for servicing, insert a fingernail or 2.5mm flathead screwdriver into the rear floor pry notch and gently lift).*
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
  * **Rear Clamp:** Print flat on build plate. Allow the spring steel build plate to cool completely to room temperature before removing to prevent deflection of the slim 1.6mm bottom bridge.
  * **Main Housing:** Print with rear backplate on build plate (cavity opening facing up).
  * **Desk Stand:** Print flat on bottom surface.
