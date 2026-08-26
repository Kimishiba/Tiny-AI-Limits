#pragma once

#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include "boot_logo_animation.h"

// Forward references to global hardware instances defined in main.cpp
extern Arduino_GFX *gcGfx;
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
