#pragma once
#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include "config.h"

// GC9A01 SPI Hardware Driver (Pin 2 as dummy MISO to satisfy ESP32-C3 SPI HAL)
inline Arduino_DataBus *createGC9A01Bus() {
    return new Arduino_HWSPI(GC9A01_DC_PIN, GC9A01_CS_PIN, GC9A01_SCK_PIN, GC9A01_MOSI_PIN, 2 /* dummy MISO on spare pin */);
}

inline Arduino_GFX *createGC9A01Display(Arduino_DataBus *bus) {
    return new Arduino_GC9A01(bus, GC9A01_RST_PIN, 0 /* rotation */, true /* IPS */);
}

inline void initGC9A01Backlight() {
    if (GC9A01_BLK_PIN >= 0) {
        pinMode(GC9A01_BLK_PIN, OUTPUT);
        digitalWrite(GC9A01_BLK_PIN, HIGH);
    }
}
