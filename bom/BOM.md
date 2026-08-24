# 📋 Bill of Materials (BOM) — Tiny AI Limits

Complete component specifications and verified purchasing links for building the **Tiny AI Limits & Desktop Companion**.

---

## ⚡ Core Electronics

### 1. ESP32-C3 SuperMini Microcontroller (Required for Both Builds)
* **Description:** Ultra-compact development board featuring the Espressif ESP32-C3 RISC-V 32-bit single-core SoC (160 MHz), built-in 2.4 GHz Wi-Fi 4 & Bluetooth 5 (LE), 400KB SRAM, 4MB Flash, and native USB-C.
* **Dimensions:** 22.5 mm × 18 mm × 4 mm
* **Quantity:** 1
* **Purchasing Links:**
  * [AliExpress (ESP32-C3 SuperMini ~ $2.50)](https://www.aliexpress.com/w/wholesale-ESP32-C3-SuperMini.html)
  * [Amazon US (ESP32-C3 SuperMini 3-Pack ~ $12.99)](https://www.amazon.com/s?k=esp32-c3+supermini)
  * [Amazon EU/DE (ESP32-C3 SuperMini ~ €4.50)](https://www.amazon.de/s?k=esp32-c3+supermini)

---

### 2. Option 1 Display: GC9A01 1.28" Circular IPS Color LCD (240×240)
* **Description:** 1.28-inch round full-color IPS TFT LCD screen module with GC9A01 controller, SPI 4-wire interface, 240×240 resolution, 65K RGB colors, and 3.3V logic level.
* **Header Pins:** 8-pin or 7-pin header (`VCC`, `GND`, `SCL`, `SDA`, `DC`, `CS`, `RST`, `BLK`).
* **Quantity:** 1 (for Option 1 Cyberdeck build)
* **Purchasing Links:**
  * [Waveshare 1.28" Round LCD Module (Official ~ $7.99)](https://www.waveshare.com/1.28inch-touch-lcd-240x240.htm)
  * [AliExpress (GC9A01 1.28" Round Display ~ $3.80)](https://www.aliexpress.com/w/wholesale-GC9A01-1.28-inch-round-lcd.html)
  * [Amazon US (GC9A01 1.28" Round SPI Display ~ $8.99)](https://www.amazon.com/s?k=GC9A01+1.28+round+display)
  * [Amazon EU/DE (GC9A01 1.28 Zoll Rundes Display ~ €8.50)](https://www.amazon.de/s?k=GC9A01+1.28+display)

---

### 3. Option 2 Display: SSD1306 0.96" / 1.3" Monochrome I2C OLED (128×64)
* **Description:** 0.96-inch (or 1.3-inch SH1106) monochrome blue/white OLED display module with SSD1306 driver, I2C 2-wire interface, 128×64 resolution, 3.3V/5V compatible.
* **Header Pins:** 4-pin header (`GND`, `VCC`, `SCL`, `SDA`).
* **Quantity:** 1 (for Option 2 Robot Face build)
* **Purchasing Links:**
  * [Adafruit 0.96" 128x64 OLED (Official Product ID 326 ~ $17.50)](https://www.adafruit.com/product/326)
  * [AliExpress (0.96" I2C OLED 128x64 ~ $1.80)](https://www.aliexpress.com/w/wholesale-0.96-i2c-oled-128x64-ssd1306.html)
  * [Amazon US (0.96" I2C OLED 5-Pack ~ $11.99)](https://www.amazon.com/s?k=0.96+i2c+oled+display+ssd1306)
  * [Amazon EU/DE (0.96 Zoll I2C OLED Display ~ €3.50)](https://www.amazon.de/s?k=0.96+oled+i2c+ssd1306)

---

## 🔩 Hardware Fasteners & Enclosure Components

### 4. M3 × 16mm (or M3 × 12mm) Socket Head Cap Screws
* **Description:** M3 metric machine screws with cylindrical socket cap head (DIN 912 / ISO 4762), 2.5mm hex drive. Brass provides a premium industrial cyberdeck aesthetic; black oxide or stainless steel also look great.
* **Quantity:** 4 per pod
* **Purchasing Links:**
  * [Amazon US (M3 Brass Socket Head Screws Assortment ~ $9.99)](https://www.amazon.com/s?k=m3+brass+socket+head+cap+screws)
  * [Amazon EU/DE (M3 Zylinderschrauben Innensechskant ~ €7.99)](https://www.amazon.de/s?k=M3+Zylinderschrauben+Innensechskant)
  * [AliExpress (M3 Brass / Black Socket Screws ~ $1.50)](https://www.aliexpress.com/w/wholesale-M3-socket-head-cap-screws-brass.html)

---

### 5. Non-Slip Adhesive Rubber Bumper Feet
* **Description:** 6 mm to 8 mm diameter hemispherical clear or black silicone rubber bumper pads with adhesive backing. Fits into the 4 molded recesses on the bottom of the Tier 1 stand base to prevent sliding.
* **Quantity:** 4 per stand
* **Purchasing Links:**
  * [Amazon US (Self-Adhesive Rubber Bumper Pads ~ $4.99)](https://www.amazon.com/s?k=rubber+bumper+feet+adhesive+small)
  * [Amazon EU/DE (Selbstklebende Gummifüße ~ €3.99)](https://www.amazon.de/s?k=Gummifuesse+selbstklebend)
  * [AliExpress (Silicone Bumper Pads 100pcs ~ $1.20)](https://www.aliexpress.com/w/wholesale-silicone-rubber-feet-adhesive.html)

---

### 6. Flexible Hookup Wire / Female-to-Female DuPont Jumpers
* **Description:** 28 AWG or 30 AWG stranded silicone flexible wire (or 10cm Female-to-Female 2.54mm pitch DuPont ribbon cables).
* **Quantity:** 7–8 wires for GC9A01 SPI; 4 wires for SSD1306 I2C.
* **Purchasing Links:**
  * [Amazon US (28/30 AWG Silicone Hookup Wire Spool Kit ~ $9.99)](https://www.amazon.com/s?k=30+awg+silicone+wire)
  * [Amazon US (10cm Female-to-Female DuPont Jumpers ~ $4.99)](https://www.amazon.com/s?k=dupont+cables+female+to+female+10cm)
  * [AliExpress (Silicone Wire 30AWG / DuPont Cables ~ $1.50)](https://www.aliexpress.com/w/wholesale-30awg-silicone-wire.html)

---

### 7. USB-C Cable (Data & Power)
* **Description:** Standard USB Type-C cable (USB-A to USB-C or USB-C to USB-C) capable of data transfer (required for initial firmware flashing and Web Serial Wi-Fi setup).
* **Length:** 0.5m – 1.5m
* **Quantity:** 1

---

## 🧵 3D Printing Filament Guide

| Part | Recommended Filament Type | Recommended Color / Finish | Approx. Filament Weight |
| :--- | :--- | :--- | :---: |
| **Main Housing Bucket** | PLA / PETG / ABS | Matte Charcoal / Galaxy Black | ~18 g |
| **Front Display Bezel** | PLA / PETG / ABS | Matte Black or Gunmetal Gray | ~10 g |
| **Tier 2 Pedestal Trunk** | PLA / PETG / ABS | Matte Dark Gray or Black | ~24 g |
| **Tier 1 Base Plate** | Wood PLA / Standard PLA | Dark Walnut / Teak Wood PLA | ~14 g |

---

## 📊 Summary of Total Build Cost

| Item | Budget Source (AliExpress) | Fast Domestic Source (Amazon) |
| :--- | :---: | :---: |
| **ESP32-C3 SuperMini** | $2.50 | $4.50 |
| **GC9A01 1.28" Round LCD** | $3.80 | $7.99 |
| **M3 Screws & Bumper Feet** | $1.20 | $3.00 |
| **Wires & Filament** | $1.00 | $1.50 |
| **Estimated Total (Option 1):** | **~$8.50** | **~$16.99** |
