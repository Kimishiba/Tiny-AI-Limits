#pragma once
#include <Arduino.h>

#define FIRMWARE_VERSION "0.5"

// ==========================================
// PIN CONFIGURATION (ESP32-C3 SuperMini)
// ==========================================
// SPI Bus for GC9A01 Circular IPS (240x240)
#define GC9A01_SCK_PIN  4
#define GC9A01_MOSI_PIN 6
#define GC9A01_CS_PIN   5
#define GC9A01_DC_PIN   7
#define GC9A01_RST_PIN  1
#define GC9A01_BLK_PIN  0

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
