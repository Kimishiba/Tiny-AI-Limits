# 🩺 Troubleshooting & Frequently Asked Questions (FAQ)

Find quick solutions to common hardware, firmware, network, and companion setup issues.

---

## 🔍 Diagnostic Matrix & Troubleshooting Guide

### 1. Hardware & Flashing Issues

#### ❓ The ESP32-C3 port does not appear or PlatformIO fails to upload
* **Cause:** Native USB CDC is in an unbooted state or wrong USB cable.
* **Fix:**
  1. Ensure you are using a **data-capable USB-C cable**, not a charge-only cable.
  2. Hold down the **BOOT** button (GPIO 9) on the ESP32-C3 SuperMini, plug in the USB-C cable, release BOOT, then run `python -m platformio run --target upload`.
  3. On Linux, ensure your user belongs to `dialout`: `sudo usermod -a -G dialout $USER`.

#### ❓ Display is blank/black or backlight does not turn on
* **Cause:** Power rail not connected or `BLK` pin floating.
* **Fix:**
  1. Verify display `VCC` is connected to ESP32 **3V3** (not 5V) and `GND` to **GND**.
  2. If `BLK` is unconnected, wire `BLK` to `GPIO 0` or bridge `BLK` to `3V3` to force full backlight illumination.

#### ❓ Screen shows white noise, static, or scrambled pixels
* **Cause:** SPI clock speed too high for wire lengths, or loose `MOSI`/`SCLK` connection.
* **Fix:**
  1. Check your solder joints on `GPIO 4` (SCLK) and `GPIO 6` (MOSI).
  2. In `platformio.ini`, try lowering `-DSPI_FREQUENCY=40000000` to `27000000`.

---

### 2. Network & mDNS Issues

#### ❓ Board fails to connect to Wi-Fi
* **Cause:** Network is 5 GHz only or captive portal.
* **Fix:**
  * ESP32-C3 microcontrollers only support **2.4 GHz Wi-Fi** (802.11 b/g/n). Ensure you connect to a 2.4 GHz SSID. Enterprise WPA2 networks with RADIUS or web captive portals are not supported.

#### ❓ Board connects to Wi-Fi but displays a Red Crown Arc (Host Disconnected)
* **Cause:** mDNS (`_tinyscreen._tcp.local`) is blocked across router subnets or host firewall.
* **Fix:**
  1. Ensure the Python companion app (`python backend/app.py`) is running on your workstation.
  2. Verify your workstation and ESP32 are on the exact same Wi-Fi subnet / router.
  3. If your network router blocks multicast DNS packets (common on corporate/guest networks), navigate to `http://localhost:5000/setup` and use **"Pair an Existing Board"** by entering the device IP directly.

---

### 3. Pairing & Multi-Board Issues

#### ❓ Board shows an Amber Crown Arc instead of Green
* **Cause:** The board is connected to Wi-Fi and reading data via unauthenticated mDNS fallback, but has not been paired with a unique `pair_id`.
* **Fix:**
  * Open `http://localhost:5000/setup` in Chrome/Edge, click **"Connect Board (Direct Serial Setup)"**, and click **"Configure & Pair"**. Once the `pair_id` is written to NVS, the crown will pulse Emerald Green.

#### ❓ How do I completely factory-reset a board?
* **Fix:** Connect via WebSerial or serial monitor (`115200` baud) and send the text command:
  ```text
  RESET
  ```
  This will wipe all stored NVS Wi-Fi credentials and pairing UUIDs, rebooting the device into initial pairing radar mode.

---

## 💬 Frequently Asked Questions (FAQ)

### Can I use a square or rectangular display instead of the GC9A01 circular display?
Yes! The repository also includes ST7789 240×240 square display and SSD1306 OLED drivers in earlier branches. However, the radial HUD gauges and circular crown arc are specifically optimized for the 1.28" GC9A01 round IPS display.

### Can I track custom API spend limits from local LLMs (Ollama / vLLM)?
Yes. You can implement a custom provider class inside `backend/providers/` inheriting from `BaseProvider`. The companion backend will automatically load and expose it to the `/setup` configuration dropdown.

### Does the Python companion backend require root or administrator privileges?
No. The backend runs completely as a standard user process and requires no special privileges.

### How much power does the device consume?
Between 95 mA and 140 mA at 5V (~0.5W to 0.7W), making it safe to power from any USB port on your PC, monitor hub, or desk charger.
