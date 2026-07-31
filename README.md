# ESP32-AI-Companion

![Framework](https://img.shields.io/badge/Framework-Arduino_ESP32-007acc?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-ESP32--WROOM-e67e22?style=flat-square)
![Display](https://img.shields.io/badge/Display-ILI9341_320x240-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

An interactive, Wi-Fi enabled desktop companion monitor powered by an ESP32 and an ILI9341 320x240 SPI display with touch support. It acts as a dedicated hardware gauge for your AI token limits and quotas.

## Key Features
- **Live Limits Monitoring:** Fetches Claude Code token consumption and Antigravity quota limits directly from your computer.
- **Wi-Fi Connectivity:** Fully wireless (power only), pulls data via a local Python backend.
- **Touch Support:** Tap the ILI9341 screen to instantly force an update of the limits.
- **Sleek UI:** Smoothly rendered progress bars and text using the highly optimized `TFT_eSPI` library.

## Getting Started

### 1. Wiring the Display
Connect your ILI9341 to the ESP32 following the [WIRING.md](WIRING.md) guide.

### 2. ESP32 Firmware
1. Open this repository in VS Code with the PlatformIO extension.
2. Edit the Wi-Fi credentials and Desktop IP address in `src/main.cpp`.
3. Upload the firmware to your ESP32.

### 3. PC Backend
The ESP32 pulls data from a lightweight Python Flask server running on your PC, which automatically scans local log files for token usage and asks the CLI for quota limits.
```bash
cd backend
pip install flask
python app.py
```
