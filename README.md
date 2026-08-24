# ⚡ Tiny AI Limits & Desktop Companion (ESP32-C3)

![Framework](https://img.shields.io/badge/Framework-Arduino_ESP32--C3-007acc?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-ESP32--C3_SuperMini-e67e22?style=flat-square)
![Displays](https://img.shields.io/badge/Displays-GC9A01_Round_%7C_SSD1306_OLED-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

An open-source, Wi-Fi enabled desktop telemetry companion powered by the ultra-compact **ESP32-C3 SuperMini** microcontroller.

It brings your AI developer environment to life with physical desktop hardware — monitoring real-time token quotas for **Claude Code** and **Google Antigravity CLI**, alerting you when AI agents require plan approvals, and serving as an expressive animated desk companion and synchronized clock.

---

## 🛠️ Two Hardware Device Options You Can Build

You can build **Tiny AI Limits** in either of two distinct physical form factors depending on your preferred display technology and aesthetic:

---

### Option 1: GC9A01 1.28" Circular IPS Cyberdeck Edition

<p align="center">
  <img src="./round 240x240/assets/gc9a01_3d_enclosure_render.jpg" alt="GC9A01 Circular Cyberdeck 3D Render" width="460">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="./round 240x240/assets/gc9a01_round_display_demo.gif" alt="GC9A01 Circular Display UI Animation Demo" width="460">
</p>

An industrial sci-fi desktop pod featuring a vibrant **1.28" Circular 240×240 IPS Color Display (GC9A01 SPI)** resting at an ergonomic $18^\circ$ backward tilt on a two-tier modular pedestal.

#### ✨ Features:
* **2×2 Split-Flap Flip Clock:** Mechanical split-card matrix animating hour and minute transitions.
* **Dual Circular Radial Telemetry Arcs:** Continuous $0\% \to 100\%$ gauges tracking Claude Code (Electric Cyan, left arc) and Antigravity CLI (Safety Orange, right arc).
* **Curved Inside Telemetry Labels:** Dynamic curved text (`CLD 68%`, `AGY 42%`) positioned inside the active gauge sweeps.
* **Top Crown Rain Forecast:** Live countdown and rain status (`Rain in 3h`, `Rain Now`, `Clear`).
* **Stacked Bottom Sub-HUD:** Day & Date, live temperature with weather condition icons, and real-time **Agent Attention Alert** banner overrides.
* **Enclosure Architecture:** Support-free 3D-printable pod with $4\times$ counterbored brass M3 socket head cap screws, raised decorative ring, and a two-tier pedestal stand (Dark Walnut wood base plate with 4 alignment pillars + matte dark truncated trapezoidal cradle trunk).

---

### Option 2: SSD1306 Monochrome OLED Robot Companion Edition

<p align="center">
  <img src="./img/ssd1306_real_robot_render.jpg" alt="SSD1306 OLED Companion 3D Render" width="460">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="./img/oled_companion_demo.gif" alt="ESP32 OLED Companion Animation Preview" width="460">
</p>

A retro-futuristic desktop robot companion utilizing a crisp **0.96" or 1.3" Monochrome I2C OLED Display (128×64, SSD1306 / SH1106)**.

#### ✨ Features:
* **👀 Expressive Animated Eyes & Eyelid Physics:** 30 FPS non-blocking animation engine with natural saccadic eye movement and randomized double-blinking.
* **🎭 Context-Aware Mood Reactions:**
  * *Normal Idle:* Calm, curious glances around your workspace.
  * *Heavy Usage Today:* Droopy, tired eyes with animated falling sweat droplets as your daily Claude token consumption reaches high thresholds.
  * *Agent Attention Alert:* Wide-eyed shock animation and retro warning banners when an AI coding agent is waiting for user approval.
* **🔄 Auto-Cycling Companion Screens:** Cycles smoothly between Full Robot Face $\to$ Split HUD $\to$ Quota Telemetry Bars $\to$ Clock & Weather.
* **Enclosure Options:** 
  * *Cyberdeck Pod:* Matching chamfered pod with rectangular bezel aperture, brass M3 hardware, and two-tier pedestal stand.
  * *Desk Console / Macropad:* Angled desk console incorporating 3 mechanical Cherry MX keyboard switches and an EC11 rotary encoder knob for quick system control and macro triggering.

---

## 📊 Feature Comparison

| Feature | GC9A01 Round Edition | SSD1306 OLED Edition |
| :--- | :--- | :--- |
| **Display Type** | 1.28" Round Color IPS (240×240) | 0.96" / 1.3" Monochrome OLED (128×64) |
| **Interface** | High-Speed SPI | Hardware I2C (400 kHz) |
| **Primary Theme** | Cyberdeck Split-Flap Clock & Dual Radial HUD | Expressive Animated Robot Companion |
| **Claude & Antigravity Gauges** | Dual Continuous $180^\circ$ Radial Arcs | Horizontal Telemetry Progress Bars |
| **Agent Approval Warning** | High-Contrast Yellow/Orange Sub-HUD Alert | Shocked Wide-Eye Animation & Flashing Banner |
| **Weather & Rain Forecast** | Top Crown Indicator + Temperature Sub-HUD | Dedicated Cycling Weather Screen |
| **Desk Stand** | Modular Two-Tier Pedestal (Walnut + Cradle) | Two-Tier Pedestal OR Angled Macropad Case |

---

## 🔌 Hardware & Wiring Schematics

### 1. ESP32-C3 SuperMini Pinout (Shared Microcontroller)
The ultra-compact ESP32-C3 SuperMini board powers both versions via USB-C (3.3V logic).

---

### 2. GC9A01 Circular Display Wiring (Hardware SPI)

| GC9A01 Display Pin | ESP32-C3 SuperMini Pin | Description |
| :--- | :--- | :--- |
| **VCC** | **3V3** | 3.3V Power Rail |
| **GND** | **GND** | Ground |
| **SCL / SCLK** | **GPIO 4** | SPI Clock |
| **SDA / MOSI** | **GPIO 6** | SPI MOSI (Data) |
| **DC** | **GPIO 7** | Data / Command Control |
| **CS** | **GPIO 10** | Chip Select |
| **RST / RES** | **GPIO 8** | Hardware Reset |
| **BLK** | **GPIO 5** (or 3V3) | Backlight PWM / Enable |

---

### 3. SSD1306 OLED Display Wiring (Hardware I2C)

| SSD1306 OLED Pin | ESP32-C3 SuperMini Pin | Description |
| :--- | :--- | :--- |
| **VCC** | **3V3** (or 5V) | 3.3V Power Rail |
| **GND** | **GND** | Ground |
| **SCL / SCK** | **GPIO 9** | Hardware I2C Clock (400 kHz) |
| **SDA** | **GPIO 8** | Hardware I2C Data |

*(For optional Macropad switches and rotary encoder pinout, see [`enclosure/ASSEMBLY_AND_WIRING.md`](enclosure/ASSEMBLY_AND_WIRING.md) and [`WIRING.md`](WIRING.md)).*

---

## 🖨️ 3D Printing & Enclosure Assembly

All enclosure CAD models are **100% support-free FDM 3D printable** and available in both parametric OpenSCAD sources and verified watertight STLs:

### Models Included:
* **Round GC9A01 Enclosure (`round 240x240/enclosure/`):**
  * `gc9a01_front_bezel.stl` — Front bezel display carrier with anti-shadow conical bevel and M3 counterbores.
  * `gc9a01_main_housing.stl` — Enclosure bucket with lowered USB-C port and M3 corner pilot holes.
  * `gc9a01_stand_tier1_base.stl` — Tier 1 base plate with 4 alignment pillars and rubber feet recesses (ideal for wood PLA or dark walnut).
  * `gc9a01_stand_tier2_trunk.stl` — Tier 2 sculpted monolithic pedestal trunk with 4 slide sockets and $18^\circ$ V-saddle cradle notch.
  * `gc9a01_desk_stand.stl` — Unified single-piece monolithic desk stand.
* **OLED Console / Macropad (`enclosure/`):**
  * `top_case.stl` & `bottom_base.stl` — Angled desktop console for 1.3" OLED, 3 Cherry MX switches, and EC11 rotary knob.

---

## 🚀 Getting Started

### 1. Build & Flash Firmware
Using **PlatformIO**:

```bash
# Build firmware
python -m platformio run

# Upload to ESP32 over USB-C
python -m platformio run --target upload
```

### 2. Launch the PC Companion Backend
The companion service monitors your local AI agent transcripts, queries live Antigravity token limits, fetches local weather data, and advertises itself via zero-config mDNS:

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Launch backend (or double-click TinyScreen.command on macOS)
python backend/app.py
```

### 3. USB WiFi Provisioning (No Recompiling)
With the device plugged in via USB-C, open **[`http://localhost:5000/setup`](http://localhost:5000/setup)** in Google Chrome or Microsoft Edge (Web Serial API). Click **"Connect & Set Up WiFi"**, select the board's serial port, and enter your Wi-Fi credentials. The device saves them to flash and automatically locates the companion server.

---

## 🎨 Interactive Browser Prototype & Visualizer

Preview and interact with all screens, animations, and telemetry states in real time:

* **Robot Face Visualizer:** `http://localhost:5000/faces`
* **Full Display Emulator (Round & Rectangular):** `http://localhost:5000/emulator`

---

## 📂 Repository Structure

```
├── backend/                  # Python Flask companion service & token trackers
│   ├── app.py
│   └── claude_statusline.py
├── round 240x240/            # GC9A01 1.28" Round IPS Edition
│   ├── enclosure/            # Parametric OpenSCAD & watertight STLs
│   │   ├── generate_stl.py
│   │   ├── gc9a01_cyberdeck_enclosure.scad
│   │   ├── gc9a01_front_bezel.stl
│   │   ├── gc9a01_main_housing.stl
│   │   ├── gc9a01_stand_tier1_base.stl
│   │   ├── gc9a01_stand_tier2_trunk.stl
│   │   └── gc9a01_desk_stand.stl
│   └── assets/               # 3D concept renders, animated demo GIF & mascot frames
│       ├── gc9a01_3d_enclosure_render.jpg
│       └── gc9a01_round_display_demo.gif
├── enclosure/                # SSD1306 Desk Console & Macropad Enclosure
│   ├── desk_console_oled13_esp32c3.scad
│   ├── top_case.stl
│   └── bottom_base.stl
├── emulator/                 # Interactive browser visualizers & emulators
│   ├── index.html            # Canvas emulator for Round & Rectangular HUDs
│   ├── qbit_faces_prototype.html
│   └── setup.html            # WebSerial USB Wi-Fi provisioning
├── img/                      # 3D product renders & animation demos
│   ├── ssd1306_real_robot_render.jpg
│   ├── oled_companion_demo.gif
│   └── ili9341_cyberdeck_render.jpg
├── src/                      # ESP32-C3 Arduino C++ firmware
│   └── main.cpp
├── platformio.ini            # PlatformIO build configuration
├── WIRING.md                 # Detailed pinout & wiring documentation
└── README.md
```

---

## 📄 License
MIT License. Feel free to build, customize, and share your own desktop AI companion!
