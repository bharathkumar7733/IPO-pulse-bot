import httpx
from typing import Dict, Any, Optional
from app.bot.client import BackendAPIClient, TelegramAPIClient
from app.bot.formatter import (
    format_start_message,
    format_help_message,
    format_ipo_list,
    format_ipo_details,
    format_gmp_analysis,
    format_gmp_history,
    format_subscription
)
from app.core.logging import logger

backend_client = BackendAPIClient()
telegram_client = TelegramAPIClient()

async def handle_start(chat_id: str):
    msg = format_start_message()
    await telegram_client.send_message(chat_id, msg)

async def handle_help(chat_id: str):
    msg = format_help_message()
    await telegram_client.send_message(chat_id, msg)

async def handle_ipo(chat_id: str):
    try:
        data = await backend_client.get_ipos(limit=10)
        ipos = data.get("ipos", [])
        msg = format_ipo_list(ipos, "Active & Upcoming IPOs")
        await telegram_client.send_message(chat_id, msg)
    except Exception as e:
        logger.error(f"Error handling /ipo: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to fetch IPO overview at this time. Please try again later.")

async def handle_open(chat_id: str):
    try:
        ipos = await backend_client.get_open_ipos()
        msg = format_ipo_list(ipos, "Currently Open IPOs")
        await telegram_client.send_message(chat_id, msg)
    except Exception as e:
        logger.error(f"Error handling /open: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to fetch open IPOs right now.")

async def handle_upcoming(chat_id: str):
    try:
        ipos = await backend_client.get_upcoming_ipos()
        msg = format_ipo_list(ipos, "Upcoming IPOs")
        await telegram_client.send_message(chat_id, msg)
    except Exception as e:
        logger.error(f"Error handling /upcoming: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to fetch upcoming IPOs right now.")

async def handle_gmp(chat_id: str, arg: Optional[str] = None):
    if not arg:
        try:
            open_ipos = await backend_client.get_open_ipos()
            if not open_ipos:
                data = await backend_client.get_ipos(limit=5)
                open_ipos = data.get("ipos", [])

            if not open_ipos:
                await telegram_client.send_message(chat_id, "📈 *GMP Dashboard*\n\nNo active IPOs found.")
                return

            analyses = []
            for ipo in open_ipos[:5]:
                sym = ipo.get("symbol")
                try:
                    analysis = await backend_client.get_gmp_analysis(sym)
                    analyses.append(analysis)
                except Exception:
                    pass

            if not analyses:
                await telegram_client.send_message(chat_id, "📈 *GMP Dashboard*\n\nNo active GMP data available.")
                return

            lines = ["📈 *Active IPOs GMP Dashboard*\n"]
            for a in analyses:
                sym = a.get("symbol", "N/A")
                gmp = a.get("current_gmp")
                pct = f" ({a.get('gmp_percent')}%)" if a.get("gmp_percent") is not None else ""
                trend = a.get("trend", "UNKNOWN")
                gmp_str = f"₹{gmp}{pct}" if gmp is not None else "No Data"
                lines.append(f"• *{sym}*: {gmp_str} | Trend: `{trend}`")

            lines.append("\n_Use /gmp <symbol> for detailed 24h trend analysis._")
            await telegram_client.send_message(chat_id, "\n".join(lines))
        except Exception as e:
            logger.error(f"Error handling /gmp global: {e}")
            await telegram_client.send_message(chat_id, "⚠️ Unable to fetch GMP dashboard right now.")
    else:
        try:
            analysis = await backend_client.get_gmp_analysis(arg.strip().upper())
            msg = format_gmp_analysis(analysis)
            await telegram_client.send_message(chat_id, msg)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                await telegram_client.send_message(chat_id, f"⚠️ IPO symbol or identifier '{arg}' not found.")
            else:
                await telegram_client.send_message(chat_id, "⚠️ Failed to retrieve GMP analysis.")
        except Exception as e:
            logger.error(f"Error handling /gmp {arg}: {e}")
            await telegram_client.send_message(chat_id, "⚠️ Failed to retrieve GMP analysis.")

async def handle_details(chat_id: str, arg: Optional[str] = None):
    if not arg:
        await telegram_client.send_message(chat_id, "⚠️ Please specify an IPO symbol or ID. Example: `/details SWIGGY`")
        return

    try:
        ipo = await backend_client.get_ipo_detail(arg.strip().upper())
        msg = format_ipo_details(ipo)
        await telegram_client.send_message(chat_id, msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await telegram_client.send_message(chat_id, f"⚠️ IPO symbol '{arg}' not found. Use /open to see active IPOs.")
        else:
            await telegram_client.send_message(chat_id, "⚠️ Unable to fetch IPO details.")
    except Exception as e:
        logger.error(f"Error handling /details {arg}: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to fetch IPO details.")

async def handle_analysis(chat_id: str, arg: Optional[str] = None):
    if not arg:
        await telegram_client.send_message(chat_id, "⚠️ Please specify an IPO symbol or ID. Example: `/analysis SWIGGY`")
        return

    try:
        data = await backend_client.get_ai_analysis(arg.strip().upper())
        msg = data.get("formatted_markdown")
        await telegram_client.send_message(chat_id, msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await telegram_client.send_message(chat_id, f"⚠️ IPO symbol '{arg}' not found.")
        else:
            await telegram_client.send_message(chat_id, "⚠️ Unable to generate AI analysis.")
    except Exception as e:
        logger.error(f"Error handling /analysis {arg}: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to generate AI analysis.")

async def handle_history(chat_id: str, arg: Optional[str] = None):
    if not arg:
        await telegram_client.send_message(chat_id, "⚠️ Please specify an IPO symbol or ID. Example: `/history SWIGGY`")
        return

    try:
        history_data = await backend_client.get_gmp_history(arg.strip().upper())
        msg = format_gmp_history(history_data)
        await telegram_client.send_message(chat_id, msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await telegram_client.send_message(chat_id, f"⚠️ IPO symbol '{arg}' not found.")
        else:
            await telegram_client.send_message(chat_id, "⚠️ Unable to fetch GMP history.")
    except Exception as e:
        logger.error(f"Error handling /history {arg}: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to fetch GMP history.")

async def handle_subscription(chat_id: str, arg: Optional[str] = None):
    if not arg:
        await telegram_client.send_message(chat_id, "⚠️ Please specify an IPO symbol or ID. Example: `/subscription SWIGGY`")
        return

    try:
        sub_data = await backend_client.get_subscription(arg.strip().upper())
        msg = format_subscription(sub_data)
        await telegram_client.send_message(chat_id, msg)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            await telegram_client.send_message(chat_id, f"⚠️ IPO symbol '{arg}' not found.")
        else:
            await telegram_client.send_message(chat_id, "⚠️ Unable to fetch subscription details.")
    except Exception as e:
        logger.error(f"Error handling /subscription {arg}: {e}")
        await telegram_client.send_message(chat_id, "⚠️ Unable to fetch subscription details.")
