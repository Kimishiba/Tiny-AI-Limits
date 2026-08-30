# 🐍 Backend Companion App & Server Architecture

The **Tiny AI Limits** companion application is a lightweight Python service built on **Flask** and **Zeroconf**. It runs locally on your workstation, continuously aggregating agent state telemetry, monitoring quota budgets, fetching local weather forecasts, and serving a high-performance REST API to paired hardware displays.

---

## 🏛️ System Architecture

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Host Workstation (Python 3.10+)                    │
 │                                                                        │
 │  ┌─────────────────────────┐         ┌──────────────────────────────┐  │
 │  │   AI Agent Transcripts  │         │    Cloud Provider APIs       │  │
 │  │  (Claude Code / AGY)    │         │ (OpenRouter / DeepSeek / etc)│  │
 │  └────────────┬────────────┘         └──────────────┬───────────────┘  │
 │               │                                     │                  │
 │               ▼                                     ▼                  │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                 Provider Adapter Engine (providers/)             │  │
 │  │        Standard 5h Reset Calculator  |  Spend & Token Aggregator  │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 │                                     │                                  │
 │                                     ▼                                  │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                         Flask REST Service                       │  │
 │  │                                                                  │  │
 │  │   /api/limits      /api/pairing      /setup      /emulator        │  │
 │  └────────────┬─────────────────────────────────────────────────────┘  │
 │               │                                                        │
 │               ▼                                                        │
 │  ┌─────────────────────────┐                                           │
 │  │    mDNS Zeroconf Daemon │ ──> Advertises _tinyscreen._tcp.local.     │
 │  │   (Broadcasts pair_id)  │     with host IP & TXT record             │
 │  └─────────────────────────┘                                           │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 🌐 REST API Endpoints

### 1. `GET /api/limits`
The primary telemetry payload polled by both physical displays and the browser emulator.

#### Example JSON Response
```json
{
  "status": "ok",
  "pair_id": "e83f12a9-c091-49b8-a726-0e7841c5d98a",
  "left_gauge": {
    "provider": "claude",
    "name": "Claude 3.7 Sonnet",
    "percent_remaining": 84.5,
    "reset_in_seconds": 16320,
    "reset_formatted": "4h 32m",
    "mode": "standard",
    "status": "healthy"
  },
  "right_gauge": {
    "provider": "antigravity",
    "name": "Google Antigravity",
    "spend_usd": 0.13,
    "budget_usd": 5.00,
    "tokens_24h": 28240,
    "tokens_formatted": "28.2k",
    "percent_used": 2.6,
    "mode": "enterprise",
    "status": "healthy"
  },
  "agents": [
    {
      "id": "agent-1",
      "name": "CAD Specialist",
      "state": "WORKING",
      "requires_approval": false,
      "updated_at": 1740000000
    },
    {
      "id": "agent-2",
      "name": "Firmware Architect",
      "state": "WAITING",
      "requires_approval": true,
      "updated_at": 1740000010
    },
    {
      "id": "agent-3",
      "name": "QA Tester",
      "state": "COMPLETE",
      "requires_approval": false,
      "updated_at": 1740000020
    }
  ],
  "weather": {
    "temperature_c": 21.5,
    "weather_code": 0,
    "condition": "Clear Sky",
    "precipitation_probability": 0,
    "is_day": 1
  }
}
```

### 2. `POST /api/pairing`
Handles browser pairing requests and manual IP pinning.
* **Payload:** `{"pair_id": "UUID", "device_ip": "192.168.1.150"}`
* **Response:** `{"status": "paired", "message": "Device successfully registered"}`

### 3. `GET /api/weather`
Returns standalone meteorological data calculated from Open-Meteo's non-commercial geocoded API.

---

## 📡 Zero-Config mDNS Discovery

The companion backend automatically starts a Zeroconf service daemon advertising on the local network:

```python
from zeroconf import ServiceInfo, Zeroconf

desc = {
    b'pair_id': current_pair_id.encode('utf-8'),
    b'version': b'2.0.0',
    b'port': b'5000'
}

info = ServiceInfo(
    "_tinyscreen._tcp.local.",
    f"TinyScreen-{hostname}._tinyscreen._tcp.local.",
    addresses=[socket.inet_aton(local_ip)],
    port=5000,
    properties=desc
)

zeroconf.register_service(info)
```

When an ESP32 boots, it scans for `_tinyscreen._tcp` services, inspects the `pair_id` property in the TXT record, and immediately resolves the host's IP address without requiring hardcoded network settings.

---

## 📁 Configuration File (`~/.tiny_ai_screen/config.json`)

User configurations, provider API keys, and paired hardware UUIDs are stored in your home directory:

```json
{
  "pair_id": "e83f12a9-c091-49b8-a726-0e7841c5d98a",
  "left_provider": "claude",
  "left_mode": "standard",
  "right_provider": "antigravity",
  "right_mode": "enterprise",
  "daily_budget_usd": 5.00,
  "weather": {
    "enabled": true,
    "latitude": 37.7749,
    "longitude": -122.4194
  },
  "api_keys": {
    "openrouter": "sk-or-v1-...",
    "deepseek": "sk-...",
    "groq": "gsk_...",
    "mistral": "..."
  }
}
```

---

## 🧪 Automated Testing & QA

The backend features a comprehensive `pytest` test suite with 100% endpoint coverage:

```bash
# Run backend test suite
pytest backend/tests/ -v

# Run with test coverage report
pytest --cov=backend backend/tests/
```
