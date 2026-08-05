# ESP32 AI Companion & Tiny Screen

![Framework](https://img.shields.io/badge/Framework-Arduino_ESP32--C3-007acc?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-ESP32--C3_SuperMini-e67e22?style=flat-square)
![Display](https://img.shields.io/badge/Display-ILI9341_240x320_Touch-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

An interactive, Wi-Fi enabled desktop companion monitor powered by a compact **ESP32-C3 SuperMini** microcontroller and a 2.8-inch 240x320 ILI9341 SPI Display with Touch Panel. It acts as a dedicated hardware gauge for your AI token limits, pending agent approvals, and local weather forecasts.

<p align="center">
  <img src="img/ai_limits.jpg" width="45%" alt="Neo-Brutalist AI Limits UI">
  &nbsp;
  <img src="img/weather.jpg" width="45%" alt="Neo-Brutalist Weather UI">
</p>

---

## Key Features

- **Live AI Quota & Limits Monitoring:** Displays real-time Claude Code token consumption and Antigravity CLI quota limits.
- **Agent Attention Alert:** Flashes a retro amber warning screen when an AI coding agent is waiting for user plan approval or input.
- **Weather & Forecast:** Auto-detects location via IP or allows manual location configuration, displaying current temperature and hours until rain.
- **Direct GitHub HTTPS OTA Updates:** ESP32 automatically queries GitHub Releases on boot. If a new version tag is pushed, it flashes wirelessly over Wi-Fi!
- **Cross-Platform PC Companion App:** Desktop utility (macOS, Windows, Linux) to configure weather locations, inspect backend data, and check for ESP32 firmware updates.

---

## Hardware & Components

- **Microcontroller:** [ESP32-C3 SuperMini Development Board](https://nl.aliexpress.com/item/1005006121404100.html) (RISC-V 160MHz, Wi-Fi & BLE, USB-C)
- **Display Module:** [2.8" 240x320 SPI TFT LCD Display Module with Touch Panel (ILI9341)](https://nl.aliexpress.com/item/1005004557916570.html)
- **Wiring:** Dupont jumper wires (Follow pinouts in [WIRING.md](WIRING.md))

---

## Desktop Companion App (macOS & Windows)

The companion application runs locally on your computer to serve data to the ESP32 screen.

### Pre-built Executables
Download the standalone executable for your operating system from the **[GitHub Releases Page](../../releases)**:
- **Windows:** `TinyAIScreenCompanion-Windows.exe`
- **macOS:** `TinyAIScreenCompanion-macOS`
- **Linux:** `TinyAIScreenCompanion-Linux`

### Running from Source
```bash
cd backend
pip install flask requests
python app.py
```

### Companion App Features
1. **Location Settings:** Toggle between IP auto-detection or type a custom city name (e.g. `"Milan"`, `"Tokyo"`).
2. **Firmware Update Checker:** One-click check against GitHub API to see if a newer ESP32 release is available.
3. **Local Server:** Hosts the REST endpoint (`http://<YOUR_IP>:5000/data`) polled by the ESP32 over Wi-Fi.

---

## Firmware Build & GitHub Actions CI/CD

This repository uses **GitHub Actions** for automated build and release pipelines:

- **On Code Push / PR:** Automatically verifies that PlatformIO builds the ESP32 firmware cleanly and PyInstaller compiles the companion executables.
- **On Version Tag Push (`git tag v0.1 && git push origin v0.1`):**
  1. Compiles `firmware.bin` for ESP32.
  2. Compiles standalone Companion App executables for macOS, Windows, and Linux.
  3. Automatically creates a GitHub Release and attaches all binaries.

---

## Getting Started

### 1. Wiring the Display
Follow the detailed pinout guide in [WIRING.md](WIRING.md).

### 2. Initial ESP32 Setup (USB)
1. Open this project in VS Code with **PlatformIO**.
2. Configure your Wi-Fi credentials (`ssid`, `password`) and GitHub details (`github_user`, `github_repo`) in [`src/main.cpp`](src/main.cpp).
3. Connect your ESP32-C3 via USB and click **Upload**.

### 3. Future Updates (Over-The-Air)
You never need to plug the ESP32 into USB again for updates! When you are ready for a new version:
```bash
git tag v0.1
git push origin v0.1
```
GitHub Actions will build the release, and your ESP32 screen will update itself over Wi-Fi on its next boot!
