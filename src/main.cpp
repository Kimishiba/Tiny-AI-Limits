#include <Arduino.h>
#include <TFT_eSPI.h>
#include <SPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

TFT_eSPI tft = TFT_eSPI();

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* backend_url = "http://YOUR_DESKTOP_IP:5000/limits"; // Replace with your desktop IP

// Dummy variables to hold limits
int claude_limit = 100;
int claude_remaining = 80;
int antigravity_limit = 50;
int antigravity_remaining = 15;

void drawLimitsUI() {
    tft.fillScreen(TFT_BLACK);
    
    // Draw Claude section
    tft.setTextColor(TFT_ORANGE, TFT_BLACK);
    tft.drawCentreString("Claude Limit", 160, 20, 4);
    
    // Draw Progress Bar
    int barWidth = 240;
    int barHeight = 25;
    int barX = 40;
    int barY = 50;
    
    tft.drawRect(barX, barY, barWidth, barHeight, TFT_WHITE);
    int fillWidth = (claude_remaining * barWidth) / claude_limit;
    tft.fillRect(barX + 1, barY + 1, fillWidth, barHeight - 2, TFT_ORANGE);
    
    // Draw value text
    String claudeText = String(claude_remaining) + " / " + String(claude_limit);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.drawCentreString(claudeText, 160, 85, 2);


    // Draw Antigravity section
    tft.setTextColor(TFT_CYAN, TFT_BLACK);
    tft.drawCentreString("Antigravity Limit", 160, 125, 4);
    
    barY = 150;
    tft.drawRect(barX, barY, barWidth, barHeight, TFT_WHITE);
    fillWidth = (antigravity_remaining * barWidth) / antigravity_limit;
    tft.fillRect(barX + 1, barY + 1, fillWidth, barHeight - 2, TFT_CYAN);
    
    // Draw value text
    String antiText = String(antigravity_remaining) + " / " + String(antigravity_limit);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.drawCentreString(antiText, 160, 185, 2);
}

void fetchLimits() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(backend_url);
        int httpResponseCode = http.GET();
        
        if (httpResponseCode > 0) {
            String payload = http.getString();
            Serial.println(payload);
            
            StaticJsonDocument<200> doc;
            DeserializationError error = deserializeJson(doc, payload);
            
            if (!error) {
                claude_limit = doc["claude"]["limit"];
                claude_remaining = doc["claude"]["remaining"];
                antigravity_limit = doc["antigravity"]["limit"];
                antigravity_remaining = doc["antigravity"]["remaining"];
                
                drawLimitsUI();
            }
        }
        http.end();
    }
}

void setup() {
    Serial.begin(115200);
    
    tft.init();
    tft.setRotation(1); // Adjust rotation as needed (1 is usually landscape for ILI9341)
    
    // Calibrate the touch screen (these values might need adjustment for your specific screen)
    uint16_t calData[5] = { 275, 3620, 264, 3532, 1 };
    tft.setTouch(calData);
    
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.drawCentreString("Connecting WiFi...", 160, 100, 2);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    tft.fillScreen(TFT_BLACK);
    tft.drawCentreString("WiFi Connected!", 160, 100, 2);
    delay(1000);
    
    // Initial draw
    drawLimitsUI();
}

unsigned long lastFetchTime = 0;
const unsigned long fetchInterval = 60000; // 60 seconds

void loop() {
    uint16_t x, y;
    bool touched = tft.getTouch(&x, &y);
    
    // Fetch limits if touched (manual refresh) OR if 60 seconds have passed
    if (touched || (millis() - lastFetchTime >= fetchInterval)) {
        if (touched) {
            // Draw a quick "Refreshing..." indicator if manually tapped
            tft.setTextColor(TFT_YELLOW, TFT_BLACK);
            tft.drawCentreString("Refreshing...", 160, 220, 2);
        }
        
        fetchLimits();
        lastFetchTime = millis();
        
        // Simple debounce
        if (touched) delay(500); 
    }
}
