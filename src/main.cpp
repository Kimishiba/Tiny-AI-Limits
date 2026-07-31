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

#define KINETIC_YELLOW 0xFFE0 // #FFFF00
#define KINETIC_CYAN   0x07FF // #00FFFF
#define KINETIC_LIME   0x07E0 // #00FF00
#define KINETIC_BLACK  0x0000 // #000000
#define KINETIC_DARK   0x1082 // Dark grey/black for surfaces

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
    // 1. Clear Background
    spr->fillSprite(KINETIC_BLACK);
    
    // 2. Draw Main Frame (Industrial Border)
    spr->drawRect(0, 0, 320, 240, KINETIC_YELLOW);
    spr->drawRect(1, 1, 318, 238, KINETIC_YELLOW); // 2px thickness

    // 3. Header: SYS_CTRL
    spr->fillRect(0, 0, 320, 28, KINETIC_YELLOW);
    spr->setTextColor(KINETIC_BLACK);
    spr->setTextDatum(ML_DATUM);
    spr->drawString("SYS_CTRL // V.04_KINETIC", 10, 14, 2);
    spr->setTextDatum(MR_DATUM);
    spr->drawString("88% [^]", 310, 14, 2);

    // 4. Central Weather Block
    int bx = 10, by = 38, bw = 170, bh = 110;
    spr->drawRect(bx, by, bw, bh, KINETIC_YELLOW);
    spr->setTextColor(KINETIC_YELLOW);
    
    // Label: Location
    spr->setTextDatum(TL_DATUM);
    spr->drawString("LOC: NEO_BERLIN", bx + 8, by + 8, 2);
    
    // Big Temperature
    spr->setTextDatum(MC_DATUM);
    char temp_str[10];
    dtostrf(current_temperature, 4, 1, temp_str);
    strcat(temp_str, "C");
    spr->drawString(temp_str, bx + (bw/2) - 20, by + (bh/2) + 10, 7); // Font 7 is big
    
    // Stylized Sun Icon (Neo-Brutalist Geometry)
    int ix = bx + bw - 45, iy = by + 45;
    spr->fillCircle(ix, iy, 15, KINETIC_YELLOW);
    for(int i=0; i<8; i++) { // Sun rays
        float angle = i * 45 * 0.01745;
        int rx = ix + cos(angle) * 22;
        int ry = iy + sin(angle) * 22;
        spr->fillRect(rx-2, ry-2, 5, 5, KINETIC_YELLOW);
    }

    // 5. Rain Forecast Bar (Cyan Accent)
    int rx = 10, ry = 158, rw = 300, rh = 65;
    spr->drawRect(rx, ry, rw, rh, KINETIC_CYAN);
    spr->setTextColor(KINETIC_CYAN);
    spr->setTextDatum(TL_DATUM);
    spr->drawString("HOURS UNTIL RAIN", rx + 8, ry + 8, 2);
    
    // Large Countdown
    spr->setTextDatum(TR_DATUM);
    if (hours_until_rain == -1) {
        spr->drawString("NONE", rx + rw - 10, ry + 15, 7);
    } else {
        char rain_str[10];
        sprintf(rain_str, "%02d.0", hours_until_rain);
        spr->drawString(rain_str, rx + rw - 10, ry + 15, 7);
    }
    
    // Progress-style visualizer
    for(int i=0; i<12; i++) {
        int bar_w = 20;
        int spacing = 4;
        int bar_x = rx + 8 + (i * (bar_w + spacing));
        if (i < 8) { // Active segments
            spr->fillRect(bar_x, ry + 45, bar_w, 12, KINETIC_CYAN);
        } else { // Empty segments
            spr->drawRect(bar_x, ry + 45, bar_w, 12, KINETIC_CYAN);
        }
    }

    // 6. Sidebar: Diagnostics (Stream)
    int sx = 190, sy = 38, sw = 120, sh = 110;
    spr->drawRect(sx, sy, sw, sh, KINETIC_YELLOW);
    spr->fillRect(sx, sy, sw, 20, KINETIC_YELLOW);
    spr->setTextColor(KINETIC_BLACK);
    spr->setTextDatum(MC_DATUM);
    spr->drawString("DIAGNOSTICS", sx + (sw/2), sy + 10, 2);
    
    spr->setTextColor(KINETIC_CYAN);
    spr->setTextDatum(TL_DATUM);
    spr->drawString("> DATA_RECV", sx + 8, sy + 65, 1);
    spr->drawString("[OK]", sx + 8, sy + 75, 1);
    spr->setTextColor(KINETIC_YELLOW);
    spr->drawString("> TEMP_SYNC:", sx + 8, sy + 90, 1);

    // 7. Footer
    spr->fillRect(0, 225, 320, 15, KINETIC_YELLOW);
    spr->setTextColor(KINETIC_BLACK);
    spr->setTextDatum(ML_DATUM);
    spr->drawString("STATUS: OK", 5, 232, 1);
    spr->setTextDatum(MR_DATUM);
    spr->drawString("08:45:22 // CLD_01", 315, 232, 1);
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
