# 🚀 Indian IPO Intelligence Agent

An enterprise-grade, real-time **Indian IPO Intelligence Platform** built with **FastAPI**, **PostgreSQL**, **n8n Automation**, **Telegram Bot**, and **Grounded AI Analysis**.

Designed for high reliability, zero data corruption, append-only time-series preservation, exponential backoff retries, rate limiting, and zero-spam idempotency deduplication.

---

## 🌟 Key Features & Enterprise Capabilities

* **FastAPI Clean Architecture**: Separated endpoints, DTO schemas, ORM models, repositories, and services.
* **PostgreSQL Append-Only Time Series**: Immutably preserves Grey Market Premium (GMP) and subscription observations over time.
* **Resilient Data Ingestion**: `tenacity` exponential backoff retries, rate-limit protection (429 handling), and Pydantic malformed payload filtering.
* **Grey Market Premium (GMP) Analytics**: Calculates current GMP, previous GMP, absolute change ($\Delta P$), percentage change ($\Delta P\%$), 24-hour delta, and dynamic trend states (🟢 `RISING`, 🔴 `FALLING`, 🟡 `STABLE`, ⚪ `UNKNOWN`).
* **Smart Alert Engine**: Triggers 7 smart alert types (GMP $+₹10$ surge, $-₹10$ drop, trend reversals, date events, subscription milestones) with PostgreSQL `idempotency_key` deduplication (0 duplicate notifications).
* **Interactive Telegram Bot**: Full command suite (`/start`, `/help`, `/ipo`, `/open`, `/upcoming`, `/gmp`, `/details`, `/analysis`, `/history`, `/subscription`) with Test/Admin mode safeguards and mandatory legal disclaimers.
* **Grounded AI Prospectus Layer**: Generates positive signals, risk factors, and overall investment synthesis strictly grounded in verified database facts without financial number hallucinations.
* **n8n Automation Workflows**: 8 modular n8n workflows (`IPO_DATA_SYNC`, `GMP_SYNC_6H`, `SUBSCRIPTION_SYNC`, `TELEGRAM_COMMAND_HANDLER`, `GMP_ALERT_ENGINE`, `DAILY_IPO_SUMMARY`, `ERROR_MONITOR`, `DATA_HEALTH_CHECK`).
* **Production Hardening**: Rate-limiting middleware, health monitoring endpoints with uptime and stale-data warnings, Docker containerization, and database backup scripts.

---

## 🏗️ System Architecture

```
                                  +---------------------------------+
                                  |     External Data Sources       |
                                  | (Upstox API, Apify, Registrars) |
                                  +---------------------------------+
                                                   │
                                                   │ HTTPS (Retries & Backoff)
                                                   ▼
+-----------------------+     Webhook     +---------------------------------+
|  n8n Automation Cloud | -------------> |          FastAPI Backend        |
|  (8 Modular Workflows)|                 | (Clean Architecture & Service)  |
+-----------------------+                 +---------------------------------+
                                                   │               │
                                   ORM Persistence │               │ API Client Calls
                                                   ▼               ▼
                                         +-------------------+   +--------------------+
                                         | PostgreSQL DB     |   | Telegram Bot API   |
                                         | (Time-Series &    |   | (Markdown Cards &  |
                                         | Idempotency Keys) |   | Smart Alerts)      |
                                         +-------------------+   +--------------------+
```

---

## 📖 Telegram Bot Command Reference

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/start` | `/start` | Displays interactive welcome menu & command shortcuts |
| `/help` | `/help` | Complete user guide & mandatory legal disclaimer |
| `/ipo` | `/ipo` | High-level market overview of active & upcoming IPOs |
| `/open` | `/open` | Lists all currently OPEN IPOs with price bands and dates |
| `/upcoming` | `/upcoming` | Lists announced upcoming IPO filings |
| `/gmp` | `/gmp` | Active IPOs Grey Market Premium (GMP) dashboard |
| `/gmp` | `/gmp SWIGGY` | Detailed GMP analysis, 24h delta, and trend state |
| `/details` | `/details SWIGGY` | Master IPO details (price band, lot size, issue breakdown, registrar) |
| `/analysis`| `/analysis SWIGGY`| Grounded AI risk assessment, positive signals, and synthesis |
| `/history` | `/history SWIGGY` | Full append-only historical GMP time-series |
| `/subscription` | `/subscription SWIGGY` | Live & category-wise subscription multipliers (QIB, NII, Retail) |

> ⚠️ **Disclaimer**: Grey Market Premium (GMP) is an informal, unorganized, and unregulated over-the-counter indicator. It is NOT endorsed by SEBI, NSE, or BSE.

---

## 🛠️ REST API Reference

| Endpoint | Method | Response Model | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | `HealthCheckResponse` | System status, DB health, uptime, stale-data warning & row counts |
| `/ipos` | `GET` | `IPOListResponse` | Paginated master list of IPOs with status/type filtering |
| `/ipos/open` | `GET` | `List[IPOResponse]` | List of currently OPEN IPOs |
| `/ipos/upcoming` | `GET` | `List[IPOResponse]` | List of UPCOMING IPOs |
| `/ipos/{id}` | `GET` | `IPOResponse` | Master details by UUID or Stock Symbol |
| `/ipos/{id}/gmp` | `GET` | `GMPResponse` | Most recent GMP snapshot |
| `/ipos/{id}/gmp/analysis` | `GET` | `GMPAnalysisResponse` | Current GMP, previous GMP, deltas, 24h change, and trend state |
| `/ipos/{id}/analysis` | `GET` | `AIAnalysisResponse` | Grounded AI positive signals, risk factors, and overall assessment |
| `/ipos/{id}/gmp/history` | `GET` | `GMPHistoryListResponse` | Complete append-only time-series history |
| `/ipos/{id}/subscription` | `GET` | `SubscriptionHistoryListResponse` | Live category-wise subscription multipliers |
| `/ingest/ipos` | `POST` | `SyncResult` | Triggers master IPO & subscription data ingestion |
| `/ingest/gmp` | `POST` | `SyncResult` | Triggers append-only GMP time-series ingestion |
| `/alerts/evaluate` | `POST` | `List[Dict]` | Triggers smart alert evaluation & deduplicated notification dispatch |
| `/telegram/webhook` | `POST` | `Dict` | Webhook endpoint for Telegram updates |

---

## ⚡ Quickstart Guide

### Option A: Local Development Setup

1. **Clone repository & install dependencies**:
   ```bash
   git clone https://github.com/your-org/ipo-bot.git
   cd ipo-bot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

3. **Initialize Database & Seed Test Data**:
   ```bash
   python -m app.db.seed
   ```

4. **Start FastAPI Application Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Option B: Production Docker Deployment

```bash
docker-compose up -d --build
```

---

## 🧪 Automated Test Suite

Run the full automated test suite covering Database, REST API, Data Ingestion, GMP Trend Engine, Telegram Bot, Smart Alerts, and AI Analysis:

```bash
python -m pytest tests/
```

```text
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-9.1.0, pluggy-1.6.0
rootdir: C:\IPO-BOT
collected 52 items

tests\test_ai_analysis.py ...                                            [  5%]
tests\test_alerts.py ....                                                [ 13%]
tests\test_api.py ..........                                             [ 32%]
tests\test_bot.py ..........                                             [ 51%]
tests\test_database.py ..........                                        [ 71%]
tests\test_e2e_flow.py .                                                 [ 73%]
tests\test_gmp.py ........                                               [ 88%]
tests\test_ingestion.py ......                                           [100%]

============================= 52 passed in 6.80s ==============================
```

---

## 📄 License & Regulatory Disclaimer

This software is for informational and educational purposes only. Financial analysis, subscription metrics, and grey market rates do not constitute investment advice under SEBI (Research Analysts) Regulations. Always consult a certified financial advisor before investing.
