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
#include <ArduinoJson.h>
#include <esp_wifi.h>
#include <Preferences.h>
#include <ImprovWiFiLibrary.h>

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

// GC9A01 SPI Hardware Driver
Arduino_DataBus *gcBus = new Arduino_ESP32SPI(GC9A01_DC_PIN, GC9A01_CS_PIN, GC9A01_SCK_PIN, GC9A01_MOSI_PIN, GFX_NOT_DEFINED);
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
void drawTallDigit(int x, int y, int w, int h, int digit, uint16_t color) {
    gcGfx->setTextSize(3);
    gcGfx->setTextColor(color);
    gcGfx->setCursor(x + (w - 18) / 2, y + (h - 24) / 2);
    gcGfx->print(digit);
}

void drawGC9A01FlipCard(int posX, int posY, int cardW, int cardH, int digit, bool isTopHalf) {
    int midY = posY + cardH / 2;
    int halfH = cardH / 2;

    // Card background
    gcGfx->fillRoundRect(posX, posY, cardW, halfH, 4, GC_COLOR_CARD_TOP);
    gcGfx->fillRoundRect(posX, midY, cardW, halfH, 4, GC_COLOR_CARD_BOT);
    gcGfx->drawRoundRect(posX, posY, cardW, cardH, 4, GC_COLOR_CARD_BORDER);

    // Mechanical split crease
    gcGfx->drawFastHLine(posX, midY, cardW, GC_COLOR_BLACK);
    gcGfx->drawFastHLine(posX, midY + 1, cardW, 0x31E7);

    // Retaining Hinge Lugs (Left, Center Seams, Right)
    auto drawHinge = [](int hx, int my) {
        gcGfx->fillRoundRect(hx - 2, my - 6, 5, 12, 2, 0x10A2);
        gcGfx->drawRoundRect(hx - 2, my - 6, 5, 12, 2, 0x39E7);
        gcGfx->fillRect(hx - 1, my - 2, 3, 4, 0x8CD1); // Steel pin
    };
    drawHinge(posX, midY);
    drawHinge(posX + cardW, midY);

    // Draw tall numeral
    drawTallDigit(posX, posY, cardW, cardH, digit, GC_COLOR_WHITE);
}

void drawGC9A01RoundFlipUI() {
    int cx = 120, cy = 120, rScreen = 114;

    // 1. Agent Alert Spinning Hazard Ring or Static Bezel
    if (agentData.waiting_for_input) {
        float spinAngle = (float)(millis() % 3350) / 3350.0f * 6.28318f;
        gcGfx->drawCircle(cx, cy, rScreen + 2, GC_COLOR_DARK_AMBER);
        gcGfx->drawCircle(cx, cy, rScreen + 3, GC_COLOR_AMBER);

        // Broken arc segments
        for (int i = 0; i < 6; i++) {
            float a = spinAngle + i * 1.047f;
            int px = cx + (int)(cos(a) * (rScreen + 3));
            int py = cy + (int)(sin(a) * (rScreen + 3));
            gcGfx->fillCircle(px, py, 2, GC_COLOR_YELLOW);
        }
    } else {
        gcGfx->drawCircle(cx, cy, rScreen + 2, 0x18E3);
    }

    // 2. Top Crown: Weather Forecast
    gcGfx->setTextSize(1);
    gcGfx->setTextColor(weatherData.hours_until_rain <= 3 && weatherData.hours_until_rain >= 0 ? GC_COLOR_ICE_BLUE : GC_COLOR_SLATE_GRAY);
    gcGfx->setCursor(cx - 36, cy - 93);
    if (weatherData.hours_until_rain == 0) {
        gcGfx->print("RAIN NOW");
    } else if (weatherData.hours_until_rain > 0) {
        gcGfx->printf("RAIN IN %dh", weatherData.hours_until_rain);
    } else {
        gcGfx->print("NO RAIN");
    }

    // 3. Flanking Radial Gauges (Left: Claude / Right: Antigravity)
    int claudePct = 100;
    int antiPct = (agData.limit > 0) ? (agData.remaining * 100 / agData.limit) : 100;

    // Left Arc (Claude Cyan) - outer main arc + inner thin arc
    for (int deg = 126; deg <= 234; deg += 3) {
        float rad = deg * 0.0174533f;
        int x1 = cx + (int)(cos(rad) * 105);
        int y1 = cy + (int)(sin(rad) * 105);
        int x2 = cx + (int)(cos(rad) * 96);
        int y2 = cy + (int)(sin(rad) * 96);

        uint16_t color = (deg <= 126 + (claudePct * 108 / 100)) ? GC_COLOR_CYAN : 0x0110;
        gcGfx->drawPixel(x1, y1, color);
        gcGfx->drawPixel(x2, y2, color);
    }

    // Right Arc (Antigravity Orange) - outer main arc + inner thin arc
    for (int deg = 54; deg >= -54; deg -= 3) {
        float rad = deg * 0.0174533f;
        int x1 = cx + (int)(cos(rad) * 105);
        int y1 = cy + (int)(sin(rad) * 105);
        int x2 = cx + (int)(cos(rad) * 96);
        int y2 = cy + (int)(sin(rad) * 96);

        uint16_t color = (deg >= 54 - (antiPct * 108 / 100)) ? GC_COLOR_ORANGE : 0x2080;
        gcGfx->drawPixel(x1, y1, color);
        gcGfx->drawPixel(x2, y2, color);
    }

    // Gauge Labels
    gcGfx->setTextSize(1);
    gcGfx->setTextColor(GC_COLOR_CYAN);
    gcGfx->setCursor(cx - 96, cy - 4);
    gcGfx->print("CLD");

    gcGfx->setTextColor(GC_COLOR_ORANGE);
    gcGfx->setCursor(cx + 74, cy - 4);
    gcGfx->print("AGY");

    // 4. Center 2x2 Split-Flap Clock Matrix (48x72px cards, 6px gap)
    int cardW = 48, cardH = 72, gap = 6;
    int x1 = cx - cardW - gap / 2;
    int x2 = cx + gap / 2;
    int yTop = cy - cardH - gap / 2;
    int yBot = cy + gap / 2;

    int dH1 = timeData.hours / 10;
    int dH2 = timeData.hours % 10;
    int dM1 = timeData.minutes / 10;
    int dM2 = timeData.minutes % 10;

    drawGC9A01FlipCard(x1, yTop, cardW, cardH, dH1, true);
    drawGC9A01FlipCard(x2, yTop, cardW, cardH, dH2, true);
    drawGC9A01FlipCard(x1, yBot, cardW, cardH, dM1, false);
    drawGC9A01FlipCard(x2, yBot, cardW, cardH, dM2, false);

    // 5. Stacked Bottom Sub-HUD
    if (agentData.waiting_for_input) {
        bool alertBlink = (millis() / 500) % 2 == 0;
        gcGfx->setTextSize(1);
        gcGfx->setTextColor(alertBlink ? GC_COLOR_AMBER : 0x4200);
        gcGfx->setCursor(cx - 38, cy + 80);
        gcGfx->print("AGENT ALERT");

        gcGfx->setTextColor(GC_COLOR_WHITE);
        gcGfx->setCursor(cx - 42, cy + 94);
        gcGfx->print(agentData.prompt_text);
    } else {
        gcGfx->setTextSize(1);
        gcGfx->setTextColor(GC_COLOR_SLATE_GRAY);
        gcGfx->setCursor(cx - 32, cy + 80);
        gcGfx->print(timeData.date_str);

        gcGfx->setTextColor(GC_COLOR_WHITE);
        gcGfx->setCursor(cx - 24, cy + 94);
        gcGfx->printf("%.1f C", weatherData.temp);
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
        pinMode(GC9A01_BLK_PIN, OUTPUT);
        digitalWrite(GC9A01_BLK_PIN, HIGH); // Backlight on
        if (gcGfx->begin()) {
            gc9a01Initialized = true;
            gcGfx->fillScreen(GC_COLOR_BLACK);
            Serial.println("[Display] GC9A01 Round IPS initialized successfully");
        }
    }
}

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
String backendUrl = "";
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
        String payload = http.getString();
        StaticJsonDocument<1536> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
            if (doc.containsKey("claude")) {
                claudeData.tokensToday = doc["claude"]["tokens_today"] | 0;
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
            }
            if (doc.containsKey("agent")) {
                agentData.waiting_for_input = doc["agent"]["waiting_for_input"] | false;
                agentData.prompt_text = doc["agent"]["prompt_text"] | "APPROVE PLAN";
            }
            if (doc.containsKey("time")) {
                timeData.hours = doc["time"]["hours"] | 12;
                timeData.minutes = doc["time"]["minutes"] | 0;
                timeData.seconds = doc["time"]["seconds"] | 0;
                timeData.time_str = doc["time"]["time_string"] | "12:00:00";
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
    }
    http.end();
}

// ==========================================
// IMPROV WIFI CALLBACKS
// ==========================================
bool connectToWifi(const char* ssid, const char* password) {
    WiFi.disconnect(true);
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < wifiConnectTimeoutMs) {
        delay(250);
        improvSerial.handleSerial();
    }
    return WiFi.status() == WL_CONNECTED;
}

void onImprovWiFiConnectedCb(const char* ssid) {
    wifiPrefs.begin("wifi", false);
    wifiPrefs.putString("ssid", ssid);
    wifiPrefs.putString("password", WiFi.psk());
    wifiPrefs.end();

    wifiConnected = true;
    provisioningMode = false;
}

void onImprovWiFiErrorCb(ImprovTypes::Error err) {
    Serial.printf("[Improv] WiFi Error code: %d\n", err);
}

void onWifiConnected() {
    wifiConnected = true;
    provisioningMode = false;
    Serial.printf("[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());

    if (!MDNS.begin("tinyscreen-device")) {
        Serial.println("[mDNS] Error starting responder");
    }

    setupWebServer();
    resolveBackendUrl();
}

// ==========================================
// SETUP
// ==========================================
void setup() {
    Serial.begin(115200);

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

    // 4. Improv Wi-Fi Provisioning Setup
    improvSerial.setDeviceInfo(
        ImprovTypes::ChipFamily::CF_ESP32_C3,
        "TinyScreenFirmware", "2.0.0", "Tiny AI Screen", ""
    );
    improvSerial.onImprovError(onImprovWiFiErrorCb);
    improvSerial.onImprovConnected(onImprovWiFiConnectedCb);
    improvSerial.setCustomConnectWiFi(connectToWifi);

    // 5. Connect Wi-Fi
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

    // 1. Improv Wi-Fi Serial Listener & Web Server
    improvSerial.handleSerial();
    if (wifiConnected) {
        server.handleClient();
    }

    // 2. Render Active Display
    if (now - lastFrameTime >= frameIntervalMs) {
        lastFrameTime = now;

        if (activeScreenType == SCREEN_GC9A01_ROUND) {
            // GC9A01 Round IPS Loop
            if (provisioningMode) {
                gcGfx->fillScreen(GC_COLOR_BLACK);
                gcGfx->setTextSize(2);
                gcGfx->setTextColor(GC_COLOR_CYAN);
                gcGfx->setCursor(60, 90);
                gcGfx->print("SETUP MODE");
                gcGfx->setTextSize(1);
                gcGfx->setTextColor(GC_COLOR_WHITE);
                gcGfx->setCursor(45, 125);
                gcGfx->print("Open Companion App");
            } else {
                gcGfx->fillScreen(GC_COLOR_BLACK);
                drawGC9A01RoundFlipUI();
            }
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
