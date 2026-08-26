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

With the device plugged in via USB-C, open `http://localhost:5000/setup` in Google Chrome or Microsoft Edge (which use the Web Serial API). Use the "Direct Serial Setup" section: select the board's serial port, scan for networks, and enter your Wi-Fi credentials. The device saves them to flash, and the same step pairs it to your computer.

## Why does my board show someone else's token quotas?

This happens when more than one person runs the companion app on the same Wi-Fi. Older firmware asked the network "who is running a companion app?" and used whichever answered first — which could be a colleague's machine.

The fix is **pairing**: your board stores your computer's address and a `pair_id`, and talks only to that machine. Re-run "Direct Serial Setup" on `http://localhost:5000/setup` to pair a board, or use the "Pair an Existing Board" box if the board is already on Wi-Fi.

If you set the board up with the "Connect & Set Up WiFi" button, it is **not** paired — that protocol can only carry Wi-Fi credentials. Use the "Pair an Existing Board" box afterwards.

## How can I tell whether my board is paired?

Watch the status light:

- **Round display**: green dot means paired, **amber** means connected but unpaired, red means no connection.
- **OLED**: a single lit pixel in the bottom-right corner means connected but unpaired.

Unpaired means the board is reading from whichever companion app answered first, so on a shared network the figures may not be yours.

You can also send `STATUS` over the serial console, which reports `paired_host` and `pair_id`.

## My board stopped finding the companion app after a router restart

Your computer's IP probably changed. A paired board re-finds it automatically by matching its `pair_id` against the mDNS records, usually within a minute.

If it does not recover, check that the companion app is running, then re-pair with the "Pair an Existing Board" box on the setup page using the board's IP.

A board that has been paired will **not** fall back to picking another companion app, even if it can no longer reach its own. It shows no data and waits to be re-paired. That is deliberate: showing nothing is better than showing someone else's numbers.

## Can I run several boards on one network?

Yes. Each board claims a unique mDNS name derived from its MAC address (`tinyscreen-F030.local` and so on), so they do not collide, and each is paired to its own companion app.

The board prints its hostname on the serial console at boot, and the setup page reports it when you connect over serial.

## Can I test the interface without building the physical hardware?

Yes! The project includes an interactive browser prototype and visualizer where you can preview and interact with all screens, animations, and telemetry states in real time:

- **Robot Face Visualizer**: `http://localhost:5000/faces`
- **Full Display Emulator (Round & Rectangular)**: `http://localhost:5000/emulator`
