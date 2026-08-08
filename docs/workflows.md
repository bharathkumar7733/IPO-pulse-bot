# n8n Automation Workflows Specification

## Executive Summary
This document provides the complete architecture, workflow IDs, schedule configurations, and node connections for the 8 modular **n8n Automation Workflows** created via the n8n MCP Server integration.

---

## Workflow Inventory Matrix

| # | Workflow Name | n8n Workflow ID | Trigger Mode | Schedule / Pattern | Node Count | Status |
| :--- | :--- | :--- | :--- | :--- | :-: | :-: |
| 1 | `IPO_DATA_SYNC` | `6IKKEBZwiKr7ZT6w` | Schedule Trigger | Every 12 Hours | 3 | Draft (Unpublished) |
| 2 | `GMP_SYNC_6H` | `GWhrhENWo2faDhtD` | Schedule Trigger | Every 6 Hours IST | 6 | Draft (Unpublished) |
| 3 | `SUBSCRIPTION_SYNC` | `BqjO5thVoFKFyjpz` | Schedule Trigger | Every 4 Hours | 3 | Draft (Unpublished) |
| 4 | `TELEGRAM_COMMAND_HANDLER` | `uwm62RmotXt2ZqnC` | Webhook | `POST /webhook/telegram-bot` | 2 | Draft (Unpublished) |
| 5 | `GMP_ALERT_ENGINE` | `60TmduiqqsRZ47H5` | Webhook | `POST /webhook/gmp-alert-trigger` | 4 | Draft (Unpublished) |
| 6 | `DAILY_IPO_SUMMARY` | `1qwdRXWfyIBz1TcK` | Schedule Trigger | Daily 8:00 AM IST (`0 8 * * *`) | 3 | Draft (Unpublished) |
| 7 | `ERROR_MONITOR` | `6LIts4ZEEYwM1txZ` | Schedule Trigger | Every 1 Hour | 4 | Draft (Unpublished) |
| 8 | `DATA_HEALTH_CHECK` | `1GQOWHGTrXV0gel7` | Schedule Trigger | Daily Midnight (`0 0 * * *`) | 3 | Draft (Unpublished) |

---

## Detailed Workflow Architecture

### 1. `IPO_DATA_SYNC` (`6IKKEBZwiKr7ZT6w`)
* **Objective**: Automates regular synchronization of master IPO listings from Upstox API v2.
* **Nodes**:
  1. `Schedule Every 12 Hours` (Schedule Trigger)
  2. `Trigger IPO Sync` (HTTP Request: `POST /ingest/ipos?provider_code=UPSTOX_API`)
  3. `Check Sync Status` (IfElse: checks `$json.status == 'SUCCESS'`)

### 2. `GMP_SYNC_6H` (`GWhrhENWo2faDhtD`)
* **Objective**: Syncs Grey Market Premium (GMP) every 6 hours in IST, compares previous GMP, detects trend changes, and dispatches notifications.
* **Nodes**:
  1. `Schedule Every 6 Hours IST` (Schedule Trigger: every 6 hours)
  2. `Trigger GMP Ingestion Service` (HTTP Request: `POST /ingest/gmp?provider_code=APIFY_GMP`)
  3. `Fetch Open IPOs` (HTTP Request: `GET /ipos/open`)
  4. `Calculate GMP Change and Trend` (HTTP Request: `GET /ipos/SWIGGY/gmp/analysis`)
  5. `Check Significant Movement` (IfElse: checks `$json.trend == 'RISING'` OR `$json.trend == 'FALLING'`)
  6. `Send Telegram Notification` (HTTP Request: `POST /telegram/webhook`)
* **Duplicate Notification Safeguard**: Notifications are only triggered when the trend shifts to `RISING` or `FALLING` with non-zero absolute change, preventing duplicate spam.

### 3. `SUBSCRIPTION_SYNC` (`BqjO5thVoFKFyjpz`)
* **Objective**: Syncs live category-wise subscription multipliers (QIB, NII, Retail) every 4 hours.
* **Nodes**:
  1. `Schedule Every 4 Hours` (Schedule Trigger)
  2. `Trigger Subscription Sync Service` (HTTP Request: `POST /ingest/ipos?provider_code=UPSTOX_API`)
  3. `Check Subscription Sync Result` (IfElse: checks `$json.status == 'SUCCESS'`)

### 4. `TELEGRAM_COMMAND_HANDLER` (`uwm62RmotXt2ZqnC`)
* **Objective**: Receives incoming webhook updates from Telegram Bot API and routes them to the FastAPI backend router.
* **Nodes**:
  1. `Telegram Webhook Receiver` (Webhook Trigger: `POST /webhook/telegram-bot`)
  2. `Forward Payload to FastAPI Bot Router` (HTTP Request: `POST /telegram/webhook`)

### 5. `GMP_ALERT_ENGINE` (`60TmduiqqsRZ47H5`)
* **Objective**: Monitors significant GMP price surges ($\ge 10\%$) and dispatches instant Telegram alerts.
* **Nodes**:
  1. `GMP Alert Webhook` (Webhook Trigger: `POST /webhook/gmp-alert-trigger`)
  2. `Fetch GMP Analysis` (HTTP Request: `GET /ipos/SWIGGY/gmp/analysis`)
  3. `Check Surge Threshold` (IfElse: `$json.percentage_change >= 10`)
  4. `Dispatch GMP Surge Alert` (HTTP Request: `POST /telegram/webhook`)

### 6. `DAILY_IPO_SUMMARY` (`1qwdRXWfyIBz1TcK`)
* **Objective**: Sends a consolidated morning summary of active IPOs to subscribers every day at 8:00 AM IST.
* **Nodes**:
  1. `Schedule Daily 8:00 AM IST` (Cron Schedule: `0 8 * * *`)
  2. `Fetch Open IPOs for Summary` (HTTP Request: `GET /ipos/open`)
  3. `Broadcast Daily Summary to Telegram` (HTTP Request: `POST /telegram/webhook` with `/open`)

### 7. `ERROR_MONITOR` (`6LIts4ZEEYwM1txZ`)
* **Objective**: Performs hourly system health checks; dispatches emergency Telegram alerts if database or API degrades.
* **Nodes**:
  1. `Schedule Every 1 Hour` (Schedule Trigger)
  2. `Check Backend Health Endpoint` (HTTP Request: `GET /health`)
  3. `Verify Database Health` (IfElse: `$json.database == 'healthy'`)
  4. `Alert Admin on Database Unhealthy` (HTTP Request: `POST /telegram/webhook` on `false` branch)

### 8. `DATA_HEALTH_CHECK` (`1GQOWHGTrXV0gel7`)
* **Objective**: Executes nightly data integrity verification at midnight IST (`0 0 * * *`).
* **Nodes**:
  1. `Schedule Daily Midnight` (Cron Schedule: `0 0 * * *`)
  2. `Check System Status` (HTTP Request: `GET /health`)
  3. `Fetch Sample IPO Data` (HTTP Request: `GET /ipos?limit=5`)

---

## Cloud Deployment & Network Notice

> ⚠️ **Important**: When running in production on `https://bharathkumar733.app.n8n.cloud`, update HTTP Request node target URLs from `http://127.0.0.1:8000` to the public FastAPI server domain or secure tunneling endpoint.
>
> All 8 workflows remain in **Draft (Unpublished)** mode per strict project guidelines until explicit user activation approval.
