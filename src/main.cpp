#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
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

DNSServer dnsServer;

// ==========================================
// PIN CONFIGURATION (ESP32-C3 SuperMini)
// ==========================================
// 1. I2C Bus for SSD1306 / SH1106 OLED (128x64)
#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9

// 2. SPI Bus for GC9A01 Circular IPS (240x240)
#define GC9A01_SCK_PIN  4
#define GC9A01_MOSI_PIN 6
#define GC9A01_CS_PIN   5
#define GC9A01_DC_PIN   7
#define GC9A01_RST_PIN  1
#define GC9A01_BLK_PIN  0

// ==========================================
// DISPLAY HARDWARE DEFINITIONS & DRIVERS
// ==========================================
#define OLED_SCREEN_WIDTH  128
#define OLED_SCREEN_HEIGHT 64
#define OLED_RESET         -1

Adafruit_SSD1306 oledDisplay(OLED_SCREEN_WIDTH, OLED_SCREEN_HEIGHT, &Wire, OLED_RESET);

// GC9A01 SPI Hardware Driver (Using reliable Arduino_HWSPI)
Arduino_DataBus *gcBus = new Arduino_HWSPI(GC9A01_DC_PIN, GC9A01_CS_PIN, GC9A01_SCK_PIN, GC9A01_MOSI_PIN, GFX_NOT_DEFINED);
Arduino_GFX *gcGfx = new Arduino_GC9A01(gcBus, GC9A01_RST_PIN, 0 /* rotation */, true /* IPS */);

// ==========================================
// SCREEN PROVISIONING & HARDWARE SELECTION
// ==========================================
enum HardwareScreenType {
    SCREEN_AUTO = 0,
    SCREEN_GC9A01_ROUND = 1,
    SCREEN_OLED_128X64 = 2
};

HardwareScreenType configuredScreenType = SCREEN_AUTO;
HardwareScreenType activeScreenType = SCREEN_GC9A01_ROUND;
bool oledFound = false;
uint8_t oledAddress = 0x3C;
bool gc9a01Initialized = false;

Preferences screenPrefs;
WebServer server(80);

const unsigned long wifiConnectTimeoutMs = 30000;

// ==========================================
// DATA STRUCTURES
// ==========================================
struct ClaudeLimits {
    long tokensToday = 0;
    int limit = 100;
    int remaining = 100;
};
const long claudeHeavyUsageThreshold = 2500000;

struct AntigravityLimits {
    int limit = 200;
    int remaining = 200;
    int used = 0;
    String period = "5h";
};

struct WeatherInfo {
    float temp = 23.5;
    int hours_until_rain = -1;
    String location = "DESKTOP";
};

struct AgentStatus {
    bool waiting_for_input = false;
    String prompt_text = "APPROVE PLAN";
};

struct TimeInfo {
    int hours = 12;
    int minutes = 0;
    int seconds = 0;
    String time_str = "12:00:00";
    String date_str = "FRI AUG 21";
};

ClaudeLimits claudeData;
AntigravityLimits agData;
WeatherInfo weatherData;
AgentStatus agentData;
TimeInfo timeData;

long lastKnownTokensToday = -1;
unsigned long lastTokenActivityMs = 0;
const unsigned long sleepIdleThresholdMs = 15UL * 60UL * 1000UL;

unsigned long lastBackendPoll = 0;
const unsigned long backendPollInterval = 3000;

unsigned long lastScreenSwitch = 0;
const unsigned long screenSwitchInterval = 8000;

enum OLEDMode {
    SCREEN_FACE = 0,
    SCREEN_SPLIT_HUD = 1,
    SCREEN_LIMITS = 2,
    SCREEN_CLOCK_WEATHER = 3,
    SCREEN_AGENT_ALERT = 4
};

OLEDMode currentOLEDMode = SCREEN_FACE;
bool wifiConnected = false;
bool backendConnected = false;
String backendUrl = "";

Preferences wifiPrefs;
ImprovWiFi improvSerial(&Serial);
bool provisioningMode = false;

// ==========================================
// OLED FACE & BLINKING ANIMATION ENGINE
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
// OLED DRAWING ROUTINES
// ==========================================
void drawCyberEye(int cx, int cy, float openPct, float pupilX, float pupilY, bool isRight) {
    int maxW = 34;
    int maxH = 26;
    int curH = (int)(maxH * openPct);
    if (curH < 2) curH = 2;

    int rX = cx - maxW / 2;
    int rY = cy - curH / 2;

    oledDisplay.drawRoundRect(rX, rY, maxW, curH, 4, SSD1306_WHITE);

    if (curH > 6) {
        int pX = cx + (int)pupilX;
        int pY = cy + (int)pupilY;
        oledDisplay.fillCircle(pX, pY, 4, SSD1306_WHITE);
    }
}

void renderFaceScreen() {
    drawCyberEye(38, 32, face.currentOpenPct, face.currentPupilX, face.currentPupilY, false);
    drawCyberEye(90, 32, face.currentOpenPct, face.currentPupilX, face.currentPupilY, true);
}

void renderSplitHUDScreen() {
    oledDisplay.setTextSize(1);
    oledDisplay.setTextColor(SSD1306_WHITE);
    oledDisplay.setCursor(4, 4);
    oledDisplay.printf("CLAUDE: %ldk", claudeData.tokensToday / 1000);

    oledDisplay.setCursor(4, 20);
    oledDisplay.printf("AGY 5h: %d/%d", agData.remaining, agData.limit);

    oledDisplay.drawFastHLine(0, 34, 128, SSD1306_WHITE);

    oledDisplay.setCursor(4, 40);
    oledDisplay.printf("TIME: %s", timeData.time_str.c_str());

    oledDisplay.setCursor(4, 52);
    if (weatherData.hours_until_rain >= 0) {
        oledDisplay.printf("%.1fC Rain:%dh", weatherData.temp, weatherData.hours_until_rain);
    } else {
        oledDisplay.printf("%.1fC No Rain", weatherData.temp);
    }
}

void renderLimitsScreen() {
    oledDisplay.setTextSize(1);
    oledDisplay.setTextColor(SSD1306_WHITE);
    oledDisplay.setCursor(4, 4);
    oledDisplay.print("=== AI LIMITS ===");

    oledDisplay.setCursor(4, 22);
    oledDisplay.printf("Claude Today: %ldk", claudeData.tokensToday / 1000);

    oledDisplay.setCursor(4, 38);
    oledDisplay.printf("Antigravity: %d rem", agData.remaining);
    int barW = map(agData.remaining, 0, agData.limit, 0, 120);
    oledDisplay.drawRect(4, 50, 120, 8, SSD1306_WHITE);
    oledDisplay.fillRect(6, 52, max(0, barW - 4), 4, SSD1306_WHITE);
}

void renderClockWeatherScreen() {
    oledDisplay.setTextSize(2);
    oledDisplay.setTextColor(SSD1306_WHITE);
    oledDisplay.setCursor(16, 12);
    oledDisplay.printf("%02d:%02d", timeData.hours, timeData.minutes);

    oledDisplay.setTextSize(1);
    oledDisplay.setCursor(4, 44);
    oledDisplay.printf("%.1f C  %s", weatherData.temp, weatherData.location.c_str());
}

void renderAgentAlertScreen() {
    bool blink = (millis() / 400) % 2 == 0;
    oledDisplay.drawRect(0, 0, 128, 64, blink ? SSD1306_WHITE : SSD1306_BLACK);
    oledDisplay.setTextSize(1);
    oledDisplay.setTextColor(SSD1306_WHITE);
    oledDisplay.setCursor(18, 14);
    oledDisplay.print("! AGENT ALERT !");
    oledDisplay.setCursor(10, 36);
    oledDisplay.print(agentData.prompt_text);
}

void renderProvisioningScreen() {
    oledDisplay.setTextSize(1);
    oledDisplay.setTextColor(SSD1306_WHITE);
    oledDisplay.setCursor(24, 6);
    oledDisplay.print("SETUP MODE");
    oledDisplay.drawFastHLine(8, 16, 112, SSD1306_WHITE);
    oledDisplay.setCursor(8, 28);
    oledDisplay.print("Open setup portal to");
    oledDisplay.setCursor(8, 40);
    oledDisplay.print("provision Wi-Fi / Screen");
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
    static int lastClaudePct = -1;
    static int lastAntiPct = -1;
    static float lastTemp = -999.0f;
    static String lastDate = "";
    static bool lastWaiting = false;

    static int oldDigits[4] = {-1, -1, -1, -1};
    static int prevTarget[4] = {-1, -1, -1, -1};
    static float flipProg[4] = {1.0f, 1.0f, 1.0f, 1.0f};

    uint16_t colHazardAmber = gcGfx->color565(255, 184, 0); // #FFB800 Kinetic Amber

    if (agentData.waiting_for_input) {
        bezelDrawn = false;
        bool flashOn = (millis() / 500) % 2 == 0;

        if (flashOn != lastFlashState || !lastWaitingState) {
            lastFlashState = flashOn;
            lastWaitingState = true;

            if (flashOn) {
                // ON Phase (flashOn == true): Draw 6 static arc dashes (radii 115..118 in Kinetic Amber #FFB800)
                for (int i = 0; i < 6; i++) {
                    float dashStart = i * 60.0f;
                    float dashEnd = dashStart + 25.0f;

                    for (float d = dashStart; d <= dashEnd; d += 0.4f) {
                        float rad = d * 0.0174532925f;
                        float cosR = cosf(rad);
                        float sinR = sinf(rad);

                        for (int r = 115; r <= 118; r++) {
                            gcGfx->drawPixel(cx + (int)roundf(cosR * r), cy + (int)roundf(sinR * r), colHazardAmber);
                        }
                    }
                }
            } else {
                // OFF Phase (flashOn == false): High-density 0.2-degree polar wipe (0.41px arc step) across radii 112..120
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
            lastClaudePct = -1;
            lastAntiPct = -1;
            lastTemp = -999.0f;
            lastDate = "";
            for (int i = 0; i < 4; i++) {
                oldDigits[i] = -1;
            }

            // Re-render static 2px gunmetal bezel ring (r = 116, 117)
            gcGfx->drawCircle(cx, cy, 116, colBezel);
            gcGfx->drawCircle(cx, cy, 117, colBezel);
        }
    }

    // 2. Top Crown: Backend Connection Status LED & Weather / Rain Indicator (Redraw on change)
    int curLedState = backendConnected ? 1 : 0;

    if (weatherData.hours_until_rain != lastHoursUntilRain || curLedState != lastLedState) {
        lastHoursUntilRain = weatherData.hours_until_rain;
        lastLedState = curLedState;

        // Clear Top Crown Area
        gcGfx->fillRect(cx - 50, cy - 110, 100, 28, GC_COLOR_BLACK);

        // LED Indicator Dot (Centered at cx=120, y=cy-105=15)
        uint16_t colLed = (curLedState == 1) ? gcGfx->color565(34, 197, 94) :  // #22C55E Emerald Connected
                                               gcGfx->color565(239, 68, 68);    // #EF4444 Crimson Red Disconnected

        // LED Housing Bezel
        gcGfx->drawCircle(cx, cy - 105, 3, colBezel);
        // LED Core Dot
        gcGfx->fillCircle(cx, cy - 105, 2, colLed);

        // Weather text (Centered at cx=120, y=cy-93=27)
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
    int claudePct = 100;
    int antiPct = (agData.limit > 0) ? (agData.remaining * 100 / agData.limit) : 100;

    if (claudePct != lastClaudePct || antiPct != lastAntiPct) {
        lastClaudePct = claudePct;
        lastAntiPct = antiPct;

        // Left Arc: Claude Cyan (126 deg at bottom to 234 deg at top)
        for (int deg = 126; deg <= 234; deg++) {
            float rad = deg * 0.0174533f;
            float cosR = cos(rad);
            float sinR = sin(rad);

            bool active = (deg <= 126 + (claudePct * 108 / 100));
            uint16_t mainCol = active ? colCyan : colCyanDim;
            uint16_t thinCol = active ? colCyan : colCyanDim;

            for (int r = 101; r <= 107; r++) {
                gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), mainCol);
            }
            for (int r = 94; r <= 95; r++) {
                gcGfx->drawPixel(cx + (int)(cosR * r), cy + (int)(sinR * r), thinCol);
            }
        }

        // Right Arc: Antigravity Orange (54 deg at bottom to -54 deg at top)
        for (int deg = 54; deg >= -54; deg--) {
            float rad = deg * 0.0174533f;
            float cosR = cos(rad);
            float sinR = sin(rad);

            bool active = (deg >= 54 - (antiPct * 108 / 100));
            uint16_t mainCol = active ? colOrange : colOrangeDim;
            uint16_t thinCol = active ? colOrange : colOrangeDim;

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
        gcGfx->drawRoundRect(31, 108, 32, 24, 3, gcGfx->color565(0, 80, 100));
        gcPrintCentered("CLD", 47, 111, colCyan);
        char cldPctStr[8];
        sprintf(cldPctStr, "%d%%", claudePct);
        gcPrintCentered(cldPctStr, 47, 121, colCyan);

        // Right Corridor: x=174 to 213 -> Centered at x=193, y=120
        gcGfx->fillRoundRect(177, 108, 32, 24, 3, gcGfx->color565(28, 18, 10));
        gcGfx->drawRoundRect(177, 108, 32, 24, 3, gcGfx->color565(120, 60, 0));
        gcPrintCentered("AGY", 193, 111, colOrange);
        char agyPctStr[8];
        sprintf(agyPctStr, "%d%%", antiPct);
        gcPrintCentered(agyPctStr, 193, 121, colOrange);
    }

    // 4. Center 2x2 Split-Flap Clock Matrix with 3D Folding Animation
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
    } else {
        if (lastWaiting || abs(weatherData.temp - lastTemp) > 0.05f || timeData.date_str != lastDate) {
            lastWaiting = false;
            lastTemp = weatherData.temp;
            lastDate = timeData.date_str;
            gcGfx->fillRect(cx - 50, cy + 74, 100, 32, GC_COLOR_BLACK);
            gcGfx->setTextSize(1);
            gcPrintCentered(timeData.date_str.c_str(), cx, cy + 80, colGray);
            char tempBuf[16];
            sprintf(tempBuf, "%.1f C", weatherData.temp);
            gcPrintCentered(tempBuf, cx, cy + 94, GC_COLOR_WHITE);
        }
    }
}

// ==========================================
// HARDWARE AUTO-DETECTION & INITIALIZATION
// ==========================================
HardwareScreenType detectHardwareDisplay() {
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.beginTransmission(0x3C);
    if (Wire.endTransmission() == 0) {
        oledAddress = 0x3C;
        oledFound = true;
        Serial.println("[Display] Auto-detected I2C OLED at 0x3C");
        return SCREEN_OLED_128X64;
    }

    Wire.beginTransmission(0x3D);
    if (Wire.endTransmission() == 0) {
        oledAddress = 0x3D;
        oledFound = true;
        Serial.println("[Display] Auto-detected I2C OLED at 0x3D");
        return SCREEN_OLED_128X64;
    }

    Serial.println("[Display] No I2C OLED detected. Defaulting to SPI GC9A01 Round 240x240");
    return SCREEN_GC9A01_ROUND;
}

void initActiveDisplay() {
    if (activeScreenType == SCREEN_OLED_128X64) {
        Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
        if (oledDisplay.begin(SSD1306_SWITCHCAPVCC, oledAddress)) {
            oledFound = true;
            oledDisplay.clearDisplay();
            oledDisplay.display();
            Serial.println("[Display] OLED initialized successfully");
        }
    } else {
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
            gcGfx->fillScreen(GC_COLOR_CARD_TOP);
            delay(100);
            gcGfx->fillScreen(GC_COLOR_BLACK);
            Serial.println("[Display] GC9A01 Round IPS initialized successfully");
        } else {
            Serial.println("[Display] Failed to initialize GC9A01 display!");
        }
    }
}

bool connectToWifi(const char* ssid, const char* password);
void onWifiConnected();

// ==========================================
// HTTP SERVER (Companion App Screen Provisioning)
// ==========================================
void setupWebServer() {
    server.on("/api/screen", HTTP_GET, []() {
        StaticJsonDocument<256> doc;
        doc["configured_mode"] = (configuredScreenType == SCREEN_AUTO) ? "auto" :
                                 ((configuredScreenType == SCREEN_GC9A01_ROUND) ? "round" : "oled");
        doc["active_screen"] = (activeScreenType == SCREEN_GC9A01_ROUND) ? "round" : "oled";
        doc["status"] = "ok";
        String out;
        serializeJson(doc, out);
        server.send(200, "application/json", out);
    });

    server.on("/api/screen", HTTP_POST, []() {
        String mode = server.arg("mode");
        if (mode.length() == 0 && server.hasArg("plain")) {
            StaticJsonDocument<200> doc;
            deserializeJson(doc, server.arg("plain"));
            mode = doc["mode"].as<String>();
        }
        mode.toLowerCase();
        if (mode == "round" || mode == "gc9a01") {
            configuredScreenType = SCREEN_GC9A01_ROUND;
        } else if (mode == "oled" || mode == "128x64") {
            configuredScreenType = SCREEN_OLED_128X64;
        } else {
            configuredScreenType = SCREEN_AUTO;
        }

        screenPrefs.begin("screen", false);
        screenPrefs.putInt("type", (int)configuredScreenType);
        screenPrefs.end();

        if (configuredScreenType == SCREEN_AUTO) {
            activeScreenType = detectHardwareDisplay();
        } else {
            activeScreenType = configuredScreenType;
        }

        initActiveDisplay();

        StaticJsonDocument<256> doc;
        doc["status"] = "ok";
        doc["configured_mode"] = mode;
        doc["active_screen"] = (activeScreenType == SCREEN_GC9A01_ROUND) ? "round" : "oled";
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

bool resolveBackendUrl() {
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

    HTTPClient http;
    http.begin(backendUrl);
    http.setTimeout(2500);

    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
        backendConnected = true;
        String payload = http.getString();
        StaticJsonDocument<1536> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
            if (doc.containsKey("claude")) {
                claudeData.tokensToday = doc["claude"]["tokens_today"] | 0;
                if (doc["claude"].containsKey("limit")) claudeData.limit = doc["claude"]["limit"] | 100;
                if (doc["claude"].containsKey("remaining")) claudeData.remaining = doc["claude"]["remaining"] | 100;
            }
            if (doc.containsKey("antigravity")) {
                agData.limit = doc["antigravity"]["limit"] | 200;
                agData.remaining = doc["antigravity"]["remaining"] | 200;
                agData.used = doc["antigravity"]["used"] | 0;
                agData.period = doc["antigravity"]["period"] | "5h";
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
                agentData.waiting_for_input = doc["agent"]["waiting_for_input"] | false;
                agentData.prompt_text = doc["agent"]["prompt_text"] | "APPROVE PLAN";
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
            if (doc.containsKey("device")) {
                String devScreen = doc["device"]["screen_type"] | "auto";
                if (configuredScreenType == SCREEN_AUTO) {
                    if (devScreen == "round" && activeScreenType != SCREEN_GC9A01_ROUND) {
                        activeScreenType = SCREEN_GC9A01_ROUND;
                        initActiveDisplay();
                    } else if (devScreen == "oled" && activeScreenType != SCREEN_OLED_128X64) {
                        activeScreenType = SCREEN_OLED_128X64;
                        initActiveDisplay();
                    }
                }
            }
        }
    } else {
        backendConnected = false;
        backendUrl = "";
    }
    http.end();
}

// ==========================================
// WIFI CONNECTION (from working commit 74e9073)
// ==========================================
bool connectToWifi(const char* ssid, const char* password) {
    WiFi.mode(WIFI_OFF);
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    delay(50);

    wifi_country_t country = {"01", 1, 13, 20, WIFI_COUNTRY_POLICY_AUTO};
    esp_wifi_set_country(&country);

    WiFi.disconnect(true, true);
    delay(50);

    Serial.printf("\n[WiFi] Connecting to '%s'...\n", ssid);
    WiFi.begin(ssid, password);
    wifi_config_t wifiConfig = {};
    esp_wifi_get_config(WIFI_IF_STA, &wifiConfig);
    wifiConfig.sta.pmf_cfg.capable = false;
    wifiConfig.sta.pmf_cfg.required = false;
    esp_wifi_set_config(WIFI_IF_STA, &wifiConfig);
    WiFi.disconnect(false);
    delay(50);
    esp_wifi_connect();

    unsigned long connectStart = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - connectStart < wifiConnectTimeoutMs) {
        delay(250);
        improvSerial.handleSerial();
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("[WiFi] SUCCESS! Local IP: %s\n", WiFi.localIP().toString().c_str());
        onWifiConnected();
        return true;
    }

    Serial.printf("[WiFi] Connection to '%s' failed.\n", ssid);
    WiFi.disconnect(true, false); // abort the pending connect attempt so the STA
                                   // returns to idle and scanNetworks() works again
    delay(50);
    return false;
}

void onWifiConnected() {
    wifiConnected = true;
    provisioningMode = false;
    Serial.printf("[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());

    if (!MDNS.begin("tinyscreen")) {
        Serial.println("[mDNS] Error starting responder");
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

void handleSerialCommunication() {
    while (Serial.available()) {
        int peekByte = Serial.peek();
        if (peekByte == 'I' && serialBuffer.length() == 0) {
            improvSerial.handleSerial();
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
                String creds = line.substring(5);
                int sep = creds.indexOf('\t');
                if (sep == -1) sep = creds.indexOf(',');
                if (sep != -1) {
                    String ssid = creds.substring(0, sep);
                    String pass = creds.substring(sep + 1);
                    ssid.trim();
                    pass.trim();
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
                Serial.printf("STATUS:{\"connected\":%s,\"ip\":\"%s\",\"screen\":\"%s\"}\n",
                    wifiConnected ? "true" : "false",
                    wifiConnected ? WiFi.localIP().toString().c_str() : "",
                    (activeScreenType == SCREEN_GC9A01_ROUND) ? "round" : "oled");
            }
        } else {
            serialBuffer += c;
            if (serialBuffer.length() > 256) {
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
    delay(200);

    // 1. Load Stored Screen Preferences
    screenPrefs.begin("screen", false);
    configuredScreenType = (HardwareScreenType)screenPrefs.getInt("type", SCREEN_AUTO);
    screenPrefs.end();

    // 2. Hardware Auto-Detection / Pin Configuration
    if (configuredScreenType == SCREEN_AUTO) {
        activeScreenType = detectHardwareDisplay();
    } else {
        activeScreenType = configuredScreenType;
    }

    // 3. Initialize Active Display
    initActiveDisplay();

    // 4. Wi-Fi Configuration for ESP32-C3 SuperMini (STA mode, power-tuned, 13-channel worldwide)
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    wifi_country_t country = {"01", 1, 13, 20, WIFI_COUNTRY_POLICY_AUTO};
    esp_wifi_set_country(&country);
    delay(50);
    WiFi.disconnect(true, true);
    delay(50);

    // 5. Improv Wi-Fi Provisioning Setup
    improvSerial.setDeviceInfo(
        ImprovTypes::ChipFamily::CF_ESP32_C3,
        "TinyScreenFirmware", "2.0.0", "Tiny AI Screen", ""
    );
    improvSerial.onImprovError(onImprovWiFiErrorCb);
    improvSerial.onImprovConnected(onImprovWiFiConnectedCb);
    improvSerial.setCustomConnectWiFi(connectToWifi);

    // 6. Connect Stored Wi-Fi
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

    lastScreenSwitch = millis();
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

    // 2. Render Active Display
    if (now - lastFrameTime >= frameIntervalMs) {
        lastFrameTime = now;

        if (activeScreenType == SCREEN_GC9A01_ROUND) {
            // GC9A01 Round IPS HUD (Render full cyberpunk flip clock HUD)
            static bool initialCleared = false;
            if (!initialCleared) {
                initialCleared = true;
                gcGfx->fillScreen(GC_COLOR_BLACK);
            }
            drawGC9A01RoundFlipUI();
        } else {
            // SSD1306 OLED Loop
            updateFacePhysics(now);
            oledDisplay.clearDisplay();

            if (provisioningMode) {
                renderProvisioningScreen();
            } else {
                switch (currentOLEDMode) {
                    case SCREEN_FACE:
                        renderFaceScreen();
                        break;
                    case SCREEN_SPLIT_HUD:
                        renderSplitHUDScreen();
                        break;
                    case SCREEN_LIMITS:
                        renderLimitsScreen();
                        break;
                    case SCREEN_CLOCK_WEATHER:
                        renderClockWeatherScreen();
                        break;
                    case SCREEN_AGENT_ALERT:
                        renderAgentAlertScreen();
                        break;
                }
            }
            oledDisplay.display();
        }
    }

    // 3. Auto-reconnect Wi-Fi
    static unsigned long lastWiFiCheck = 0;
    if (now - lastWiFiCheck >= 10000) {
        lastWiFiCheck = now;
        if (WiFi.status() != WL_CONNECTED && !provisioningMode) {
            WiFi.reconnect();
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

    // 5. Backend Polling
    if (now - lastBackendPoll >= backendPollInterval) {
        lastBackendPoll = now;
        fetchBackendData();
    }

    // 6. OLED Screen Mode Cycler
    if (agentData.waiting_for_input) {
        currentOLEDMode = SCREEN_AGENT_ALERT;
    } else if (activeScreenType == SCREEN_OLED_128X64) {
        if (now - lastScreenSwitch >= screenSwitchInterval) {
            lastScreenSwitch = now;
            if (currentOLEDMode == SCREEN_FACE) currentOLEDMode = SCREEN_SPLIT_HUD;
            else if (currentOLEDMode == SCREEN_SPLIT_HUD) currentOLEDMode = SCREEN_LIMITS;
            else if (currentOLEDMode == SCREEN_LIMITS) currentOLEDMode = SCREEN_CLOCK_WEATHER;
            else currentOLEDMode = SCREEN_FACE;
        }
    }
}
