#include <Arduino.h>
#include <Arduino_GFX_Library.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ST77916 SPI Display Pins
#define TFT_SCLK 18
#define TFT_MOSI 23
#define TFT_MISO 19
#define TFT_CS   15
#define TFT_DC   2
#define TFT_RST  4

Arduino_DataBus *bus = new Arduino_ESP32SPI(TFT_DC, TFT_CS, TFT_SCLK, TFT_MOSI, TFT_MISO);
Arduino_GFX *gfx = new Arduino_ST77916(bus, TFT_RST, 0 /* rotation */, true /* IPS */, 360 /* width */, 360 /* height */);
Arduino_Canvas *sprCurrent = new Arduino_Canvas(360, 360, gfx);
Arduino_Canvas *sprNext = new Arduino_Canvas(360, 360, gfx);

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
String date_string = "LOADING...";

#define KINETIC_YELLOW 0xFFE0 // #FFFF00
#define KINETIC_CYAN   0x07FF // #00FFFF
#define KINETIC_LIME   0x07E0 // #00FF00
#define KINETIC_AMBER  0xFD20 // #FF6600 Warm Amber/Orange
#define KINETIC_BLACK  0x0000 // #000000
#define KINETIC_DARK   0x1082 // Dark grey/black for surfaces

bool waiting_for_input = false;
String prompt_text = "APPROVE PLAN";
unsigned long lastBlinkTime = 0;
bool blinkState = false;

void drawLimitsUI(TFT_eSprite* spr) {
    // Fill entire sprite with Kinetic Black first
    spr->fillSprite(KINETIC_BLACK);

    // 1. Top Header Bar (0 to 24)
    spr->fillRect(0, 0, 320, 24, KINETIC_BLACK);
    spr->setTextColor(KINETIC_YELLOW);
    spr->setTextDatum(ML_DATUM);
    spr->setFreeFont(&FreeSans9pt7b);
    
    // Draw date on the left
    spr->drawString(date_string, 10, 11, 1);
    
    // Draw temperature on the right
    char temp_top[10];
    dtostrf(current_temperature, 4, 1, temp_top);
    strcat(temp_top, " C");
    spr->setTextDatum(MR_DATUM);
    spr->drawString(temp_top, 310, 11, 1);

    // 2. Main Content Area (Yellow)
    spr->fillRect(5, 24, 310, 140, KINETIC_YELLOW);
    
    // Vertical Divider
    int midX = 180;
    spr->fillRect(midX, 24, 5, 140, KINETIC_BLACK);

    // Calculate Percentages
    float claude_p = 0;
    if (claude_limit > 0) claude_p = (float)claude_remaining / claude_limit;
    
    float anti_p = 0;
    if (antigravity_limit > 0) anti_p = (float)antigravity_remaining / antigravity_limit;

    // --- CLAUDE SECTION (Left) ---
    int lx = 12;
    int y1 = 30;
    spr->setTextColor(KINETIC_BLACK);
    spr->setFreeFont(&FreeSansBold12pt7b);
    spr->setTextDatum(TL_DATUM);
    spr->drawString("CLAUDE", lx, y1);
    spr->setTextDatum(TR_DATUM);
    spr->drawString(String((int)(claude_p * 100)) + "%", midX - 8, y1);

    // Progress Bar (Thick border, yellow empty space, cyan fill)
    spr->fillRect(lx, y1 + 25, midX - 20, 24, KINETIC_BLACK); // outer border
    spr->fillRect(lx + 3, y1 + 28, midX - 26, 18, KINETIC_YELLOW); // empty area
    int c_width = (int)((midX - 26) * claude_p);
    if (c_width > 0) spr->fillRect(lx + 3, y1 + 28, c_width, 18, KINETIC_CYAN); // fill
    spr->fillRect(lx + 3 + c_width, y1 + 28, 3, 18, KINETIC_BLACK); // inner dividing line

    // Raw Values
    spr->setTextFont(1);
    spr->setTextDatum(TL_DATUM);
    spr->drawString(String(claude_remaining) + " / " + String(claude_limit), lx, y1 + 54, 2);

    // --- ANTIGRAVITY SECTION (Left) ---
    int y2 = 100;
    spr->setFreeFont(&FreeSansBold12pt7b);
    spr->drawString("ANTIGRAVITY", lx, y2);
    spr->setTextDatum(TR_DATUM);
    spr->drawString(String((int)(anti_p * 100)) + "%", midX - 8, y2);

    // Progress Bar
    spr->fillRect(lx, y2 + 25, midX - 20, 24, KINETIC_BLACK);
    spr->fillRect(lx + 3, y2 + 28, midX - 26, 18, KINETIC_YELLOW);
    int a_width = (int)((midX - 26) * anti_p);
    if (a_width > 0) spr->fillRect(lx + 3, y2 + 28, a_width, 18, KINETIC_LIME);
    spr->fillRect(lx + 3 + a_width, y2 + 28, 3, 18, KINETIC_BLACK);

    // Raw Values
    spr->setTextFont(1);
    spr->setTextDatum(TL_DATUM);
    spr->drawString(String(antigravity_remaining) + " / " + String(antigravity_limit), lx, y2 + 54, 2);

    // --- SYSTEM STREAM SECTION (Right) ---
    int rx = midX + 10;
    
    if (waiting_for_input) {
        // Amber Alert System Stream Box
        uint16_t alertColor = blinkState ? KINETIC_AMBER : KINETIC_BLACK;
        uint16_t textColor  = blinkState ? KINETIC_BLACK : KINETIC_AMBER;
        
        spr->fillRect(rx - 4, 26, 130, 134, alertColor);
        spr->setTextColor(textColor);
        spr->setTextDatum(TL_DATUM);
        spr->drawString("! ATTENTION !", rx, 30, 2);
        spr->drawString("> AGENT: WAITING", rx, 52, 2);
        spr->drawString("> INPUT REQ", rx, 70, 2);
        spr->drawString("> " + prompt_text, rx, 88, 2);
        spr->drawString("> ACTION NEEDED", rx, 106, 2);
        if (blinkState) {
            spr->fillRect(rx, 126, 12, 12, textColor); // Retro Cursor
        }
    } else {
        spr->setTextColor(KINETIC_BLACK);
        spr->setTextDatum(TL_DATUM);
        spr->drawString("SYSTEM STREAM", rx, 30, 2);
        spr->drawLine(rx, 46, 310, 46, KINETIC_BLACK); // underline

        // Monospace Logs
        spr->drawString("> KERNEL: ACTIVE", rx, 52, 2);
        spr->drawString("> MEM_SYNC: 0X2A", rx, 70, 2);
        spr->drawString("> PWR_CELL: NOM", rx, 88, 2);
        spr->drawString("> FR_RATE: 60FPS", rx, 106, 2);
        spr->drawString("> UPLINK: OK", rx, 124, 2);
    }

    // 3. Status Bar (164 to 194)
    spr->fillRect(0, 164, 320, 30, KINETIC_BLACK);
    spr->setTextDatum(ML_DATUM);
    if (waiting_for_input) {
        spr->setTextColor(KINETIC_AMBER);
        spr->drawString("! INPUT REQUIRED !", 10, 179, 2);
        spr->setTextDatum(MR_DATUM);
        spr->drawString("STATUS: WAITING", 310, 179, 2);
        uint16_t sqColor = blinkState ? KINETIC_AMBER : KINETIC_BLACK;
        spr->fillRect(190, 174, 10, 10, sqColor); // Blinking amber square
    } else {
        spr->setTextColor(KINETIC_YELLOW);
        spr->drawString("08:45:22.04", 10, 179, 2);
        spr->setTextDatum(MR_DATUM);
        spr->drawString("STATUS: OPERATIONAL", 310, 179, 2);
        spr->fillRect(195, 174, 10, 10, KINETIC_LIME); // Green status square
    }

    // 4. Navigation Footer (194 to 240)
    int tabW = 320 / 4;
    // Active Tab (Yellow)
    spr->fillRect(0, 194, tabW, 46, KINETIC_YELLOW);
    // Draw Grid Icon
    int cx = tabW / 2;
    int cy = 194 + 23;
    spr->fillRect(cx - 8, cy - 8, 6, 6, KINETIC_BLACK);
    spr->fillRect(cx + 2, cy - 8, 6, 6, KINETIC_BLACK);
    spr->fillRect(cx - 8, cy + 2, 6, 6, KINETIC_BLACK);
    spr->fillRect(cx + 2, cy + 2, 6, 6, KINETIC_BLACK);

    // Draw lines between tabs
    spr->drawLine(tabW, 194, tabW, 240, KINETIC_DARK);
    spr->drawLine(tabW * 2, 194, tabW * 2, 240, KINETIC_DARK);
    spr->drawLine(tabW * 3, 194, tabW * 3, 240, KINETIC_DARK);

    // Icon 2 (Chart placeholder)
    cx = (tabW * 1) + (tabW / 2);
    spr->drawRect(cx - 8, cy - 8, 16, 16, KINETIC_DARK);
    spr->fillRect(cx - 4, cy, 3, 8, KINETIC_DARK);
    spr->fillRect(cx, cy - 4, 3, 12, KINETIC_DARK);

    // Icon 3 (Chip placeholder)
    cx = (tabW * 2) + (tabW / 2);
    spr->drawRect(cx - 6, cy - 6, 12, 12, KINETIC_DARK);
    spr->fillRect(cx - 8, cy - 3, 2, 6, KINETIC_DARK);
    spr->fillRect(cx + 6, cy - 3, 2, 6, KINETIC_DARK);

    // Icon 4 (Settings gear placeholder)
    cx = (tabW * 3) + (tabW / 2);
    spr->drawCircle(cx, cy, 6, KINETIC_DARK);
    spr->drawLine(cx - 9, cy, cx + 9, cy, KINETIC_DARK);
    spr->drawLine(cx, cy - 9, cx, cy + 9, KINETIC_DARK);
}

void drawWeatherUI(TFT_eSprite* spr) {
    // 1. Clear Background
    spr->fillSprite(KINETIC_BLACK);
    
    // 2. Draw Main Frame (Industrial Border)
    spr->drawRect(0, 0, 320, 240, KINETIC_YELLOW);
    spr->drawRect(1, 1, 318, 238, KINETIC_YELLOW); // 2px thickness

    // 3. Header
    spr->fillRect(0, 0, 320, 28, KINETIC_YELLOW);
    spr->setTextColor(KINETIC_BLACK);
    spr->setTextDatum(ML_DATUM);
    spr->drawString(date_string, 10, 14, 2);
    
    char temp_top_w[10];
    dtostrf(current_temperature, 4, 1, temp_top_w);
    strcat(temp_top_w, " C");
    spr->setTextDatum(MR_DATUM);
    spr->drawString(temp_top_w, 310, 14, 2);

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
                
                if (doc["weather"].containsKey("date_string")) {
                    const char* dateStr = doc["weather"]["date_string"];
                    date_string = String(dateStr);
                }
                
                if (doc.containsKey("agent")) {
                    waiting_for_input = doc["agent"]["waiting_for_input"] | false;
                    if (doc["agent"].containsKey("prompt_text")) {
                        prompt_text = String((const char*)doc["agent"]["prompt_text"]);
                    }
                }
                
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
    
    gfx->begin();
    gfx->fillScreen(BLACK);
    
    // Initialize Canvas (360x360)
    sprCurrent->begin();
    sprNext->begin();
    
    sprCurrent->fillScreen(BLACK);
    sprCurrent->setTextColor(WHITE);
    sprCurrent->setTextSize(2);
    sprCurrent->setCursor(80, 170);
    sprCurrent->println("Connecting WiFi...");
    sprCurrent->flush();
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    sprCurrent->fillScreen(BLACK);
    sprCurrent->setCursor(90, 170);
    sprCurrent->println("WiFi Connected!");
    sprCurrent->flush();
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
    
    // Blinking animation logic (500ms cycle when waiting for input)
    if (waiting_for_input && (millis() - lastBlinkTime >= 500)) {
        lastBlinkTime = millis();
        blinkState = !blinkState;
        renderScreen(currentScreen, &sprCurrent);
        sprCurrent.pushSprite(0, 0);
    }
    
    if (millis() - lastFetchTime >= fetchInterval) {
        fetchData();
        lastFetchTime = millis();
    }
}
