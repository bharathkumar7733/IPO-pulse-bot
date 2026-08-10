"""
Master IPO Bot Daemon
- Refreshes IPO data from ipowatch.in every 6 hours
- Sends 12-hour digest at 11:30 AM and 11:30 PM IST daily
"""
import sys, os, asyncio
from datetime import datetime, timezone, timedelta, date

sys.path.insert(0, "c:/IPO-BOT")
from dotenv import load_dotenv
load_dotenv("c:/IPO-BOT/.env")

from app.core.logging import logger

IST = timedelta(hours=5, minutes=30)
REFRESH_INTERVAL_SEC = 6 * 60 * 60  # 6 hours


async def run_refresh():
    from scripts.realtime_ipo_scraper import run_realtime_update
    logger.info("[Master] Running real-time IPO data refresh from ipowatch.in...")
    try:
        ok = run_realtime_update()
        if ok:
            logger.info("[Master] Refresh complete.")
        else:
            logger.warning("[Master] Refresh returned no new data.")
    except Exception as e:
        logger.error(f"[Master] Refresh error: {e}")


async def run_digest():
    from scripts.send_12h_ipo_digest import test_and_send_digest
    logger.info("[Master] Sending 12h digest...")
    try:
        await test_and_send_digest()
        logger.info("[Master] Digest sent successfully.")
    except Exception as e:
        logger.error(f"[Master] Digest error: {e}")


async def refresh_loop():
    """Refresh data every 6 hours continuously."""
    while True:
        await run_refresh()
        logger.info(f"[Master] Next data refresh in 6 hours.")
        await asyncio.sleep(REFRESH_INTERVAL_SEC)


async def digest_loop():
    """Send digest at 11:30 AM and 11:30 PM IST every day."""
    while True:
        now_ist = datetime.now(timezone.utc) + IST
        today = now_ist.date()

        t_am  = datetime(today.year, today.month, today.day, 11, 30, 0).replace(tzinfo=None)
        t_pm  = datetime(today.year, today.month, today.day, 23, 30, 0).replace(tzinfo=None)
        now_naive = now_ist.replace(tzinfo=None)

        if now_naive < t_am:
            wait_sec = (t_am - now_naive).total_seconds()
            next_label = "11:30 AM IST"
        elif now_naive < t_pm:
            wait_sec = (t_pm - now_naive).total_seconds()
            next_label = "11:30 PM IST"
        else:
            tomorrow = today + timedelta(days=1)
            t_next = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 11, 30, 0)
            wait_sec = (t_next - now_naive).total_seconds()
            next_label = "11:30 AM IST (tomorrow)"

        logger.info(f"[Master] Next digest at {next_label} — waiting {wait_sec/60:.1f} minutes")
        await asyncio.sleep(wait_sec)

        # Refresh data right before sending digest
        await run_refresh()
        await run_digest()

        await asyncio.sleep(90)  # Prevent double-fire within same minute


async def main():
    logger.info("=" * 60)
    logger.info("  IPO BOT MASTER DAEMON — Started")
    logger.info("  Refresh: every 6h from ipowatch.in")
    logger.info("  Digest:  11:30 AM & 11:30 PM IST daily")
    logger.info("=" * 60)

    # Run first refresh immediately on startup
    await run_refresh()

    # Start both loops concurrently
    await asyncio.gather(
        refresh_loop(),
        digest_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
