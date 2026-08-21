#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <ESPmDNS.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>
#include "secrets.h"

// ==========================================
// PIN CONFIGURATION (ESP32-C3 SuperMini)
// ==========================================
#define I2C_SDA_PIN 8
#define I2C_SCL_PIN 9

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

const unsigned long wifiConnectTimeoutMs = 15000;

// ==========================================
// DATA STRUCTURES
// ==========================================
struct ClaudeLimits {
    long limit = 500000;
    long remaining = 500000;
};

struct AntigravityLimits {
    int limit = 200;
    int remaining = 200;
    int used = 0;
    String period = "5h";
};

struct WeatherInfo {
    float temp = 21.5;
    int hours_until_rain = -1;
    String location = "DESKTOP";
};

struct AgentStatus {
    bool waiting_for_input = false;
    String prompt_text = "INPUT REQ";
};

struct TimeInfo {
    int hours = 12;
    int minutes = 0;
    int seconds = 0;
    String time_str = "12:00:00";
};

ClaudeLimits claudeData;
AntigravityLimits agData;
WeatherInfo weatherData;
AgentStatus agentData;
TimeInfo timeData;

unsigned long lastBackendPoll = 0;
const unsigned long backendPollInterval = 3000;

unsigned long lastScreenSwitch = 0;
const unsigned long screenSwitchInterval = 8000;

enum ScreenMode {
    SCREEN_FACE = 0,
    SCREEN_SPLIT_HUD = 1,
    SCREEN_LIMITS = 2,
    SCREEN_CLOCK_WEATHER = 3,
    SCREEN_AGENT_ALERT = 4
};

ScreenMode currentScreen = SCREEN_FACE;
bool wifiConnected = false;
bool oledFound = false;
uint8_t oledAddress = 0x3C;
int blinkCounter = 0;

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

    // 1. Blink State Machine (25% faster response)
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

                // 25% chance of a quick double-blink
                if (!face.isDoubleBlink && random(0, 100) < 25 && face.blinkCountInBurst < 2) {
                    face.isDoubleBlink = true;
                    face.nextBlinkTime = now + random(75, 180);
                } else {
                    face.isDoubleBlink = false;
                    face.blinkCountInBurst = 0;
                    face.nextBlinkTime = now + random(1800, 4000); // 25% faster interval
                }
            } else {
                face.currentOpenPct = 0.08f + (float)elapsed / 38.0f * 0.92f;
            }
            break;
        }
    }

    // 2. Eye Looking / Saccade Machine (25% faster)
    if (now >= face.nextLookTime) {
        int r = random(0, 100);
        if (r < 40) {
            face.targetPupilX = 0; // Look center
            face.targetPupilY = 0;
        } else if (r < 65) {
            face.targetPupilX = -5; // Look left
            face.targetPupilY = 0;
        } else if (r < 90) {
            face.targetPupilX = 5; // Look right
            face.targetPupilY = 0;
        } else {
            face.targetPupilX = 0;
            face.targetPupilY = -3; // Look up
        }
        face.nextLookTime = now + random(1500, 3400); // 25% faster looking intervals
    }

    // Snappy spring smoothing for pupil
    face.currentPupilX += (face.targetPupilX - face.currentPupilX) * 0.45f;
    face.currentPupilY += (face.targetPupilY - face.currentPupilY) * 0.45f;
}

// ==========================================
// DRAWING ROUTINES (Adafruit GFX)
// ==========================================

void drawEye(int cx, int cy, int width, int height, int radius, float openPct, int pupilXOffset, int pupilYOffset) {
    int eyeH = max(2, (int)round(height * openPct));
    int topY = cy - eyeH / 2;

    // Outer Eye
    display.fillRoundRect(cx - width / 2, topY, width, eyeH, radius, SSD1306_WHITE);

    // Inner Pupil Cutout (Dark highlight inside eye when open)
    if (openPct > 0.45f && width > 14) {
        int pupilW = max(3, (int)round(width * 0.38f));
        int pupilH = max(3, (int)round(eyeH * 0.46f));
        int px = cx + pupilXOffset - pupilW / 2;
        int py = cy + pupilYOffset - pupilH / 2;
        display.fillRect(px, py, pupilW, pupilH, SSD1306_BLACK);
    }
}

void renderFaceScreen() {
    int cx = 64;
    int cy = 32;
    int eyeW = 28;
    int eyeH = 40;
    int eyeRadius = 8;
    int eyeDist = 26;

    // Check if token quota is low (< 20%): show tired droopy eyes with sweat
    long claudeUsed = max(0L, claudeData.limit - claudeData.remaining);
    float claudePercentLeft = claudeData.limit > 0 ? (float)claudeData.remaining / (float)claudeData.limit : 1.0f;
    bool isLowQuota = (claudePercentLeft < 0.20f) && (claudeData.limit > 0);

    if (isLowQuota) {
        // Tired / Low Battery Droopy Eyes
        int tiredH = eyeH / 2;
        display.fillRoundRect(cx - eyeDist - eyeW / 2, cy - 2, eyeW, tiredH, 4, SSD1306_WHITE);
        display.fillRoundRect(cx + eyeDist - eyeW / 2, cy - 2, eyeW, tiredH, 4, SSD1306_WHITE);

        // Animated falling sweat drop
        int sweatY = cy - 12 + ((animTicks / 2) % 20);
        display.drawPixel(cx + eyeDist + eyeW / 2 + 5, sweatY, SSD1306_WHITE);
        display.drawPixel(cx + eyeDist + eyeW / 2 + 5, sweatY + 1, SSD1306_WHITE);
        display.drawPixel(cx + eyeDist + eyeW / 2 + 4, sweatY + 2, SSD1306_WHITE);
        display.drawPixel(cx + eyeDist + eyeW / 2 + 6, sweatY + 2, SSD1306_WHITE);

        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(34, 54);
        display.print("LOW TOKENS");
        return;
    }

    // Normal Expressive Blinking Eyes
    int leftX = cx - eyeDist;
    int rightX = cx + eyeDist;
    int pX = (int)round(face.currentPupilX);
    int pY = (int)round(face.currentPupilY);

    drawEye(leftX, cy, eyeW, eyeH, eyeRadius, face.currentOpenPct, pX, pY);
    drawEye(rightX, cy, eyeW, eyeH, eyeRadius, face.currentOpenPct, pX, pY);
}

void renderSplitHUDScreen() {
    // Left side: Mini animated robot face (scale 0.65)
    int cx = 24;
    int cy = 32;
    int eyeW = 18;
    int eyeH = 26;
    int eyeRadius = 5;
    int eyeDist = 16;
    int pX = (int)round(face.currentPupilX * 0.6f);
    int pY = (int)round(face.currentPupilY * 0.6f);

    drawEye(cx - eyeDist, cy, eyeW, eyeH, eyeRadius, face.currentOpenPct, pX, pY);
    drawEye(cx + eyeDist, cy, eyeW, eyeH, eyeRadius, face.currentOpenPct, pX, pY);

    // Vertical Divider
    for (int y = 4; y < 60; y += 2) {
        display.drawPixel(50, y, SSD1306_WHITE);
    }

    // Right side: AI Token Gauges & Clock
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(55, 4);
    display.print("AI LIMITS");

    // Claude Progress Bar
    long claudeUsed = max(0L, claudeData.limit - claudeData.remaining);
    float claudePercent = claudeData.limit > 0 ? (float)claudeUsed / (float)claudeData.limit : 0.0f;
    display.setCursor(55, 16);
    display.print("C:");
    display.drawRect(68, 16, 56, 7, SSD1306_WHITE);
    int cFill = (int)(52 * claudePercent);
    if (cFill > 0) display.fillRect(70, 18, cFill, 3, SSD1306_WHITE);

    // Antigravity Progress Bar
    float agPercent = agData.limit > 0 ? (float)agData.used / (float)agData.limit : 0.0f;
    display.setCursor(55, 28);
    display.print("A:");
    display.drawRect(68, 28, 56, 7, SSD1306_WHITE);
    int aFill = (int)(52 * agPercent);
    if (aFill > 0) display.fillRect(70, 30, aFill, 3, SSD1306_WHITE);

    // Digital Time & Temp
    char timeBuf[16];
    snprintf(timeBuf, sizeof(timeBuf), "%02d:%02d:%02d", timeData.hours, timeData.minutes, timeData.seconds);
    display.setCursor(56, 42);
    display.print(timeBuf);

    display.setCursor(56, 52);
    display.printf("%.1fC OK", weatherData.temp);
}

void drawHeader(const char* title, const char* rightTag = "") {
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(2, 2);
    display.print(title);

    if (strlen(rightTag) > 0) {
        int16_t x1, y1;
        uint16_t w, h;
        display.getTextBounds(rightTag, 0, 0, &x1, &y1, &w, &h);
        display.setCursor(126 - w, 2);
        display.print(rightTag);
    }
    display.drawFastHLine(0, 11, 128, SSD1306_WHITE);
}

void drawProgressBar(int x, int y, int w, int h, float percentage) {
    if (percentage < 0.0) percentage = 0.0;
    if (percentage > 1.0) percentage = 1.0;
    display.drawRect(x, y, w, h, SSD1306_WHITE);
    int fillW = (int)((w - 4) * percentage);
    if (fillW > 0) {
        display.fillRect(x + 2, y + 2, fillW, h - 4, SSD1306_WHITE);
    }
}

void renderLimitsScreen() {
    drawHeader("AI QUOTAS", wifiConnected ? "ONLINE" : "DEMO");

    // Claude Tokens
    long claudeUsed = max(0L, claudeData.limit - claudeData.remaining);
    float claudePercent = claudeData.limit > 0 ? (float)claudeUsed / (float)claudeData.limit : 0.0f;

    display.setTextSize(1);
    display.setCursor(2, 16);
    display.printf("Claude: %ldk/%ldk", claudeUsed / 1000, claudeData.limit / 1000);
    drawProgressBar(2, 26, 124, 6, claudePercent);

    // Antigravity Quota
    float agPercent = agData.limit > 0 ? (float)agData.used / (float)agData.limit : 0.0f;
    int agRemainingPct = (int)round(100.0f * (1.0f - agPercent));
    display.setCursor(2, 36);
    display.printf("Antigrav: %d%% left", agRemainingPct);
    drawProgressBar(2, 46, 124, 6, agPercent);

    // Bottom Status
    display.setCursor(2, 56);
    display.print(wifiConnected ? "Companion Active" : "Waiting for Wi-Fi");
}

void renderClockWeatherScreen() {
    drawHeader("TIME & WEATHER", weatherData.location.c_str());

    // Big Digital Clock
    display.setTextSize(2);
    char timeStr[16];
    snprintf(timeStr, sizeof(timeStr), "%02d:%02d:%02d", timeData.hours, timeData.minutes, timeData.seconds);
    int16_t x1, y1;
    uint16_t w, h;
    display.getTextBounds(timeStr, 0, 0, &x1, &y1, &w, &h);
    display.setCursor((128 - w) / 2, 18);
    display.print(timeStr);

    display.drawFastHLine(4, 38, 120, SSD1306_WHITE);

    // Weather
    display.setTextSize(1);
    display.setCursor(4, 46);
    display.printf("%.1f C", weatherData.temp);

    // Rain status
    char rainBuf[24];
    if (weatherData.hours_until_rain == 0) {
        snprintf(rainBuf, sizeof(rainBuf), "Rain: NOW");
    } else if (weatherData.hours_until_rain > 0) {
        snprintf(rainBuf, sizeof(rainBuf), "Rain: %dh", weatherData.hours_until_rain);
    } else {
        snprintf(rainBuf, sizeof(rainBuf), "No Rain");
    }
    display.getTextBounds(rainBuf, 0, 0, &x1, &y1, &w, &h);
    display.setCursor(124 - w, 46);
    display.print(rainBuf);

    display.setCursor(4, 56);
    display.print("Desktop Companion");
}

void renderAgentAlertScreen() {
    blinkCounter++;
    bool inverted = (blinkCounter % 2 == 0);

    if (inverted) {
        display.fillRect(0, 0, 128, 64, SSD1306_WHITE);
        display.setTextColor(SSD1306_BLACK, SSD1306_WHITE);
    } else {
        display.drawRect(0, 0, 128, 64, SSD1306_WHITE);
        display.drawRect(2, 2, 124, 60, SSD1306_WHITE);
        display.setTextColor(SSD1306_WHITE, SSD1306_BLACK);
    }

    display.setTextSize(1);
    const char* alertTitle = "! AGENT ATTENTION !";
    int16_t x1, y1;
    uint16_t w, h;
    display.getTextBounds(alertTitle, 0, 0, &x1, &y1, &w, &h);
    display.setCursor((128 - w) / 2, 8);
    display.print(alertTitle);

    // Shocked alert wide eyes in center
    int cx = 64;
    int cy = 32;
    int eyeW = 20;
    int eyeH = 22;
    if (inverted) {
        display.fillRoundRect(cx - 20 - eyeW / 2, cy - eyeH / 2, eyeW, eyeH, 6, SSD1306_BLACK);
        display.fillRoundRect(cx + 20 - eyeW / 2, cy - eyeH / 2, eyeW, eyeH, 6, SSD1306_BLACK);
        display.fillRect(cx - 20 - 2, cy - 2, 4, 4, SSD1306_WHITE);
        display.fillRect(cx + 20 - 2, cy - 2, 4, 4, SSD1306_WHITE);
    } else {
        display.fillRoundRect(cx - 20 - eyeW / 2, cy - eyeH / 2, eyeW, eyeH, 6, SSD1306_WHITE);
        display.fillRoundRect(cx + 20 - eyeW / 2, cy - eyeH / 2, eyeW, eyeH, 6, SSD1306_WHITE);
        display.fillRect(cx - 20 - 2, cy - 2, 4, 4, SSD1306_BLACK);
        display.fillRect(cx + 20 - 2, cy - 2, 4, 4, SSD1306_BLACK);
    }

    display.setTextSize(1);
    const char* subTitle = "PLAN APPROVAL REQ";
    display.getTextBounds(subTitle, 0, 0, &x1, &y1, &w, &h);
    display.setCursor((128 - w) / 2, 50);
    display.print(subTitle);

    display.setTextColor(SSD1306_WHITE, SSD1306_BLACK);
}

// ==========================================
// DATA FETCHING
// ==========================================
String httpStatusMsg = "OK";

const char* getWiFiStatusStr(wl_status_t status) {
    switch (status) {
        case WL_NO_SHIELD: return "NO_SHIELD";
        case WL_IDLE_STATUS: return "IDLE";
        case WL_NO_SSID_AVAIL: return "NO_SSID";
        case WL_SCAN_COMPLETED: return "SCAN_OK";
        case WL_CONNECTED: return "CONNECTED";
        case WL_CONNECT_FAILED: return "AUTH_FAIL";
        case WL_CONNECTION_LOST: return "LOST";
        case WL_DISCONNECTED: return "DISCONN";
        default: return "UNKNOWN";
    }
}

String backendUrl = "";
unsigned long lastMdnsResolve = 0;
const unsigned long mdnsResolveCooldownMs = 30000;

// Resolves the Mac's Bonjour hostname to its current IP via mDNS, so the
// backend URL keeps working regardless of which WiFi network the Mac is on
// or what IP it was handed by DHCP. Falls back to a fixed IP on networks
// that block mDNS multicast (some corporate/guest WiFi allow plain unicast
// between clients but filter multicast for security).
bool resolveBackendUrl() {
    IPAddress ip = MDNS.queryHost(backend_mdns_host, 3000);
    if (ip != IPAddress(0, 0, 0, 0)) {
        backendUrl = "http://" + ip.toString() + ":" + String(backend_port) + "/data";
        Serial.printf("[mDNS] Resolved %s.local -> %s\n", backend_mdns_host, ip.toString().c_str());
        return true;
    }
    Serial.printf("[mDNS] Failed to resolve %s.local, using fallback IP\n", backend_mdns_host);
    backendUrl = "http://" + String(backend_fallback_ip) + ":" + String(backend_port) + "/data";
    return false;
}

void fetchBackendData() {
    if (WiFi.status() != WL_CONNECTED) {
        wifiConnected = false;
        httpStatusMsg = getWiFiStatusStr(WiFi.status());
        return;
    }
    wifiConnected = true;

    if (backendUrl.length() == 0) {
        if (millis() - lastMdnsResolve > mdnsResolveCooldownMs) {
            lastMdnsResolve = millis();
            resolveBackendUrl();
        }
        httpStatusMsg = "NO_MDNS";
        return;
    }

    HTTPClient http;
    http.begin(backendUrl);
    http.setTimeout(2500);

    int httpCode = http.GET();
    if (httpCode <= 0) {
        // Connection-level failure (not just a bad HTTP status) -- the
        // Mac's IP likely changed. Re-resolve on the next fetch attempt.
        httpStatusMsg = "CONN_ERR " + String(httpCode);
        backendUrl = "";
        http.end();
        return;
    }
    if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        StaticJsonDocument<2048> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
            claudeData.limit = doc["claude"]["limit"] | 500000L;
            claudeData.remaining = doc["claude"]["remaining"] | 500000L;

            agData.limit = doc["antigravity"]["limit"] | 200;
            agData.used = doc["antigravity"]["used"] | 0;
            agData.remaining = doc["antigravity"]["remaining"] | 200;
            agData.period = doc["antigravity"]["period"].as<String>();

            if (doc["weather"].containsKey("temperature")) {
                weatherData.temp = doc["weather"]["temperature"].as<float>();
            } else {
                weatherData.temp = doc["weather"]["temp"] | 0.0f;
            }
            weatherData.hours_until_rain = doc["weather"]["hours_until_rain"] | -1;
            if (doc["weather"].containsKey("location_name")) {
                weatherData.location = doc["weather"]["location_name"].as<String>();
            } else if (doc["weather"].containsKey("location")) {
                weatherData.location = doc["weather"]["location"].as<String>();
            }

            timeData.hours = doc["time"]["hours"] | 12;
            timeData.minutes = doc["time"]["minutes"] | 0;
            timeData.seconds = doc["time"]["seconds"] | 0;
            timeData.time_str = doc["time"]["time_string"].as<String>();

            agentData.waiting_for_input = doc["agent"]["waiting_for_input"] | false;
            agentData.prompt_text = doc["agent"]["prompt_text"].as<String>();
            httpStatusMsg = "LIVE";
        } else {
            httpStatusMsg = "JSON_ERR";
        }
    } else {
        httpStatusMsg = "HTTP " + String(httpCode);
    }
    http.end();
}

// ==========================================
// I2C SCANNER HELPER
// ==========================================
uint8_t scanI2C() {
    Serial.println("\n--- Scanning I2C Bus on SDA=8, SCL=9 ---");
    uint8_t detected = 0;
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.printf(" [✓] I2C device found at address 0x%02X\n", addr);
            if (addr == 0x3C || addr == 0x3D) {
                detected = addr;
            }
        }
    }
    return detected;
}

// ==========================================
// SETUP & MAIN LOOP
// ==========================================
void setup() {
    Serial.begin(115200);
    delay(200);

    // Start I2C
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(400000); // 400kHz fast I2C for 30+ FPS animation

    // Scan I2C
    uint8_t detected = scanI2C();
    if (detected == 0) {
        detected = 0x3C;
    }
    oledAddress = detected;

    // Initialize OLED with charge pump enabled
    if (display.begin(SSD1306_SWITCHCAPVCC, oledAddress)) {
        oledFound = true;
    } else {
        display.begin(SSD1306_SWITCHCAPVCC, 0x3D);
        oledAddress = 0x3D;
    }

    // Wake-up Animation (Cute eyes opening)
    for (int i = 0; i <= 10; i++) {
        display.clearDisplay();
        drawEye(40, 32, 28, 40, 8, (float)i / 10.0f, 0, 0);
        drawEye(88, 32, 28, 40, 8, (float)i / 10.0f, 0, 0);
        display.display();
        delay(35);
    }
    delay(400);

    // WiFi Configuration
    WiFi.mode(WIFI_OFF);
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    delay(50);
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
        // Play gentle blinking animation while connecting
        updateFacePhysics(millis());
        display.clearDisplay();
        renderFaceScreen();
        display.display();
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.printf("[WiFi] SUCCESS! Local IP: %s\n", WiFi.localIP().toString().c_str());
        MDNS.begin("tinyscreen");
        resolveBackendUrl();
        lastMdnsResolve = millis();
        fetchBackendData();
    } else {
        wifiConnected = false;
        Serial.printf("[WiFi] Connection FAILED. Starting in Demo mode.\n");
    }

    lastScreenSwitch = millis();
}

unsigned long lastFrameTime = 0;
const unsigned long frameIntervalMs = 33; // ~30 FPS for buttery smooth animation

void loop() {
    unsigned long now = millis();

    // 1. Smooth ~30 FPS Face Physics & Animation Update
    if (now - lastFrameTime >= frameIntervalMs) {
        lastFrameTime = now;
        updateFacePhysics(now);

        display.clearDisplay();
        switch (currentScreen) {
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
        display.display();
    }

    // 2. Auto-reconnect Wi-Fi if lost
    static unsigned long lastWiFiCheck = 0;
    if (now - lastWiFiCheck >= 10000) {
        lastWiFiCheck = now;
        if (WiFi.status() != WL_CONNECTED) {
            WiFi.reconnect();
        }
    }

    // 3. Demo Time Counter (if offline)
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

    // 4. Fetch Backend Data every 3s
    if (now - lastBackendPoll >= backendPollInterval) {
        lastBackendPoll = now;
        fetchBackendData();
    }

    // 5. Automatic Screen Switcher
    if (agentData.waiting_for_input) {
        currentScreen = SCREEN_AGENT_ALERT;
    } else {
        if (now - lastScreenSwitch >= screenSwitchInterval) {
            lastScreenSwitch = now;
            // Cycle: Face (8s) -> Split HUD (8s) -> Quotas (8s) -> Weather (8s)
            if (currentScreen == SCREEN_FACE) currentScreen = SCREEN_SPLIT_HUD;
            else if (currentScreen == SCREEN_SPLIT_HUD) currentScreen = SCREEN_LIMITS;
            else if (currentScreen == SCREEN_LIMITS) currentScreen = SCREEN_CLOCK_WEATHER;
            else currentScreen = SCREEN_FACE;
        }
    }
}
