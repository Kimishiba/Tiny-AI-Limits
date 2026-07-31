# Wiring Guide (ESP32 to ILI9341 2.4"/2.8" SPI Display)

Here is the recommended wiring for connecting the ILI9341 display to a generic ESP32 development board using the hardware SPI pins.

| ILI9341 Pin | ESP32 Pin | Description |
|---|---|---|
| VCC / VIN | 3V3 | Power (3.3V) |
| GND | GND | Ground |
| CS | GPIO 15 | Screen Chip Select |
| RESET / RST | GPIO 4 | Reset pin |
| DC / RS | GPIO 2 | Data/Command pin |
| SDI / MOSI | GPIO 23 | SPI Data Input |
| SCK / SCLK | GPIO 18 | SPI Clock |
| LED / BLK | 3V3 (Optional) | Backlight Power (Connect to 3.3V) |
| SDO / MISO | GPIO 19 | SPI Data Output |
| T_CLK | GPIO 18 | Touch SPI Clock (Shares SCK) |
| T_CS | GPIO 21 | Touch Chip Select |
| T_DIN | GPIO 23 | Touch SPI Data In (Shares MOSI) |
| T_DO | GPIO 19 | Touch SPI Data Out (Shares MISO) |
| T_IRQ | Not Connected | Touch Interrupt (Optional) |

*Note: Depending on your specific ESP32 board model (like the NodeMCU-32S, ESP32-WROOM, or ESP32-S3), the exact location of the pins might vary, but standard Hardware SPI pins are usually GPIO 18 (SCK) and GPIO 23 (MOSI).*
