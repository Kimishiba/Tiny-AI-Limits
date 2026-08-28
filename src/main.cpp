#include <Arduino.h>
#include <SPI.h>
#include <Arduino_GFX_Library.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>
#include <Preferences.h>
#include <ImprovWiFiLibrary.h>
#include <Update.h>
#include "boot_logo.h"

#define FIRMWARE_VERSION "0.5"

DNSServer dnsServer;

// ==========================================
// PIN CONFIGURATION (ESP32-C3 SuperMini)
// ==========================================
// SPI Bus for GC9A01 Circular IPS (240x240)
#define GC9A01_SCK_PIN  4
#define GC9A01_MOSI_PIN 6
#define GC9A01_CS_PIN   5
#define GC9A01_DC_PIN   7
#define GC9A01_RST_PIN  1
#define GC9A01_BLK_PIN  0

// ==========================================
// DISPLAY HARDWARE DEFINITIONS & DRIVERS
// ==========================================
// GC9A01 SPI Hardware Driver (Using reliable Arduino_HWSPI)
Arduino_DataBus *gcBus = new Arduino_HWSPI(GC9A01_DC_PIN, GC9A01_CS_PIN, GC9A01_SCK_PIN, GC9A01_MOSI_PIN, GFX_NOT_DEFINED);
Arduino_GFX *gcGfx = new Arduino_GC9A01(gcBus, GC9A01_RST_PIN, 0 /* rotation */, true /* IPS */);

bool gc9a01Initialized = false;

WebServer server(80);

const unsigned long wifiConnectTimeoutMs = 30000;

// ==========================================
// DATA STRUCTURES
// ==========================================
struct ClaudeLimits {
    long tokensToday = 0;
    int limit = 100;
    int remaining = 100;
    String reset_time = "";
    int reset_in_seconds = -1;
    String reset_str = "";
};
const long claudeHeavyUsageThreshold = 2500000;

struct AntigravityLimits {
    int limit = 200;
    int remaining = 200;
    int used = 0;
    String period = "5h";
    String reset_time = "";
    int reset_in_seconds = -1;
    String reset_str = "";
};

struct WeatherInfo {
    float temp = 23.5;
    int hours_until_rain = -1;
    String location = "DESKTOP";
};

struct SingleAgentInfo {
    String name = "";
    String source = "antigravity"; // antigravity or claude
    String state = "IDLE"; // WAITING, WORKING, COMPLETE, IDLE
    String detail = "";
    uint16_t color = 0x9D37; // default muted slate
};

struct AgentStatus {
    bool waiting_for_input = false;
    bool work_completed = false;
    bool has_active_agents = false;
    int active_agent_count = 0;
    SingleAgentInfo active_agents[4];
    String prompt_text = "APPROVE PLAN";
    String completion_text = "WORK COMPLETE";
};

struct TimeInfo {
    int hours = 12;
    int minutes = 0;
    int seconds = 0;
    String time_str = "12:00:00";
    String date_str = "FRI AUG 21";
};

struct GaugeInfo {
    String id = "claude";
    String label = "CLD";
    String name = "Claude";
    String mode = "standard"; // "standard" | "enterprise"
    String cost_str = "$0.00";
    String curved_text = "";
    int percent = 100;
    uint16_t color = 0x07FF; // Cyan
    String reset_str = "READY";
};

ClaudeLimits claudeData;
AntigravityLimits agData;
GaugeInfo leftGauge;
GaugeInfo rightGauge;
WeatherInfo weatherData;
AgentStatus agentData;
TimeInfo timeData;

long lastKnownTokensToday = -1;
unsigned long lastTokenActivityMs = 0;
const unsigned long sleepIdleThresholdMs = 15UL * 60UL * 1000UL;

unsigned long lastBackendPoll = 0;
unsigned long lastBackendPollSuccessMs = 0;
const unsigned long backendPollInterval = 3000;

bool wifiConnected = false;
bool backendConnected = false;
String backendUrl = "";

// Pairing: which companion app this board belongs to. When pairedHost is set
// the board talks only to that host and never falls back to picking whichever
// companion answers mDNS first, which is how it used to end up showing
// another user's quota data on a shared network.
String pairedHost = "";
uint16_t pairedPort = 0;
String pairedId = "";
// Latch: set the first time a board is ever paired and never cleared. A board
// that has been paired once must not fall back to first-responder discovery
// again, even if its stored host later stops answering -- that fallback is
// what let it pick up another user's companion app.
bool everPaired = false;
Preferences pairPrefs;

// Defined with the data-fetching code below, used by the web server above it.
bool savePairing(const String& host, uint16_t port, const String& id);
bool isValidIPv4(const String& s);
void applyPairedBackendUrl();
String deviceHostname();

Preferences wifiPrefs;
ImprovWiFi improvSerial(&Serial);
bool provisioningMode = false;

// ==========================================
// FACE & BLINKING ANIMATION ENGINE
// ==========================================
enum BlinkPhase {
    EYES_OPEN,
    EYES_CLOSING,
    EYES_CLOSED,
    EYES_OPENING
};

struct FaceEngine {
    BlinkPhase blinkPhase = EYES_OPEN;
    unsigned long phaseStartTime = 0;
    unsigned long nextBlinkTime = 2500;
    float currentOpenPct = 1.0f;

    int targetPupilX = 0;
    int targetPupilY = 0;
    float currentPupilX = 0.0f;
    float currentPupilY = 0.0f;
    unsigned long nextLookTime = 3000;

    bool isDoubleBlink = false;
    int blinkCountInBurst = 0;
};

FaceEngine face;
unsigned long animTicks = 0;

void updateFacePhysics(unsigned long now) {
    animTicks++;

    switch (face.blinkPhase) {
        case EYES_OPEN:
            face.currentOpenPct = 1.0f;
            if (now >= face.nextBlinkTime) {
                face.blinkPhase = EYES_CLOSING;
                face.phaseStartTime = now;
            }
            break;

        case EYES_CLOSING: {
            unsigned long elapsed = now - face.phaseStartTime;
            if (elapsed >= 30) {
                face.blinkPhase = EYES_CLOSED;
                face.phaseStartTime = now;
                face.currentOpenPct = 0.08f;
            } else {
                face.currentOpenPct = 1.0f - (float)elapsed / 30.0f * 0.92f;
            }
            break;
        }

        case EYES_CLOSED: {
            unsigned long elapsed = now - face.phaseStartTime;
            face.currentOpenPct = 0.08f;
            if (elapsed >= 38) {
                face.blinkPhase = EYES_OPENING;
                face.phaseStartTime = now;
            }
            break;
        }

        case EYES_OPENING: {
            unsigned long elapsed = now - face.phaseStartTime;
            if (elapsed >= 38) {
                face.blinkPhase = EYES_OPEN;
                face.currentOpenPct = 1.0f;
                face.blinkCountInBurst++;

                if (!face.isDoubleBlink && random(0, 100) < 25 && face.blinkCountInBurst < 2) {
                    face.isDoubleBlink = true;
                    face.nextBlinkTime = now + random(75, 180);
                } else {
                    face.isDoubleBlink = false;
                    face.blinkCountInBurst = 0;
                    face.nextBlinkTime = now + random(1800, 4000);
                }
            } else {
                face.currentOpenPct = 0.08f + (float)elapsed / 38.0f * 0.92f;
            }
            break;
        }
    }

    if (now >= face.nextLookTime) {
        int r = random(0, 100);
        if (r < 40) {
            face.targetPupilX = 0;
            face.targetPupilY = 0;
        } else if (r < 60) {
            face.targetPupilX = random(-5, 6);
            face.targetPupilY = 0;
        } else if (r < 80) {
            face.targetPupilX = random(-5, 6);
            face.targetPupilY = random(-2, 3);
        } else {
            face.targetPupilX = 0;
            face.targetPupilY = random(-2, 3);
        }
        face.nextLookTime = now + random(1500, 5000);
    }

    face.currentPupilX += (face.targetPupilX - face.currentPupilX) * 0.25f;
    face.currentPupilY += (face.targetPupilY - face.currentPupilY) * 0.25f;
}

// ==========================================
// GC9A01 (240x240 ROUND) C++ RENDERING ENGINE
// ==========================================
#define GC_COLOR_BLACK       0x0000
#define GC_COLOR_WHITE       0xFFFF
#define GC_COLOR_CYAN        0x073F // Electric Cyan (#00E5FF)
#define GC_COLOR_ORANGE      0xFD20 // Safety Orange (#FF7A00)
#define GC_COLOR_AMBER       0xFDC0 // Hazard Amber (#FFB800)
#define GC_COLOR_YELLOW      0xFFE0 // Neon Spark Yellow
#define GC_COLOR_CARD_TOP    0x2126 // Lighter Slate (#222633)
#define GC_COLOR_CARD_BOT    0x10A3 // Deeper Obsidian (#12141C)
#define GC_COLOR_CARD_BORDER 0x2988 // Border Slate (#2B3042)
#define GC_COLOR_SLATE_GRAY  0x9D37 // Muted Slate (#94A3B8)
#define GC_COLOR_ICE_BLUE    0x3DFE // Weather Rain Blue (#38BDF8)
#define GC_COLOR_DARK_AMBER  0x2080
#define GC_COLOR_RED         0xF800 // Safety Red (#FF0000)

// Digit transition flip states
int prevDigits[4] = {-1, -1, -1, -1};
float flipProgress[4] = {1.0f, 1.0f, 1.0f, 1.0f};

// Vector 7-segment / condensed numeral drawing
// High-Resolution Heavy Bold Vector Numerals (28px wide, 54px tall, 8px ultra-bold strokes)
void drawVectorDigit(int x, int y, int digit, uint16_t color) {
    int t = 8;
    int w = 28;
    int h = 54;
    int midY = y + h / 2 - t / 2;
    int botY = y + h - t;
    int rightX = x + w - t;

    switch (digit) {
        case 0:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            gcGfx->fillRoundRect(x, y, t, h, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h, 2, color);
            break;
        case 1:
            gcGfx->fillRoundRect(x + (w - t) / 2, y, t, h, 2, color);
            gcGfx->fillRoundRect(x + (w - t) / 2 - 7, y, 7, t, 1, color);
            gcGfx->fillRoundRect(x + 2, botY, w - 4, t, 1, color);
            break;
        case 2:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, midY, w, t, 2, color);
            gcGfx->fillRoundRect(x, midY, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            break;
        case 3:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h, 2, color);
            gcGfx->fillRoundRect(x + 4, midY, w - 4, t, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            break;
        case 4:
            gcGfx->fillRoundRect(x, y, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, midY, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h, 2, color);
            break;
        case 5:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(x, y, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, midY, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, midY, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            break;
        case 6:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(x, y, t, h, 2, color);
            gcGfx->fillRoundRect(x, midY, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, midY, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            break;
        case 7:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h, 2, color);
            break;
        case 8:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            gcGfx->fillRoundRect(x, midY, w, t, 2, color);
            gcGfx->fillRoundRect(x, y, t, h, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h, 2, color);
            break;
        case 9:
            gcGfx->fillRoundRect(x, y, w, t, 2, color);
            gcGfx->fillRoundRect(x, y, t, h / 2 + 2, 2, color);
            gcGfx->fillRoundRect(x, midY, w, t, 2, color);
            gcGfx->fillRoundRect(rightX, y, t, h, 2, color);
            gcGfx->fillRoundRect(x, botY, w, t, 2, color);
            break;
        default:
            break;
    }
}

void drawVectorDigitHalf(int x, int y, int digit, uint16_t color, bool topHalfOnly, float yScale = 1.0f) {
    int t = 8;
    int w = 28;
    int h = (int)(54 * yScale);
    if (h < 2) return;
    int midY = y + h / 2 - t / 2;
    int botY = y + h - t;
    int rightX = x + w - t;

    auto drawBar = [&](int bx, int by, int bw, int bh, int r) {
        int clipY = y + h / 2;
        int endY = by + bh;
        if (topHalfOnly) {
            if (by >= clipY) return;
            if (endY > clipY) bh = clipY - by;
        } else {
            if (endY <= clipY) return;
            if (by < clipY) {
                bh = endY - clipY;
                by = clipY;
            }
        }
        if (bw <= 0 || bh <= 0) return;
        gcGfx->fillRoundRect(bx, by, bw, bh, r, color);
    };

    switch (digit) {
        case 0:
            drawBar(x, y, w, t, 2);
            drawBar(x, botY, w, t, 2);
            drawBar(x, y, t, h, 2);
            drawBar(rightX, y, t, h, 2);
            break;
        case 1:
            drawBar(x + (w - t) / 2, y, t, h, 2);
            drawBar(x + (w - t) / 2 - 7, y, 7, t, 1);
            drawBar(x + 2, botY, w - 4, t, 1);
            break;
        case 2:
            drawBar(x, y, w, t, 2);
            drawBar(rightX, y, t, h / 2 + 2, 2);
            drawBar(x, midY, w, t, 2);
            drawBar(x, midY, t, h / 2 + 2, 2);
            drawBar(x, botY, w, t, 2);
            break;
        case 3:
            drawBar(x, y, w, t, 2);
            drawBar(rightX, y, t, h, 2);
            drawBar(x + 4, midY, w - 4, t, 2);
            drawBar(x, botY, w, t, 2);
            break;
        case 4:
            drawBar(x, y, t, h / 2 + 2, 2);
            drawBar(x, midY, w, t, 2);
            drawBar(rightX, y, t, h, 2);
            break;
        case 5:
            drawBar(x, y, w, t, 2);
            drawBar(x, y, t, h / 2 + 2, 2);
            drawBar(x, midY, w, t, 2);
            drawBar(rightX, midY, t, h / 2 + 2, 2);
            drawBar(x, botY, w, t, 2);
            break;
        case 6:
            drawBar(x, y, w, t, 2);
            drawBar(x, y, t, h, 2);
            drawBar(x, midY, w, t, 2);
            drawBar(rightX, midY, t, h / 2 + 2, 2);
            drawBar(x, botY, w, t, 2);
            break;
        case 7:
            drawBar(x, y, w, t, 2);
            drawBar(rightX, y, t, h, 2);
            break;
        case 8:
            drawBar(x, y, w, t, 2);
            drawBar(x, botY, w, t, 2);
            drawBar(x, midY, w, t, 2);
            drawBar(x, y, t, h, 2);
            drawBar(rightX, y, t, h, 2);
            break;
        case 9:
            drawBar(x, y, w, t, 2);
            drawBar(x, y, t, h / 2 + 2, 2);
            drawBar(x, midY, w, t, 2);
            drawBar(rightX, y, t, h, 2);
            drawBar(x, botY, w, t, 2);
            break;
        default:
            break;
    }
}

// Helper function for pixel-perfect centered text in Adafruit_GFX / Arduino_GFX
void gcPrintCentered(const char* str, int centerX, int y, uint16_t color) {
    if (!str) return;
    int len = strlen(str);
    int textW = len * 6 - 1;
    gcGfx->setTextColor(color);
    gcGfx->setCursor(centerX - textW / 2, y);
    gcGfx->print(str);
}

void drawGC9A01AnimatedFlipCard(int posX, int posY, int cardW, int cardH, int oldDigit, int newDigit, float progress) {
    int midY = posY + cardH / 2;
    int halfH = cardH / 2;

    uint16_t colTop = gcGfx->color565(34, 38, 51);     // #222633 Slate Top
    uint16_t colBot = gcGfx->color565(18, 20, 28);     // #12141C Obsidian Bot
    uint16_t colBorder = gcGfx->color565(43, 48, 66);  // #2B3042 Card Border
    uint16_t colSeam = gcGfx->color565(52, 58, 78);    // #343A4E Crease Line
    uint16_t colLug = gcGfx->color565(18, 21, 31);     // #12151F Lug Bracket
    uint16_t colPin = gcGfx->color565(138, 150, 171);  // #8A96AB Steel Pin

    int numX = posX + (cardW - 28) / 2;
    int numY = posY + (cardH - 54) / 2;

    if (progress >= 1.0f || oldDigit == newDigit) {
        // Static resting card
        gcGfx->fillRoundRect(posX, posY, cardW, halfH, 4, colTop);
        gcGfx->fillRoundRect(posX, midY, cardW, halfH, 4, colBot);
        gcGfx->drawRoundRect(posX, posY, cardW, cardH, 4, colBorder);

        gcGfx->drawFastHLine(posX + 1, midY - 1, cardW - 2, GC_COLOR_BLACK);
        gcGfx->drawFastHLine(posX + 1, midY, cardW - 2, colSeam);

        drawVectorDigit(numX, numY, newDigit, GC_COLOR_WHITE);
        gcGfx->drawFastHLine(posX + 2, midY, cardW - 4, GC_COLOR_BLACK);
    } else {
        // --- 3D PERSPECTIVE FLIP ANIMATION ---
        // 1. Static Top Background (Shows NEW digit)
        gcGfx->fillRoundRect(posX, posY, cardW, halfH, 4, colTop);
        drawVectorDigitHalf(numX, numY, newDigit, GC_COLOR_WHITE, true);

        // 2. Static Bottom Background (Shows OLD digit)
        gcGfx->fillRoundRect(posX, midY, cardW, halfH, 4, colBot);
        drawVectorDigitHalf(numX, numY, oldDigit, gcGfx->color565(236, 238, 244), false);

        // 3. Falling / Unfolding 3D Flap
        if (progress < 0.5f) {
            // Phase 1: Top half of OLD digit folds downward
            float scale = cos(progress * 3.14159f); // 1.0 -> 0.0
            int flapH = max(1, (int)(halfH * scale));
            int flapY = midY - flapH;

            // Redraw top visible part
            gcGfx->fillRect(posX, posY, cardW, halfH - flapH, colTop);
            drawVectorDigitHalf(numX, numY, newDigit, GC_COLOR_WHITE, true);

            // Draw falling flap
            gcGfx->fillRect(posX, flapY, cardW, flapH, colTop);
            drawVectorDigitHalf(numX, flapY, oldDigit, GC_COLOR_WHITE, true, scale);
        } else {
            // Phase 2: Bottom half of NEW digit unfolds downward
            float scale = -cos(progress * 3.14159f); // 0.0 -> 1.0
            int flapH = max(1, (int)(halfH * scale));

            // Redraw bottom visible part
            gcGfx->fillRect(posX, midY + flapH, cardW, halfH - flapH, colBot);
            drawVectorDigitHalf(numX, numY, oldDigit, gcGfx->color565(236, 238, 244), false);

            // Draw unfolding flap
            gcGfx->fillRect(posX, midY, cardW, flapH, colBot);
            drawVectorDigitHalf(numX, midY - (int)(26 * scale), newDigit, gcGfx->color565(236, 238, 244), false, scale);
        }

        // Draw borders & seam
        gcGfx->drawRoundRect(posX, posY, cardW, cardH, 4, colBorder);
        gcGfx->drawFastHLine(posX + 1, midY - 1, cardW - 2, GC_COLOR_BLACK);
        gcGfx->drawFastHLine(posX + 1, midY, cardW - 2, colSeam);
    }

    // Flank retention hinge brackets (lug width = 4, height = 10, extending 2px outside)
    gcGfx->fillRoundRect(posX - 2, midY - 5, 4, 10, 1, colLug);
    gcGfx->drawRoundRect(posX - 2, midY - 5, 4, 10, 1, colBorder);
    gcGfx->drawFastHLine(posX - 1, midY, 2, colPin);

    gcGfx->fillRoundRect(posX + cardW - 2, midY - 5, 4, 10, 1, colLug);
    gcGfx->drawRoundRect(posX + cardW - 2, midY - 5, 4, 10, 1, colBorder);
    gcGfx->drawFastHLine(posX + cardW - 1, midY, 2, colPin);
}

void drawGC9A01TopConnectionArc(int cx, int cy, int ledState) {
    if (ledState == 0) {
        // Red Disconnected
        uint16_t colRed = gcGfx->color565(239, 68, 68);
        for (int deg = 246; deg <= 294; deg++) {
            float rad = deg * 0.0174533f;
            float cosR = cosf(rad);
            float sinR = sinf(rad);
            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), colRed);
            }
        }
        return;
    }

    if (ledState == 2) {
        // Amber Unpaired / Searching
        uint16_t colAmber = gcGfx->color565(245, 158, 11);
        for (int deg = 246; deg <= 294; deg++) {
            float rad = deg * 0.0174533f;
            float cosR = cosf(rad);
            float sinR = sinf(rad);
            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), colAmber);
            }
        }
        return;
    }

    // ledState == 1: Backend Connected (Concept A: Telemetry Packet Ping)
    bool hasAlert = agentData.waiting_for_input || agentData.work_completed;
    unsigned long elapsed = hasAlert ? 9999 : (millis() - lastBackendPollSuccessMs);
    uint16_t colDim = gcGfx->color565(0, 68, 34);         // #004422 Dim resting emerald
    uint16_t colBright = gcGfx->color565(0, 255, 136);    // #00FF88 Neon emerald
    uint16_t colCore = gcGfx->color565(190, 255, 225);     // White-hot highlight core

    if (elapsed >= 600) {
        // Resting state: Subtle dim emerald green
        for (int deg = 246; deg <= 294; deg++) {
            float rad = deg * 0.0174533f;
            float cosR = cosf(rad);
            float sinR = sinf(rad);
            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), colDim);
            }
        }
    } else {
        // Active Ping Ripple (0..600ms): Expanding wavefront from center 270 deg
        float progress = (float)elapsed / 600.0f;
        float waveFront = progress * 28.0f; // 0 to 28 deg away from center (270)

        for (int deg = 246; deg <= 294; deg++) {
            float rad = deg * 0.0174533f;
            float cosR = cosf(rad);
            float sinR = sinf(rad);
            float dist = fabsf((float)deg - 270.0f);
            float distToWave = fabsf(dist - waveFront);

            uint16_t pixelCol;
            if (distToWave < 3.5f) {
                pixelCol = (distToWave < 1.5f && progress < 0.6f) ? colCore : colBright;
            } else if (dist < waveFront) {
                float tailFade = 1.0f - progress;
                pixelCol = (tailFade > 0.35f) ? colBright : colDim;
            } else {
                pixelCol = colDim;
            }

            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), pixelCol);
            }
        }
    }
}

void drawGC9A01RoundFlipUI() {
    int cx = 120, cy = 120, rScreen = 114;

    uint16_t colCyan = gcGfx->color565(0, 229, 255);       // #00E5FF Claude Cyan
    uint16_t colCyanDim = gcGfx->color565(0, 36, 44);      // Dim background arc
    uint16_t colOrange = gcGfx->color565(255, 122, 0);     // #FF7A00 Antigravity Orange
    uint16_t colOrangeDim = gcGfx->color565(44, 20, 0);    // Dim background arc
    uint16_t colBezel = gcGfx->color565(31, 35, 48);       // #1F2330 Bezel Ring
    uint16_t colRain = gcGfx->color565(56, 189, 248);      // #38BDF8 Sky Blue
    uint16_t colGray = gcGfx->color565(148, 163, 184);     // #94A3B8 Slate Gray

    // 1. Static Bezel or Flashing Static Hazard Arc Dashes (500ms ON / 500ms OFF)
    static bool bezelDrawn = false;
    static bool lastFlashState = false;
    static bool lastWaitingState = false;

    // Component redraw state cache
    static int lastHoursUntilRain = -999;
    static int lastLedState = -1;
    static int lastPulseLevel = -1;
    static int lastClaudePct = -1;
    static int lastAntiPct = -1;
    static String lastLeftCostStr = "";
    static String lastLeftMode = "";
    static float lastTemp = -999.0f;
    static String lastDate = "";
    static bool lastWaiting = false;

    static int oldDigits[4] = {-1, -1, -1, -1};
    static int prevTarget[4] = {-1, -1, -1, -1};
    static float flipProg[4] = {1.0f, 1.0f, 1.0f, 1.0f};

    static bool wasShowingAgents = false;
    static String lastAgentNames[4] = {"", "", "", ""};
    static String lastAgentDetails[4] = {"", "", "", ""};
    static uint16_t lastAgentColors[4] = {0, 0, 0, 0};
    static int lastAgentRowCount = -1;
    static int lastAgentDotPulses[4] = {-1, -1, -1, -1};

    uint16_t colHazardAmber = gcGfx->color565(255, 184, 0); // #FFB800 Kinetic Amber
    uint16_t colEmerald = gcGfx->color565(0, 255, 136);     // #00FF88 Neon Emerald

    if (agentData.waiting_for_input || agentData.work_completed) {
        bezelDrawn = false;
        bool flashOn = (millis() / 500) % 2 == 0;

        if (flashOn != lastFlashState || !lastWaitingState) {
            lastFlashState = flashOn;
            lastWaitingState = true;

            if (flashOn) {
                uint16_t ringColor = agentData.waiting_for_input ? colHazardAmber : colEmerald;
                // ON Phase: Draw 6 static arc dashes (radii 115..118)
                for (int i = 0; i < 6; i++) {
                    float dashStart = i * 60.0f;
                    float dashEnd = dashStart + 25.0f;

                    for (float d = dashStart; d <= dashEnd; d += 0.4f) {
                        float rad = d * 0.0174532925f;
                        float cosR = cosf(rad);
                        float sinR = sinf(rad);

                        for (int r = 115; r <= 118; r++) {
                            gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), ringColor);
                        }
                    }
                }
            } else {
                // OFF Phase: High-density 0.2-degree polar wipe (0.41px arc step) across radii 112..120
                for (int r = 112; r <= 120; r++) {
                    gcGfx->drawCircle(cx, cy, r, GC_COLOR_BLACK);
                }
                for (float deg = 0.0f; deg < 360.0f; deg += 0.2f) {
                    float rad = deg * 0.0174532925f;
                    float cosR = cosf(rad);
                    float sinR = sinf(rad);
                    for (int r = 112; r <= 120; r++) {
                        gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), GC_COLOR_BLACK);
                    }
                }

                // Draw base gunmetal bezel track (#1F2330) on radii 116, 117
                gcGfx->drawCircle(cx, cy, 116, colBezel);
                gcGfx->drawCircle(cx, cy, 117, colBezel);
            }
        }
    } else {
        if (lastWaitingState || !bezelDrawn) {
            lastWaitingState = false;
            bezelDrawn = true;
            lastFlashState = false;

            // Full-Screen Hardware Wipe on Alert Exit: Erases 100% of framebuffer pixels to BLACK
            gcGfx->fillScreen(GC_COLOR_BLACK);

            // Reset cache state variables to force 100% fresh re-render of all display components
            lastHoursUntilRain = -999;
            lastLedState = -1;
            lastPulseLevel = -1;
            lastClaudePct = -1;
            lastAntiPct = -1;
            lastTemp = -999.0f;
            lastDate = "";
            wasShowingAgents = false;
            lastAgentRowCount = -1;
            for (int i = 0; i < 4; i++) {
                oldDigits[i] = -1;
                lastAgentNames[i] = "";
                lastAgentDetails[i] = "";
                lastAgentColors[i] = 0;
                lastAgentDotPulses[i] = -1;
            }

            // Re-render static 2px gunmetal bezel ring (r = 116, 117)
            gcGfx->drawCircle(cx, cy, 116, colBezel);
            gcGfx->drawCircle(cx, cy, 117, colBezel);
        }
    }

    // 2. Top Crown: Backend Connection Status Indicator Arc & Weather / Rain Indicator
    // 0 = no backend (red), 1 = paired (solid green / telemetry ping), 2 = connected but unpaired (amber)
    int curLedState = !backendConnected ? 0 : (pairedHost.length() > 0 ? 1 : 2);
    bool hasAlert = agentData.waiting_for_input || agentData.work_completed;
    bool isPinging = (curLedState == 1) && !hasAlert && ((millis() - lastBackendPollSuccessMs) < 600);
    static bool wasPinging = false;

    if (curLedState != lastLedState || isPinging || wasPinging) {
        lastLedState = curLedState;
        wasPinging = isPinging;
        drawGC9A01TopConnectionArc(cx, cy, curLedState);
    }

    if (weatherData.hours_until_rain != lastHoursUntilRain) {
        lastHoursUntilRain = weatherData.hours_until_rain;

        // Clear weather text area (Centered at cx=120, y=cy-93=27)
        gcGfx->fillRect(cx - 50, cy - 98, 100, 12, GC_COLOR_BLACK);

        // Weather text
        gcGfx->setTextSize(1);
        if (weatherData.hours_until_rain == -1) {
            gcPrintCentered("NO RAIN", cx, cy - 93, colGray);
        } else if (weatherData.hours_until_rain == 0) {
            gcPrintCentered("RAIN NOW", cx, cy - 93, colRain);
        } else {
            char rainBuf[20];
            sprintf(rainBuf, "RAIN IN %dh", weatherData.hours_until_rain);
            gcPrintCentered(rainBuf, cx, cy - 93, (weatherData.hours_until_rain <= 3) ? colRain : GC_COLOR_WHITE);
        }
    }

    // 3. Solid Continuous Dual Radial Arcs & Micro-HUD Badges (Redraw on change)
    int leftPct = leftGauge.percent;
    int rightPct = rightGauge.percent;

    if (leftPct != lastClaudePct || rightPct != lastAntiPct || leftGauge.cost_str != lastLeftCostStr || leftGauge.mode != lastLeftMode) {
        lastClaudePct = leftPct;
        lastAntiPct = rightPct;
        lastLeftCostStr = leftGauge.cost_str;
        lastLeftMode = leftGauge.mode;

        uint16_t leftCol = leftGauge.color;
        uint16_t leftColDim = gcGfx->color565(14, 40, 50);

        // Left Arc (126 deg at bottom to 234 deg at top)
        for (int deg = 126; deg <= 234; deg++) {
            float rad = deg * 0.0174533f;
            float cosR = cos(rad);
            float sinR = sin(rad);

            bool active = (deg <= 126 + (leftPct * 108 / 100));
            uint16_t mainCol = active ? leftCol : leftColDim;
            uint16_t thinCol = active ? leftCol : leftColDim;

            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), mainCol);
            }
            for (int r = 94; r <= 95; r++) {
                gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), thinCol);
            }
        }

        uint16_t rightCol = rightGauge.color;
        uint16_t rightColDim = gcGfx->color565(50, 25, 10);

        // Right Arc (54 deg at bottom to -54 deg at top)
        for (int deg = 54; deg >= -54; deg--) {
            float rad = deg * 0.0174533f;
            float cosR = cos(rad);
            float sinR = sin(rad);

            bool active = (deg >= 54 - (rightPct * 108 / 100));
            uint16_t mainCol = active ? rightCol : rightColDim;
            uint16_t thinCol = active ? rightCol : rightColDim;

            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), mainCol);
            }
            for (int r = 94; r <= 95; r++) {
                gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), thinCol);
            }
        }

        // Micro-HUD Badges (Centered in 40px corridors with 5px padding, ZERO overlap)
        // Left Corridor: x=27 to 66 -> Centered at x=47, y=120
        gcGfx->fillRoundRect(31, 108, 32, 24, 3, gcGfx->color565(14, 20, 28));
        gcGfx->drawRoundRect(31, 108, 32, 24, 3, leftCol);
        if (leftGauge.mode == "enterprise" && leftGauge.cost_str.length() > 0) {
            gcPrintCentered(leftGauge.cost_str.c_str(), 47, 111, leftCol);
            gcPrintCentered("SPENT", 47, 121, leftCol);
        } else {
            gcPrintCentered(leftGauge.label.c_str(), 47, 111, leftCol);
            char leftPctStr[8];
            sprintf(leftPctStr, "%d%%", leftPct);
            gcPrintCentered(leftPctStr, 47, 121, leftCol);
        }

        // Right Corridor: x=174 to 213 -> Centered at x=193, y=120
        gcGfx->fillRoundRect(177, 108, 32, 24, 3, gcGfx->color565(28, 18, 10));
        gcGfx->drawRoundRect(177, 108, 32, 24, 3, rightCol);
        gcPrintCentered(rightGauge.label.c_str(), 193, 111, rightCol);
        char rightPctStr[8];
        sprintf(rightPctStr, "%d%%", rightPct);
        gcPrintCentered(rightPctStr, 193, 121, rightCol);
    }

    // 4. Center Screen: 2x2 Split-Flap Clock OR Multi-Agent Status Dashboard
    bool showAgents = agentData.has_active_agents && (agentData.active_agent_count > 0);

    if (showAgents) {
        bool forceRedrawAll = false;
        if (!wasShowingAgents) {
            // First transition into agent view: clear central safe corridor
            gcGfx->fillRect(68, 44, 104, 152, GC_COLOR_BLACK);
            wasShowingAgents = true;
            forceRedrawAll = true;
            for (int j = 0; j < 4; j++) {
                lastAgentNames[j] = "";
                lastAgentDetails[j] = "";
                lastAgentColors[j] = 0;
                lastAgentDotPulses[j] = -1;
                oldDigits[j] = -1;
                prevTarget[j] = -1;
            }
        }

        // Draw Multi-Agent Status Dashboard inside the 102px x 140px safe corridor
        int startY = cy - 65; // y = 55
        int visibleRows = min(agentData.active_agent_count, 3);

        if (visibleRows != lastAgentRowCount) {
            forceRedrawAll = true;
            lastAgentRowCount = visibleRows;
            // Clear entire area if row count changed
            gcGfx->fillRect(68, 44, 104, 152, GC_COLOR_BLACK);
            for (int j = 0; j < 4; j++) {
                lastAgentNames[j] = "";
                lastAgentDetails[j] = "";
                lastAgentColors[j] = 0;
                lastAgentDotPulses[j] = -1;
            }
        }

        for (int i = 0; i < visibleRows; i++) {
            int rowY = startY + (i * 44);
            SingleAgentInfo &ag = agentData.active_agents[i];

            // Determine Provider Brand Color (Orange for AGY, Teal for Claude)
            bool isAGY = (ag.source.equalsIgnoreCase("antigravity") || ag.source.indexOf("anti") >= 0 || ag.name.startsWith("AGY"));
            uint16_t brandCol = isAGY ? colOrange : colCyan;
            uint16_t cardBorderCol = isAGY ? gcGfx->color565(160, 80, 0) : gcGfx->color565(0, 140, 160);
            uint16_t cardBgCol = isAGY ? gcGfx->color565(36, 20, 10) : gcGfx->color565(14, 26, 36);

            bool textChanged = forceRedrawAll ||
                (lastAgentNames[i] != ag.name) ||
                (lastAgentDetails[i] != ag.detail) ||
                (lastAgentColors[i] != ag.color);

            if (textChanged) {
                lastAgentNames[i] = ag.name;
                lastAgentDetails[i] = ag.detail;
                lastAgentColors[i] = ag.color;

                // Card container background
                gcGfx->fillRoundRect(cx - 49, rowY, 98, 40, 4, cardBgCol);
                gcGfx->drawRoundRect(cx - 49, rowY, 98, 40, 4, cardBorderCol);

                // Left brand accent bar (Orange for AGY, Teal for Claude)
                gcGfx->fillRoundRect(cx - 49, rowY, 3, 40, 2, brandCol);

                // Row 1: Agent Label
                gcGfx->setTextSize(1);
                gcGfx->setTextColor(brandCol, cardBgCol);
                gcGfx->setCursor(cx - 42, rowY + 6);
                gcGfx->print(ag.name);

                // Row 2: Detail / Action
                gcGfx->setTextColor(ag.color, cardBgCol);
                gcGfx->setCursor(cx - 42, rowY + 22);
                String det = ag.detail;
                if (det.length() > 14) det = det.substring(0, 13) + ".";
                gcGfx->print(det);
            }

            // Pulsating Status Badge Dot (Phase-shifted sine wave per agent row)
            float pulse = (sinf((millis() * 0.006f) + (i * 1.3f)) + 1.0f) * 0.5f; // 0.0 .. 1.0
            int pulseLevel = (int)(pulse * 3.99f); // 0, 1, 2, 3

            if (textChanged || pulseLevel != lastAgentDotPulses[i]) {
                lastAgentDotPulses[i] = pulseLevel;

                // Clear tiny dot sub-rectangle (14x14 px) inside card
                gcGfx->fillRect(cx + 33, rowY + 3, 14, 14, cardBgCol);

                int dotR = (pulseLevel >= 2) ? 3 : 2;
                if (pulseLevel == 3) {
                    // Soft outer glow halo
                    uint8_t r = min(255, (int)(((ag.color >> 11) & 0x1F) * 8) + 20);
                    uint8_t g = min(255, (int)(((ag.color >> 5) & 0x3F) * 4) + 20);
                    uint8_t b = min(255, (int)((ag.color & 0x1F) * 8) + 20);
                    gcGfx->drawCircle(cx + 40, rowY + 10, 4, gcGfx->color565(r / 2, g / 2, b / 2));
                }
                gcGfx->fillCircle(cx + 40, rowY + 10, dotR, ag.color);
            }
        }
    } else {
        if (wasShowingAgents) {
            // Clear center corridor when switching back to clock
            gcGfx->fillRect(68, 44, 104, 152, GC_COLOR_BLACK);
            wasShowingAgents = false;
            lastAgentRowCount = -1;
            for (int i = 0; i < 4; i++) {
                oldDigits[i] = -1;
                prevTarget[i] = -1;
                lastAgentNames[i] = "";
                lastAgentDetails[i] = "";
                lastAgentColors[i] = 0;
                lastAgentDotPulses[i] = -1;
            }
        }

        // 2x2 Split-Flap Clock Matrix with 3D Folding Animation
        int cardW = 48, cardH = 72, gap = 6;
        int x1 = cx - cardW - gap / 2;
        int x2 = cx + gap / 2;
        int yTop = cy - cardH - gap / 2;
        int yBot = cy + gap / 2;

        int safeHours = constrain(timeData.hours, 0, 23);
        int safeMinutes = constrain(timeData.minutes, 0, 59);

        int dH1 = safeHours / 10;
        int dH2 = safeHours % 10;
        int dM1 = safeMinutes / 10;
        int dM2 = safeMinutes % 10;

        int targetDigits[4] = {dH1, dH2, dM1, dM2};

        for (int i = 0; i < 4; i++) {
            if (prevTarget[i] != -1 && prevTarget[i] != targetDigits[i]) {
                oldDigits[i] = prevTarget[i];
                flipProg[i] = 0.0f; // Start 3D flip animation!
            }
            prevTarget[i] = targetDigits[i];

            if (flipProg[i] < 1.0f) {
                flipProg[i] += 0.10f; // ~10 frames @ 30 FPS = ~300ms flip
                if (flipProg[i] > 1.0f) flipProg[i] = 1.0f;
            }

            // Draw card when animating or on first boot
            if (flipProg[i] < 1.0f || oldDigits[i] == -1) {
                if (oldDigits[i] == -1) oldDigits[i] = targetDigits[i];
                int px = (i % 2 == 0) ? x1 : x2;
                int py = (i < 2) ? yTop : yBot;
                drawGC9A01AnimatedFlipCard(px, py, cardW, cardH, oldDigits[i], targetDigits[i], flipProg[i]);
            }
        }
    }

    // 5. Stacked Bottom Sub-HUD (Redraw on change)
    if (agentData.waiting_for_input) {
        bool alertBlink = (millis() / 500) % 2 == 0;
        static bool lastBlink = false;
        if (alertBlink != lastBlink || !lastWaiting) {
            lastBlink = alertBlink;
            lastWaiting = true;
            gcGfx->fillRect(cx - 50, cy + 74, 100, 32, GC_COLOR_BLACK);
            gcGfx->setTextSize(1);
            gcPrintCentered("AGENT ALERT", cx, cy + 80, alertBlink ? GC_COLOR_AMBER : 0x4200);
            gcPrintCentered(agentData.prompt_text.c_str(), cx, cy + 94, GC_COLOR_WHITE);
        }
    } else if (agentData.work_completed) {
        bool compBlink = (millis() / 500) % 2 == 0;
        static bool lastCompBlink = false;
        if (compBlink != lastCompBlink || !lastWaiting) {
            lastCompBlink = compBlink;
            lastWaiting = true;
            gcGfx->fillRect(cx - 50, cy + 74, 100, 32, GC_COLOR_BLACK);
            gcGfx->setTextSize(1);
            gcPrintCentered("TASK COMPLETE", cx, cy + 80, compBlink ? colEmerald : gcGfx->color565(5, 150, 105));
            gcPrintCentered(agentData.completion_text.c_str(), cx, cy + 94, GC_COLOR_WHITE);
        }
    } else {
        static String lastLeftResetStr = "";
        static String lastRightResetStr = "";

        if (lastWaiting || leftGauge.reset_str != lastLeftResetStr || rightGauge.reset_str != lastRightResetStr) {
            lastWaiting = false;
            lastLeftResetStr = leftGauge.reset_str;
            lastRightResetStr = rightGauge.reset_str;

            // Clear bottom sub-HUD area (Centered at cx=120, y=cy+74..cy+106)
            gcGfx->fillRect(cx - 55, cy + 74, 110, 32, GC_COLOR_BLACK);
            gcGfx->setTextSize(1);

            // Line 1: Left Gauge Reset Countdown
            String leftStr = leftGauge.label + ": " + (leftGauge.reset_str.length() > 0 ? leftGauge.reset_str : "READY");
            gcPrintCentered(leftStr.c_str(), cx, cy + 80, leftGauge.color);

            // Line 2: Right Gauge Reset Countdown
            String rightStr = rightGauge.label + ": " + (rightGauge.reset_str.length() > 0 ? rightGauge.reset_str : "READY");
            gcPrintCentered(rightStr.c_str(), cx, cy + 94, rightGauge.color);
        }
    }
}

void drawGC9A01RoundFaceUI() {
    int cx = 120, cy = 120, rScreen = 114;

    uint16_t colCyan = gcGfx->color565(0, 229, 255);       // #00E5FF Qbit Cyan
    uint16_t colBezel = gcGfx->color565(31, 35, 48);       // #1F2330 Bezel Ring
    uint16_t colRain = gcGfx->color565(56, 189, 248);      // #38BDF8 Sky Blue
    uint16_t colGray = gcGfx->color565(148, 163, 184);     // #94A3B8 Slate Gray
    uint16_t colAmber = gcGfx->color565(255, 184, 0);      // #FFB800 Kinetic Amber

    // 1. Static Bezel Ring
    static bool bezelDrawn = false;
    if (!bezelDrawn) {
        bezelDrawn = true;
        gcGfx->drawCircle(cx, cy, 116, colBezel);
        gcGfx->drawCircle(cx, cy, 117, colBezel);
    }

    // 2. Top Crown: Connection Status Arc & Rain Indicator
    // Amber means connected but unpaired -- see STATUS_UNPAIRED_NOTE.
    int curFaceLedState = !backendConnected ? 0 : (pairedHost.length() > 0 ? 1 : 2);
    drawGC9A01TopConnectionArc(cx, cy, curFaceLedState);

    char rainStr[24];
    if (weatherData.hours_until_rain < 0) {
        strcpy(rainStr, "NO RAIN");
    } else if (weatherData.hours_until_rain == 0) {
        strcpy(rainStr, "RAIN NOW");
    } else {
        sprintf(rainStr, "RAIN IN %dh", weatherData.hours_until_rain);
    }
    gcGfx->setTextSize(1);
    gcPrintCentered(rainStr, cx, cy - 93, colRain);

    // 3. Central Dual Capsule Pill Eyes (Expressive Qbit Face - Enriched Bold Scale)
    int eyeW = 54;
    int eyeH = 80;
    int leftEyeX = cx - 52;
    int rightEyeX = cx + 52;
    int eyeY = cy;

    float openPct = face.currentOpenPct;
    int curH = (int)(eyeH * openPct);
    if (curH < 6) curH = 6;
    int cornerR = min(26, curH / 2);

    static int lastCurH = -1;
    static float lastPupilX = -999.0f, lastPupilY = -999.0f;

    if (curH != lastCurH || abs(face.currentPupilX - lastPupilX) > 0.1f || abs(face.currentPupilY - lastPupilY) > 0.1f) {
        // Redraw eye bounding regions to black
        gcGfx->fillRect(leftEyeX - eyeW / 2 - 2, eyeY - eyeH / 2 - 2, eyeW + 4, eyeH + 4, GC_COLOR_BLACK);
        gcGfx->fillRect(rightEyeX - eyeW / 2 - 2, eyeY - eyeH / 2 - 2, eyeW + 4, eyeH + 4, GC_COLOR_BLACK);

        // Fill capsule pill eyes
        gcGfx->fillRoundRect(leftEyeX - eyeW / 2, eyeY - curH / 2, eyeW, curH, cornerR, colCyan);
        gcGfx->fillRoundRect(rightEyeX - eyeW / 2, eyeY - curH / 2, eyeW, curH, cornerR, colCyan);

        // Inner Pupil Iris Highlights (Radius 7px positioned at (-7, -16) relative to eye center)
        if (openPct > 0.3f) {
            int pX = (int)face.currentPupilX;
            int pY = (int)face.currentPupilY;
            gcGfx->fillCircle(leftEyeX - 7 + pX, eyeY - 16 + pY, 7, GC_COLOR_WHITE);
            gcGfx->fillCircle(rightEyeX - 7 + pX, eyeY - 16 + pY, 7, GC_COLOR_WHITE);
        }

        lastCurH = curH;
        lastPupilX = face.currentPupilX;
        lastPupilY = face.currentPupilY;
    }

    // 4. Bottom Sub-HUD (Date & Weather / Agent Alert / Work Complete)
    uint16_t colEmerald = gcGfx->color565(0, 255, 136);
    if (agentData.waiting_for_input) {
        bool alertBlink = (millis() / 500) % 2 == 0;
        gcGfx->fillRect(cx - 60, cy + 74, 120, 32, GC_COLOR_BLACK);
        gcGfx->setTextSize(1);
        gcPrintCentered("AGENT ALERT", cx, cy + 80, alertBlink ? colAmber : gcGfx->color565(153, 110, 0));
        gcPrintCentered(agentData.prompt_text.c_str(), cx, cy + 94, GC_COLOR_WHITE);
    } else if (agentData.work_completed) {
        bool compBlink = (millis() / 500) % 2 == 0;
        gcGfx->fillRect(cx - 60, cy + 74, 120, 32, GC_COLOR_BLACK);
        gcGfx->setTextSize(1);
        gcPrintCentered("TASK COMPLETE", cx, cy + 80, compBlink ? colEmerald : gcGfx->color565(5, 150, 105));
        gcPrintCentered(agentData.completion_text.c_str(), cx, cy + 94, GC_COLOR_WHITE);
    } else {
        gcGfx->fillRect(cx - 60, cy + 74, 120, 32, GC_COLOR_BLACK);
        gcGfx->setTextSize(1);
        gcPrintCentered(timeData.date_str.c_str(), cx, cy + 80, colGray);
        char tempBuf[16];
        sprintf(tempBuf, "%.1f C", weatherData.temp);
        gcPrintCentered(tempBuf, cx, cy + 94, GC_COLOR_WHITE);
    }
}

// ==========================================
// HARDWARE AUTO-DETECTION & INITIALIZATION
// ==========================================
void initActiveDisplay() {
    // GC9A01 Round Screen Init
    pinMode(GC9A01_RST_PIN, OUTPUT);
    digitalWrite(GC9A01_RST_PIN, HIGH);
    delay(10);
    digitalWrite(GC9A01_RST_PIN, LOW);
    delay(20);
    digitalWrite(GC9A01_RST_PIN, HIGH);
    delay(100);

    if (gcGfx->begin(40000000)) {
        gc9a01Initialized = true;
        gcGfx->draw16bitRGBBitmap(0, 0, boot_logo_cyber, BOOT_LOGO_WIDTH, BOOT_LOGO_HEIGHT);
        Serial.println("[Display] GC9A01 Round IPS initialized with boot logo");
    } else {
        Serial.println("[Display] Failed to initialize GC9A01 display!");
    }
}

bool connectToWifi(const char* ssid, const char* password);
void onWifiConnected();

// ==========================================
// HTTP SERVER (Companion App Screen Provisioning)
// ==========================================
void setupWebServer() {
    // The setup page is served from the companion app's origin
    // (http://localhost:5000), so pairing calls to the board are
    // cross-origin and are preflighted.
    server.enableCORS(true);

    // Pair over HTTP as well as over serial. Improv provisioning carries only
    // an SSID and password -- the protocol has no room for a host address --
    // so a board set up that way can only be paired once it is on the network.
    // This also lets a user re-pair without plugging the board back in.
    server.on("/api/pair", HTTP_OPTIONS, []() {
        server.send(204);
    });

    server.on("/api/pair", HTTP_POST, []() {
        StaticJsonDocument<256> doc;
        if (!server.hasArg("plain") || deserializeJson(doc, server.arg("plain"))) {
            server.send(400, "application/json", "{\"error\":\"invalid_json\"}");
            return;
        }

        // Default to the caller's address: the setup page runs in a browser on
        // the same machine as the companion app, so it is the right host.
        String host = doc["host"] | "";
        if (host.length() == 0) host = server.client().remoteIP().toString();
        long port = doc["port"] | 0;
        String id = doc["pair_id"] | "";

        if (!isValidIPv4(host) || port <= 0 || port > 65535) {
            server.send(400, "application/json", "{\"error\":\"invalid_host_or_port\"}");
            return;
        }

        if (!savePairing(host, (uint16_t)port, id)) {
            server.send(400, "application/json", "{\"error\":\"missing_pair_id\"}");
            return;
        }
        applyPairedBackendUrl();

        StaticJsonDocument<256> out;
        out["status"] = "ok";
        out["paired_host"] = pairedHost;
        out["paired_port"] = pairedPort;
        out["pair_id"] = pairedId;
        String body;
        serializeJson(out, body);
        server.send(200, "application/json", body);
    });

    server.on("/api/pair", HTTP_GET, []() {
        StaticJsonDocument<256> doc;
        doc["paired"] = pairedHost.length() > 0;
        doc["paired_host"] = pairedHost;
        doc["paired_port"] = pairedPort;
        doc["pair_id"] = pairedId;
        doc["hostname"] = deviceHostname();
        String out;
        serializeJson(doc, out);
        server.send(200, "application/json", out);
    });

    server.begin();
    Serial.println("[HTTP] Provisioning Web Server started on port 80");
}

// ==========================================
// DATA FETCHING & MDNS
// ==========================================
unsigned long lastMdnsResolve = 0;
const unsigned long mdnsResolveCooldownMs = 10000;

// A paired board keeps using its stored host across transient failures. Only
// after this many consecutive failures does it consider that the companion
// may have moved (DHCP lease change) and try to re-locate it.
const int maxBackendFailures = 5;
int consecutiveBackendFailures = 0;

void loadPairing() {
    pairPrefs.begin("pair", true);
    pairedHost = pairPrefs.getString("host", "");
    pairedPort = (uint16_t)pairPrefs.getUShort("port", 0);
    pairedId = pairPrefs.getString("id", "");
    everPaired = pairPrefs.getBool("ever", false);
    pairPrefs.end();
    if (pairedHost.length() > 0) {
        Serial.printf("[Pair] Paired with %s:%u (id: %s)\n",
                      pairedHost.c_str(), pairedPort, pairedId.c_str());
    } else if (everPaired) {
        Serial.println("[Pair] Previously paired but no host stored; will not auto-discover");
    } else {
        Serial.println("[Pair] No pairing stored; will discover via mDNS");
    }
}

// Callers must supply a non-empty id: without one the board cannot re-find its
// companion after a DHCP change, and a half-paired board is a state we would
// rather not have to reason about.
bool savePairing(const String& host, uint16_t port, const String& id) {
    if (id.length() == 0) {
        Serial.println("[Pair] Rejecting pairing with empty pair_id");
        return false;
    }
    pairPrefs.begin("pair", false);
    pairPrefs.putString("host", host);
    pairPrefs.putUShort("port", port);
    pairPrefs.putString("id", id);
    pairPrefs.putBool("ever", true);
    pairPrefs.end();
    pairedHost = host;
    pairedPort = port;
    pairedId = id;
    everPaired = true;
    Serial.printf("[Pair] Stored pairing %s:%u (id: %s)\n", host.c_str(), port, id.c_str());
    return true;
}

// Accepts only a dotted quad, so a malformed provisioning payload can't put
// garbage into NVS that the board would then retry forever.
bool isValidIPv4(const String& s) {
    IPAddress probe;
    return probe.fromString(s);
}

// The companion serves /data only to boards that prove which companion they
// belong to (#38): without pair_id, any board on the LAN could read the
// owner's email, token volume and location.
void applyPairedBackendUrl() {
    backendUrl = "http://" + pairedHost + ":" + String(pairedPort) + "/data?pair_id=" + pairedId;
}

// Confirm a candidate host actually serves us before we commit it to NVS.
// MDNS.IP() returns only the first IPv4 a host advertises, and a machine on
// Wi-Fi plus Ethernet/VPN/Docker may advertise an address the board cannot
// route to. Probing is cheaper than exposing the full address list.
bool probeBackend(const String& host, uint16_t port) {
    HTTPClient probe;
    // Same pair_id the real poll will use, so the probe fails on a companion
    // that would reject us rather than reporting it reachable.
    probe.begin("http://" + host + ":" + String(port) + "/data?pair_id=" + pairedId);
    probe.setTimeout(2000);
    int code = probe.GET();
    probe.end();
    return code == HTTP_CODE_OK;
}

// Re-locate our own companion after its IP changed, matching on pair_id from
// the mDNS TXT records. Never falls back to "first responder": with no match
// we keep the old URL and keep retrying, because guessing is what leaked
// another user's data in the first place.
bool repairViaTxtRecords() {
    if (pairedId.length() == 0) return false;

    int n = MDNS.queryService("tinyscreen", "tcp");
    Serial.printf("[Pair] Re-locating companion %s across %d service(s)\n", pairedId.c_str(), n);
    for (int i = 0; i < n; i++) {
        String sPairId = "";
        if (MDNS.hasTxt(i, "pair_id")) {
            sPairId = MDNS.txt(i, "pair_id");
        }
        if (sPairId != pairedId && n > 1) continue;

        IPAddress ip = MDNS.IP(i);
        uint16_t port = MDNS.port(i);
        if (ip == IPAddress() || !probeBackend(ip.toString(), port)) {
            Serial.printf("[Pair] Candidate %s:%u is unreachable; trying next\n",
                          ip.toString().c_str(), port);
            continue;
        }

        savePairing(ip.toString(), port, pairedId);
        applyPairedBackendUrl();
        Serial.printf("[Pair] Re-paired to %s:%u\n", ip.toString().c_str(), port);
        return true;
    }
    Serial.println("[Pair] No companion matched our pair_id; keeping stored host");
    return false;
}

bool resolveBackendUrl() {
    // Some networks (enterprise/guest WiFi in particular) filter multicast
    // traffic, which silently breaks mDNS while normal unicast HTTP still
    // works fine. A manually configured backend URL (set via the BACKEND:
    // serial command) takes priority and skips mDNS entirely in that case.
    // It outranks pairing too: it is an explicit instruction from the user.
    Preferences backendPrefs;
    backendPrefs.begin("backend", true);
    String manualUrl = backendPrefs.getString("url", "");
    backendPrefs.end();
    if (manualUrl.length() > 0) {
        backendUrl = manualUrl;
        // An updated companion serves /data only to boards that identify
        // themselves, so carry pair_id when we have one -- otherwise a
        // manual URL would be refused with 403.
        if (pairedId.length() > 0 && manualUrl.indexOf("pair_id=") == -1) {
            backendUrl += (manualUrl.indexOf('?') >= 0) ? "&" : "?";
            backendUrl += "pair_id=" + pairedId;
        }
        Serial.printf("[Backend] Using manually configured URL: %s\n", backendUrl.c_str());
        return true;
    }

    // Paired boards never run discovery -- that is the whole point.
    if (pairedHost.length() > 0) {
        applyPairedBackendUrl();
        return true;
    }

    // Paired once, host since lost: still refuse to guess. Re-pair via the
    // setup page rather than risk adopting someone else's companion.
    if (everPaired) {
        Serial.println("[Pair] Previously paired; refusing mDNS fallback. Re-pair from the setup page.");
        backendUrl = "";
        return false;
    }

    int n = MDNS.queryService("tinyscreen", "tcp");
    if (n > 0) {
        IPAddress ip = MDNS.IP(0);
        uint16_t port = MDNS.port(0);
        backendUrl = "http://" + ip.toString() + ":" + String(port) + "/data";
        Serial.printf("[mDNS] Found companion app at %s:%d\n", ip.toString().c_str(), port);
        return true;
    }
    Serial.println("[mDNS] No companion app found (_tinyscreen._tcp)");
    backendUrl = "";
    return false;
}

// ==========================================
// OVER-THE-AIR (OTA) FIRMWARE UPDATE
// ==========================================
void drawOTAProgressScreen(int percent, const char* statusMsg, const char* verStr) {
    if (!gc9a01Initialized) return;
    int cx = 120, cy = 120;

    // Outer circle
    if (percent <= 0) {
        gcGfx->fillScreen(GC_COLOR_BLACK);
        gcGfx->drawCircle(cx, cy, 118, GC_COLOR_AMBER);
    }

    // Center card background
    gcGfx->fillRect(cx - 90, cy - 60, 180, 120, GC_COLOR_BLACK);

    // Dynamic progress arc
    if (percent >= 0) {
        float maxDeg = (constrain(percent, 0, 100) / 100.0f) * 360.0f;
        for (float deg = 0; deg <= maxDeg; deg += 1.5f) {
            float rad = (deg - 90.0f) * 0.0174532925f;
            float cosR = cosf(rad);
            float sinR = sinf(rad);
            for (int r = 112; r <= 116; r++) {
                gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), GC_COLOR_AMBER);
            }
        }
    }

    // Title
    gcGfx->setTextSize(1);
    gcPrintCentered("FIRMWARE OTA", cx, cy - 40, GC_COLOR_CYAN);

    // Version jump tag
    if (verStr && strlen(verStr) > 0) {
        String verDisplay = "v" + String(FIRMWARE_VERSION) + " -> v" + String(verStr);
        gcPrintCentered(verDisplay.c_str(), cx, cy - 25, GC_COLOR_SLATE_GRAY);
    }

    // Main Percentage or Error
    gcGfx->setTextSize(2);
    if (percent >= 0) {
        String pctStr = String(percent) + "%";
        gcPrintCentered(pctStr.c_str(), cx, cy + 2, GC_COLOR_WHITE);
    } else {
        gcPrintCentered("ERROR", cx, cy + 2, GC_COLOR_RED);
    }

    // Sub-status
    gcGfx->setTextSize(1);
    gcPrintCentered(statusMsg, cx, cy + 28, GC_COLOR_AMBER);
    gcPrintCentered("DO NOT UNPLUG", cx, cy + 45, gcGfx->color565(150, 150, 150));
}

bool performOTAUpdate(const String& pathOrUrl, const char* newVersion) {
    String fullUrl;
    if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
        fullUrl = pathOrUrl;
    } else {
        int idx = backendUrl.indexOf("/data");
        String baseUrl = (idx != -1) ? backendUrl.substring(0, idx) : backendUrl;
        fullUrl = baseUrl + pathOrUrl;
    }

    Serial.printf("[OTA] Starting update from: %s (target ver: %s)\n", fullUrl.c_str(), newVersion);
    drawOTAProgressScreen(0, "CONNECTING...", newVersion);

    HTTPClient http;
    WiFiClient client;
    http.begin(client, fullUrl);
    http.setTimeout(15000);

    int httpCode = http.GET();
    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("[OTA] HTTP GET failed: %d\n", httpCode);
        drawOTAProgressScreen(-1, "HTTP ERROR", newVersion);
        delay(3000);
        http.end();
        return false;
    }

    int contentLength = http.getSize();
    Serial.printf("[OTA] Image size: %d bytes\n", contentLength);
    if (contentLength <= 0) {
        Serial.println("[OTA] Invalid content length");
        drawOTAProgressScreen(-1, "INVALID SIZE", newVersion);
        delay(3000);
        http.end();
        return false;
    }

    if (!Update.begin(contentLength, U_FLASH)) {
        Serial.printf("[OTA] Cannot begin update: error %d\n", Update.getError());
        drawOTAProgressScreen(-1, "PARTITION FULL", newVersion);
        delay(3000);
        http.end();
        return false;
    }

    WiFiClient *stream = http.getStreamPtr();
    size_t written = 0;
    uint8_t buff[1024];
    int lastPercent = -1;
    unsigned long lastActivity = millis();

    while (http.connected() && (written < (size_t)contentLength)) {
        size_t availableBytes = stream->available();
        if (availableBytes > 0) {
            int readBytes = stream->readBytes(buff, min(availableBytes, sizeof(buff)));
            if (readBytes > 0) {
                Update.write(buff, readBytes);
                written += readBytes;
                lastActivity = millis();
                int percent = (int)((written * 100) / contentLength);
                if (percent != lastPercent) {
                    lastPercent = percent;
                    drawOTAProgressScreen(percent, "DOWNLOADING...", newVersion);
                }
            }
        } else {
            if (millis() - lastActivity > 10000) {
                Serial.println("[OTA] Download timeout");
                drawOTAProgressScreen(-1, "TIMEOUT", newVersion);
                delay(3000);
                Update.abort();
                http.end();
                return false;
            }
            delay(5);
        }
    }

    http.end();

    if (written < (size_t)contentLength) {
        Serial.printf("[OTA] Incomplete write: %u / %d\n", written, contentLength);
        drawOTAProgressScreen(-1, "INCOMPLETE", newVersion);
        delay(3000);
        Update.abort();
        return false;
    }

    if (Update.end(true)) {
        Serial.println("[OTA] Update successful! Rebooting...");
        drawOTAProgressScreen(100, "REBOOTING...", newVersion);
        delay(1500);
        ESP.restart();
        return true;
    } else {
        Serial.printf("[OTA] Update.end() failed: error %d\n", Update.getError());
        drawOTAProgressScreen(-1, "FLASH ERROR", newVersion);
        delay(3000);
        return false;
    }
}

uint16_t parseHexColor565(const String& hexStr, uint16_t fallback) {
    if (hexStr.length() == 0) return fallback;
    const char* s = hexStr.c_str();
    if (hexStr.startsWith("0x")) s += 2;
    else if (hexStr.startsWith("#")) s += 1;
    long val = strtol(s, NULL, 16);
    if (hexStr.length() > 6 || val > 0xFFFF) {
        uint8_t r = (val >> 16) & 0xFF;
        uint8_t g = (val >> 8) & 0xFF;
        uint8_t b = val & 0xFF;
        return gcGfx->color565(r, g, b);
    }
    return (uint16_t)val;
}

void fetchBackendData() {
    if (WiFi.status() != WL_CONNECTED) {
        wifiConnected = false;
        return;
    }
    wifiConnected = true;

    if (backendUrl.length() == 0) {
        if (millis() - lastMdnsResolve > mdnsResolveCooldownMs) {
            lastMdnsResolve = millis();
            resolveBackendUrl();
        }
        return;
    }

    // A paired board that has failed repeatedly may have had its companion
    // move to a new IP. Try to find it again by pair_id, rate-limited so a
    // genuinely offline companion doesn't mean an mDNS query every cycle.
    if (consecutiveBackendFailures >= maxBackendFailures &&
        pairedHost.length() > 0 &&
        millis() - lastMdnsResolve > mdnsResolveCooldownMs) {
        lastMdnsResolve = millis();
        if (repairViaTxtRecords()) {
            consecutiveBackendFailures = 0;
        }
    }

    HTTPClient http;
    http.begin(backendUrl);
    http.setTimeout(3500);

    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
        backendConnected = true;
        lastBackendPollSuccessMs = millis();
        consecutiveBackendFailures = 0;
        String payload = http.getString();
        StaticJsonDocument<4096> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
            if (doc.containsKey("claude")) {
                claudeData.tokensToday = doc["claude"]["tokens_today"] | 0;
                if (doc["claude"].containsKey("limit")) claudeData.limit = doc["claude"]["limit"] | 100;
                if (doc["claude"].containsKey("remaining")) claudeData.remaining = doc["claude"]["remaining"] | 100;
                claudeData.reset_time = doc["claude"]["reset_time"] | "";
                claudeData.reset_in_seconds = doc["claude"]["reset_in_seconds"] | -1;
                claudeData.reset_str = doc["claude"]["reset_str"] | "";
            }
            if (doc.containsKey("antigravity")) {
                agData.limit = doc["antigravity"]["limit"] | 200;
                agData.remaining = doc["antigravity"]["remaining"] | 200;
                agData.used = doc["antigravity"]["used"] | 0;
                agData.period = doc["antigravity"]["period"] | "5h";
                agData.reset_time = doc["antigravity"]["reset_time"] | "";
                agData.reset_in_seconds = doc["antigravity"]["reset_in_seconds"] | -1;
                agData.reset_str = doc["antigravity"]["reset_str"] | "";
            }
            if (doc.containsKey("left_gauge")) {
                leftGauge.id = doc["left_gauge"]["id"] | "claude";
                leftGauge.label = doc["left_gauge"]["label"] | "CLD";
                leftGauge.name = doc["left_gauge"]["name"] | "Claude";
                leftGauge.mode = doc["left_gauge"]["mode"] | "standard";
                leftGauge.cost_str = doc["left_gauge"]["cost_str"] | "$0.00";
                leftGauge.curved_text = doc["left_gauge"]["curved_text"] | "";
                leftGauge.percent = doc["left_gauge"]["percent"] | 100;
                leftGauge.reset_str = doc["left_gauge"]["reset_str"] | "READY";
                String colStr = doc["left_gauge"]["color"] | "0x00E5FF";
                leftGauge.color = parseHexColor565(colStr, gcGfx->color565(0, 229, 255));
            } else {
                leftGauge.label = "CLD";
                leftGauge.mode = "standard";
                leftGauge.cost_str = "$0.00";
                leftGauge.percent = 100;
                leftGauge.color = gcGfx->color565(0, 229, 255);
                leftGauge.reset_str = claudeData.reset_str;
            }
            if (doc.containsKey("right_gauge")) {
                rightGauge.id = doc["right_gauge"]["id"] | "antigravity";
                rightGauge.label = doc["right_gauge"]["label"] | "AGY";
                rightGauge.name = doc["right_gauge"]["name"] | "Antigravity";
                rightGauge.percent = doc["right_gauge"]["percent"] | 100;
                rightGauge.reset_str = doc["right_gauge"]["reset_str"] | "5h";
                String colStr = doc["right_gauge"]["color"] | "0xFF9100";
                rightGauge.color = parseHexColor565(colStr, gcGfx->color565(255, 145, 0));
            } else {
                rightGauge.label = "AGY";
                rightGauge.percent = (agData.limit > 0) ? (agData.remaining * 100 / agData.limit) : 100;
                rightGauge.color = gcGfx->color565(255, 122, 0);
                rightGauge.reset_str = agData.reset_str;
            }
            if (doc.containsKey("weather")) {
                weatherData.temp = doc["weather"]["temp"] | 23.5;
                weatherData.hours_until_rain = doc["weather"]["hours_until_rain"] | -1;
                weatherData.location = doc["weather"]["location"] | "DESKTOP";
                if (doc["weather"].containsKey("date_string")) {
                    timeData.date_str = doc["weather"]["date_string"].as<String>();
                }
            }
            if (doc.containsKey("agent")) {
                AgentStatus tempAgent;
                tempAgent.waiting_for_input = doc["agent"]["waiting_for_input"] | false;
                tempAgent.work_completed = doc["agent"]["work_completed"] | (doc["agent"]["completion_flash"] | false);
                tempAgent.prompt_text = doc["agent"]["prompt_text"] | "APPROVE PLAN";
                tempAgent.completion_text = doc["agent"]["completion_text"] | "WORK COMPLETE";
                tempAgent.has_active_agents = doc["agent"]["has_active_agents"] | (tempAgent.waiting_for_input || tempAgent.work_completed);
                
                JsonArray arr = doc["agent"]["active_agents"].as<JsonArray>();
                if (!arr.isNull()) {
                    int count = 0;
                    for (JsonObject obj : arr) {
                        if (count >= 4) break;
                        tempAgent.active_agents[count].name = obj["name"] | "Agent";
                        tempAgent.active_agents[count].source = obj["source"] | "antigravity";
                        tempAgent.active_agents[count].state = obj["state"] | "IDLE";
                        tempAgent.active_agents[count].detail = obj["detail"] | "";
                        String colStr = obj["color"] | "#94A3B8";
                        if (colStr.equalsIgnoreCase("#FFB800")) tempAgent.active_agents[count].color = GC_COLOR_AMBER;
                        else if (colStr.equalsIgnoreCase("#00FF88")) tempAgent.active_agents[count].color = gcGfx->color565(0, 255, 136);
                        else if (colStr.equalsIgnoreCase("#00E5FF")) tempAgent.active_agents[count].color = GC_COLOR_CYAN;
                        else if (colStr.equalsIgnoreCase("#FF7A00")) tempAgent.active_agents[count].color = GC_COLOR_ORANGE;
                        else tempAgent.active_agents[count].color = GC_COLOR_SLATE_GRAY;
                        count++;
                    }
                    tempAgent.active_agent_count = count;
                } else {
                    tempAgent.active_agent_count = 0;
                }
                agentData = tempAgent;
            }
            if (doc.containsKey("time")) {
                timeData.hours = constrain((int)(doc["time"]["hours"] | 12), 0, 23);
                timeData.minutes = constrain((int)(doc["time"]["minutes"] | 0), 0, 59);
                timeData.seconds = constrain((int)(doc["time"]["seconds"] | 0), 0, 59);
                timeData.time_str = doc["time"]["time_string"] | "12:00:00";
                if (doc["time"].containsKey("date_string")) {
                    timeData.date_str = doc["time"]["date_string"].as<String>();
                }
            }
            if (doc.containsKey("ota")) {
                JsonObject otaObj = doc["ota"];
                bool otaTrigger = otaObj["trigger"] | false;
                const char* otaVer = otaObj["version"] | "";
                String otaPath = otaObj["url"] | "/firmware/latest.bin";
                if (otaTrigger && otaPath.length() > 0) {
                    performOTAUpdate(otaPath, otaVer);
                }
            }
        }
    } else {
        Serial.printf("[Backend] GET %s failed: %s (%d)\n", backendUrl.c_str(), http.errorToString(httpCode).c_str(), httpCode);
        if (consecutiveBackendFailures < maxBackendFailures) consecutiveBackendFailures++;
        if (consecutiveBackendFailures >= 4) {
            backendConnected = false;
        }
        if (!everPaired && pairedHost.length() == 0 &&
            consecutiveBackendFailures >= maxBackendFailures) {
            backendUrl = "";
        }
    }
    http.end();
}

// ==========================================
// WIFI CONNECTION
// ==========================================
bool connectToWifi(const char* ssid, const char* password) {
    WiFi.disconnect(true, true);
    delay(150);
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.setSleep(false);
    WiFi.setTxPower(WIFI_POWER_19_5dBm);

    wifi_country_t country = {"NL", 1, 13, 20, WIFI_COUNTRY_POLICY_AUTO};
    esp_wifi_set_country(&country);
    delay(50);

    Serial.printf("\n[WiFi] Connecting to '%s' (TX: 19.5dBm)...\n", ssid);
    WiFi.begin(ssid, password);

    unsigned long connectStart = millis();
    int attempts = 0;
    // Poll every 50ms (not 500ms): Improv WiFi's browser-side handshake sends a
    // single request-current-state call with no retry, and a serial connection
    // opening resets this board -- so if the timing lands inside this loop with
    // only 500ms granularity, the handshake can time out before we ever service it.
    while (WiFi.status() != WL_CONNECTED && millis() - connectStart < wifiConnectTimeoutMs) {
        delay(50);
        attempts++;
        if (attempts % 40 == 0) {
            Serial.printf("  [WiFi] In progress... status: %d\n", WiFi.status());
        }
        // handleSerial() consumes exactly one byte per call -- drain everything
        // waiting so a full Improv packet doesn't take multiple ticks to parse.
        while (Serial.available()) {
            improvSerial.handleSerial();
        }
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("[WiFi] SUCCESS! Local IP: %s\n", WiFi.localIP().toString().c_str());
        onWifiConnected();
        return true;
    }

    Serial.printf("[WiFi] Connection to '%s' failed (status: %d).\n", ssid, WiFi.status());
    WiFi.disconnect(true, false);
    delay(50);
    return false;
}

// Per-board mDNS name, e.g. "tinyscreen-F030". Without this every board
// claims "tinyscreen.local" and they collide as soon as two share a subnet.
//
// Reads the efuse directly so STATUS can report the hostname on a board that
// has never connected to WiFi. esp_efuse_mac_get_default() packs the six MAC
// bytes into a little-endian u64, so byte N is (mac >> 8*N); the suffix as
// printed on the board is bytes 4 then 5. Note the ordering: extracting a
// u16 in one shot yields those two bytes reversed.
String deviceHostname() {
    uint64_t mac = ESP.getEfuseMac();
    char hostStr[24];
    snprintf(hostStr, sizeof(hostStr), "tinyscreen-%02X%02X",
             (uint8_t)((mac >> 32) & 0xFF), (uint8_t)((mac >> 40) & 0xFF));
    return String(hostStr);
}

void onWifiConnected() {
    wifiConnected = true;
    provisioningMode = false;
    Serial.printf("[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());

    String hostname = deviceHostname();
    if (!MDNS.begin(hostname.c_str())) {
        Serial.println("[mDNS] Error starting responder");
    } else {
        Serial.printf("[mDNS] Responder started as %s.local\n", hostname.c_str());
    }

    setupWebServer();
    resolveBackendUrl();
    lastMdnsResolve = millis();
    fetchBackendData();
}

void onImprovWiFiConnectedCb(const char* ssid, const char* password) {
    wifiPrefs.begin("wifi", false);
    wifiPrefs.putString("ssid", ssid);
    wifiPrefs.putString("password", password);
    wifiPrefs.end();

    onWifiConnected();
}

void onImprovWiFiErrorCb(ImprovTypes::Error err) {
    Serial.printf("[Improv] WiFi Error code: %d\n", err);
}

static String serialBuffer = "";

// The provisioning line is tab-delimited, so the setup page percent-escapes
// any tab, newline or '%' inside the SSID/password rather than letting them
// shift the later fields.
String percentDecode(const String& in) {
    String out;
    out.reserve(in.length());
    for (unsigned int i = 0; i < in.length(); i++) {
        if (in[i] == '%' && i + 2 < in.length()) {
            char hex[3] = { in[i + 1], in[i + 2], 0 };
            char* end;
            long v = strtol(hex, &end, 16);
            if (*end == 0) {
                out += (char)v;
                i += 2;
                continue;
            }
        }
        out += in[i];
    }
    return out;
}

void handleSerialCommunication() {
    while (Serial.available()) {
        int peekByte = Serial.peek();
        if (peekByte == 'I' && serialBuffer.length() == 0) {
            // handleSerial() consumes exactly one byte per call -- drain everything
            // waiting so a full Improv packet doesn't take multiple loop() ticks to parse.
            while (Serial.available()) {
                improvSerial.handleSerial();
            }
            return;
        }

        char c = (char)Serial.read();
        if (c == '\r') continue;
        if (c == '\n') {
            String line = serialBuffer;
            serialBuffer = "";
            line.trim();
            if (line.length() == 0) continue;

            if (line == "SCAN") {
                WiFi.mode(WIFI_STA);
                int16_t n = WiFi.scanNetworks();
                Serial.print("SCAN_RESULT:[");
                if (n > 0) {
                    for (int i = 0; i < n; ++i) {
                        if (i > 0) Serial.print(",");
                        Serial.printf("{\"ssid\":\"%s\",\"rssi\":%d,\"secure\":%s}",
                            WiFi.SSID(i).c_str(), WiFi.RSSI(i), (WiFi.encryptionType(i) == WIFI_AUTH_OPEN) ? "false" : "true");
                    }
                }
                Serial.println("]");
                WiFi.scanDelete();
            } else if (line.startsWith("WIFI:")) {
                // WIFI:<ssid>\t<pass>[\t<host>\t<port>[\t<pair_id>]]
                // Two fields is the legacy form and still works, so a cached
                // copy of the old setup page keeps provisioning boards.
                String creds = line.substring(5);
                String fields[5];
                int fieldCount = 0;
                int start = 0;
                while (fieldCount < 5) {
                    int sep = creds.indexOf('\t', start);
                    // Legacy setup pages sent a comma when there was no tab.
                    if (sep == -1 && fieldCount == 0) sep = creds.indexOf(',', start);
                    if (sep == -1) { fields[fieldCount++] = creds.substring(start); break; }
                    fields[fieldCount++] = creds.substring(start, sep);
                    start = sep + 1;
                }

                if (fieldCount >= 2) {
                    // Trim before decoding: whitespace the user meant to keep
                    // arrives percent-escaped and so survives.
                    fields[0].trim();
                    fields[1].trim();
                    String ssid = percentDecode(fields[0]);
                    String pass = percentDecode(fields[1]);

                    if (fieldCount >= 4) {
                        String host = fields[2]; host.trim();
                        String portStr = fields[3]; portStr.trim();
                        String id = (fieldCount >= 5) ? fields[4] : "";
                        id.trim();
                        long port = portStr.toInt();
                        if (isValidIPv4(host) && port > 0 && port <= 65535) {
                            savePairing(host, (uint16_t)port, id);
                        } else {
                            Serial.printf("[Pair] Ignoring invalid host/port '%s:%s'\n",
                                          host.c_str(), portStr.c_str());
                        }
                    } else if (fieldCount == 3) {
                        Serial.println("[Pair] Ignoring incomplete pairing fields");
                    }

                    Serial.printf("[WiFi] Connecting to '%s'...\n", ssid.c_str());
                    if (connectToWifi(ssid.c_str(), pass.c_str())) {
                        wifiPrefs.begin("wifi", false);
                        wifiPrefs.putString("ssid", ssid);
                        wifiPrefs.putString("password", pass);
                        wifiPrefs.end();
                        Serial.printf("CONNECTED:%s\n", WiFi.localIP().toString().c_str());
                    } else {
                        Serial.println("ERROR:CONNECTION_FAILED");
                    }
                }
            } else if (line == "STATUS") {
                Serial.printf("STATUS:{\"connected\":%s,\"ip\":\"%s\",\"screen\":\"%s\",\"hostname\":\"%s\",\"paired_host\":\"%s\",\"paired_port\":%u,\"pair_id\":\"%s\",\"backend_connected\":%s,\"backend_url\":\"%s\",\"failures\":%d}\n",
                    wifiConnected ? "true" : "false",
                    wifiConnected ? WiFi.localIP().toString().c_str() : "",
                    "round",
                    deviceHostname().c_str(),
                    pairedHost.c_str(), pairedPort, pairedId.c_str(),
                    backendConnected ? "true" : "false",
                    backendUrl.c_str(),
                    consecutiveBackendFailures);
            } else if (line.startsWith("BACKEND:")) {
                // Manual override for when mDNS discovery of the backend fails
                // (e.g. multicast filtered by an enterprise/guest network).
                String value = line.substring(8);
                value.trim();
                int sep = value.indexOf(':');
                String host = (sep != -1) ? value.substring(0, sep) : value;
                uint16_t port = (sep != -1) ? (uint16_t)value.substring(sep + 1).toInt() : 5000;
                host.trim();
                if (host.length() > 0) {
                    String url = "http://" + host + ":" + String(port) + "/data";
                    Preferences backendPrefs;
                    backendPrefs.begin("backend", false);
                    backendPrefs.putString("url", url);
                    backendPrefs.end();
                    backendConnected = false;
                    // Go through resolveBackendUrl() rather than assigning
                    // directly, so the manual URL picks up pair_id the same
                    // way it does on boot -- otherwise the very next poll is
                    // refused with 403 by an updated companion.
                    resolveBackendUrl();
                    Serial.printf("BACKEND_SET:%s\n", backendUrl.c_str());
                } else {
                    Serial.println("ERROR:INVALID_BACKEND");
                }
            } else if (line == "CLEAR_BACKEND") {
                Preferences backendPrefs;
                backendPrefs.begin("backend", false);
                backendPrefs.clear();
                backendPrefs.end();
                backendUrl = "";
                // Fall back to whatever pairing says, rather than leaving the
                // board with no target until the next poll cycle.
                resolveBackendUrl();
                Serial.println("[Backend] Manual override cleared.");
            }
        } else {
            serialBuffer += c;
            // Raised from 256: a provisioning line now carries host, port and
            // pair_id on top of the credentials, and percent-escaping can
            // triple an SSID or password in the worst case.
            if (serialBuffer.length() > 512) {
                serialBuffer = "";
            }
        }
    }
}

// ==========================================
// SETUP
// ==========================================
void setup() {
    Serial.begin(115200);

    // Register Improv WiFi as early as physically possible, before the slower
    // display/WiFi init below. Opening a serial connection resets this board,
    // and the browser-side Improv handshake sends a single request with no
    // retry -- if we don't start servicing it until after display + WiFi setup
    // (~700ms+ of blocking work), it can time out before we ever see it.
    improvSerial.setDeviceInfo(
        ImprovTypes::ChipFamily::CF_ESP32_C3,
        "TinyScreenFirmware", "0.4.0", "Tiny AI Screen", ""
    );
    improvSerial.onImprovError(onImprovWiFiErrorCb);
    improvSerial.onImprovConnected(onImprovWiFiConnectedCb);
    improvSerial.setCustomConnectWiFi(connectToWifi);
    // handleSerial() consumes exactly one byte per call -- drain everything
    // waiting each tick so a full Improv packet doesn't take multiple ticks to parse.
    for (int i = 0; i < 4; i++) {
        while (Serial.available()) {
            improvSerial.handleSerial();
        }
        delay(50);
    }

    loadPairing();

    // 1. Initialize Display
    initActiveDisplay();

    // 2. Wi-Fi Configuration for ESP32-C3
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    wifi_country_t country = {"NL", 1, 13, 20, WIFI_COUNTRY_POLICY_AUTO};
    esp_wifi_set_country(&country);
    delay(50);

    WiFi.onEvent([](WiFiEvent_t event, WiFiEventInfo_t info) {
        if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
            Serial.printf("[WiFi] Disconnected! Reason code: %d\n", info.wifi_sta_disconnected.reason);
        } else if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
            Serial.printf("[WiFi] Got IP: %s\n", IPAddress(info.got_ip.ip_info.ip.addr).toString().c_str());
        }
    });

    WiFi.disconnect(true, true);
    delay(50);

    // 3. Connect Stored Wi-Fi
    wifiPrefs.begin("wifi", false);
    String storedSsid = wifiPrefs.getString("ssid", "");
    String storedPassword = wifiPrefs.getString("password", "");

    bool connected = false;
    if (storedSsid.length() > 0) {
        connected = connectToWifi(storedSsid.c_str(), storedPassword.c_str());
    }

    if (connected) {
        onWifiConnected();
    } else {
        wifiConnected = false;
        provisioningMode = true;
        Serial.println("[WiFi] Ready for setup over USB Serial or Improv Wi-Fi.");
    }

    // 4. Launch Asynchronous FreeRTOS Background Worker for Backend HTTP Polling
    xTaskCreate(
        [](void *pvParameters) {
            for (;;) {
                if (WiFi.status() == WL_CONNECTED && !provisioningMode) {
                    wifiConnected = true;
                    fetchBackendData();
                }
                vTaskDelay(pdMS_TO_TICKS(backendPollInterval));
            }
        },
        "backendTask",
        8192,
        NULL,
        1,
        NULL
    );

}

// ==========================================
// MAIN LOOP
// ==========================================
unsigned long lastFrameTime = 0;
const unsigned long frameIntervalMs = 33; // ~30 FPS

void loop() {
    unsigned long now = millis();

    // 1. Unified Serial Listener (Direct & Improv) & Web Server
    handleSerialCommunication();
    if (wifiConnected) {
        server.handleClient();
    }

    // 2. Render Active Display (Uninterrupted ~30 FPS rendering)
    if (now - lastFrameTime >= frameIntervalMs) {
        lastFrameTime = now;

        // GC9A01 Round IPS HUD (Render full cyberpunk flip clock HUD)
        // Keeps the blink/gaze state live for drawGC9A01RoundFaceUI(), which
        // is wired up but not currently selected by the loop.
        updateFacePhysics(now);
        drawGC9A01RoundFlipUI();
    }

    // 3. Auto-reconnect Wi-Fi
    static unsigned long lastWiFiCheck = 0;
    if (now - lastWiFiCheck >= 5000) {
        lastWiFiCheck = now;
        if (WiFi.status() != WL_CONNECTED) {
            wifiConnected = false;
            if (!provisioningMode) {
                WiFi.reconnect();
            } else {
                // A failed first-boot attempt leaves us here permanently otherwise --
                // RF flakiness (auth/handshake timeouts) means a retry often succeeds.
                wifiPrefs.begin("wifi", false);
                String storedSsid = wifiPrefs.getString("ssid", "");
                String storedPassword = wifiPrefs.getString("password", "");
                wifiPrefs.end();
                if (storedSsid.length() > 0 && connectToWifi(storedSsid.c_str(), storedPassword.c_str())) {
                    provisioningMode = false;
                    onWifiConnected();
                }
            }
        } else {
            wifiConnected = true;
        }
    }

    // 4. Offline Demo Clock Tick
    static unsigned long lastSecondTick = 0;
    if (now - lastSecondTick >= 1000) {
        lastSecondTick = now;
        timeData.seconds++;
        if (timeData.seconds >= 60) {
            timeData.seconds = 0;
            timeData.minutes++;
            if (timeData.minutes >= 60) {
                timeData.minutes = 0;
                timeData.hours = (timeData.hours + 1) % 24;
            }
        }
    }
}
