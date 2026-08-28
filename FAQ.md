# Frequently Asked Questions (FAQ)

## What is Tiny AI Limits & Desktop Companion?

It is an open-source, Wi-Fi enabled desktop telemetry companion powered by the ultra-compact ESP32-C3 SuperMini microcontroller. It brings your AI developer environment to life with physical desktop hardware — monitoring real-time token quotas for Claude Code and Google Antigravity CLI, alerting you when AI agents require plan approvals, and serving as an expressive animated desk companion and synchronized clock.

## Which display does the hardware use?

There is a single build: the **GC9A01 1.28" Circular IPS Cyberdeck Edition**, an industrial sci-fi desktop pod featuring a vibrant 1.28" Circular 240×240 IPS Color Display driven over SPI.

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

Watch the status arc at the top of the display: pulsing green means paired & connected, **amber** means connected but unpaired, and red means no connection.

Unpaired means the board is reading from whichever companion app answered first, so on a shared network the figures may not be yours.

You can also send `STATUS` over the serial console, which reports `paired_host` and `pair_id`.

## My board stopped finding the companion app after a router restart

Your computer's IP probably changed. A paired board re-finds it automatically by matching its `pair_id` against the mDNS records, usually within a minute.

If it does not recover, check that the companion app is running, then re-pair with the "Pair an Existing Board" box on the setup page using the board's IP.

A board that has been paired will **not** fall back to picking another companion app, even if it can no longer reach its own. It shows no data and waits to be re-paired. That is deliberate: showing nothing is better than showing someone else's numbers.

## Can I run several boards on one network?

Yes. Each board claims a unique mDNS name derived from its MAC address (`tinyscreen-F030.local` and so on), so they do not collide, and each is paired to its own companion app.

The board prints its hostname on the serial console at boot, and the setup page reports it when you connect over serial.

## How do I choose which 2 AI models are displayed on the radial gauges?

You can customize the Left and Right radial arcs through either:
1. **The macOS Menu Bar App**: Click the `🖥️` icon in your top bar $\to$ `🔌 Set Up New Device (WiFi)` $\to$ **Gauge Mapping & Providers**.
2. **The Web Setup Page**: Open `http://localhost:5000/setup` and select your providers in the dropdowns.
3. **The Config File**: Set `"selected_gauges": {"left": "claude", "right": "antigravity"}` in `~/.tiny_ai_screen/config.json`.

Supported providers include Anthropic Claude (`CLD`), Google Antigravity (`AGY`), OpenAI Codex (`COD`), Cursor IDE (`CUR`), GitHub Copilot (`COP`), Gemini (`GEM`), OpenRouter (`ROUT`), DeepSeek (`DSK`), Mistral (`MST`), and Groq (`GRQ`).

## What do the names on the multi-agent cards mean?

When multiple AI agents or subagents are running concurrently, the screen displays a multi-row HUD showing each agent's active task with contextual multi-word names (e.g. `3D Printer`, `Firmware QA`, `AI Limits`, `State Mach`). The background styling and accent bar indicate the provider (Safety Orange for Antigravity, Electric Cyan for Claude), while the pulsating status dot tracks real-time progress (`WORKING 🔵/🟠`, `COMPLETE 🟢`, `WAITING 🟡`).

## What do the reset times below the gauges indicate?

The timers below each gauge (e.g. `3h 22m`, `4h 10m`) indicate the exact remaining time until that provider's 5-hour rolling usage window expires and your quota replenishes.

## How do I run the macOS Top Menu Bar Companion?

Make sure all dependencies are installed with `pip install -r backend/requirements.txt`, then launch `python3 backend/app.py` or double-click `TinyScreen.command`. The `🖥️` icon will appear in your top menu bar with quick access to the Emulator, Setup, Location settings, and OTA updates.

## Can I test the interface without building the physical hardware?

Yes! The project includes an interactive browser prototype and visualizer where you can preview and interact with all screens, animations, and telemetry states in real time:

- **Full Display Emulator**: `http://localhost:5000/emulator`
