# Wiring Guide (ESP32-C3 SuperMini to ILI9341 2.8" SPI Touch Display)

Here is the recommended wiring for connecting the 2.8-inch ILI9341 SPI Touch display to an **ESP32-C3 SuperMini** board using hardware SPI pins.

| ILI9341 Pin | ESP32-C3 Pin | Description |
|---|---|---|
| VCC / VIN | 3V3 / 5V | Power (3.3V / 5V input) |
| GND | GND | Ground |
| CS | GPIO 7 | Screen Chip Select |
| RESET / RST | GPIO 2 | Reset pin |
| DC / RS | GPIO 3 | Data/Command pin |
| SDI / MOSI | GPIO 6 | Hardware SPI Data Out (MOSI) |
| SCK / SCLK | GPIO 4 | Hardware SPI Clock (SCLK) |
| SDO / MISO | GPIO 5 | Hardware SPI Data In (MISO) |
| LED / BLK | 3V3 | Backlight Power |
| T_CLK | GPIO 4 | Touch SPI Clock (Shares SCLK) |
| T_CS | GPIO 1 | Touch Chip Select |
| T_DIN | GPIO 6 | Touch SPI Data In (Shares MOSI) |
| T_DO | GPIO 5 | Touch SPI Data Out (Shares MISO) |
| T_IRQ | Not Connected | Touch Interrupt (Optional) |

*Note: ESP32-C3 hardware SPI defaults to SCK=GPIO4, MOSI=GPIO6, MISO=GPIO5.*



