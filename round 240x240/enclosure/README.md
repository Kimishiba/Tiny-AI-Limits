# 🖨️ GC9A01 1.28″ Round Display & ESP32-C3 SuperMini Cyberdeck Enclosure

3D printable enclosure files, slicer settings, hardware BOM, and assembly instructions for the **Tiny AI Limits Round Cyberdeck Desk Pod**.

---

## 📁 Included CAD & STL Files

All models are located in [`enclosure/`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/enclosure/):

| File | Description | Triangles | Print Time (est.) |
| :--- | :--- | :---: | :---: |
| **[`gc9a01_front_bezel.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/enclosure/gc9a01_front_bezel.stl)** | Front bezel plate with $32.6\text{mm}$ circular screen window & counterbored M2 screw pockets | 896 | ~25 mins |
| **[`gc9a01_main_housing.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/enclosure/gc9a01_main_housing.stl)** | Main housing body ($22\text{mm}$ depth) with internal cavity for ESP32 SuperMini & USB-C port cutout | 434 | ~50 mins |
| **[`gc9a01_desk_stand.stl`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/enclosure/gc9a01_desk_stand.stl)** | $20^\circ$ ergonomic weighted desk cradle with cable relief channel & rubber foot recesses | 274 | ~45 mins |
| **[`gc9a01_cyberdeck_enclosure.scad`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/enclosure/gc9a01_cyberdeck_enclosure.scad)** | Fully parametric OpenSCAD source file for custom modifications | — | — |
| **[`generate_stl.py`](file:///c:/Users/Alex/Documents/Antigravity/Tiny%20AI%20Limits/enclosure/generate_stl.py)** | Standalone Python mesh generator script used to build all STL files | — | — |

---

## 🔩 Hardware Bill of Materials (BOM)

| Item | Quantity | Purpose |
| :--- | :---: | :--- |
| **GC9A01 1.28″ Round IPS SPI Display** | 1 | Circular $240\times 240$ color screen module |
| **ESP32-C3 SuperMini** | 1 | Microcontroller board |
| **M2 $\times$ 12mm Socket Head Cap Screws** | 4 | Fastens front bezel to main housing (Brass or Black Oxide) |
| **M2 Brass Heat-Set Inserts** *(optional)* | 4 | Inserted into main housing posts (or direct self-tap) |
| **8mm $\times$ 1.5mm Adhesive Rubber Feet** | 4 | Fitted into stand base recesses for non-slip desk grip |
| **Right-Angle or Braided USB-C Cable** | 1 | Power delivery & firmware flashing |

---

## ⚙️ Slicer Print Settings (Cura / PrusaSlicer / Bambu Studio / Orca)

* **Material:** Matte Charcoal Black PLA, PETG, or ABS/ASA.
* **Layer Height:** `0.16mm` (Optimal balance of speed and chamfer resolution).
* **Perimeters / Walls:** `3` (for rigid screw threading).
* **Top/Bottom Solid Layers:** `4` top, `4` bottom.
* **Infill:** `20% Gyroid` or `Grid`.
* **Supports:** **NO SUPPORTS NEEDED** when oriented properly:
  * **Front Bezel:** Print face-down on build plate (flat side down).
  * **Main Housing:** Print with rear face on build plate (open front facing up).
  * **Desk Stand:** Print flat on base bottom (angled arms facing up).

---

## 🪛 Assembly Step-by-Step

1. **Solder Wiring Harness:** Connect the 7 SPI wires between the **GC9A01** and **ESP32-C3 SuperMini** as specified in `WIRING.md`:
   * `SCL` $\to$ `GPIO 4`
   * `SDA` $\to$ `GPIO 6`
   * `CS` $\to$ `GPIO 5`
   * `DC` $\to$ `GPIO 7`
   * `RST` $\to$ `GPIO 1`
   * `BLK` $\to$ `3V3` or `GPIO 0`
   * `VCC` $\to$ `3V3` / `GND` $\to$ `GND`
2. **Mount ESP32-C3:** Slide the SuperMini into the main housing cavity, aligning its USB-C port with the left side pass-through window.
3. **Seat the Display:** Place the GC9A01 display PCB into the front circular pocket of the main housing.
4. **Fasten Bezel:** Place the front bezel plate over the glass and secure with 4 $\times$ M2 screws through the corner holes into the main housing.
5. **Slot into Stand:** Slide the assembled pod into the $20^\circ$ desk cradle stand and route the USB-C cable through the rear channel.
