#pragma once
#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include "Arduino_GC9B72.h"
#include "config.h"

inline Arduino_DataBus *createGC9B72Bus() {
    return new Arduino_ESP32SPI(GC9B72_DC_PIN, GC9B72_CS_PIN, GC9B72_SCK_PIN, GC9B72_MOSI_PIN, GFX_NOT_DEFINED);
}

inline Arduino_GFX *createGC9B72Display(Arduino_DataBus *bus) {
    return new Arduino_GC9B72(bus, GC9B72_RST_PIN, 0 /* rotation */, false /* IPS */, 360, 360);
}

inline void initGC9B72Backlight() {
    // Drive BLK pin HIGH if configured
    if (GC9B72_BLK_PIN >= 0) {
        pinMode(GC9B72_BLK_PIN, OUTPUT);
        digitalWrite(GC9B72_BLK_PIN, HIGH);
    }
    // Also ensure GPIO 0 and GPIO 8 are both driven HIGH solidly (prevents any floating or blinking)
    pinMode(0, OUTPUT);
    digitalWrite(0, HIGH);
    pinMode(8, OUTPUT);
    digitalWrite(8, HIGH);
}
