# 🔌 Hardware & Wiring Guide

This document provides complete technical specifications, component sourcing recommendations, pinout diagrams, and assembly schematics for the **Tiny AI Limits** hardware.

---

## 🛒 Bill of Materials (BOM)

| Item | Component | Key Specification | Qty | Approx. Cost | Sourcing Links |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **MCU** | ESP32-C3 SuperMini | RISC-V 160MHz, 4MB Flash, USB-C CDC, 2.4GHz Wi-Fi/BLE | 1 | \$2.50 – \$4.00 | [AliExpress](https://aliexpress.com) / [Amazon](https://amazon.com) |
| **Display** | GC9A01 1.28" IPS Round LCD | 240×240 IPS, 4-Wire Hardware SPI, 3.3V Logic | 1 | \$4.00 – \$6.50 | [Waveshare](https://waveshare.com) / [AliExpress](https://aliexpress.com) |
| **Fasteners** | M3 Socket Head Screws | M3 × 6mm or M3 × 8mm Stainless Steel | 4 | < \$1.00 | Local Hardware / Amazon |
| **Wiring** | 28–30 AWG Silicone Wire | Ultra-flexible stranded silicone wire | 7 | < \$0.50 | Generic |
| **Enclosure** | 3D Printed PETG / PLA | 2-tier stand, main bucket, front bezel | 1 set | ~\$1.00 (filament) | Self-printed |

---

## 📟 Microcontroller: ESP32-C3 SuperMini Pinout

The **ESP32-C3 SuperMini** is an ultra-compact (22.5mm × 18mm) development board featuring an Espressif ESP32-C3 RISC-V 32-bit single-core processor running at 160 MHz with native USB-C CDC serial communication.

```
                  ┌──────────────────────┐
                  │   [ USB-C CONNECTOR ]│
                  │                      │
         GPIO 0  ─┤ [ ]              [ ] ├─ 5V (VBUS)
         GPIO 1  ─┤ [ ]              [ ] ├─ GND
         GPIO 2  ─┤ [ ]              [ ] ├─ 3V3
         GPIO 3  ─┤ [ ]              [ ] ├─ GPIO 10
         GPIO 4  ─┤ [ ]              [ ] ├─ GPIO 9 (BOOT)
         GPIO 5  ─┤ [ ]              [ ] ├─ GPIO 8
         GPIO 6  ─┤ [ ]              [ ] ├─ GPIO 7
                  └──────────────────────┘
```

---

## 🖥️ GC9A01 1.28" Display Pinout & Hardware SPI

The **GC9A01** is a high-contrast circular TFT IPS LCD panel with 240×240 pixel resolution and a wide viewing angle. It communicates via high-speed 4-wire SPI (clocked at up to 40MHz in firmware).

```
   GC9A01 Pin      ESP32-C3 Pin      Signal Name       Description
 ═══════════════════════════════════════════════════════════════════════════════
   VCC             3V3               Power (3.3V)      3.3V Power Rail (Max 80mA)
   GND             GND               Ground            System Common Ground
   SCL / SCLK      GPIO 4            SPI_SCK           Hardware SPI Clock Line
   SDA / MOSI      GPIO 6            SPI_MOSI          Hardware SPI Data In (Master Out)
   DC              GPIO 7            TFT_DC            Data / Command Select Line
   CS              GPIO 5            TFT_CS            Chip Select (Active LOW)
   RST / RES       GPIO 1            TFT_RST           Hardware Display Reset
   BLK             GPIO 0 (or 3V3)   TFT_BL            Backlight PWM Dimming / Enable
 ═══════════════════════════════════════════════════════════════════════════════
```

> [!IMPORTANT]
> **Logic Level Warning:** The GC9A01 is a **3.3V logic** device. Always power the display's **VCC** from the ESP32-C3 **3V3** pin, NOT the 5V pin. Connecting 5V directly to the display logic pins will permanently damage the controller IC.

---

## 📐 Detailed Wiring Schematics

### 1. Direct Soldered Compact Assembly (Recommended for 3D Enclosure)

For the cleanest enclosure fit, use 40mm lengths of 30 AWG flexible silicone wire soldered directly between the ESP32-C3 castellated/through-hole pads and the back of the GC9A01 module.

```
       GC9A01 Circular Display                     ESP32-C3 SuperMini
   ┌──────────────────────────────┐              ┌────────────────────┐
   │ ( ) ( ) ( ) ( ) ( ) ( ) ( )  │              │                    │
   │ VCC GND SCL SDA DC  CS  RST  │              │                    │
   └──┬───┬───┬───┬───┬───┬───┬───┘              │                    │
      │   │   │   │   │   │   │                  │                    │
      │   │   │   │   │   │   └────────────────> │ GPIO 1 (RST)       │
      │   │   │   │   │   └────────────────────> │ GPIO 5 (CS)        │
      │   │   │   │   └────────────────────────> │ GPIO 7 (DC)        │
      │   │   │   └────────────────────────────> │ GPIO 6 (MOSI)      │
      │   │   └────────────────────────────────> │ GPIO 4 (SCK)       │
      │   └────────────────────────────────────> │ GND                │
      └────────────────────────────────────────> │ 3V3                │
                                                 │                    │
                                                 │ [ USB-C PORT ]     │
                                                 └────────────────────┘
```

---

## 💡 Backlight Brightness Control (PWM)

The firmware configures **GPIO 0** using the ESP32 LEDC (LED Control) hardware PWM peripheral:
* **PWM Channel:** 0
* **PWM Frequency:** 5000 Hz
* **PWM Resolution:** 8-bit (0 – 255 levels)

When `BLK` is left unconnected or bridged to `3V3`, the backlight runs at 100% full brightness. Connecting `BLK` to `GPIO 0` allows dynamic dimming and night mode schedules.

---

## ⚡ Power Supply Considerations

* **Active Consumption:** ~95 mA to 140 mA (Wi-Fi polling + 100% display backlight).
* **Peak Surge:** ~280 mA during Wi-Fi transmission bursts.
* **Recommended Supply:** Any standard USB 2.0/3.0 port or 5V 1A USB-C wall charger.

---

## 🛠️ Step-by-Step Soldering Checklist

1. **Tin the pads:** Apply lead-free solder with flux to both the GC9A01 breakout header pads and the ESP32-C3 SuperMini edge pins.
2. **Cut silicone wires:** Strip ~1.5mm insulation from each end of seven 40mm wires.
3. **Solder in order:** Begin with GND and 3V3 power rails, followed by the high-speed SPI lines (SCL, SDA), then control lines (DC, CS, RST, BLK).
4. **Insulate:** Place a small square of Kapton tape or non-conductive foam between the rear metal shielding of the display and the back of the ESP32 board to prevent short circuits when seated in the 3D-printed enclosure.
