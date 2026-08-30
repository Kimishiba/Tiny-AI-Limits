# 🤖 AI Providers & Quota Tracking

**Tiny AI Limits** includes modular provider adapters capable of parsing local agent session transcripts, reading statusline hooks, or querying cloud model management APIs.

---

## 📋 Supported Providers Matrix

| Provider Identifier | Service Name | Data Source / Mechanism | Supported Modes |
| :--- | :--- | :--- | :--- |
| **`claude`** | Anthropic Claude | Claude Code session transcripts & statusline | Standard (5h Reset) / Enterprise |
| **`antigravity`** | Google Antigravity | Antigravity engine telemetry & token logs | Standard / Enterprise |
| **`openrouter`** | OpenRouter.ai | Cloud `/api/v1/auth/key` endpoint | Enterprise (\$ Spend & Credits) |
| **`deepseek`** | DeepSeek | Cloud `/user/balance` API | Enterprise (\$ Spend & Tokens) |
| **`groq`** | Groq Cloud | Cloud rate limits & token analytics | Standard / Enterprise |
| **`mistral`** | Mistral AI | Cloud usage analytics API | Standard / Enterprise |
| **`copilot`** | GitHub Copilot | Local editor session telemetry | Standard (% Quota) |
| **`cursor`** | Cursor IDE | Local composer session transcripts | Standard (% Quota) |
| **`gemini`** | Google Gemini API | Cloud Generative Language API | Standard / Enterprise |
| **`codex`** | OpenAI Codex / GPT-4o | Usage & Billing API | Enterprise (\$ Spend) |

---

## ⚙️ Gauge Modes: Standard vs. Enterprise

Each of the two radial arcs (Left Gauge and Right Gauge) can be independently configured in either of two operating modes:

```
    STANDARD QUOTA MODE                     ENTERPRISE SPEND MODE
 ╭─────────────────────────╮             ╭─────────────────────────╮
 │     [CLAUDE CODE]       │             │      [ANTIGRAVITY]      │
 │                         │             │                         │
 │        84.5%            │             │         $0.13           │
 │      REMAINING          │             │       SPEND TODAY       │
 │                         │             │                         │
 │     Resets: 4h 32m      │             │      28.2k TOKENS       │
 ╰─────────────────────────╯             ╰─────────────────────────╯
```

### 1. Standard Quota Mode
* **Target Users:** Claude Pro, Claude Team, Antigravity standard plans with 5-hour sliding-window quotas.
* **Corridor Center:** Displays remaining quota percentage (`84.5%`).
* **Footer:** Displays active countdown until the current rolling 5-hour quota window resets (`4h 32m`).
* **Radial Arc Sweep:** Tracks remaining quota from $100\%$ down to $0\%$.

### 2. Enterprise / Pay-As-You-Go Mode
* **Target Users:** Enterprise accounts, pay-as-you-go API keys (OpenRouter, DeepSeek, Groq, Mistral).
* **Corridor Center:** Displays today's live dollar spend in **`$`** (e.g. `$0.13`).
* **Footer:** Displays total 24-hour token consumption (e.g. `28.2k TOK`).
* **Radial Arc Sweep:** Fills upward against your user-defined **Daily Budget ($ USD)**.

---

## 🔑 Provider Configuration Guide

### 1. Anthropic Claude (Claude Code)
Claude Code stores real-time session transcripts and usage metrics locally on your machine.
* **Automatic Detection:** The companion app automatically detects Claude Code statusline files at `~/.claude/` or active shell hooks.
* **No API Key Required:** Runs 100% locally from your local CLI session.

### 2. Google Antigravity
The companion connects directly to the local Antigravity daemon and workspace transcripts to calculate real-time token utilization and active subagent states.

### 3. OpenRouter.ai
1. Generate an API Key at [openrouter.ai/keys](https://openrouter.ai/keys).
2. Open `http://localhost:5000/setup`.
3. In the **Cloud API Keys** accordion, paste your key into the **OpenRouter API Key** field.
4. Click **Save Settings**.

### 4. DeepSeek, Groq, and Mistral
1. Acquire your API keys from their respective developer dashboards.
2. Enter them into the configuration UI at `http://localhost:5000/setup`.
3. The companion service will automatically query token usage and account balances on a 60-second polling cycle.
