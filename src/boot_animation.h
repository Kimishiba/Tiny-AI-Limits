#pragma once

#include <Arduino.h>
#include <Arduino_GFX_Library.h>

// Forward references to global hardware instances defined in main.cpp
extern Arduino_GFX *gcGfx;
extern void gcPrintCentered(const char* text, int cx, int y, uint16_t color);

// =========================================================================
// GC9A01 ROUND 240x240 BOOT ANIMATION -- PROCEDURAL SPINNING CIRCUIT RING
// =========================================================================
// Originally 8 pre-rendered 240x240 RGB565 frames of a rotating mascot
// graphic (900KB+ of flash for a few seconds of boot-time animation, which
// only overflowed once the round-only refactor's headroom covered it).
// A continuously rotating dashed ring, drawn with the same per-degree polar
// loop the main HUD already uses for its telemetry arcs, gets a smoother,
// indefinitely-long spin for a few hundred bytes of code and zero bytes of
// image data.

inline void renderGC9A01BootAnimationFrame(int frameIndex, const char* statusText = nullptr, bool wifiOk = false) {
    if (!gcGfx) return;

    const int cx = 120, cy = 120;
    const uint16_t bg      = gcGfx->color565(4, 6, 8);
    const uint16_t colCyan = gcGfx->color565(0, 229, 255);
    const uint16_t colCyanDim = gcGfx->color565(10, 40, 48);
    const uint16_t colGreen = gcGfx->color565(0, 255, 136);
    const uint16_t colGreenDim = gcGfx->color565(6, 48, 34);
    const uint16_t colBezel = gcGfx->color565(31, 35, 48);

    // frameIndex 0 means "paint this fresh": every call site either passes
    // 0 explicitly for a one-shot screen (STARTING SYSTEM, READY FOR SETUP),
    // or calls it once with 0 before starting an animation loop that then
    // increments before its own first call (see connectToWifi()). No static
    // latch needed -- each such call really does want a clean background.
    if (frameIndex == 0) {
        gcGfx->fillScreen(bg);
        gcGfx->drawCircle(cx, cy, 116, colBezel);
        gcGfx->drawCircle(cx, cy, 117, colBezel);
        gcGfx->setTextSize(2);
        gcPrintCentered("TINY AI", cx, cy - 16, gcGfx->color565(255, 255, 255));
        gcGfx->setTextSize(1);
        gcPrintCentered("SCREEN", cx, cy + 4, gcGfx->color565(148, 163, 184));
    }

    uint16_t ringCol = wifiOk ? colGreen : colCyan;
    uint16_t ringDim = wifiOk ? colGreenDim : colCyanDim;

    // Spinning circuit ring: every angle is sampled every frame (unlike a
    // sparse dashed ring, there is no stale pixel to erase), so the "comet"
    // effect comes purely from how far each angle sits behind the moving
    // head, not from tracking what was drawn last frame.
    const int headDeg = (frameIndex * 12) % 360;
    const int tailSpanDeg = 70;
    for (int deg = 0; deg < 360; deg += 2) {
        float rad = deg * 0.0174533f;
        float cosR = cos(rad);
        float sinR = sin(rad);

        int behind = headDeg - deg;
        if (behind < 0) behind += 360;
        bool lit = behind <= tailSpanDeg;
        uint16_t col = lit ? ringCol : ringDim;

        for (int r = 95; r <= 100; r++) {
            gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), col);
        }
        if (lit) {
            gcGfx->drawPixel(cx + (int)(cosR * 90), cy + (int)(sinR * 90), col);
        }
    }

    // Status pill, unchanged from the original design.
    if (statusText && strlen(statusText) > 0) {
        int pillW = 140;
        int pillH = 16;
        int pillY = 222;

        gcGfx->fillRoundRect(cx - pillW / 2, pillY - pillH / 2, pillW, pillH, 3, gcGfx->color565(8, 12, 18));
        gcGfx->drawRoundRect(cx - pillW / 2, pillY - pillH / 2, pillW, pillH, 3, gcGfx->color565(36, 48, 68));

        uint16_t textCol = wifiOk ? colGreen : colCyan;
        gcGfx->setTextSize(1);
        gcPrintCentered(statusText, cx, pillY - 3, textCol);
    }
}
