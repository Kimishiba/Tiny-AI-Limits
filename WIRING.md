# Wiring Guide (ESP32 to ILI9341 2.8" SPI Touch Display)

Here is the recommended wiring for connecting the 2.8-inch ILI9341 touch display module to a generic ESP32 development board using hardware SPI pins.

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

*Note: Hardware SPI pins on standard ESP32 boards are GPIO 18 (SCK), GPIO 23 (MOSI), and GPIO 19 (MISO).*


