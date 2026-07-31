#include <Arduino.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Include standard TFT_eSPI FreeFonts
#include <Fonts/FreeSansBold12pt7b.h>
#include <Fonts/FreeSans9pt7b.h>

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

// Neo-Brutalist Color Palette (16-bit RGB565)
#define KINETIC_YELLOW 0xFFE0 // #FFFF00
#define KINETIC_CYAN   0x07FF // #00FFFF
#define KINETIC_LIME   0x07E0 // #00FF00
#define KINETIC_BLACK  0x0000 // #000000

void drawLimitsUI(TFT_eSprite* spr) {
    // 2. Clear background to Kinetic Yellow
    spr->fillSprite(KINETIC_YELLOW);

    // 3. Header Bar
    spr->fillRect(0, 0, 320, 32, KINETIC_BLACK);
    spr->setTextColor(KINETIC_YELLOW);
    spr->setTextDatum(MC_DATUM);
    spr->drawString("ILI9341 CTRL // KINETIC ZERO", 160, 16, 2);

    // 4. Calculate Percentages
    float claude_p = 0;
    if (claude_limit > 0) claude_p = (float)claude_remaining / claude_limit;
    
    float anti_p = 0;
    if (antigravity_limit > 0) anti_p = (float)antigravity_remaining / antigravity_limit;

    // --- CLAUDE SECTION ---
    int y1 = 48;
    spr->setTextColor(KINETIC_BLACK);
    spr->setFreeFont(&FreeSansBold12pt7b);
    spr->setTextDatum(TL_DATUM);
    spr->drawString("CLAUDE", 12, y1);
    
    // Percent Text
    spr->setTextDatum(TR_DATUM);
    spr->drawString(String((int)(claude_p * 100)) + "%", 240, y1);

    // Progress Bar (Neo-Brutalist chunky style)
    spr->drawRoundRect(12, y1 + 28, 230, 42, 4, KINETIC_BLACK);
    spr->drawRoundRect(13, y1 + 29, 228, 40, 4, KINETIC_BLACK); // Inner border for thickness
    int c_width = (int)(224 * claude_p);
    spr->fillRoundRect(15, y1 + 31, c_width, 36, 2, KINETIC_CYAN);

    // Raw Values
    spr->setFreeFont(&FreeSans9pt7b);
    spr->setTextDatum(TL_DATUM);
    spr->drawString(String(claude_remaining) + " / " + String(claude_limit), 12, y1 + 75);


    // --- ANTIGRAVITY SECTION ---
    int y2 = 142;
    spr->setFreeFont(&FreeSansBold12pt7b);
    spr->drawString("ANTIGRAVITY", 12, y2);
    
    // Percent Text
    spr->setTextDatum(TR_DATUM);
    spr->drawString(String((int)(anti_p * 100)) + "%", 240, y2);

    // Progress Bar
    spr->drawRoundRect(12, y2 + 28, 230, 42, 4, KINETIC_BLACK);
    spr->drawRoundRect(13, y2 + 29, 228, 40, 4, KINETIC_BLACK);
    int a_width = (int)(224 * anti_p);
    spr->fillRoundRect(15, y2 + 31, a_width, 36, 2, KINETIC_LIME);

    // Raw Values
    spr->setFreeFont(&FreeSans9pt7b);
    spr->setTextDatum(TL_DATUM);
    spr->drawString(String(antigravity_remaining) + " / " + String(antigravity_limit), 12, y2 + 75);


    // 5. Sidebar Divider and Diagnostics
    spr->fillRect(255, 32, 3, 208, KINETIC_BLACK);
    spr->setTextColor(KINETIC_BLACK);
    
    // Reset font for standard drawing
    spr->setTextFont(1);
    spr->setTextDatum(TC_DATUM);
    spr->drawString("STREAM", 288, 45, 2);
    
    // Minimalist Log (Monospace)
    spr->setTextDatum(TL_DATUM);
    spr->drawString("> KERNEL: OK", 265, 75, 1);
    spr->drawString("> SYNC: 0x2A", 265, 90, 1);
    spr->drawString("> FPS: 60", 265, 105, 1);
    
    // Reset datum back to TL for other screens
    spr->setTextDatum(TL_DATUM);
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
