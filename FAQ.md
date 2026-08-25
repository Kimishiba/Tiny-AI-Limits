# Frequently Asked Questions (FAQ)

## What is Tiny AI Limits & Desktop Companion?

It is an open-source, Wi-Fi enabled desktop telemetry companion powered by the ultra-compact ESP32-C3 SuperMini microcontroller. It brings your AI developer environment to life with physical desktop hardware — monitoring real-time token quotas for Claude Code and Google Antigravity CLI, alerting you when AI agents require plan approvals, and serving as an expressive animated desk companion and synchronized clock.

## What are the different hardware options available?

You can build the companion in two distinct forms:

1. **GC9A01 1.28" Circular IPS Cyberdeck Edition**: An industrial sci-fi desktop pod featuring a vibrant 1.28" Circular 240×240 IPS Color Display.
2. **SSD1306 Monochrome OLED Robot Companion Edition**: A retro-futuristic desktop robot companion utilizing a crisp 0.96" or 1.3" Monochrome I2C OLED Display.

## Which microcontroller is used?

The project uses the ultra-compact **ESP32-C3 SuperMini** microcontroller.

## Where can I find the Bill of Materials (BOM) and purchase parts?

The comprehensive Bill of Materials (BOM) with verified purchasing links can be found in `BOM/BOM.md`, and quick-start shopping kits can be found in `BOM/README.md`.

## Are 3D printable enclosures available?

Yes, all enclosure CAD models are 100% support-free FDM 3D printable and available in both parametric OpenSCAD sources and verified watertight STLs in the `round 240x240/enclosure/` directory.

## How do I build and flash the firmware?

You can use PlatformIO to build and flash the firmware over USB-C. First, install PlatformIO, then run:

```bash
python -m platformio run
python -m platformio run --target upload
```

## How do I set up Wi-Fi on the device?

With the device plugged in via USB-C, open `http://localhost:5000/setup` in Google Chrome or Microsoft Edge (which use the Web Serial API). Click "Connect & Set Up WiFi", select the board's serial port, and enter your Wi-Fi credentials. The device saves them to flash and automatically locates the companion server.

## Can I test the interface without building the physical hardware?

Yes! The project includes an interactive browser prototype and visualizer where you can preview and interact with all screens, animations, and telemetry states in real time:

- **Robot Face Visualizer**: `http://localhost:5000/faces`
- **Full Display Emulator (Round & Rectangular)**: `http://localhost:5000/emulator`
