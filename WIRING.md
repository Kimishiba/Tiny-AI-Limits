# Wiring Guide (ESP32 to ST77916 1.5" 360x360 Round Display)

Here is the recommended wiring for connecting the ST77916 round display module to a generic ESP32 development board.

| ST77916 Pin | ESP32 Pin | Description |
|---|---|---|
| VCC / VIN | 3V3 | Power (3.3V) |
| GND | GND | Ground |
| CS | GPIO 15 | Screen Chip Select |
| RESET / RST | GPIO 4 | Reset pin |
| DC / RS | GPIO 2 | Data/Command pin |
| SCLK / CLK | GPIO 18 | SPI Clock |
| MOSI / D0 | GPIO 23 | SPI Data Input / D0 |
| MISO / D1 | GPIO 19 | SPI Data Output / D1 |
| D2 (Optional QSPI) | GPIO 22 | QSPI Data Line 2 |
| D3 (Optional QSPI) | GPIO 21 | QSPI Data Line 3 |
| BL / LED | 3V3 | Backlight Power (Connect to 3.3V or GPIO pin for PWM dimming) |

*Note: The ST77916 supports SPI / QSPI modes. Standard 1-bit SPI uses SCLK, MOSI, CS, DC, and RST.*

