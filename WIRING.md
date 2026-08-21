# Wiring Guide: ESP32-C3 SuperMini to 0.96" I2C OLED (SSD1306)

This guide shows how to wire your **4-pin 0.96" I2C OLED Display (128x64)** to the **ESP32-C3 SuperMini** on a breadboard.

---

## ⚡ 1. Easiest Breadboard Pinout (Standard Hardware I2C)

| OLED Pin (0.96") | ESP32-C3 SuperMini Pin | Description |
| :--- | :--- | :--- |
| **GND** | **GND** (Pin 2 on Left Header) | Ground |
| **VCC** | **3V3** (Pin 3 on Left Header) | 3.3V Power |
| **SCL / SCK** | **GPIO 9** (Pin 4 on Right Header) | I2C Clock |
| **SDA** | **GPIO 8** (Pin 3 on Right Header) | I2C Data |

---

## 📍 ESP32-C3 SuperMini Physical Pin Reference

Looking at the board top-down with the **USB-C port pointing UP**:

```
                       [ USB-C PORT ]
                   +--------------------+
         [ 5V  ] --|  [1]          [16] |-- [ GPIO6  ]
         [ GND ] --|  [2]          [15] |-- [ GPIO7  ]
         [ 3V3 ] --|  [3]          [14] |-- [ GPIO8  ] ---> OLED SDA
         [ GPIO0] -|  [4]          [13] |-- [ GPIO9  ] ---> OLED SCL
         [ GPIO1] -|  [5]          [12] |-- [ GPIO10 ]
         [ GPIO2] -|  [6]          [11] |-- [ GPIO20 / RX ]
         [ GPIO3] -|  [7]          [10] |-- [ GPIO21 / TX ]
         [ GPIO4] -|  [8]          [9]  |-- [ GND    ]
         [ GPIO5] -|  [9]          [8]  |-- [ 5V     ]
                   +--------------------+
```

---

## 💡 Breadboard Hookup Steps

1. Plug the **ESP32-C3 SuperMini** into your breadboard straddling the center divider.
2. Plug the **0.96" OLED** into an open 4-column section of the breadboard.
3. Check the label on your OLED module pins (usually either `GND-VCC-SCL-SDA` or `VCC-GND-SCL-SDA`):
   - Connect **GND** on the OLED to **GND** (Pin 2, left side of SuperMini).
   - Connect **VCC** on the OLED to **3V3** (Pin 3, left side of SuperMini).
   - Connect **SCL** on the OLED to **GPIO 9** (Pin 13, right side of SuperMini).
   - Connect **SDA** on the OLED to **GPIO 8** (Pin 14, right side of SuperMini).
4. Connect the USB-C cable to your Mac.

---

## 🔁 "Adjacent 4-Pin" Alternative (Left Side Only)

Because the ESP32-C3 allows mapping I2C to any GPIO, you can also wire all 4 pins in an unbroken row on the left header by changing two lines in [`src/main.cpp`](src/main.cpp):

```cpp
#define I2C_SDA_PIN 0
#define I2C_SCL_PIN 1
```

With this, your 4 breadboard jumpers sit side-by-side on pins `[2]`, `[3]`, `[4]`, `[5]`:
- **GND** -> Pin 2 (`GND`)
- **VCC** -> Pin 3 (`3V3`)
- **SDA** -> Pin 4 (`GPIO 0`)
- **SCL** -> Pin 5 (`GPIO 1`)
