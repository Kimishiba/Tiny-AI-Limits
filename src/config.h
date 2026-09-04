#pragma once
#include <Arduino.h>

#define FIRMWARE_VERSION "0.5"

// ==========================================
// PIN CONFIGURATION (ESP32-C3 SuperMini)
// ==========================================
// SPI Bus for GC9A01 Circular IPS (240x240) - Standard Pinout
#define GC9A01_SCK_PIN  4   // SCL -> GPIO 4 (Left Pin 4)
#define GC9A01_MOSI_PIN 6   // SDA -> GPIO 6 (Right Pin 2)
#define GC9A01_DC_PIN   7   // DC  -> GPIO 7 (Right Pin 3)
#define GC9A01_CS_PIN   5   // CS  -> GPIO 5 (Right Pin 1)
#define GC9A01_RST_PIN  1   // RST -> GPIO 1 (Left Pin 7)
#define GC9A01_BLK_PIN  -1  // Backlight hardwired to VCC on 7-pin display

// WS2812B Addressable LED Status Configuration (ESP32-C3 SuperMini)
#define WS2812_PIN 10
#define WS2812_MAX_LEDS 64
#define WS2812_DEFAULT_ACTIVE_LEDS 16

// ==========================================
// TIMING & THRESHOLDS
// ==========================================
const unsigned long wifiConnectTimeoutMs = 8000;
const unsigned long backendPollInterval = 3000;
const unsigned long sleepIdleThresholdMs = 15UL * 60UL * 1000UL;
const long claudeHeavyUsageThreshold = 2500000;

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
    SingleAgentInfo active_agents[8];
    String prompt_text = "APPROVE PLAN";
    String completion_text = "WORK COMPLETE";
};

struct LedConfig {
    String waiting_anim = "breathe";
    uint8_t brightness = 35;
    uint16_t active_leds = 16;
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
