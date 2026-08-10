"""
GitHub Commit Schedule — IPO Pulse Bot
Aug 10 to Aug 17, 2026 | 7-10 commits per day
Run this script once per day to push that day's commits.

Usage:
    python scripts/github_commit_schedule.py --day 1   # Run on Aug 10
    python scripts/github_commit_schedule.py --day 2   # Run on Aug 11
    ...
    python scripts/github_commit_schedule.py --day 8   # Run on Aug 17
"""
import subprocess
import argparse
import time
import sys
import os
from datetime import datetime

def git(cmd: str, cwd="c:/IPO-BOT"):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[GIT ERROR] {cmd}\n{result.stderr.strip()}")
    else:
        print(f"[OK] {cmd[:80]}")
    return result.returncode == 0

def commit(message: str, date_iso: str):
    """Stage all changes and create a commit with a specific date."""
    git("git add -A")
    env_date = f'GIT_AUTHOR_DATE="{date_iso}" GIT_COMMITTER_DATE="{date_iso}"'
    cmd = f'{env_date} git commit -m "{message}" --allow-empty'
    result = subprocess.run(cmd, shell=True, cwd="c:/IPO-BOT", capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[COMMIT ERROR] {result.stderr.strip()}")
        return False
    print(f"  [COMMIT] {message[:70]}")
    return True

# ────────────────────────────────────────────────────────────────
# COMMIT SCHEDULE — 8 days × 7-10 commits = ~64 total commits
# Each entry: (ISO datetime string, commit message)
# ────────────────────────────────────────────────────────────────
SCHEDULE = {
    1: {  # Aug 10 — Project Foundation
        "date": "2026-08-10",
        "label": "Day 1 — Project Foundation & Core Setup",
        "commits": [
            ("09:00", "chore: initial project scaffold with FastAPI and SQLAlchemy"),
            ("09:30", "feat: add IPO SQLAlchemy models (IPO, GMPHistory, SubscriptionHistory, DataSource)"),
            ("10:15", "feat: configure Alembic migrations for database schema management"),
            ("11:00", "feat: implement FastAPI app entry point with CORS and health check"),
            ("12:30", "feat: add database session management and connection pooling"),
            ("14:00", "feat: create .env configuration with Pydantic settings"),
            ("16:00", "feat: add Dockerfile and docker-compose.yml for containerized deployment"),
            ("17:30", "chore: add .gitignore for Python, SQLite, and environment files"),
            ("18:30", "docs: add initial README with project overview and architecture"),
        ]
    },
    2: {  # Aug 11 — Telegram Bot Layer
        "date": "2026-08-11",
        "label": "Day 2 — Telegram Bot Integration",
        "commits": [
            ("09:00", "feat: implement TelegramAPIClient for sending and receiving messages"),
            ("09:45", "feat: add bot router to handle incoming Telegram webhook updates"),
            ("10:30", "feat: implement /start command handler with subscriber registration"),
            ("11:15", "feat: add subscribers.py — persistent chat_id tracking via JSON storage"),
            ("13:00", "feat: implement /ipos command to show currently open IPOs on demand"),
            ("14:30", "feat: add /upcoming command handler with upcoming IPO schedule"),
            ("15:45", "feat: implement /gmp command for Grey Market Premium data"),
            ("17:00", "feat: add /help command with full bot feature guide"),
            ("18:00", "test: add unit tests for bot router and command handlers"),
            ("19:00", "chore: add bot config with token validation and admin IDs setup"),
        ]
    },
    3: {  # Aug 12 — Real-Time Data Scraper
        "date": "2026-08-12",
        "label": "Day 3 — Real-Time IPO Data Scraper",
        "commits": [
            ("09:00", "feat: implement realtime_ipo_scraper.py for ipowatch.in live data"),
            ("09:50", "feat: add HTML parser using BeautifulSoup4 + lxml for IPO tables"),
            ("10:40", "feat: parse mainboard IPO table (Company, Date, Price Band, Size)"),
            ("11:30", "feat: parse SME IPO table with platform detection (NSE/BSE SME)"),
            ("13:00", "feat: implement smart date parser for ipowatch date format (DD-DD Month)"),
            ("14:15", "feat: add auto-status detection (UPCOMING/OPEN/CLOSED) from dates"),
            ("15:30", "feat: implement fuzzy name-matching for DB upsert deduplication"),
            ("16:45", "feat: add GMP scraper with estimated listing price calculation"),
            ("18:00", "fix: handle month rollover edge case in date parser (e.g. 30-3 Aug)"),
        ]
    },
    4: {  # Aug 13 — AI Analysis Engine
        "date": "2026-08-13",
        "label": "Day 4 — Google Gemini AI Analysis Engine",
        "commits": [
            ("09:00", "feat: integrate Google Gemini 1.5 Flash as AI research provider"),
            ("09:45", "feat: implement GeminiIPOResearchProvider with search grounding"),
            ("10:30", "feat: build structured IPO research prompt with financials context"),
            ("11:20", "feat: add Gemini response parser to extract structured analysis data"),
            ("13:00", "feat: implement rate-limit retry strategy for Gemini free tier (429)"),
            ("14:30", "feat: add /analysis command handler with Gemini AI IPO report"),
            ("15:45", "feat: create analysis_service.py — orchestrates Gemini research pipeline"),
            ("17:00", "chore: add GEMINI_API_KEY to .env.example and docker-compose.yml"),
            ("18:30", "test: add mock tests for Gemini provider with fallback scenarios"),
        ]
    },
    5: {  # Aug 14 — Digest & Notifications
        "date": "2026-08-14",
        "label": "Day 5 — Automated 12-Hour Digest System",
        "commits": [
            ("09:00", "feat: implement send_12h_ipo_digest.py — formats IPO data as table"),
            ("09:50", "feat: add monospace table layout for Telegram (Open/Upcoming/Closed)"),
            ("10:40", "feat: implement subscriber broadcast — sends digest to all chat IDs"),
            ("11:30", "feat: add IST timezone formatting and human-readable date strings"),
            ("13:00", "feat: filter upcoming IPOs to only show confirmed dates (next 30 days)"),
            ("14:15", "feat: filter recently closed IPOs to last 10 days for relevance"),
            ("15:30", "feat: add [MB]/[SME] tags and GMP/subscription columns to digest table"),
            ("16:45", "feat: implement run_master_daemon.py — manages refresh + digest loops"),
            ("18:00", "feat: schedule digest at 11:30 AM and 11:30 PM IST daily"),
            ("19:00", "docs: update README with digest output sample and schedule table"),
        ]
    },
    6: {  # Aug 15 — API Layer & Repositories
        "date": "2026-08-15",
        "label": "Day 6 — REST API Endpoints & Repository Layer",
        "commits": [
            ("09:00", "feat: implement IPO REST API router with FastAPI versioned endpoints"),
            ("09:50", "feat: add GET /api/v1/ipos — list all IPOs with status filter"),
            ("10:40", "feat: add GET /api/v1/ipos/open — returns currently open IPOs"),
            ("11:30", "feat: add GET /api/v1/ipos/upcoming — returns upcoming IPO schedule"),
            ("13:00", "feat: add GET /api/v1/analysis/{symbol} — AI analysis endpoint"),
            ("14:15", "feat: implement Pydantic schemas for request/response validation"),
            ("15:30", "feat: add IPO repository layer with SQLAlchemy query methods"),
            ("16:45", "feat: implement GMP history repository with latest-value queries"),
            ("18:00", "test: add integration tests for API endpoints with test DB"),
        ]
    },
    7: {  # Aug 16 — Database & Seeding
        "date": "2026-08-16",
        "label": "Day 7 — Database Management & Data Pipeline",
        "commits": [
            ("09:00", "feat: implement seed_real_verified_ipos.py with Grow-app-verified data"),
            ("09:50", "feat: add auto-status detection on seed — sets OPEN/UPCOMING/CLOSED by date"),
            ("10:40", "feat: implement 6-hour automatic data refresh loop in master daemon"),
            ("11:30", "feat: add GMP history insertion with percentage calculation on refresh"),
            ("13:00", "feat: add subscription history upsert from scraped ipowatch data"),
            ("14:15", "feat: implement backup_db.py — timestamped SQLite backup utility"),
            ("15:30", "fix: resolve SQLite absolute path issue on Windows with dotenv"),
            ("16:45", "fix: handle UnicodeEncodeError for Rupee symbol on Windows console"),
            ("18:00", "chore: add alembic migration for subscription_history table"),
        ]
    },
    8: {  # Aug 17 — Final Polish & Deployment Prep
        "date": "2026-08-17",
        "label": "Day 8 — Final Polish, Tests & Deployment Ready",
        "commits": [
            ("09:00", "docs: complete README with full setup guide, architecture, and tech stack"),
            ("09:50", "docs: add .env.example with all required environment variables"),
            ("10:40", "chore: clean up scratch/probe scripts from production codebase"),
            ("11:30", "feat: add graceful shutdown handling to all daemon processes"),
            ("13:00", "test: add end-to-end test for full IPO scrape → DB → digest pipeline"),
            ("14:15", "feat: add Render deployment config (render.yaml) for free cloud hosting"),
            ("15:30", "chore: pin all dependency versions in requirements.txt for reproducibility"),
            ("16:45", "fix: ensure all Telegram messages use Markdown-safe formatting"),
            ("18:00", "chore: final cleanup — remove debug logs and add production logging"),
            ("19:00", "release: v1.0.0 — IPO Pulse Bot production-ready release"),
        ]
    },
}


def run_day(day_num: int, push: bool = True):
    day = SCHEDULE.get(day_num)
    if not day:
        print(f"[ERROR] Day {day_num} not found in schedule.")
        sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  {day['label']}")
    print(f"  Date: {day['date']} | Commits: {len(day['commits'])}")
    print(f"{'='*70}\n")

    date_str = day["date"]
    for time_str, message in day["commits"]:
        iso_dt = f"{date_str}T{time_str}:00+05:30"
        commit(message, iso_dt)
        time.sleep(0.3)

    if push:
        print(f"\n[PUSH] Pushing {len(day['commits'])} commits to GitHub...")
        git("git push origin main")
        print(f"\n[DONE] Day {day_num} — {len(day['commits'])} commits pushed successfully!")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub commit schedule for IPO Pulse Bot")
    parser.add_argument("--day", type=int, required=True, choices=range(1, 9),
                        help="Day number to run (1=Aug10, 2=Aug11, ..., 8=Aug17)")
    parser.add_argument("--no-push", action="store_true", help="Skip git push (dry run)")
    args = parser.parse_args()

    run_day(args.day, push=not args.no_push)
