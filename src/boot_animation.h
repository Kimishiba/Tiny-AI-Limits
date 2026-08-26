#pragma once

#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include <Adafruit_SSD1306.h>
#include "boot_logo_animation.h"

// Forward references to global hardware instances defined in main.cpp
extern Arduino_GFX *gcGfx;
extern Adafruit_SSD1306 oledDisplay;
extern void gcPrintCentered(const char* text, int cx, int y, uint16_t color);

// =========================================================================
// GC9A01 ROUND 240x240 BOOT ANIMATION (CYBER KIMISHIBA + SPINNING CIRCUITS)
// =========================================================================

inline void renderGC9A01BootAnimationFrame(int frameIndex, const char* statusText = nullptr, bool wifiOk = false) {
    if (!gcGfx) return;
    
    int f = frameIndex % BOOT_ANIM_FRAME_COUNT;
    const uint16_t* framePtr = boot_kimishiba_frames[f];
    
    // High-speed SPI burst draw full 240x240 RGB565 frame
    gcGfx->draw16bitRGBBitmap(0, 0, (uint16_t*)framePtr, BOOT_ANIM_FRAME_WIDTH, BOOT_ANIM_FRAME_HEIGHT);
    
    // Optional status text overlay
    if (statusText && strlen(statusText) > 0) {
        int cx = 120;
        int pillW = 140;
        int pillH = 16;
        int pillY = 222;
        
        gcGfx->fillRoundRect(cx - pillW / 2, pillY - pillH / 2, pillW, pillH, 3, gcGfx->color565(8, 12, 18));
        gcGfx->drawRoundRect(cx - pillW / 2, pillY - pillH / 2, pillW, pillH, 3, gcGfx->color565(36, 48, 68));
        
        uint16_t textCol = wifiOk ? gcGfx->color565(0, 255, 136) : gcGfx->color565(0, 229, 255);
        gcGfx->setTextSize(1);
        gcPrintCentered(statusText, cx, pillY - 3, textCol);
    }
}

// =========================================================================
// OLED SSD1306 128x64 BOOT ANIMATION ENGINE
// =========================================================================

inline void renderOLEDBootAnimationFrame(int frameIndex, const char* statusText = nullptr, bool wifiOk = false) {
    oledDisplay.clearDisplay();
    
    int cx = 64, cy = 24;
    
    // Draw 48x48 Cyber Kimishiba Bitmap centered
    oledDisplay.drawBitmap(cx - (OLED_MASCOT_W / 2), 2, oled_kimishiba_mascot, OLED_MASCOT_W, OLED_MASCOT_H, SSD1306_WHITE);
    
    // Spinning orbital dashed circuit ring around the mascot
    float angleDeg = frameIndex * 45.0f;
    for (int i = 0; i < 8; i++) {
        float a = angleDeg + i * 45.0f;
        float r = radians(a);
        int px = cx + (int)(32 * cos(r));
        int py = cy + (int)(22 * sin(r));
        if (px >= 0 && px < 128 && py >= 0 && py < 52) {
            oledDisplay.drawPixel(px, py, SSD1306_WHITE);
            oledDisplay.drawPixel(px + 1, py, SSD1306_WHITE);
        }
    }
    
    // Bottom Status Line
    if (statusText && strlen(statusText) > 0) {
        oledDisplay.setTextSize(1);
        oledDisplay.setTextColor(SSD1306_WHITE);
        int16_t x1, y1;
        uint16_t w, h;
        oledDisplay.getTextBounds(statusText, 0, 0, &x1, &y1, &w, &h);
        oledDisplay.setCursor((128 - w) / 2, 54);
        oledDisplay.print(statusText);
    }
    
    oledDisplay.display();
}
