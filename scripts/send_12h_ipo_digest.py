"""
12-Hour Periodic IPO Market Digest Generator & Broadcast Script.
Uses REAL LIVE data from the DB (populated by realtime_ipo_scraper.py every 6 hours).
Formats Open, Upcoming, and Recently Closed IPOs into aligned monospace tables.
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, date as date_type, timedelta

sys.path.insert(0, "c:/IPO-BOT")
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.db.session import SessionLocal
from app.models.ipo import IPO, IPOStatus
from app.models.gmp_history import GMPHistory
from app.models.subscription_history import SubscriptionHistory
from app.bot.client import TelegramAPIClient
from app.core.logging import logger


def format_12h_digest_table(db) -> str:
    all_ipos = db.query(IPO).all()
    today = date_type.today()

    # ── Filter & sort ───────────────────────────────────────────────────────
    open_ipos = sorted(
        [i for i in all_ipos if i.status == IPOStatus.OPEN],
        key=lambda x: x.close_date or date_type(2099, 1, 1)
    )
    upcoming_ipos = sorted(
        [i for i in all_ipos
         if i.status == IPOStatus.UPCOMING
         and i.open_date and i.open_date <= today + timedelta(days=30)],
        key=lambda x: x.open_date
    )
    closed_ipos = sorted(
        [i for i in all_ipos
         if i.status in (IPOStatus.CLOSED, IPOStatus.ALLOTTED, IPOStatus.LISTED)
         and i.close_date and i.close_date >= today - timedelta(days=10)],
        key=lambda x: x.close_date,
        reverse=True
    )

    # IST time
    try:
        from zoneinfo import ZoneInfo
        now_ist_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y %I:%M %p IST")
    except Exception:
        now_ist_str = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    lines = [
        "LIVE IPO MARKET DIGEST",
        f"Updated: {now_ist_str}\n",
    ]

    def get_gmp(ipo):
        return (db.query(GMPHistory)
                .filter(GMPHistory.ipo_id == ipo.id)
                .order_by(GMPHistory.observation_time.desc())
                .first())

    def get_sub(ipo):
        return (db.query(SubscriptionHistory)
                .filter(SubscriptionHistory.ipo_id == ipo.id)
                .order_by(SubscriptionHistory.observation_time.desc())
                .first())

    def tag(ipo):
        return "[MB]" if str(ipo.issue_type.value).upper() in ("MAINBOARD", "MB") else "[SME]"

    def short_name(name, n=18):
        return (name[:n] + "..") if len(name) > n else name

    def band(ipo):
        if ipo.min_price and ipo.max_price and ipo.min_price != ipo.max_price:
            return f"Rs{int(ipo.min_price)}-{int(ipo.max_price)}"
        elif ipo.max_price:
            return f"Rs{int(ipo.max_price)}"
        return "TBA"

    def fmt_date(d):
        return d.strftime("%d %b") if d else "TBA"

    # ── OPEN IPOs ───────────────────────────────────────────────────────────
    lines.append("🔴 OPEN IPOs — Apply Now")
    if open_ipos:
        tbl = [
            f"{'NAME':<24} {'BAND':<14} {'GMP':<9} {'SUB':<7} CLOSE",
            "─" * 65,
        ]
        for ipo in open_ipos:
            gmp_r = get_gmp(ipo)
            sub_r = get_sub(ipo)
            nm    = tag(ipo) + " " + short_name(ipo.company_name)
            gmp_s = f"+Rs{gmp_r.gmp_price:.0f}" if (gmp_r and gmp_r.gmp_price) else "-"
            sub_s = f"{sub_r.overall_x:.1f}x"   if (sub_r and sub_r.overall_x)  else "-"
            tbl.append(f"{nm:<24} {band(ipo):<14} {gmp_s:<9} {sub_s:<7} {fmt_date(ipo.close_date)}")
        lines.append("```\n" + "\n".join(tbl) + "\n```")
    else:
        lines.append("No IPOs currently open.\n")

    # ── UPCOMING IPOs ────────────────────────────────────────────────────────
    lines.append("\n📅 UPCOMING IPOs — Opening Soon")
    if upcoming_ipos:
        tbl = [
            f"{'NAME':<24} {'BAND':<14} {'OPEN':<10} CLOSE",
            "─" * 58,
        ]
        for ipo in upcoming_ipos[:8]:
            nm = tag(ipo) + " " + short_name(ipo.company_name)
            tbl.append(f"{nm:<24} {band(ipo):<14} {fmt_date(ipo.open_date):<10} {fmt_date(ipo.close_date)}")
        lines.append("```\n" + "\n".join(tbl) + "\n```")
    else:
        lines.append("No upcoming IPOs with confirmed dates.\n")

    # ── RECENTLY CLOSED ──────────────────────────────────────────────────────
    lines.append("\n✅ RECENTLY CLOSED — Results & Listing")
    if closed_ipos:
        tbl = [
            f"{'NAME':<24} {'PRICE':<10} {'GMP':<9} {'SUB':<8} CLOSE",
            "─" * 62,
        ]
        for ipo in closed_ipos[:6]:
            gmp_r = get_gmp(ipo)
            sub_r = get_sub(ipo)
            nm     = tag(ipo) + " " + short_name(ipo.company_name)
            price_s = f"Rs{int(ipo.max_price)}" if ipo.max_price else "TBA"
            gmp_s  = f"+Rs{gmp_r.gmp_price:.0f}" if (gmp_r and gmp_r.gmp_price) else "-"
            sub_s  = f"{sub_r.overall_x:.1f}x"   if (sub_r and sub_r.overall_x)  else "-"
            tbl.append(f"{nm:<24} {price_s:<10} {gmp_s:<9} {sub_s:<8} {fmt_date(ipo.close_date)}")
        lines.append("```\n" + "\n".join(tbl) + "\n```")
    else:
        lines.append("No recently closed IPOs in the last 10 days.\n")

    lines.append("\n_Live data from NSE/BSE via ipowatch.in. GMP is unofficial/unregulated._")
    lines.append("_Data refreshes automatically every 6 hours._")

    return "\n".join(lines)


async def test_and_send_digest():
    db = SessionLocal()
    try:
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        msg = format_12h_digest_table(db)
        try:
            print("=== GENERATED 12-HOUR DIGEST TABLE MESSAGE ===")
            print(msg)
            print("=============================================")
        except Exception as pe:
            logger.info(f"Console print skipped: {pe}")

        from app.bot.config import bot_settings
        from app.bot.subscribers import load_subscribers
        telegram_client = TelegramAPIClient()

        recipients = set(bot_settings.ADMIN_CHAT_IDS) | load_subscribers()
        recipients = {r for r in recipients if r and r != "123456789"}

        if not recipients:
            logger.info("[Digest] No active subscriber chat IDs. Waiting for /start.")

        for chat_id in recipients:
            try:
                await telegram_client.send_message(chat_id, msg)
                logger.info(f"[PASS] Digest sent to {chat_id}")
            except Exception as e:
                logger.error(f"[FAIL] Send to {chat_id}: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_and_send_digest())
