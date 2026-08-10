# 🚀 IPO Pulse Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=for-the-badge&logo=fastapi)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![Gemini](https://img.shields.io/badge/Google-Gemini%20AI-orange?style=for-the-badge&logo=google)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Real-time Indian IPO tracking, AI-powered analysis, and automated Telegram alerts — all in one bot.**

[Features](#-features) • [Architecture](#-architecture) • [Setup](#-setup) • [Usage](#-usage) • [Screenshots](#-screenshots) • [Deployment](#-deployment)

</div>

---

## 📌 What is IPO Pulse Bot?

**IPO Pulse Bot** is a fully automated Indian IPO intelligence system built with Python, FastAPI, and Google Gemini AI.

It scrapes **live IPO data** from NSE/BSE (via ipowatch.in) every 6 hours and delivers a clean, formatted **market digest to your Telegram** — twice daily at 11:30 AM and 11:30 PM IST.

> 💡 Think of it as your personal IPO tracker that never sleeps — covering Mainboard, SME IPOs, Grey Market Premium (GMP), subscription data, AI analysis, and listing predictions.

---

## ✨ Features

### 📊 Real-Time IPO Data
- **Live scraping** from ipowatch.in (NSE/BSE verified data) every 6 hours
- Tracks **Mainboard** and **SME** IPOs separately
- Covers all IPO stages: Upcoming → Open → Closed → Allotted → Listed

### 🤖 AI-Powered Analysis (Google Gemini)
- Uses **Gemini 1.5 Flash** with Google Search grounding
- AI generates **buy/avoid recommendations** with reasoning
- Analyses company fundamentals, GMP trends, and sector outlook

### 📱 Telegram Bot Alerts
- Automated **12-hour digest** at 11:30 AM & 11:30 PM IST daily
- Clean **monospace table format** for easy reading
- Shows: Price Band, GMP, Subscription (x), Close Date
- Broadcasts to **multiple subscribers** simultaneously
- Supports `/start`, `/ipos`, `/analysis`, `/upcoming` commands

### 📈 Grey Market Premium (GMP) Tracking
- Fetches live GMP data automatically
- Calculates estimated listing price
- Stores historical GMP trend in database

### 🔔 Smart Subscription Alerts
- Live subscription data (QIB / NII / Retail / Overall)
- Automatically flags heavily oversubscribed IPOs

### 🗄️ Persistent Database
- SQLite database with full IPO history
- Models: IPO, GMPHistory, SubscriptionHistory, DataSource
- Alembic migrations for schema management

---

## 🏗️ Architecture

```
ipo-pulse-bot/
│
├── app/                          # Core FastAPI application
│   ├── main.py                   # FastAPI app entry point
│   ├── api/                      # REST API routes (v1)
│   │   └── v1/endpoints/         # IPO, Analysis, Health endpoints
│   ├── bot/                      # Telegram bot layer
│   │   ├── router.py             # Handles incoming Telegram updates
│   │   ├── client.py             # Telegram API client (send messages)
│   │   ├── config.py             # Bot token & admin config
│   │   └── subscribers.py        # Subscriber tracking (chat IDs)
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── ipo.py                # IPO model (status, dates, prices)
│   │   ├── gmp_history.py        # GMP price history
│   │   ├── subscription_history.py # Subscription data history
│   │   └── data_source.py        # Data source registry
│   ├── providers/                # AI & data providers
│   │   └── gemini_ipo_provider.py # Google Gemini AI research engine
│   ├── services/                 # Business logic layer
│   │   ├── ipo_service.py        # IPO CRUD operations
│   │   └── analysis_service.py   # AI analysis orchestration
│   ├── repositories/             # Data access layer
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── db/                       # Database session & seeding
│   └── core/                     # Config, logging, settings
│
├── scripts/                      # Automation & utility scripts
│   ├── run_master_daemon.py      # 🔑 Master daemon (refresh + digest)
│   ├── run_bot_polling.py        # Telegram long-polling loop
│   ├── realtime_ipo_scraper.py   # Live scraper from ipowatch.in
│   ├── send_12h_ipo_digest.py    # Digest formatter & Telegram sender
│   ├── seed_real_verified_ipos.py # Seed DB with verified IPO data
│   └── backup_db.py              # Database backup utility
│
├── migrations/                   # Alembic DB migration files
├── tests/                        # Unit & integration tests
├── docs/                         # Documentation assets
├── docker-compose.yml            # Docker deployment config
├── Dockerfile                    # Container build instructions
├── .env.example                  # Environment variable template
└── README.md                     # This file
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.12+
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A Google Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ipo-pulse-bot.git
cd ipo-pulse-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_IDS=["your_telegram_chat_id"]

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///./ipo_agent.db
```

> 💡 To get your Telegram Chat ID: Send `/start` to your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 5. Initialize Database

```bash
python -m alembic upgrade head
```

### 6. Seed Initial IPO Data

```bash
python scripts/seed_real_verified_ipos.py
```

---

## 🚀 Usage

### Start Everything (Recommended)

Run these 3 commands in **separate terminals**:

```bash
# Terminal 1 — FastAPI Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Telegram Bot Polling
python scripts/run_bot_polling.py

# Terminal 3 — Master Daemon (Data Refresh + Digest Scheduler)
python scripts/run_master_daemon.py
```

### What Happens Automatically

| Time | Action |
|:---|:---|
| Every **6 hours** | Scrapes fresh IPO data from ipowatch.in (NSE/BSE) |
| **11:30 AM IST** | Sends morning IPO digest to all subscribers on Telegram |
| **11:30 PM IST** | Sends evening IPO digest to all subscribers on Telegram |
| **On /start** | Registers user as subscriber for auto-digests |

### Telegram Bot Commands

| Command | Description |
|:---|:---|
| `/start` | Register for automated digest alerts |
| `/ipos` | Get current open IPOs right now |
| `/upcoming` | See upcoming IPOs with dates |
| `/analysis <company>` | Get AI analysis for a specific IPO |
| `/gmp` | See Grey Market Premium for open IPOs |

---

## 📱 Sample Telegram Output

```
LIVE IPO MARKET DIGEST
Updated: 09 Aug 2026 11:30 AM IST

🔴 OPEN IPOs — Apply Now
────────────────────────────────────────────────────────────────
NAME                     BAND           GMP       SUB     CLOSE
─────────────────────────────────────────────────────────────────
[MB] Technocraft Ventur.. Rs200-212      +Rs18     2.6x    11 Aug
[MB] LEAP India Limited  Rs151-159      +Rs32     0.3x    11 Aug
[MB] Molbio Diagnostics  Rs768-807      +Rs145    9.5x    12 Aug
[MB] Milky Mist Dairy F.. Rs133-140     +Rs40     -       13 Aug
[MB] Shiprocket Limited  Rs92-97        +Rs55     -       14 Aug

📅 UPCOMING IPOs — Opening Soon
────────────────────────────────────────────────────────────────
NAME                     BAND           OPEN       CLOSE
──────────────────────────────────────────────────────────────
[MB] Behari Lal Enginee.. Rs271-285      12 Aug     14 Aug

✅ RECENTLY CLOSED — Results & Listing
────────────────────────────────────────────────────────────────
NAME                     PRICE      GMP       SUB      CLOSE
──────────────────────────────────────────────────────────────
[MB] Ardee Industries L.. Rs53       +Rs68     133.3x   07 Aug
[MB] Juniper Green Ener.. Rs225      +Rs14     38.5x    03 Aug

_Live data from NSE/BSE via ipowatch.in. GMP is unofficial/unregulated._
_Data refreshes automatically every 6 hours._
```

---

## 🗃️ Database Schema

```
IPO
├── id, symbol, company_name
├── issue_type (MAINBOARD / SME)
├── status (UPCOMING / OPEN / CLOSED / ALLOTTED / LISTED)
├── min_price, max_price, issue_price
├── lot_size, total_issue_size_cr
├── open_date, close_date, allotment_date, listing_date
└── primary_source_id → DataSource

GMPHistory
├── ipo_id → IPO
├── gmp_price, gmp_percent
├── estimated_listing_price
└── observation_time

SubscriptionHistory
├── ipo_id → IPO
├── overall_x, qib_x, nii_x, retail_x
└── observation_time
```

---

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

The `docker-compose.yml` spins up:
- FastAPI backend on port `8000`
- Telegram bot polling daemon
- Master daemon (data refresh + digest scheduler)

---

## ☁️ Free Cloud Deployment (Render)

1. Fork this repo to your GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set environment variables from `.env.example`
5. Set Start Command: `python scripts/run_master_daemon.py`
6. Deploy — runs 24/7 for **free**!

---

## 🔧 Tech Stack

| Layer | Technology |
|:---|:---|
| **Backend API** | FastAPI (Python 3.12) |
| **Database** | SQLite + SQLAlchemy ORM + Alembic |
| **AI Engine** | Google Gemini 1.5 Flash |
| **Bot Platform** | Telegram Bot API |
| **Data Source** | ipowatch.in (NSE/BSE scraped data) |
| **HTTP Client** | httpx (async) |
| **HTML Parser** | BeautifulSoup4 + lxml |
| **Containerization** | Docker + Docker Compose |

---

## 📁 Key Scripts Reference

| Script | Purpose |
|:---|:---|
| `run_master_daemon.py` | **Main entry point** — runs all background tasks |
| `realtime_ipo_scraper.py` | Scrapes live data from ipowatch.in every 6h |
| `send_12h_ipo_digest.py` | Formats & broadcasts digest to Telegram |
| `run_bot_polling.py` | Listens for user commands on Telegram |
| `seed_real_verified_ipos.py` | One-time seed for verified IPO data |
| `backup_db.py` | Backs up the SQLite database |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## ⚠️ Disclaimer

> This bot is for **informational purposes only**. Grey Market Premium (GMP) data is **unofficial and unregulated**. Nothing here constitutes financial advice. Always do your own research before investing in any IPO.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Made with ❤️ for Indian IPO investors

⭐ **Star this repo** if it helped you!

</div>
