# 🖨️ GC9A01 1.28″ Round Display & ESP32-C3 SuperMini Cyberdeck Enclosure

3D printable enclosure files, slicer settings, hardware BOM, and assembly instructions for the **Tiny AI Limits Round Cyberdeck Desk Console** (reengineered directly from the concept 3D renders [`gc9a01_3d_enclosure_render.jpg`](../assets/gc9a01_3d_enclosure_render.jpg) and [`gc9a01_enclosure_rear_view.jpg`](../assets/gc9a01_enclosure_rear_view.jpg)).

> [!IMPORTANT]
> **v2 Thermal Aeration Vents & Anti-Movement Board Lock:**
> * **Convective Aeration Vents:** Dual-zone horizontal chimney slots on the rear backplate and exhaust slots on the top edge allow passive thermal airflow (cool air intake from bottom DuPont trench, exhaust through rear & top).
> * **Anti-Movement ESP32-C3 Retention:** Reinforced rear thrust bulkhead ($+X$), USB-C collar pull stop ($-X$), and side guide walls with snap-fit retention lips ($\pm Y, +Z$) prevent any board movement when inserting/unplugging the USB-C cable.
> * **Bottom Wire Drop Trench ($26\text{mm} \times 5\text{mm}$):** Positioned directly beneath the GC9A01 7-pin header, allowing DuPont connectors to plug in and drop directly into the desk stand channel with zero vertical pinch.
> * **Direct Screen Bolting:** 2 $\times$ M2 threaded pilot holes on the front bezel matching the GC9A01 bottom tab mounting holes ($19.26\text{mm}$ pitch).
> * **Sculpted Two-Tier Pedestal Stand:** $22^\circ$ ergonomic V-saddle cradle with tapered body, rear cable channel, and optional standalone accent base plate.

---

## 📁 Included CAD & STL Files

All models are located in [`round 240x240/enclosure/`](./):

| File | Description | Outer Dims ($W \times D \times H$) | Print Time (est.) |
| :--- | :--- | :---: | :---: |
| **[`gc9a01_front_bezel.stl`](./gc9a01_front_bezel.stl)** | Front bezel plate with $\varnothing 33.0\text{mm}$ conical anti-shadow window, clean $\varnothing 39.0\text{mm}$ screen pocket, 2 blind M2 pilot holes, and 4 M3 counterbored corner pockets | $54 \times 54 \times 7.0\text{mm}$ | ~25 mins |
| **[`gc9a01_mid_clamp.stl`](./gc9a01_mid_clamp.stl)** | Sandwich mid clamp diagonal X-brace with $7.0\text{mm}$ cross arms, forward compression pads, $\varnothing 14.0\text{mm}$ center component-relief hole, and open wiring quadrants | $54 \times 54 \times 2.6\text{mm}$ | ~10 mins |
| **[`gc9a01_main_housing.stl`](./gc9a01_main_housing.stl)** | Support-free $27.5\text{mm}$ deep main housing with rear/top aeration vents, rigid snap-fit ESP32-C3 lock cradle, bottom DuPont trench, and flared USB-C entry | $54 \times 54 \times 27.5\text{mm}$ | ~45 mins |
| **[`gc9a01_desk_stand.stl`](./gc9a01_desk_stand.stl)** | Sculpted two-tier pedestal cradle stand with $22^\circ$ V-saddle & slide-in pod channel | $64 \times 68 \times 29.0\text{mm}$ | ~45 mins |
| **[`gc9a01_stand_tier1_base.stl`](./gc9a01_stand_tier1_base.stl)** | Standalone Tier-1 bottom plate with 4 alignment pillars for wood PLA or dual-material printing | $64 \times 68 \times 8.5\text{mm}$ | ~20 mins |
| **[`gc9a01_stand_tier2_trunk.stl`](./gc9a01_stand_tier2_trunk.stl)** | Tier-2 cradle trunk with alignment sockets and $22^\circ$ V-saddle | $62 \times 66 \times 24.0\text{mm}$ | ~40 mins |
| **[`gc9a01_cyberdeck_enclosure.scad`](./gc9a01_cyberdeck_enclosure.scad)** | Fully parametric OpenSCAD source file | — | — |
| **[`generate_stl.py`](./generate_stl.py)** | Standalone Boolean CSG mesh generator script generating 100% watertight binary STLs | — | — |

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
* **Perimeters / Walls:** `3` walls (for solid screw hole threading).
* **Top/Bottom Solid Layers:** `4` top, `4` bottom.
* **Infill:** `20% Gyroid` or `Grid`.
* **Supports:** **NO SUPPORTS NEEDED** when oriented properly:
  * **Front Bezel:** Print face-down on build plate (flat side down).
  * **Mid Clamp:** Print flat on build plate (compression lip facing up).
  * **Main Housing:** Print with rear face on build plate (open front cavity facing up).
  * **Desk Stand:** Print flat on base bottom (angled V-saddle cradle facing up).

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
