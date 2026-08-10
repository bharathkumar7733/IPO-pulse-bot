"""
12-Hour Automated IPO Market Digest Background Daemon.
Configured to align with 11:30 AM IST and 11:30 PM IST daily broadcasts.
First trigger: August 9th, 2026 at 11:30 AM IST.
Subsequent triggers: Every 12 hours (11:30 AM & 11:30 PM IST daily).
"""
import sys
import os
import asyncio
import io
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "c:/IPO-BOT")

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from scripts.send_12h_ipo_digest import test_and_send_digest
from app.core.logging import logger

IST_OFFSET = timedelta(hours=5, minutes=30)
TWELVE_HOURS_SEC = 12 * 60 * 60

def get_seconds_until_next_target():
    """Calculates seconds until the next 11:30 AM or 11:30 PM IST target slot."""
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc + IST_OFFSET

    target_1130am = now_ist.replace(hour=11, minute=30, second=0, microsecond=0)
    target_1130pm = now_ist.replace(hour=23, minute=30, second=0, microsecond=0)

    if now_ist < target_1130am:
        next_target = target_1130am
    elif now_ist < target_1130pm:
        next_target = target_1130pm
    else:
        # Next day 11:30 AM
        next_target = target_1130am + timedelta(days=1)

    diff_sec = (next_target - now_ist).total_seconds()
    return max(0, diff_sec), next_target

async def start_12h_digest_loop():
    logger.info("[12H Digest Daemon] Daemon initialized. Target schedules: 11:30 AM IST & 11:30 PM IST.")

    sec_to_wait, next_slot = get_seconds_until_next_target()
    logger.info(
        f"[12H Digest Daemon] First scheduled run set for: {next_slot.strftime('%Y-%m-%d %H:%M:%S IST')} "
        f"(Waiting {int(sec_to_wait)} seconds / ~{sec_to_wait/60:.1f} minutes)..."
    )

    await asyncio.sleep(sec_to_wait)

    while True:
        try:
            logger.info("[12H Digest Daemon] Triggering scheduled 12-hour market digest broadcast...")
            await test_and_send_digest()
            logger.info("[12H Digest Daemon] Broadcast successfully completed!")
        except Exception as e:
            logger.error(f"[12H Digest Daemon] Error during digest broadcast: {e}")

        logger.info(f"[12H Digest Daemon] Sleeping for 12 hours until next slot ({TWELVE_HOURS_SEC}s)...")
        await asyncio.sleep(TWELVE_HOURS_SEC)

if __name__ == "__main__":
    asyncio.run(start_12h_digest_loop())
