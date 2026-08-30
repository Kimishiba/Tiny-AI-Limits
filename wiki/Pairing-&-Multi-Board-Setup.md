# 🔐 Pairing & Multi-Board Setup

In a shared office, co-working space, or household with multiple developers running **Tiny AI Limits** on the same local Wi-Fi network, devices must never accidentally intercept a colleague's token telemetry or private agent states.

To ensure strict privacy and 100% deterministic device-to-workstation mapping, **Tiny AI Limits** implements a dedicated **Cryptographic Pairing Protocol**.

---

## 🛡️ The Pairing Security Model

```
       WORKSTATION A                                    WORKSTATION B
  (Companion App: pair_id_A)                       (Companion App: pair_id_B)
              │                                                │
              │  mDNS: _tinyscreen._tcp                        │  mDNS: _tinyscreen._tcp
              │  TXT: pair_id=pair_id_A                        │  TXT: pair_id=pair_id_B
              │                                                │
              ▼                                                ▼
  ┌───────────────────────┐                        ┌───────────────────────┐
  │   TINY SCREEN #1      │                        │   TINY SCREEN #2      │
  │   (NVS: pair_id_A)    │                        │   (NVS: pair_id_B)    │
  │                       │                        │                       │
  │ [PULSING GREEN CROWN] │                        │ [PULSING GREEN CROWN] │
  │   Paired to Dev A     │                        │   Paired to Dev B     │
  └───────────────────────┘                        └───────────────────────┘
```

1. **Unique Host Token (`pair_id`):** When the companion app first launches, it generates a persistent UUIDv4 token stored in `~/.tiny_ai_screen/config.json`.
2. **NVS Pinning:** During initial USB-C setup, the host's `pair_id` is written into the ESP32-C3's non-volatile storage (NVS flash partition).
3. **One-Way Cryptographic Pinning:** Once paired, the board **strictly rejects** any mDNS advertisements or HTTP responses whose `pair_id` does not match its stored token.
4. **No Cross-Talk Fallback:** If a paired board loses connection to its host, it will **never** latch onto another developer's companion app. It will display a disconnected warning until its assigned host returns.

---

## 👑 Status Crown Arc Visual Semantics

The top crown arc of the circular HUD immediately communicates network, pairing, and connection health:

```
            ╭─────────────────────────────╮
          ╭─╯   TOP CROWN STATUS ARC      ╰─╮
         ╭╯                                 ╰╮
```

| Crown Arc Visual | Connection State | Operational Meaning |
| :--- | :--- | :--- |
| 🟢 **Pulsing Emerald Green** | **Paired & Active** | Authenticated to your specific companion app. Data is 100% verified. |
| 🟡 **Solid / Pulsing Amber** | **Connected (Unpaired)** | Board is connected to Wi-Fi but has no stored `pair_id`. Falling back to first available companion. |
| 🔴 **Solid Red** | **Offline / Disconnected** | Cannot reach Wi-Fi network or host companion is unreachable. |

---

## ⚡ Pairing Methods

### Method 1: Direct Serial Setup (Recommended)
1. Plug your ESP32-C3 into your workstation via USB-C.
2. Open `http://localhost:5000/setup` in Chrome or Edge.
3. Click **"Connect Board (Direct Serial Setup)"**.
4. Enter your Wi-Fi credentials and click **"Configure & Pair"**.
5. The browser automatically injects your workstation's `pair_id` into the board's NVS over serial.

---

### Method 2: Pair an Existing / Remote Board
If your board is already connected to Wi-Fi via standard Improv-WiFi:
1. Open `http://localhost:5000/setup`.
2. Scroll to the **"Pair an Existing Board"** card.
3. Enter the board's local IP address (e.g. `192.168.1.150`).
4. Click **"Send Pair Request"**. The companion app will transmit its `pair_id` over the local network to permanently bind the device.

---

## 🔄 DHCP & IP Address Migration

If your workstation receives a new local IP address via DHCP lease renewal:
* The companion app updates its mDNS TXT record immediately.
* The ESP32-C3's background mDNS resolver matches the `pair_id` in the TXT record, extracts the new IP address, and updates its internal route table seamlessly without requiring a re-flash.

---

## 🏷️ Unique Per-Device Hostnames

To prevent DNS hostname collisions when multiple boards operate on the same subnet, each device constructs its mDNS hostname from the last 4 characters of its hardware MAC address:

$$\text{Hostname} = \texttt{tinyscreen-} + \text{MAC}[4..5] + \texttt{.local}$$

*(For example: `tinyscreen-F030.local` or `tinyscreen-8A1C.local`).*
