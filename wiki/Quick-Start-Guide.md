# 🚀 Quick Start Guide

Get your **Tiny AI Screen** assembled, flashed, and paired with your development environment in under 15 minutes!

---

## ⏱️ What You'll Need
* **ESP32-C3 SuperMini** microcontroller board.
* **GC9A01 1.28" Circular IPS Display** (SPI interface, 240×240 resolution).
* USB-C data cable.
* 7 jumper wires (or soldering tools for direct hookup).
* Python 3.10+ installed on your host machine.
* PlatformIO CLI or VS Code PlatformIO extension.
* Google Chrome or Microsoft Edge (for WebSerial setup).

---

## Step 1: Wire the Display

Connect your GC9A01 circular display to the ESP32-C3 SuperMini using this hardware SPI pin mapping:

```
  GC9A01 Display Pin               ESP32-C3 SuperMini Pin
 ┌───────────────────┐             ┌─────────────────────┐
 │ VCC               │ ──────────> │ 3V3                 │
 │ GND               │ ──────────> │ GND                 │
 │ SCL / SCLK        │ ──────────> │ GPIO 4              │
 │ SDA / MOSI        │ ──────────> │ GPIO 6              │
 │ DC                │ ──────────> │ GPIO 7              │
 │ CS                │ ──────────> │ GPIO 5              │
 │ RST / RES         │ ──────────> │ GPIO 1              │
 │ BLK               │ ──────────> │ GPIO 0 (or 3V3)     │
 └───────────────────┘             └─────────────────────┘
```

> [!TIP]
> Connecting **BLK** to **GPIO 0** enables software backlight brightness control and dimming. If your display module does not break out BLK, it is tied internally to 3.3V.

---

## Step 2: Build & Flash the Firmware

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Kimishiba/Tiny-AI-Limits.git
   cd Tiny-AI-Limits
   ```

2. **Plug in your ESP32-C3** via USB-C.

3. **Build and upload using PlatformIO:**
   ```bash
   # Build the firmware
   python -m platformio run

   # Flash the firmware over USB
   python -m platformio run --target upload
   ```

   *(Once uploaded, the screen will boot and display the initial pairing screen with a spinning circular radar animation).*

---

## Step 3: Launch the Companion Backend

The Python companion backend monitors your active AI agents, calculates rolling quotas, fetches weather, and advertises the local mDNS service.

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install requirements:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Launch the backend server:**
   ```bash
   python backend/app.py
   ```
   *(Or on macOS, simply double-click `TinyScreen.command`)*

The server will start at `http://localhost:5000` and begin advertising `_tinyscreen._tcp.local.` via mDNS.

---

## Step 4: WebSerial Provisioning & Gauge Pairing

1. Open **[http://localhost:5000/setup](http://localhost:5000/setup)** in **Google Chrome** or **Microsoft Edge**.
2. Click **"Connect Board (Direct Serial Setup)"**.
3. Select your ESP32-C3 serial port from the browser prompt (e.g. `usbmodem...` on macOS or `COMx` on Windows).
4. Enter your 2.4GHz Wi-Fi network SSID and Password.
5. Click **"Configure & Pair"**.

```
╔═════════════════════════════════════════════════════════════════╗
║                      PAIRING SUCCESSFUL!                        ║
║  Host Pair ID: e83f12a9-c091-49b8-a726-0e7841c5d98a             ║
║  Board Status: CONNECTED & PAIRED                               ║
║  Crown Status: Pulsing Emerald Green Arc                        ║
╚═════════════════════════════════════════════════════════════════╝
```

The device will immediately connect to your local Wi-Fi, locate your host machine via mDNS, sync its first telemetry payload, and enter active HUD mode!

---

## Step 5: Choose Your Gauges & Providers

On the **[Setup Page](http://localhost:5000/setup)**:
* **Left Gauge:** Choose between *Claude (Anthropic)*, *Google Antigravity*, *OpenRouter*, *DeepSeek*, *Groq*, *Mistral*, *Cursor*, *Copilot*, or *Gemini*.
* **Right Gauge:** Select your secondary AI provider.
* **Mode Selection:**
  * Toggle **Standard Quota Mode** (5-hour rolling reset window, percentage remaining).
  * Or toggle **Enterprise Mode** (live spend in `$`, 24-hour token volume, custom daily budget).
* **Save Preferences:** Settings apply instantly over the air.

---

## ⏭️ Next Steps
* Learn how to customize hardware and 3D print an enclosure: [[3D Printing & Enclosure Assembly|3D-Printing-&-Enclosure-Assembly]]
* Understand the multi-board collision prevention system: [[Pairing & Multi-Board Setup|Pairing-&-Multi-Board-Setup]]
* Check deep firmware internals: [[Firmware Architecture|Firmware-Architecture]]
