# ESP32-AI-Companion

![Framework](https://img.shields.io/badge/Framework-Arduino_ESP32--C3-007acc?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-ESP32--C3_SuperMini-e67e22?style=flat-square)
![Display](https://img.shields.io/badge/Display-ILI9341_240x320_Touch-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

An interactive, Wi-Fi enabled desktop companion monitor powered by a cheap, compact **ESP32-C3 SuperMini** micro-controller and a 2.8-inch 240x320 ILI9341 SPI Display with Touch Panel. It acts as a dedicated hardware gauge for your AI token limits and quotas.

<p align="center">
  <img src="img/ai_limits.jpg" width="45%" alt="Neo-Brutalist AI Limits UI">
  &nbsp;
  <img src="img/weather.jpg" width="45%" alt="Neo-Brutalist Weather UI">
</p>

## Hardware & Components

- **Microcontroller Board:** [Cheap ESP32-C3 SuperMini Development Board](https://nl.aliexpress.com/item/1005006121404100.html) (RISC-V Single-Core 160MHz, Wi-Fi & BLE, USB-C)
- **Display Module:** [2.8" 240x320 SPI TFT LCD Display Module with Touch Panel (ILI9341)](https://nl.aliexpress.com/item/1005004557916570.html)
- **Power Supply / Cable:** USB-C 5V Cable
- **Jumper Wires:** Dupont / Breadboard Jumper Wires for SPI connection



## Key Features
- **Live Limits Monitoring:** Fetches Claude Code token consumption and Antigravity quota limits directly from your computer.
- **Weather Forecast:** Auto-detects your location and displays the current temperature and hours until the next rain.
- **Smooth UI Animations:** Clean presentation designed specifically for circular screen geometry.
- **Wi-Fi Connectivity:** Fully wireless data sync over local Wi-Fi via a lightweight local Python backend.

## Getting Started

### 1. Wiring the Display
Connect your ST77916 1.5" Round Display to the ESP32 following the detailed pinout guide in [WIRING.md](WIRING.md).

### 2. ESP32 Firmware
1. Open this repository in VS Code with the PlatformIO extension.
2. Edit the Wi-Fi credentials (`ssid`, `password`) and your PC's IP address (`backend_url`) in `src/main.cpp`.
3. Build and upload the firmware to your ESP32.

### 3. PC Backend
The ESP32 pulls data from a lightweight Python Flask server running on your PC, which automatically scans local log files for token usage and asks the CLI for quota limits.
```bash
cd backend
pip install flask
python app.py
```

