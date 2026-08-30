# 🌐 WebSerial Provisioning & Web UI

**Tiny AI Limits** provides a browser-based management and emulation suite accessible at `http://localhost:5000`. It features zero-install **WebSerial API** USB provisioning, live gauge configuration, and a full-fidelity HTML5 Canvas hardware emulator.

---

## ⚡ WebSerial USB Provisioning Interface (`/setup`)

Built using the modern W3C **WebSerial API**, the setup interface enables direct bidirectional serial communication between Google Chrome / Microsoft Edge and the ESP32-C3 microcontroller over standard USB-C without requiring external driver installations or CLI flashing tools.

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                    TINY AI SCREEN - DEVICE SETUP                       │
 │                                                                        │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │ 🔌 STEP 1: CONNECT & PROVISION VIA SERIAL                        │  │
 │  │                                                                  │  │
 │  │   [ Connect Board (Direct Serial Setup) ]                         │  │
 │  │                                                                  │  │
 │  │   SSID: [ MyOfficeWiFi          ]                                │  │
 │  │   PASS: [ •••••••••••••••••     ]                                │  │
 │  │                                                                  │  │
 │  │   [ CONFIGURE & PAIR TO THIS HOST ]                              │  │
 │  └──────────────────────────────────────────────────────────────────┘  │
 │                                                                        │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │ 🎛️ STEP 2: DUAL HUD GAUGE CUSTOMIZER                             │  │
 │  │                                                                  │  │
 │  │   LEFT GAUGE:   [ Anthropic Claude   ▼ ]   MODE: (•) 5h Reset    │  │
 │  │   RIGHT GAUGE:  [ Google Antigravity ▼ ]   MODE: (•) Spend ($)   │  │
 │  │                                                                  │  │
 │  │   DAILY BUDGET ($ USD): [   5.00 ]                               │  │
 │  └──────────────────────────────────────────────────────────────────┘  │
 └────────────────────────────────────────────────────────────────────────┘
```

### Key Features of `/setup`:
* **Direct Serial Protocol:** Sends `WIFI:<ssid>:<pass>:<pair_id>` strings directly over the WebSerial text stream.
* **Improv Wi-Fi Compatibility:** Full fallback support for the standardized Improv-WiFi BLE/Serial protocol.
* **Live Configuration Sync:** Changes made to gauge providers or daily budget limits are immediately saved to `~/.tiny_ai_screen/config.json` and pushed to the display.
* **Collapsible Cloud API Keys:** Clean, secure accordions for entering OpenRouter, DeepSeek, Groq, and Mistral API keys with local encryption.

---

## 🖥️ Full Display Browser Emulator (`/emulator`)

The project includes an interactive 60 FPS HTML5 Canvas visualizer that faithfully reproduces all graphics routines, radial math, mascot animations, and alert states of the physical circular display.

```
                       ╭────────────────────────╮
                     ╭─╯        21.5°C          ╰─╮
                    ╭╯      CLEAR SKY (0% RAIN)   ╰╮
                   ╭╯                              ╰╮
                   │  [CLAUDE]           [AGY]      │
                   │   84.5%             $0.13      │
                   │  REMAINING         SPEND TODAY │
                   │  (4h 32m)          (28.2k TOK) │
                   │ ────────────────────────────── │
                   │ AGENT 1: CAD SPECIALIST (WORK) │
                   │ AGENT 2: ARCHITECT     (WAIT)  │
                   │ AGENT 3: QA TESTER     (DONE)  │
                   ╰╮                              ╭╯
                    ╰╮     PULSING GREEN CROWN    ╭╯
                     ╰─╮   (PAIRED & ACTIVE)    ╭─╯
                       ╰────────────────────────╯
```

### Capabilities of the Browser Visualizer:
1. **Live Data Binding:** Polls `/api/limits` in real time, reflecting exactly what the physical hardware renders.
2. **State Simulation Controls:** Test suite toolbar to inject mock states, trigger agent approval warnings, simulate network disconnections, and test weather forecast transitions.
3. **Circular Anti-Aliasing:** Replicates the 240×240 pixel circular boundary mask and pixel aspect ratio of the GC9A01 panel.
4. **Development Sandboxing:** Perfect for designing new UI widgets, mascot animations, or themes without needing hardware connected.
