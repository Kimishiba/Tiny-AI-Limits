#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
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
const unsigned long screenSwitchInterval = 6000;

enum ScreenMode {
    SCREEN_LIMITS = 0,
    SCREEN_CLOCK_WEATHER = 1,
    SCREEN_AGENT_ALERT = 2
};

ScreenMode currentScreen = SCREEN_LIMITS;
bool wifiConnected = false;
bool oledFound = false;
uint8_t oledAddress = 0x3C;
int blinkCounter = 0;

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
    if (detected == 0) {
        Serial.println(" [X] No OLED found at 0x3C or 0x3D. Check wiring!");
    }
    return detected;
}

// ==========================================
// DRAWING ROUTINES (Adafruit GFX)
// ==========================================

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
    float claudePercent = claudeData.limit > 0 ? (float)claudeUsed / (float)claudeData.limit : 0.0;
    
    display.setTextSize(1);
    display.setCursor(2, 16);
    display.printf("Claude: %ldk/%ldk", claudeUsed / 1000, claudeData.limit / 1000);
    drawProgressBar(2, 26, 124, 6, claudePercent);

    // Antigravity Quota
    float agPercent = agData.limit > 0 ? (float)agData.used / (float)agData.limit : 0.0;
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
    display.setCursor((128 - w) / 2, 10);
    display.print(alertTitle);

    display.setTextSize(1);
    const char* subTitle = "INPUT REQUIRED";
    display.getTextBounds(subTitle, 0, 0, &x1, &y1, &w, &h);
    display.setCursor((128 - w) / 2, 26);
    display.print(subTitle);

    display.getTextBounds(agentData.prompt_text.c_str(), 0, 0, &x1, &y1, &w, &h);
    display.setCursor((128 - w) / 2, 42);
    display.print(agentData.prompt_text);

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

// ==========================================
// DATA FETCHING
// ==========================================
void fetchBackendData() {
    if (WiFi.status() != WL_CONNECTED) {
        wifiConnected = false;
        httpStatusMsg = getWiFiStatusStr(WiFi.status());
        return;
    }
    wifiConnected = true;

    HTTPClient http;
    http.begin(backend_url);
    http.setTimeout(2500);

    int httpCode = http.GET();
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
// SETUP & MAIN LOOP
// ==========================================
void setup() {
    Serial.begin(115200);
    delay(200);

    // Start I2C
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(100000);

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

    // Register detailed WiFi event listener
    WiFi.onEvent([](WiFiEvent_t event, WiFiEventInfo_t info) {
        if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
            Serial.printf("[WiFi-Event] Disconnected! Reason Code: %d\n", info.wifi_sta_disconnected.reason);
        } else if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
            Serial.printf("[WiFi-Event] Got IP: %s\n", IPAddress(info.got_ip.ip_info.ip.addr).toString().c_str());
        }
    });

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);

    display.setCursor(4, 2);
    display.println("CONNECTING WIFI...");
    display.setCursor(4, 18);
    display.printf("SSID: %s", ssid);
    display.drawFastHLine(0, 11, 128, SSD1306_WHITE);
    display.display();

    WiFi.mode(WIFI_OFF);
    delay(200);
    WiFi.mode(WIFI_STA);
    WiFi.setSleep(false);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
    delay(100);
    WiFi.disconnect(true, true);
    delay(100);

    Serial.printf("\n[WiFi] Connecting to '%s'...\n", ssid);
    WiFi.begin(ssid, password);

    unsigned long connectStart = millis();
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && millis() - connectStart < wifiConnectTimeoutMs) {
        delay(500);
        attempts++;
        Serial.printf("  Attempt %d... Status: %s (%d)\n", attempts, getWiFiStatusStr(WiFi.status()), WiFi.status());
        drawProgressBar(4, 48, 120, 8, (float)(millis() - connectStart) / (float)wifiConnectTimeoutMs);
        display.display();
    }
    display.clearDisplay();

    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(6, 8);
    display.println("WI-FI RESULT");
    display.drawFastHLine(0, 18, 128, SSD1306_WHITE);

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.printf("[WiFi] SUCCESS! Connected to '%s'. Local IP: %s\n", ssid, WiFi.localIP().toString().c_str());
        display.setCursor(6, 26);
        display.println("SUCCESS! Connected.");
        display.setCursor(6, 40);
        display.printf("IP: %s", WiFi.localIP().toString().c_str());
        display.display();
        delay(1500);
        // Immediate first fetch
        fetchBackendData();
    } else {
        wifiConnected = false;
        Serial.printf("[WiFi] Connection FAILED. Final Status: %s (%d)\n", getWiFiStatusStr(WiFi.status()), WiFi.status());
        display.setCursor(6, 26);
        display.println("Connection Failed!");
        display.setCursor(6, 40);
        display.printf("Code: %s", getWiFiStatusStr(WiFi.status()));
        display.display();
        delay(2500);
    }
}


void loop() {
    unsigned long now = millis();

    // Auto-reconnect Wi-Fi if lost
    static unsigned long lastWiFiCheck = 0;
    if (now - lastWiFiCheck >= 10000) {
        lastWiFiCheck = now;
        if (WiFi.status() != WL_CONNECTED) {
            WiFi.reconnect();
        }
    }

    // Increment demo time counter if offline
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

    // Fetch Backend Data
    if (now - lastBackendPoll >= backendPollInterval) {
        lastBackendPoll = now;
        fetchBackendData();
    }

    // Switch Screens
    if (agentData.waiting_for_input) {
        currentScreen = SCREEN_AGENT_ALERT;
    } else {
        if (now - lastScreenSwitch >= screenSwitchInterval) {
            lastScreenSwitch = now;
            currentScreen = (currentScreen == SCREEN_LIMITS) ? SCREEN_CLOCK_WEATHER : SCREEN_LIMITS;
        }
    }

    // Render Display
    display.clearDisplay();
    switch (currentScreen) {
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

    delay(agentData.waiting_for_input ? 400 : 200);
}

