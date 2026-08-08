from typing import Dict, Any, List, Optional

GMP_DISCLAIMER = (
    "\n\n⚠️ *Disclaimer*: Grey Market Premium (GMP) is an informal, unorganized, "
    "and unregulated over-the-counter indicator. It is NOT endorsed by SEBI, NSE, or BSE."
)

def get_trend_badge(trend: str) -> str:
    t = (trend or "").upper()
    if t == "RISING":
        return "🟢 RISING"
    elif t == "FALLING":
        return "🔴 FALLING"
    elif t == "STABLE":
        return "🟡 STABLE"
    return "⚪ UNKNOWN"

def format_start_message() -> str:
    return (
        "🤖 *Welcome to the Indian IPO Intelligence Agent!*\n\n"
        "Your real-time platform for tracking Indian Mainboard & SME IPOs, "
        "live subscription rates, Grey Market Premium (GMP) trends, AI synthesis, and allotment links.\n\n"
        "📌 *Quick Commands*:\n"
        "• /open - List currently open IPOs\n"
        "• /upcoming - List upcoming IPOs\n"
        "• /gmp - Overview of active GMP rates\n"
        "• /gmp `<symbol>` - Detailed GMP analysis & 24h trend\n"
        "• /details `<symbol>` - Master IPO details & prospectus\n"
        "• /analysis `<symbol>` - Grounded AI IPO risk & financial analysis\n"
        "• /subscription `<symbol>` - Live & category-wise subscription\n"
        "• /history `<symbol>` - Full GMP time-series history\n"
        "• /help - Display command guide & legal notices"
    )

def format_help_message() -> str:
    return (
        "📖 *Indian IPO Intelligence Bot Guide*\n\n"
        "Available Commands:\n"
        "• `/start` - Start bot and show main menu\n"
        "• `/help` - Show command help\n"
        "• `/ipo` - High-level market overview\n"
        "• `/open` - List IPOs open for bidding\n"
        "• `/upcoming` - List upcoming IPO filings\n"
        "• `/gmp` - Active GMP rates dashboard\n"
        "• `/gmp <symbol>` - Check GMP, deltas & 24h trend for an IPO\n"
        "• `/details <symbol>` - View price band, lot size, issue size, dates\n"
        "• `/analysis <symbol>` - Grounded AI positive signals & risk assessment\n"
        "• `/history <symbol>` - View full historical GMP time-series\n"
        "• `/subscription <symbol>` - View QIB, NII, Retail & Overall subscription rates"
        + GMP_DISCLAIMER
    )

def format_ipo_list(ipos: List[Dict[str, Any]], title: str) -> str:
    if not ipos:
        return f"📋 *{title}*\n\nNo IPOs found matching this criteria."

    lines = [f"📋 *{title}* ({len(ipos)} Found)\n"]
    for idx, ipo in enumerate(ipos, start=1):
        sym = ipo.get("symbol", "N/A")
        name = ipo.get("company_name", "N/A")
        price = f"₹{ipo.get('min_price', 0)} - ₹{ipo.get('max_price', 0)}" if ipo.get("max_price") else "TBA"
        status = ipo.get("status", "N/A")
        open_d = ipo.get("open_date", "TBA")
        close_d = ipo.get("close_date", "TBA")

        lines.append(
            f"{idx}. *{sym}* ({name})\n"
            f"   • Price: {price} | Lot: {ipo.get('lot_size', 'TBA')}\n"
            f"   • Dates: {open_d} to {close_d}\n"
            f"   • Status: `{status}`\n"
        )
    return "\n".join(lines)

def format_ipo_details(ipo: Dict[str, Any]) -> str:
    sym = ipo.get("symbol", "N/A")
    name = ipo.get("company_name", "N/A")
    type_str = ipo.get("issue_type", "MAINBOARD")
    status = ipo.get("status", "N/A")
    price = f"₹{ipo.get('min_price', 0)} - ₹{ipo.get('max_price', 0)}" if ipo.get("max_price") else "TBA"
    issue_price = f"₹{ipo.get('issue_price')}" if ipo.get("issue_price") else "TBA"
    lot = ipo.get("lot_size", "TBA")
    total_size = f"₹{ipo.get('total_issue_size_cr')} Cr" if ipo.get("total_issue_size_cr") else "TBA"
    fresh = f"₹{ipo.get('fresh_issue_cr')} Cr" if ipo.get("fresh_issue_cr") else "TBA"
    ofs = f"₹{ipo.get('offer_for_sale_cr')} Cr" if ipo.get("offer_for_sale_cr") else "TBA"
    
    open_d = ipo.get("open_date", "TBA")
    close_d = ipo.get("close_date", "TBA")
    allot_d = ipo.get("allotment_date", "TBA")
    list_d = ipo.get("listing_date", "TBA")
    registrar = ipo.get("registrar_name", "N/A")
    reg_url = ipo.get("registrar_url", "")

    msg = (
        f"🏢 *{name}* (`{sym}`)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Category*: {type_str} | Status: `{status}`\n"
        f"• *Price Band*: {price}\n"
        f"• *Cut-off / Issue Price*: {issue_price}\n"
        f"• *Lot Size*: {lot} Shares\n"
        f"• *Issue Size*: {total_size} (Fresh: {fresh} | OFS: {ofs})\n\n"
        f"📅 *Event Timeline*:\n"
        f"• Bidding Open: {open_d}\n"
        f"• Bidding Close: {close_d}\n"
        f"• Allotment Finalization: {allot_d}\n"
        f"• Exchange Listing: {list_d}\n\n"
        f"🏛️ *Registrar*: {registrar}\n"
    )
    if reg_url:
        msg += f"🔗 [Check Allotment Status]({reg_url})\n"
    return msg

def format_gmp_analysis(analysis: Dict[str, Any]) -> str:
    sym = analysis.get("symbol", "N/A")
    name = analysis.get("company_name", "N/A")
    curr_gmp = analysis.get("current_gmp")
    gmp_pct = analysis.get("gmp_percent")
    prev_gmp = analysis.get("previous_gmp")
    abs_change = analysis.get("absolute_change")
    pct_change = analysis.get("percentage_change")
    h24_change = analysis.get("twenty_four_hour_change")
    trend = analysis.get("trend", "UNKNOWN")
    badge = get_trend_badge(trend)
    obs_time = analysis.get("latest_observation_time", "N/A")
    src = analysis.get("source_code", "N/A")

    if curr_gmp is None:
        return f"📈 *GMP Analysis: {sym}*\n\nNo GMP observations recorded for this IPO yet." + GMP_DISCLAIMER

    abs_str = f"+₹{abs_change}" if abs_change and abs_change > 0 else (f"₹{abs_change}" if abs_change is not None else "N/A")
    pct_str = f"+{pct_change}%" if pct_change and pct_change > 0 else (f"{pct_change}%" if pct_change is not None else "N/A")
    h24_str = f"+₹{h24_change}" if h24_change and h24_change > 0 else (f"₹{h24_change}" if h24_change is not None else "N/A")
    prev_str = f"₹{prev_gmp}" if prev_gmp is not None else "N/A"
    gmp_pct_str = f" ({gmp_pct}%)" if gmp_pct is not None else ""

    return (
        f"📈 *GMP Analysis: {name}* (`{sym}`)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Current GMP*: ₹{curr_gmp}{gmp_pct_str}\n"
        f"• *Previous GMP*: {prev_str}\n"
        f"• *Absolute Change*: {abs_str} ({pct_str})\n"
        f"• *24-Hour Change*: {h24_str}\n"
        f"• *Current Trend*: {badge}\n"
        f"• *Source*: `{src}` ({obs_time})\n"
        + GMP_DISCLAIMER
    )

def format_gmp_history(history_data: Dict[str, Any]) -> str:
    sym = history_data.get("symbol", "N/A")
    history = history_data.get("history", [])

    if not history:
        return f"📜 *GMP History: {sym}*\n\nNo historical observations recorded." + GMP_DISCLAIMER

    lines = [f"📜 *GMP History: {sym}* ({len(history)} Observations)\n"]
    for item in history[:10]:
        price = item.get("gmp_price", 0)
        pct = f" ({item.get('gmp_percent')}%)" if item.get("gmp_percent") is not None else ""
        time_str = item.get("observation_time", "N/A")
        src = item.get("source_code", "N/A")
        lines.append(f"• *₹{price}*{pct} — `{src}` ({time_str})")

    lines.append(GMP_DISCLAIMER)
    return "\n".join(lines)

def format_subscription(sub_data: Dict[str, Any]) -> str:
    sym = sub_data.get("symbol", "N/A")
    latest = sub_data.get("latest")

    if not latest:
        return f"📊 *Subscription Status: {sym}*\n\nNo subscription records available yet."

    overall = latest.get("overall_x", 0)
    qib = latest.get("qib_x", "N/A")
    nii = latest.get("nii_x", "N/A")
    b_nii = latest.get("b_nii_x", "N/A")
    s_nii = latest.get("s_nii_x", "N/A")
    retail = latest.get("retail_x", "N/A")
    emp = latest.get("employee_x", "N/A")
    obs_time = latest.get("observation_time", "N/A")

    return (
        f"📊 *Subscription Status: {sym}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Overall Subscription*: *{overall}x*\n"
        f"• *QIB Category*: {qib}x\n"
        f"• *NII Category*: {nii}x (bNII: {b_nii}x | sNII: {s_nii}x)\n"
        f"• *Retail Category*: {retail}x\n"
        f"• *Employee Quota*: {emp}x\n"
        f"• *Last Updated*: `{obs_time}`"
    )
