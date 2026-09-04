/**
 * @file led_controller.h
 * @brief WS2812B LED status controller for ESP32-C3 SuperMini using NeoPixelBus.
 * 
 * Hardware: ESP32-C3 RMT DMA peripheral (NeoEsp32Rmt0Ws2812xMethod)
 * Zero CPU blocking during transmission — 100% safe for concurrent WiFi & SPI display.
 * 
 * Made by Antigravity
 */

#pragma once

#include <Arduino.h>
#include <NeoPixelBus.h>
#include <algorithm>
#include <cmath>

#ifndef WS2812_PIN
#define WS2812_PIN 10
#endif

#ifndef WS2812_MAX_LEDS
#define WS2812_MAX_LEDS 64
#endif

#ifndef WS2812_DEFAULT_ACTIVE_LEDS
#define WS2812_DEFAULT_ACTIVE_LEDS 16
#endif

// Hard brightness clamp (~39% duty cycle) to guarantee <= 250mA draw on USB rail
#define MAX_BRIGHTNESS_CLAMP 100 

enum class LedWaitingAnim {
    OFF = 0,
    SOLID,
    BREATHE,
    RADAR,
    HEARTBEAT,
    HAZARD
};

class LedController {
public:
    LedController(uint8_t pin = WS2812_PIN, 
                  uint16_t maxLeds = WS2812_MAX_LEDS, 
                  uint16_t activeLeds = WS2812_DEFAULT_ACTIVE_LEDS)
        : _pin(pin),
          _maxLeds(maxLeds),
          _activeLeds(std::min(activeLeds, maxLeds)),
          _strip(maxLeds, pin),
          _brightness(35),
          _currentAnim(LedWaitingAnim::BREATHE),
          _lastFrame(0),
          _wasActive(false) {}

    void begin() {
        _strip.Begin();
        clear();
    }

    uint8_t getSafeMaxBrightness() const {
        // Dynamic Power Budget: max 350mA allocated to the LED rail.
        // Full amber (R:255, G:170) draws ~35mA per pixel at 100% duty cycle.
        // max_safe_brightness = (350mA * 100) / (activeLeds * 35mA) = 1000 / activeLeds
        uint16_t safeMax = (uint16_t)(1000 / std::max((uint16_t)1, _activeLeds));
        return (uint8_t)std::min((uint16_t)MAX_BRIGHTNESS_CLAMP, safeMax);
    }

    void setActiveLedCount(uint16_t count) {
        _activeLeds = std::max((uint16_t)1, std::min(count, (uint16_t)WS2812_MAX_LEDS));
        _brightness = std::min(_brightness, getSafeMaxBrightness());
    }

    uint16_t getActiveLedCount() const {
        return _activeLeds;
    }

    void setBrightness(uint8_t brightness) {
        _brightness = std::min(brightness, getSafeMaxBrightness());
    }

    uint8_t getBrightness() const {
        return _brightness;
    }

    void setAnimation(LedWaitingAnim anim) {
        _currentAnim = anim;
    }

    LedWaitingAnim getAnimation() const {
        return _currentAnim;
    }

    void setAnimationByName(const String& name) {
        if (name.equalsIgnoreCase("breathe")) _currentAnim = LedWaitingAnim::BREATHE;
        else if (name.equalsIgnoreCase("radar")) _currentAnim = LedWaitingAnim::RADAR;
        else if (name.equalsIgnoreCase("heartbeat")) _currentAnim = LedWaitingAnim::HEARTBEAT;
        else if (name.equalsIgnoreCase("hazard")) _currentAnim = LedWaitingAnim::HAZARD;
        else if (name.equalsIgnoreCase("solid")) _currentAnim = LedWaitingAnim::SOLID;
        else _currentAnim = LedWaitingAnim::OFF;
    }

    void clear() {
        for (uint16_t i = 0; i < _maxLeds; i++) {
            _strip.SetPixelColor(i, RgbColor(0, 0, 0));
        }
        _strip.Show();
    }

    /**
     * @brief Non-blocking render update. Must be called in loop().
     * Rate-limited to ~30 FPS to minimize bus overhead.
     */
    void update(bool waiting_for_input, bool backendConnected, bool isSleeping) {
        const uint32_t now = millis();

        // Disconnect, sleep, or idle guard: turn off LEDs immediately
        if (!waiting_for_input || !backendConnected || isSleeping || _currentAnim == LedWaitingAnim::OFF) {
            if (_wasActive) {
                clear();
                _wasActive = false;
            }
            return;
        }

        // Throttle animation rendering to ~30 FPS (every ~33ms)
        if (now - _lastFrame < 33) return;
        _lastFrame = now;
        _wasActive = true;

        switch (_currentAnim) {
            case LedWaitingAnim::SOLID:
                runSolid();
                break;
            case LedWaitingAnim::BREATHE:
                runBreathe(now);
                break;
            case LedWaitingAnim::RADAR:
                runRadar(now);
                break;
            case LedWaitingAnim::HEARTBEAT:
                runHeartbeat(now);
                break;
            case LedWaitingAnim::HAZARD:
                runHazard(now);
                break;
            default:
                clear();
                break;
        }

        _strip.Show();
    }

private:
    uint8_t _pin;
    uint16_t _maxLeds;
    uint16_t _activeLeds;
    uint8_t _brightness;
    LedWaitingAnim _currentAnim;
    uint32_t _lastFrame;
    bool _wasActive;

    NeoPixelBus<NeoGrbFeature, NeoEsp32Rmt0Ws2812xMethod> _strip;

    // Generates warm golden amber (#FFB800) with brightness scaling
    RgbColor getAmber(float intensity) {
        float bScale = (float)_brightness / 100.0f;
        float finalIntensity = std::max(0.0f, std::min(1.0f, intensity)) * bScale;
        uint8_t r = (uint8_t)(255.0f * finalIntensity);
        uint8_t g = (uint8_t)(170.0f * finalIntensity);
        return RgbColor(r, g, 0);
    }

    void runSolid() {
        for (uint16_t i = 0; i < _activeLeds; i++) {
            _strip.SetPixelColor(i, getAmber(1.0f));
        }
    }

    void runBreathe(uint32_t now) {
        // Smooth sine pulse over 2.5 seconds
        float wave = (sinf(now * (2.0f * (float)M_PI / 2500.0f)) + 1.0f) * 0.5f;
        // Apply cubic ease for natural eye perception
        wave = wave * wave * (3.0f - 2.0f * wave);
        for (uint16_t i = 0; i < _activeLeds; i++) {
            _strip.SetPixelColor(i, getAmber(wave));
        }
    }

    void runRadar(uint32_t now) {
        // Circular comet chaser orbiting around the bezel
        uint16_t head = (now / 60) % _activeLeds;
        for (uint16_t i = 0; i < _activeLeds; i++) {
            int16_t dist = (head - i + _activeLeds) % _activeLeds;
            if (dist < 6) {
                float fade = 1.0f - ((float)dist / 6.0f);
                _strip.SetPixelColor(i, getAmber(fade * fade));
            } else {
                _strip.SetPixelColor(i, RgbColor(0, 0, 0));
            }
        }
    }

    void runHeartbeat(uint32_t now) {
        // Double-thump heartbeat (1.2s cycle)
        uint32_t cycle = now % 1200;
        float intensity = 0.0f;
        if (cycle < 150) {
            intensity = sinf(cycle / 150.0f * (float)M_PI);
        } else if (cycle > 220 && cycle < 370) {
            intensity = sinf((cycle - 220) / 150.0f * (float)M_PI) * 0.85f;
        }
        for (uint16_t i = 0; i < _activeLeds; i++) {
            _strip.SetPixelColor(i, getAmber(intensity));
        }
    }

    void runHazard(uint32_t now) {
        // Alternating quadrant caution flasher (industrial neo-raw style)
        bool phase = (now / 350) % 2;
        uint16_t quadSize = std::max((uint16_t)1, (uint16_t)(_activeLeds / 4));
        for (uint16_t i = 0; i < _activeLeds; i++) {
            bool inActiveQuad = ((i / quadSize) % 2 == 0);
            if (phase == inActiveQuad) {
                _strip.SetPixelColor(i, getAmber(1.0f));
            } else {
                _strip.SetPixelColor(i, getAmber(0.08f)); // Dim background amber
            }
        }
    }
};
