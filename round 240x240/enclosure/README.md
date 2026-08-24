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
| :--- | :--- | :---: | :---: |
| **[`gc9a01_front_bezel.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_front_bezel.stl)** | Front bezel plate with $\varnothing 32.6\text{mm}$ active window, 2 M2 screen bolting holes, and 4 M2 counterbored corner pockets | $54 \times 54 \times 4.5\text{mm}$ | ~25 mins |
| **[`gc9a01_main_housing.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_main_housing.stl)** | Slim $26\text{mm}$ main housing with bottom DuPont wire trench, pin-locking standoffs, and USB-C cutout | $54 \times 54 \times 26.0\text{mm}$ | ~45 mins |
| **[`gc9a01_desk_stand.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_desk_stand.stl)** | Sculpted two-tier pedestal cradle stand with $22^\circ$ V-saddle & $20\text{mm}$ cable channel | $64 \times 68 \times 34.0\text{mm}$ | ~45 mins |
| **[`gc9a01_stand_accent_base.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_stand_accent_base.stl)** | Optional standalone Tier-1 bottom plate for wood PLA or dual-material printing | $64 \times 68 \times 6.0\text{mm}$ | ~20 mins |
| **[`gc9a01_cyberdeck_enclosure.scad`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_cyberdeck_enclosure.scad)** | Fully parametric OpenSCAD source file | — | — |
| **[`generate_stl.py`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/generate_stl.py)** | Standalone Boolean CSG mesh generator script generating 100% watertight binary STLs | — | — |

---

## 🔩 Hardware Bill of Materials (BOM)

| Item | Quantity | Purpose |
| :--- | :---: | :--- |
| **GC9A01 1.28″ Round IPS SPI Display** | 1 | Circular $240\times 240$ color screen module |
| **ESP32-C3 SuperMini** | 1 | Microcontroller board (pin headers soldered facing up) |
| **Female-to-Female DuPont Jumpers (10cm)** | 7 | Standard jumper wires for SPI wiring harness |
| **M2 $\times$ 4mm or 6mm Pan/Socket Screws** | 2 | Fastens GC9A01 bottom tab directly to the front bezel |
| **M2 $\times$ 12mm Socket Head Cap Screws** | 4 | Fastens front bezel to main housing (Brass or Black Oxide) |
| **M2 Brass Heat-Set Inserts** *(optional)* | 4–6 | Inserted into bezel & housing posts (or direct self-tap) |
| **8mm $\times$ 1.5mm Adhesive Rubber Feet** | 4 | Fitted into stand base recesses for non-slip desk grip |
| **USB-C Cable (Braided or Right-Angle)** | 1 | Power delivery & firmware flashing |

---

## ⚙️ Slicer Print Settings (Cura / PrusaSlicer / Bambu Studio / OrcaSlicer)

* **Material:** Matte Charcoal Black PLA / PETG for the body, Wood PLA or Walnut Brown for the base.
* **Layer Height:** `0.16mm` or `0.20mm`.
* **Perimeters / Walls:** `3` walls (for solid screw hole threading).
* **Top/Bottom Solid Layers:** `4` top, `4` bottom.
* **Infill:** `20% Gyroid` or `Grid`.
* **Supports:** **NO SUPPORTS NEEDED** when oriented properly:
  * **Front Bezel:** Print face-down on build plate (flat side down).
  * **Main Housing:** Print with rear face on build plate (open front cavity facing up).
  * **Desk Stand:** Print flat on base bottom (angled V-saddle cradle facing up).

---

## 🪛 Assembly Step-by-Step

1. **Bolt Display to Front Bezel:** Seat the GC9A01 display into the rear of the front bezel and secure it with 2 $\times$ M2 screws through the bottom tab holes ($X = \pm 9.63\text{mm}, Y = -18.91\text{mm}$).
2. **Mount ESP32-C3:** Drop the ESP32-C3 SuperMini onto the standoff rails with upward-pointing pin headers. The solder pin tails will lock into the 16 registration holes, aligning the USB-C port with the left-side window.
3. **Connect DuPont Wiring Harness:** Connect the 7 SPI jumper wires between the **GC9A01** and **ESP32-C3 SuperMini**:
   * `SCL` $\to$ `GPIO 4`
   * `SDA` $\to$ `GPIO 6`
   * `CS` $\to$ `GPIO 5`
   * `DC` $\to$ `GPIO 7`
   * `RST` $\to$ `GPIO 1`
   * `BLK` $\to$ `3V3` or `GPIO 0`
   * `VCC` $\to$ `3V3` / `GND` $\to$ `GND`
4. **Fasten Bezel to Housing:** Place the assembled front bezel over the main housing and fasten with 4 $\times$ M2 $\times$ 12mm corner screws.
5. **Slot into Stand:** Slide the assembled pod into the sculpted $22^\circ$ V-saddle desk cradle and route the USB-C cable through the rear channel.
