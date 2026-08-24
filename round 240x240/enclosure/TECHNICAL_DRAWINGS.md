# 📐 GC9A01 Cyberdeck Enclosure - Mechanical Engineering Technical Drawings

Comprehensive mechanical engineering drawing sheets and dimensional specifications for CAD modeling (Fusion 360, FreeCAD, SolidWorks, Blender, Onshape, Rhino).

---

## 📑 Drawing Sheets Overview

### 1. Sheet 1: Front Bezel Ring Plate (`GC9A01-BEZEL-01`)
![Sheet 1: Front Bezel Plate](technical_drawings_front_bezel.png)

* **Outer Profile:** $54.00\text{mm} \times 54.00\text{mm}$ with $6.00\text{mm} \times 45^\circ$ corner chamfers.
* **Plate Thickness:** $4.50\text{mm}$ base $+ 1.50\text{mm}$ raised decorative trim ring ($\varnothing 44.00\text{mm}$) = $6.00\text{mm}$ Overall Length (OAL).
* **Active Screen Viewport:** $\varnothing 32.60\text{mm}$ through-hole with $45^\circ$ inner bevel ring (aperture dia $\varnothing 30.60\text{mm}$).
* **Glass Lens Retention Pocket:** $\varnothing 36.00\text{mm} \times 1.60\text{mm}$ deep (from rear).
* **PCB Retention Pocket:** $\varnothing 38.60\text{mm}$ circular top $+ 23.60\text{mm}$ wide bottom tab down to $Y = -26.80\text{mm}$ ($1.80\text{mm}$ deep from rear).
* **Screen Bolting Pilot Holes:** $2 \times \varnothing 1.75\text{mm}$ blind pilot holes at $X = \pm 9.63\text{mm}, Y = -18.91\text{mm}$ ($19.26\text{mm}$ pitch), depth $3.40\text{mm}$ from rear (leaves $1.20\text{mm}$ solid front face).
* **Corner Enclosure Screws:** $4 \times$ M2 through-holes ($\varnothing 2.60\text{mm}$) with counterbore pockets ($\varnothing 4.80\text{mm} \times 2.20\text{mm}$ deep) at $X = \pm 21.00\text{mm}, Y = \pm 21.00\text{mm}$ ($42.00\text{mm}$ Bolt Circle).

---

### 2. Sheet 2: Main Housing Pod 26mm (`GC9A01-BODY-26`)
![Sheet 2: Main Housing Pod](technical_drawings_main_housing.png)

* **Outer Profile:** $54.00\text{mm} \times 54.00\text{mm} \times 26.00\text{mm}$ total depth with $6.00\text{mm} \times 45^\circ$ corner chamfers.
* **Electronics & Wire Cavity:** $44.00\text{mm} \times 44.00\text{mm} \times 19.50\text{mm}$ usable interior depth.
* **Rear Floor Thickness:** $2.50\text{mm}$.
* **Bottom DuPont Wire Drop Trench:** $20.00\text{mm} \text{ wide} \times 12.00\text{mm} \text{ deep}$ cutout directly under the GC9A01 7-pin SPI header ($Y = -24.74\text{mm}$) connecting straight to the desk stand.
* **USB-C Side Window:** $13.00\text{mm} \text{ wide} \times 8.00\text{mm} \text{ tall}$ through left wall at $X = -27.00\text{mm}$.
* **ESP32-C3 SuperMini Mounting:**
  * Standoff rails at $Y = \pm 7.62\text{mm}$ ($0.6''$ pin row spacing), height $2.50\text{mm}$.
  * $16 \times \varnothing 1.50\text{mm}$ blind pin-registration holes ($2.00\text{mm}$ deep) at $2.54\text{mm}$ pitch along $X$.
  * Rear mechanical thrust stop block ($2.50\text{mm}$ thick) at $+X$ end.
* **Corner Enclosure Pilot Holes:** $4 \times \varnothing 2.00\text{mm} \times 12.00\text{mm}$ deep at $X = \pm 21.00\text{mm}, Y = \pm 21.00\text{mm}$.

---

### 3. Sheet 3: Sculpted Two-Tier Desk Stand (`GC9A01-STAND-01`)
![Sheet 3: Sculpted Desk Stand](technical_drawings_desk_stand.png)

* **Tier 1 Base Plate:** $64.00\text{mm} \text{ wide} \times 68.00\text{mm} \text{ deep} \times 6.00\text{mm} \text{ height}$ with $R = 6.00\text{mm}$ rounded corners.
* **Tier 2 Pyramidal Trunk:** $28.00\text{mm}$ height with $12^\circ$ draft angle tapered body ($34.00\text{mm}$ total stand height).
* **Cradle V-Saddle Pocket:** $54.80\text{mm} \text{ wide} \times 35.00\text{mm} \text{ deep}$ octagonal recess at an ergonomic **$22.0^\circ$ tilt angle**.
* **Pass-Through Cable Relief Channel:** $20.00\text{mm} \text{ wide} \times 14.00\text{mm} \text{ tall}$ continuous channel running front-to-back.
* **Anti-Slip Rubber Foot Recesses:** $4 \times \varnothing 8.20\text{mm} \times 1.40\text{mm}$ deep on underside ($X = \pm 22.00\text{mm}, Y = \pm 24.00\text{mm}$).

---

### 4. Sheet 4: Exploded System Assembly & Hardware BOM
![Sheet 4: Exploded Assembly & BOM](technical_drawings_full_assembly.png)

* **Stackup Sequence:**
  1. Front Bezel Plate ($4.50\text{mm}$)
  2. GC9A01 1.28″ Round Display Module ($3.10\text{mm}$) — fastened to bezel with $2 \times$ M2 screws
  3. Main Housing Pod ($26.00\text{mm}$) with ESP32-C3 SuperMini inside
  4. Sculpted Two-Tier Desk Stand ($34.00\text{mm}$)
* **Hardware BOM:**
  * $2 \times \text{M2} \times 4\text{mm} / 6\text{mm}$ pan/socket screws (screen to bezel)
  * $4 \times \text{M2} \times 12\text{mm}$ socket head cap screws (bezel to housing)
  * $4 \times \varnothing 8.0\text{mm}$ adhesive rubber feet
  * $7 \times 10\text{cm}$ female-to-female DuPont jumper wires
