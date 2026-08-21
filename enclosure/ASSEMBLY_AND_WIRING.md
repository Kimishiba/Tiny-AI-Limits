# 3D Printable Angled Desk Console & Macropad
### Hardware: 1.3" OLED + ESP32-C3 SuperMini + 3x MX Switches + EC11 Rotary Encoder

This custom enclosure houses:
- **1x 1.3" I2C OLED Display** (128x64 pixels, SH1106 / SSD1306)
- **1x ESP32-C3 SuperMini Microcontroller** (USB-C powered)
- **3x Standard Mechanical Keyboard Switches** (Cherry MX / Gateron / Outemu 14x14mm)
- **1x EC11 Rotary Encoder with Push Button** (Knob for volume, scrolling, menu navigation)

---

## 🛠️ 3D Printing Instructions

### 1. Model Files
The parametric CAD file is located at:
`enclosure/desk_console_oled13_esp32c3.scad`

Open it in [OpenSCAD](https://openscad.org/) (free & open source) to export `.stl` or `.3mf` files:
- Change `RENDER_PART = "top_case";` -> Press **F6** (Render) -> **F7** (Export STL).
- Change `RENDER_PART = "bottom_base";` -> Press **F6** (Render) -> **F7** (Export STL).

### 2. Slicer Settings (Bambu Studio / PrusaSlicer / Cura / OrcaSlicer)
| Parameter | Recommendation |
| :--- | :--- |
| **Material** | PLA, PETG, or ABS/ASA |
| **Layer Height** | 0.20mm (0.16mm for top surface details) |
| **Perimeters / Walls** | 3 - 4 walls (for rigid switch snaps) |
| **Top / Bottom Layers**| 4 / 4 |
| **Infill** | 20% - 25% Gyroid or Grid |
| **Print Orientation** | **Top Case:** Print upside-down (angled face flat on bed with supports) OR upright with minimal tree supports under the OLED window. <br>**Bottom Base:** Print flat on bed (no supports needed). |

---

## 🔌 Complete Wiring Pinout Table (ESP32-C3 SuperMini)

The ESP32-C3 SuperMini has 13 accessible GPIO pins. Here is the conflict-free pin mapping:

| Component | Component Pin | ESP32-C3 Pin | Notes |
| :--- | :--- | :--- | :--- |
| **1.3" OLED Screen** | `VCC` | **3.3V** or **5V** | Power rail |
| | `GND` | **GND** | Ground |
| | `SCL` | **GPIO 9** | Default Hardware I2C Clock |
| | `SDA` | **GPIO 8** | Default Hardware I2C Data |
| **Rotary Encoder (EC11)** | `A` (CLK / Phase A) | **GPIO 0** | Use internal `INPUT_PULLUP` |
| | `B` (DT / Phase B) | **GPIO 1** | Use internal `INPUT_PULLUP` |
| | `SW` (Encoder Button)| **GPIO 2** | Push button to GND |
| | `GND` / Common | **GND** | Ground |
| **MX Switch 1 (Left)** | Pin 1 / Signal | **GPIO 3** | Use internal `INPUT_PULLUP` |
| | Pin 2 / Ground | **GND** | Ground |
| **MX Switch 2 (Center)** | Pin 1 / Signal | **GPIO 4** | Use internal `INPUT_PULLUP` |
| | Pin 2 / Ground | **GND** | Ground |
| **MX Switch 3 (Right)** | Pin 1 / Signal | **GPIO 5** | Use internal `INPUT_PULLUP` |
| | Pin 2 / Ground | **GND** | Ground |

*(Pins GPIO 6, 7, 10, 20, 21 remain free for optional WS2812B RGB underglow, buzzer, or sensors).*

---

## 💻 Sample Firmware Snippet (Arduino / PlatformIO)

```cpp
#include <Arduino.h>
#include <Wire.h>
#include <U8g2lib.h>

// U8g2 driver for 1.3" SH1106 I2C OLED (GPIO 8 SDA, GPIO 9 SCL)
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, /* clock=*/ 9, /* data=*/ 8);

// Pin Definitions
#define ENC_CLK 0
#define ENC_DT  1
#define ENC_SW  2
#define SW1_PIN 3
#define SW2_PIN 4
#define SW3_PIN 5

void setup() {
  Serial.begin(115200);

  // Initialize Inputs with Internal Pullups
  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT,  INPUT_PULLUP);
  pinMode(ENC_SW,  INPUT_PULLUP);
  pinMode(SW1_PIN, INPUT_PULLUP);
  pinMode(SW2_PIN, INPUT_PULLUP);
  pinMode(SW3_PIN, INPUT_PULLUP);

  // Initialize OLED
  Wire.begin(8, 9);
  u8g2.begin();
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr);
  u8g2.drawStr(10, 24, "Tiny Desk Console");
  u8g2.drawStr(10, 48, "Ready!");
  u8g2.sendBuffer();
}

void loop() {
  if (digitalRead(SW1_PIN) == LOW) {
    Serial.println("Switch 1 Pressed!");
    delay(150); // Simple debounce
  }
  if (digitalRead(SW2_PIN) == LOW) {
    Serial.println("Switch 2 Pressed!");
    delay(150);
  }
  if (digitalRead(SW3_PIN) == LOW) {
    Serial.println("Switch 3 Pressed!");
    delay(150);
  }
}
```

---

## 🔩 Bill of Materials (Hardware & Fasteners)

- **4x M3 x 8mm - 12mm screws** (for joining top case and base plate)
- **4x M2 x 4mm self-tapping screws** (for mounting 1.3" OLED PCB)
- **3x MX Mechanical Key Switches** (with keycaps of your choice)
- **1x EC11 Rotary Encoder** (with 6mm D-shaft or knurled shaft + knob)
- **4x Adhesive Rubber Bumper Feet** (for bottom base non-slip desk grip)
