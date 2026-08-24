# 🖨️ GC9A01 1.28″ Round Display & ESP32-C3 SuperMini Cyberdeck Enclosure

3D printable enclosure files, slicer settings, hardware BOM, and assembly instructions for the **Tiny AI Limits Round Cyberdeck Desk Pod**.

> [!IMPORTANT]
> **Redesigned for Full DuPont Cable Clearance & Upward Pin Headers:**
> * Pod depth increased to **$36.0\text{mm}$** with a **$44\text{mm} \times 44\text{mm}$** internal electronics cavity ($29.5\text{mm}$ usable depth).
> * Provides generous strain-relief clearance for standard $14\text{mm}$ DuPont female connector housings and upward-pointing ESP32-C3 pin headers without pinching or wire fatigue.
> * Modular, independent $20^\circ$ ergonomic weighted desk cradle stand.

---

## 📁 Included CAD & STL Files

All models are located in [`round 240x240/enclosure/`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/):

| File | Description | Outer Dims ($W \times H \times D$) | Print Time (est.) |
| :--- | :--- | :---: | :---: |
| **[`gc9a01_front_bezel.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_front_bezel.stl)** | Front bezel plate with $\varnothing 32.8\text{mm}$ active window & 4 M2 counterbored screw pockets | $54 \times 54 \times 4.5\text{mm}$ | ~25 mins |
| **[`gc9a01_main_housing.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_main_housing.stl)** | Main housing body ($36\text{mm}$ depth) with $44\times 44\text{mm}$ DuPont cavity, ESP32 mounting rails, and USB-C cutout | $54 \times 54 \times 36.0\text{mm}$ | ~55 mins |
| **[`gc9a01_desk_stand.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_desk_stand.stl)** | $20^\circ$ ergonomic modular desk cradle with $16\text{mm}$ rear cable channel & rubber foot recesses | $62 \times 68 \times 32.0\text{mm}$ | ~45 mins |
| **[`gc9a01_cyberdeck_enclosure.scad`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/gc9a01_cyberdeck_enclosure.scad)** | Fully parametric OpenSCAD source file for custom modifications | — | — |
| **[`generate_stl.py`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/round%20240x240/enclosure/generate_stl.py)** | Standalone Python mesh generator script used to build all binary STL files | — | — |

---

## 🔩 Hardware Bill of Materials (BOM)

| Item | Quantity | Purpose |
| :--- | :---: | :--- |
| **GC9A01 1.28″ Round IPS SPI Display** | 1 | Circular $240\times 240$ color screen module |
| **ESP32-C3 SuperMini** | 1 | Microcontroller board (pin headers soldered facing up) |
| **Female-to-Female DuPont Jumpers (10cm)** | 7 | Standard jumper wires for SPI wiring harness |
| **M2 $\times$ 14mm Socket Head Cap Screws** | 4 | Fastens front bezel to main housing (Brass or Black Oxide) |
| **M2 Brass Heat-Set Inserts** *(optional)* | 4 | Inserted into main housing posts (or direct self-tap) |
| **8mm $\times$ 1.5mm Adhesive Rubber Feet** | 4 | Fitted into stand base recesses for non-slip desk grip |
| **USB-C Cable (Braided or Right-Angle)** | 1 | Power delivery & firmware flashing |

---

## ⚙️ Slicer Print Settings (Cura / PrusaSlicer / Bambu Studio / OrcaSlicer)

* **Material:** Matte Charcoal Black PLA, PETG, or ABS/ASA.
* **Layer Height:** `0.16mm` or `0.20mm`.
* **Perimeters / Walls:** `3` walls (for solid screw hole threading).
* **Top/Bottom Solid Layers:** `4` top, `4` bottom.
* **Infill:** `20% Gyroid` or `Grid`.
* **Supports:** **NO SUPPORTS NEEDED** when oriented properly:
  * **Front Bezel:** Print face-down on build plate (flat side down).
  * **Main Housing:** Print with rear face on build plate (open front cavity facing up).
  * **Desk Stand:** Print flat on base bottom (angled cradle facing up).

---

## 🪛 Assembly Step-by-Step

1. **Connect DuPont Wiring Harness:** Connect the 7 SPI jumper wires between the **GC9A01** and **ESP32-C3 SuperMini**:
   * `SCL` $\to$ `GPIO 4`
   * `SDA` $\to$ `GPIO 6`
   * `CS` $\to$ `GPIO 5`
   * `DC` $\to$ `GPIO 7`
   * `RST` $\to$ `GPIO 1`
   * `BLK` $\to$ `3V3` or `GPIO 0`
   * `VCC` $\to$ `3V3` / `GND` $\to$ `GND`
2. **Mount ESP32-C3:** Slide the SuperMini into the bottom guide rails of the main housing with the upward pin headers facing forward into the cavity. Align the USB-C port with the left side window.
3. **Route Wire Bundle:** Loop the 7 DuPont wires gracefully around the $44\text{mm} \times 44\text{mm}$ circular perimeter cavity.
4. **Seat the Display:** Place the GC9A01 display PCB into the front circular pocket of the main housing.
5. **Fasten Bezel:** Place the front bezel plate over the display glass and secure with 4 $\times$ M2 screws through the corner holes into the main housing.
6. **Slot into Stand:** Slide the assembled pod into the modular $20^\circ$ desk cradle stand and route the USB-C cable through the rear channel.
