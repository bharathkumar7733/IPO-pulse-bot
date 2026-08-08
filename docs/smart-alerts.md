# Smart Alerts & Deduplication Engine Specification

## Executive Summary
This document provides the technical design, trigger conditions, idempotency key strategy, and deduplication safeguards for the **Smart Alerts Engine**.

The engine evaluates live conditions across active IPOs, generates rich formatted Telegram alert cards, and guarantees **zero duplicate notification spam** by storing unique idempotency keys in PostgreSQL.

---

## 1. Trigger Conditions & Alert Types

| Alert Type | Trigger Threshold | Idempotency Key Pattern | Card Emoji & Header |
| :--- | :--- | :--- | :--- |
| `GMP_SURGE` | $\Delta P \ge +₹10.0$ | `GMP_SURGE:{symbol}:{observation_time}` | 🚀 `GMP SURGE ALERT: +₹10` |
| `GMP_DROP` | $\Delta P \le -₹10.0$ | `GMP_DROP:{symbol}:{observation_time}` | 🔻 `GMP DROP ALERT: -₹10` |
| `GMP_TREND_REVERSAL` | Trend reverses (`FALLING` $\rightarrow$ `RISING` or vice-versa) | `GMP_REVERSAL:{symbol}:{trend}:{observation_time}` | 🔄 `GMP TREND REVERSAL ALERT` |
| `IPO_OPENED` | Bidding opens today (`open_date == today`) | `IPO_OPENED:{symbol}:{today_date}` | 🔔 `IPO Opened For Bidding Today!` |
| `IPO_CLOSING_SOON` | Bidding closes today (`close_date == today`) | `IPO_CLOSING_SOON:{symbol}:{today_date}` | ⏳ `Bidding Closes Today!` |
| `IPO_LISTING_TOMORROW` | Listing date tomorrow (`listing_date == tomorrow`) | `IPO_LISTING_TOMORROW:{symbol}:{tomorrow_date}` | 🎯 `Exchange Listing Tomorrow!` |
| `SUBSCRIPTION_MILESTONE` | Overall demand crosses $1\times, 5\times, 10\times, 25\times, 50\times, 100\times$ | `SUBSCRIPTION_MILESTONE:{symbol}:{level}X` | 🔥 `SUBSCRIPTION MILESTONE PASSED!` |

---

## 2. Deduplication & Idempotency Safeguards

```
+-------------------------------------------------------+
| SmartAlertService.evaluate_and_dispatch()             |
+-------------------------------------------------------+
                           │
             Check idempotency_key in DB
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
   Key EXISTS in DB               Key NOT in DB
   ────────────────            ──────────────────
 [SKIP - No Duplicate]         1. Insert Notification into DB
                               2. Dispatch Telegram Alert
                               3. Update status = SENT
```

---

## 3. Endpoints & Orchestration

* **API Endpoint**: `POST /alerts/evaluate`
* **Query Parameters**: `chat_id` (target Telegram channel or admin chat)
* **Response**: List of newly dispatched alert summary DTOs

---

## 4. Test Verification Summary

* `test_date_based_alerts`: Verifies `IPO_OPENED`, `IPO_CLOSING_SOON`, `IPO_LISTING_TOMORROW`.
* `test_gmp_surge_and_drop_alerts`: Verifies $+₹10$ surge and $-₹10$ drop thresholds.
* `test_subscription_milestone_and_deduplication`: Verifies milestone triggers ($1\times, 5\times, 10\times$) and asserts **0 duplicate notifications** on re-execution.
* `test_alerts_endpoint`: Verifies `POST /alerts/evaluate` endpoint.
