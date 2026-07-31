#include <Arduino.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

TFT_eSPI tft = TFT_eSPI();
TFT_eSprite sprCurrent = TFT_eSprite(&tft);
TFT_eSprite sprNext = TFT_eSprite(&tft);

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* backend_url = "http://YOUR_DESKTOP_IP:5000/data"; // Updated endpoint

enum ScreenState {
    SCREEN_LIMITS,
    SCREEN_WEATHER
};

ScreenState currentScreen = SCREEN_LIMITS;

// Data variables
int claude_limit = 500000;
int claude_remaining = 500000;
int antigravity_limit = 100;
int antigravity_remaining = 100;
float current_temperature = 0.0;
int hours_until_rain = -1;

void drawLimitsUI(TFT_eSprite* spr) {
    spr->fillSprite(TFT_BLACK);
    
    // Draw Claude section
    spr->setTextColor(TFT_ORANGE, TFT_BLACK);
    spr->drawCentreString("Claude Limit", 160, 20, 4);
    
    int barWidth = 240;
    int barHeight = 25;
    int barX = 40;
    int barY = 50;
    
    spr->drawRoundRect(barX, barY, barWidth, barHeight, 5, TFT_WHITE);
    int fillWidth = 0;
    if (claude_limit > 0) fillWidth = (claude_remaining * barWidth) / claude_limit;
    spr->fillRoundRect(barX + 2, barY + 2, fillWidth - 4, barHeight - 4, 3, TFT_ORANGE);
    
    String claudeText = String(claude_remaining) + " / " + String(claude_limit);
    spr->setTextColor(TFT_WHITE, TFT_BLACK);
    spr->drawCentreString(claudeText, 160, 85, 2);

    // Draw Antigravity section
    spr->setTextColor(TFT_CYAN, TFT_BLACK);
    spr->drawCentreString("Antigravity Limit", 160, 125, 4);
    
    barY = 150;
    spr->drawRoundRect(barX, barY, barWidth, barHeight, 5, TFT_WHITE);
    fillWidth = 0;
    if (antigravity_limit > 0) fillWidth = (antigravity_remaining * barWidth) / antigravity_limit;
    spr->fillRoundRect(barX + 2, barY + 2, fillWidth - 4, barHeight - 4, 3, TFT_CYAN);
    
    String antiText = String(antigravity_remaining) + " / " + String(antigravity_limit);
    spr->setTextColor(TFT_WHITE, TFT_BLACK);
    spr->drawCentreString(antiText, 160, 185, 2);
}

void drawWeatherUI(TFT_eSprite* spr) {
    spr->fillSprite(TFT_BLACK);
    
    // Weather Title
    spr->setTextColor(TFT_YELLOW, TFT_BLACK);
    spr->drawCentreString("Daily Weather", 160, 30, 4);
    
    // Temperature
    String tempStr = String(current_temperature, 1) + " C";
    spr->setTextColor(TFT_WHITE, TFT_BLACK);
    spr->drawCentreString(tempStr, 160, 90, 7); // Large font
    
    // Rain info
    spr->setTextColor(TFT_SKYBLUE, TFT_BLACK);
    if (hours_until_rain == -1) {
        spr->drawCentreString("No rain expected today", 160, 180, 4);
    } else if (hours_until_rain == 0) {
        spr->drawCentreString("Raining right now!", 160, 180, 4);
    } else {
        String rainStr = "Next rain in: " + String(hours_until_rain) + " hours";
        spr->drawCentreString(rainStr, 160, 180, 4);
    }
}

void renderScreen(ScreenState state, TFT_eSprite* spr) {
    if (state == SCREEN_LIMITS) {
        drawLimitsUI(spr);
    } else {
        drawWeatherUI(spr);
    }
}

void doSlideTransition(ScreenState nextState) {
    // Render current screen to sprCurrent, and next screen to sprNext
    renderScreen(currentScreen, &sprCurrent);
    renderScreen(nextState, &sprNext);
    
    // Slide animation (Left swipe)
    int slideSteps = 20;
    for (int i = 0; i <= slideSteps; i++) {
        int xOffset = (320 * i) / slideSteps;
        
        // Push both sprites to screen at offset positions
        sprCurrent.pushSprite(-xOffset, 0);
        sprNext.pushSprite(320 - xOffset, 0);
        delay(10); // Adjust for speed
    }
    
    currentScreen = nextState;
}

void fetchData() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(backend_url);
        int httpResponseCode = http.GET();
        
        if (httpResponseCode > 0) {
            String payload = http.getString();
            
            StaticJsonDocument<512> doc;
            DeserializationError error = deserializeJson(doc, payload);
            
            if (!error) {
                claude_limit = doc["claude"]["limit"];
                claude_remaining = doc["claude"]["remaining"];
                antigravity_limit = doc["antigravity"]["limit"];
                antigravity_remaining = doc["antigravity"]["remaining"];
                current_temperature = doc["weather"]["temperature"];
                hours_until_rain = doc["weather"]["hours_until_rain"];
                
                // Immediately update current display
                renderScreen(currentScreen, &sprCurrent);
                sprCurrent.pushSprite(0, 0);
            }
        }
        http.end();
    }
}

void setup() {
    Serial.begin(115200);
    
    tft.init();
    tft.setRotation(1); 
    
    // Calibrate the touch screen
    uint16_t calData[5] = { 275, 3620, 264, 3532, 1 };
    tft.setTouch(calData);
    
    // Initialize Sprites (320x240, 16-bit color)
    sprCurrent.createSprite(320, 240);
    sprNext.createSprite(320, 240);
    
    sprCurrent.fillSprite(TFT_BLACK);
    sprCurrent.setTextColor(TFT_WHITE, TFT_BLACK);
    sprCurrent.drawCentreString("Connecting WiFi...", 160, 100, 2);
    sprCurrent.pushSprite(0, 0);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    sprCurrent.fillSprite(TFT_BLACK);
    sprCurrent.drawCentreString("WiFi Connected!", 160, 100, 2);
    sprCurrent.pushSprite(0, 0);
    delay(1000);
    
    fetchData();
}

unsigned long lastFetchTime = 0;
const unsigned long fetchInterval = 60000; 

void loop() {
    uint16_t x, y;
    bool touched = tft.getTouch(&x, &y);
    
    if (touched) {
        // Toggle screen state
        ScreenState nextState = (currentScreen == SCREEN_LIMITS) ? SCREEN_WEATHER : SCREEN_LIMITS;
        doSlideTransition(nextState);
        delay(500); // Debounce
    }
    
    if (millis() - lastFetchTime >= fetchInterval) {
        fetchData();
        lastFetchTime = millis();
    }
}
