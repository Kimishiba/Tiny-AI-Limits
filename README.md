# ESP32 AI Companion & Tiny Screen (QBIT-Style Robot)

![Framework](https://img.shields.io/badge/Framework-Arduino_ESP32--C3-007acc?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-ESP32--C3_SuperMini-e67e22?style=flat-square)
![Display](https://img.shields.io/badge/Display-0.96%22_OLED_SSD1306_128x64-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

An open-source, Wi-Fi enabled desktop companion robot powered by the ultra-compact **ESP32-C3 SuperMini** microcontroller and a **0.96" 128x64 I2C OLED Display (SSD1306)**.

It combines an expressive, retro animated robot face with real-time hardware gauges for your AI coding token quotas (Claude Code & Antigravity CLI), agent plan approval notifications, and local weather forecasts.

<p align="center">
  <img src="./img/oled_companion_demo.gif" alt="ESP32 OLED Companion Animation Preview" width="512">
</p>

---

## ✨ Key Features

- **👀 Expressive Animated Face & Blinking Engine:**
  - 30 FPS non-blocking animation engine with natural eyelid physics and saccadic eye movements (looking center, left, right, and up).
  - Randomized blinking intervals with realistic double-blinks.
  - **Mood Reactions:**
    - *Normal Idle:* Friendly, calm blinking and glancing.
    - *Heavy Usage Today:* Droopy/sleepy eyes with animated falling sweat droplets once your real Claude token usage for the day crosses a calibrated threshold.
    - *Agent Attention Alert:* Flashes shocked wide eyes and a retro warning banner when an AI coding agent is waiting for user approval.
- **📊 Real-Time AI Quota Monitoring:** Monitors Claude Code token consumption, plus your *real* Antigravity quota — read directly from Antigravity's own local API, not a guess. If you're signed into multiple Antigravity accounts at once, pick which one to track from the companion app.
- **🌦️ Local Weather & Digital Clock:** Displays temperature, rain forecasts, and live synchronized time.
- **🔄 Auto-Cycling Companion Screens:** Cycles smoothly between Full Face (8s) $\rightarrow$ Split HUD (8s) $\rightarrow$ Detailed Quotas (8s) $\rightarrow$ Clock & Weather (8s).
- **🔌 USB Setup, No Recompiling:** Configure WiFi over USB from a browser page served by the companion app — enter your network name/password once, no editing files or reflashing.
- **📡 Automatic Zero-Config mDNS Backend Discovery:** The ESP32 finds the companion app on your network automatically by browsing for its advertised service (`_tinyscreen._tcp`)—no hardcoded hostnames or IP addresses, works for any user on any network.
- **📶 Robust Wi-Fi Connectivity:** Tuned RF TX power to prevent voltage brownouts on USB power, with PMF auto-negotiation compatibility for mixed WPA2/WPA3 enterprise routers.
- **🖥️ Web Simulator & Prototype:** Interactive browser visualizer (`/faces` or `/emulator`) to test all 10+ robot emotions and companion states.
- **🖨️ 3D-Printable Enclosure:** Parametric OpenSCAD and STL files included in `enclosure/` for desktop casing.

---

## 🛠️ Hardware & Pinout

### Required Components
- **Microcontroller:** [ESP32-C3 SuperMini Development Board](https://nl.aliexpress.com/item/1005006121404100.html) (RISC-V 160MHz, Wi-Fi & BLE, USB-C)
- **Display Module:** 0.96" or 1.3" I2C Monochrome OLED Display (128x64, SSD1306 / SH1106)
- **Wiring:** 4x Female-to-Female or Male-to-Male Dupont jumper wires

### Standard Wiring Table (Hardware I2C)

| OLED Pin (0.96" SSD1306) | ESP32-C3 SuperMini Pin | Description |
| :--- | :--- | :--- |
| **GND** | **GND** (Pin 2, Left Header) | Ground |
| **VCC** | **3V3** (Pin 3, Left Header) | 3.3V Power |
| **SCL / SCK** | **GPIO 9** (Pin 13, Right Header) | I2C Clock (400 kHz) |
| **SDA** | **GPIO 8** (Pin 14, Right Header) | I2C Data |

*(For alternative 4-in-a-row pinouts or breadboard layouts, see [WIRING.md](WIRING.md)).*

---

## 🚀 Getting Started

Nothing is hardcoded per-user at compile time anymore — the same firmware
works for anyone. WiFi is provisioned at runtime over USB, and the board
finds the companion app on the network automatically.

> **Prefer not to build from source?** Tagged versions publish two separate
> [GitHub Releases](../../releases) — `firmware-vX.Y.Z` (the `firmware.bin`
> to flash) and `app-vX.Y.Z` (companion app executables for Windows/macOS/Linux,
> no Python install needed). Grab those and skip straight to step 3 below.

### 1. Build & Flash Firmware
Using **PlatformIO** (only needed once per board — skip this if you received
an already-flashed device or downloaded a `firmware-vX.Y.Z` release):

```bash
# Build firmware
python3 -m platformio run

# Upload to ESP32 over USB-C
python3 -m platformio run --target upload
```

### 2. Run the PC Companion Backend
The companion service monitors your local AI agent transcripts and weather
data, reads your real Antigravity quota, hosts the REST endpoint the board
polls, and advertises itself on the network so the board can find it.

If you downloaded an `app-vX.Y.Z` release, just run that executable directly.
Otherwise, from source:

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Launch backend (or double-click TinyScreen.command on macOS)
python3 backend/app.py
```

### 3. Set Up WiFi
With the board plugged into this computer via USB-C, open
**[http://localhost:5000/setup](http://localhost:5000/setup)** in
**Google Chrome or Microsoft Edge** (required — Web Serial isn't supported
in Safari or Firefox), or click **"🔌 Set Up New Device (WiFi)"** in the
companion app. Click "Connect & Set Up WiFi," pick the board's serial port
("USB JTAG/serial debug unit"), and enter your network name and password.

The board saves the credentials, connects, and finds this companion app on
its own — no further configuration needed. If the board is ever moved to a
different network, or the router password changes, it automatically falls
back into setup mode so you can reprovision the same way.

---

## 🎨 Interactive Browser Prototype

You can test and preview all face animations and companion states without flashing hardware:

1. Start the backend: `python3 backend/app.py`
2. Open in your browser:
   * **Robot Face Visualizer:** `http://localhost:5000/faces`
   * **Full Display Emulator:** `http://localhost:5000/emulator`

---

## 📂 Project Structure

```
├── backend/                  # Python Flask companion service & token trackers
│   └── app.py
├── enclosure/                # 3D printable case models & assembly guide
│   ├── top_case.stl
│   ├── bottom_base.stl
│   └── desk_console_oled13_esp32c3.scad
├── emulator/                 # Interactive browser visualizers & emulators
│   ├── qbit_faces_prototype.html
│   ├── setup.html            # USB WiFi provisioning page (served at /setup)
│   ├── vendor/               # Self-bundled JS deps, no runtime CDN calls
│   └── index.html
├── tools/                    # Asset generators (GIF animator, format converters)
│   └── generate_preview_gif.py
├── src/                      # ESP32-C3 Arduino firmware
│   └── main.cpp
├── platformio.ini            # PlatformIO board & library configuration
├── WIRING.md                 # Detailed pinout & wiring schematics
└── README.md
```

---

## 📄 License
MIT License. Feel free to use, modify, and build your own desktop companion!
