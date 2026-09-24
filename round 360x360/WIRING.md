# ⚡ Hardware Wiring Guide: GC9B72 2.1″ Round Display (360×360)

Complete pinout and hardware wiring guide for connecting the **GC9B72 2.1″ circular IPS display (360×360)** to the **ESP32-C3 SuperMini** microcontroller.

---

## 🔘 GC9B72 10-Pin Header Mapping

The GC9B72 module interfaces via a 10-pin single-row header ($2.54\text{mm}$ pitch) communicating over high-speed hardware SPI.

| Pin # | Silk Label | ESP32-C3 SuperMini Pin | Physical Location | Status / Action | Description |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **1** | **VCC** | **3V3** | Left Header (Pin 3) | **Required** | 3.3V Logic & Power Supply |
| **2** | **GND** | **GND** | Left Header (Pin 2) | **Required** | Common Ground |
| **3** | **SCL / SCK** | **GPIO 3** | Left Header (Pin 7) | **Required** | Hardware SPI Clock |
| **4** | **SDA / MOSI** | **GPIO 4** | Left Header (Pin 8) | **Required** | Hardware SPI MOSI (Data In) |
| **5** | **RST / RES** | **GPIO 5** | Left Header (Pin 9) | **Required** | Hardware Reset |
| **6** | **DC** | **GPIO 6** | Right Header (Pin 16) | **Required** | Data / Command Selection |
| **7** | **CS** | **GPIO 7** | Right Header (Pin 15) | **Required** | SPI Chip Select |
| **8** | **BLK** | **GPIO 0** *(or 3V3)* | Left Header (Pin 4) | **Required** | Backlight Control (Driven HIGH in FW) |
| **9** | **TE** | *(Not Connected)* | — | **NC (Leave Open)** | Tearing Effect Sync output from driver |
| **10** | **SDO** | *(Not Connected)* | — | **NC (Leave Open)** | SPI MISO (Serial Data Out / Read) |

---

## 💡 Notes on Unused Pins (TE & SDO)

1. **`SDO` (Pin 10 - SPI MISO):**
   - The firmware initializes the display bus in transmit-only mode (`Arduino_ESP32SPI` with `miso_pin = GFX_NOT_DEFINED`).
   - The ESP32 pushes framebuffers directly into display GRAM and never reads back display contents. Leaving SDO disconnected saves a vital GPIO pin for peripherals (e.g. WS2812B addressable LEDs on GPIO 10).
2. **`TE` (Pin 9 - Tearing Effect):**
   - The TE signal provides an optional V-Sync frame sync pulse.
   - Because the display runs over high-speed SPI ($40\text{--}80\text{MHz}$) updating circular telemetry gauges and split-flap numbers, software raster synchronization without TE is tear-free and avoids dedicating an interrupt GPIO.

---

## 📍 ESP32-C3 SuperMini Pinout Reference

Looking top-down at the ESP32-C3 SuperMini board with the **USB-C port pointing UP**:

```
                       [ USB-C PORT ]
                   +--------------------+
         [ 5V  ] --|  [1]          [16] |-- [ GPIO 6 ] ---> GC9B72 DC   (Pin 6)
         [ GND ] --|  [2]          [15] |-- [ GPIO 7 ] ---> GC9B72 CS   (Pin 7)
         [ 3V3 ] --|  [3]          [14] |-- [ GPIO 8 ]
GC9B72 - [ GPIO0] -|  [4]          [13] |-- [ GPIO 9 ]
         [ GPIO1] -|  [5]          [12] |-- [ GPIO 10] ---> WS2812B DIN (if used)
         [ GPIO2] -|  [6]          [11] |-- [ GPIO 20]
GC9B72 - [ GPIO3] -|  [7]          [10] |-- [ GPIO 21]
GC9B72 - [ GPIO4] -|  [8]          [9]  |-- [ GND    ]
GC9B72 - [ GPIO5] -|  [9]          [8]  |-- [ 5V     ]
                   +--------------------+

GC9B72 Pin 1 (VCC) ---> ESP32-C3 Pin 3 (3V3)
GC9B72 Pin 2 (GND) ---> ESP32-C3 Pin 2 (GND)
GC9B72 Pin 8 (BLK) ---> ESP32-C3 Pin 4 (GPIO 0)
GC9B72 Pin 9 (TE)  ---> NC (Leave floating / unconnected)
GC9B72 Pin 10 (SDO)---> NC (Leave floating / unconnected)
```

---

## ⚙️ Firmware Configuration & Flashing

This pinout is pre-configured in `src/config.h` under the `SCREEN_360` definition. 

To build and flash the 360×360 firmware:

```bash
pio run -e esp32c3_360 -t upload
```
