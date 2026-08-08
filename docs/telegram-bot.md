# Telegram Bot Interface & Command Specifications

## Executive Summary
This document provides the specification, command guide, safety guardrails, and architecture for the **Indian IPO Intelligence Telegram Bot**.

The Telegram Bot interacts exclusively with the **FastAPI Backend Services** (`BackendAPIClient`) rather than calling external raw providers directly, ensuring consistent data normalization and validation.

---

## 1. Architectural Design

```
+------------------+         HTTP Webhook / Command         +------------------+
|                  | -------------------------------------> |                  |
|  Telegram User   |                                        |  Telegram Bot    |
|  /gmp, /details  | <------------------------------------- |  (app/bot/*)     |
+------------------+         Formatted Markdown Message     +------------------+
                                                                     │
                                                             BackendAPIClient
                                                                     │
                                                                     ▼
                                                            +------------------+
                                                            |  FastAPI Backend |
                                                            |  (http/127.0.0.1)|
                                                            +------------------+
```

---

## 2. Command Reference

| Command | Arguments | Description | Output Content |
| :--- | :--- | :--- | :--- |
| `/start` | None | Welcome message & quick action menu | Main menu & command shortcuts |
| `/help` | None | Guide and legal disclaimers | Command list & mandatory GMP disclaimer |
| `/ipo` | None | Market overview of IPOs | Top 10 active & upcoming IPOs |
| `/open` | None | Currently open IPOs | Open IPOs with price bands and bidding dates |
| `/upcoming` | None | Upcoming IPO filings | Announced IPOs awaiting bidding |
| `/gmp` | None | Active GMP dashboard | Dashboard of open IPOs with current GMP & trends |
| `/gmp` | `<symbol>` | Detailed GMP analysis | Current GMP, previous GMP, 24h change, trend badge & disclaimer |
| `/details` | `<symbol>` | Master IPO information | Price band, lot size, issue size, timeline, registrar link |
| `/history` | `<symbol>` | Historical time-series | Up to 10 latest append-only GMP time-series observations |
| `/subscription`| `<symbol>`| Subscription status | QIB, NII (bNII/sNII), Retail, Employee & Overall multipliers |

---

## 3. Mandatory Disclaimers & Safety Guardrails

### A. Unofficial GMP Notice
Every message containing Grey Market Premium (GMP) data includes the mandatory disclaimer:
> ⚠️ **Disclaimer**: Grey Market Premium (GMP) is an informal, unorganized, and unregulated over-the-counter indicator. It is NOT endorsed by SEBI, NSE, or BSE.

### B. Error Sanitization
Unhandled exceptions or HTTP errors (e.g. 404 Not Found) are caught by handler blocks and return friendly guidance (e.g., *"⚠️ IPO symbol 'XYZ' not found. Use /open to see active IPOs."*). Raw stack traces or database errors are **never** sent to Telegram users.

### C. Test & Admin Mode Protection
When `BOT_TEST_MODE=true` is enabled in configuration (`app/bot/config.py`), automated broadcasts or test commands are restricted to chat IDs listed in `ADMIN_CHAT_IDS`. Broadcasts to public chat IDs are intercepted and logged to prevent development spam.

---

## 4. Test Suite Verification

Full unit and integration testing of bot command handlers, update routers, and webhook endpoints:

```bash
python -m pytest tests/test_bot.py
```

**Test Coverage**:
* `test_bot_start_command`: Validates `/start` menu output.
* `test_bot_help_command`: Validates `/help` and mandatory disclaimer.
* `test_bot_open_command`: Validates `/open` backend lookup.
* `test_bot_gmp_command`: Validates `/gmp <symbol>` analysis and trend badge.
* `test_bot_details_command`: Validates `/details <symbol>` master data output.
* `test_bot_history_command`: Validates `/history <symbol>` time-series list.
* `test_bot_subscription_command`: Validates `/subscription <symbol>` breakdown.
* `test_bot_unknown_symbol_graceful_error`: Validates friendly 404 handling.
* `test_bot_test_mode_protection`: Validates admin chat ID restriction.
* `test_telegram_webhook_endpoint`: Validates `POST /telegram/webhook` API.
