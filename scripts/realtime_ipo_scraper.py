"""
Real-Time IPO Data Scraper — ipowatch.in (Mainboard + SME)
Scrapes live IPO data every 6 hours and updates the database.
Also fetches GMP from ipowatch.in/ipo-gmp-grey-market-premium/
"""
import sys, os, re
sys.path.insert(0, "c:/IPO-BOT")
from dotenv import load_dotenv
load_dotenv("c:/IPO-BOT/.env")

import httpx
from bs4 import BeautifulSoup
from datetime import date, datetime, timezone
from typing import Optional

from app.db.session import SessionLocal, engine
from app.models import Base
from app.models.ipo import IPO, IPOStatus, IssueType
from app.models.gmp_history import GMPHistory
from app.models.subscription_history import SubscriptionHistory
from app.models.data_source import DataSource
from app.core.logging import logger

Base.metadata.create_all(bind=engine)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://ipowatch.in/",
}

CURRENT_YEAR = 2026


def parse_price(s: str) -> Optional[float]:
    """Extract the max price from a string like '₹92 to ₹97' or '₹285'."""
    if not s:
        return None
    nums = re.findall(r"[\d,]+(?:\.\d+)?", s.replace(",", ""))
    floats = [float(n) for n in nums if n]
    return floats[-1] if floats else None


def parse_min_price(s: str) -> Optional[float]:
    if not s:
        return None
    nums = re.findall(r"[\d,]+(?:\.\d+)?", s.replace(",", ""))
    floats = [float(n) for n in nums if n]
    return floats[0] if floats else None


def parse_issue_size(s: str) -> Optional[float]:
    """Parse '₹1,617.48 Cr.' to 1617.48"""
    if not s:
        return None
    m = re.search(r"[\d,]+(?:\.\d+)?", s.replace(",", ""))
    return float(m.group()) if m else None


def parse_ipo_dates(date_str: str) -> tuple[Optional[date], Optional[date]]:
    """
    Parse dates like '12-14 August' or '7-11 August' → (open_date, close_date).
    ipowatch format: 'DD-DD Month' or 'DD Month - DD Month'
    """
    date_str = date_str.strip()
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }

    # Pattern: "12-14 August" → day1=12, day2=14, month=August
    m = re.match(r"(\d+)-(\d+)\s+([A-Za-z]+)", date_str)
    if m:
        d1, d2, mon = int(m.group(1)), int(m.group(2)), m.group(3).lower()
        month_num = months.get(mon)
        if month_num:
            # Handle month roll-over e.g. "30-3 August" = July 30 to Aug 3
            if d1 > d2:
                prev_month = month_num - 1 if month_num > 1 else 12
                prev_year = CURRENT_YEAR if month_num > 1 else CURRENT_YEAR - 1
                open_d = date(prev_year, prev_month, d1)
                close_d = date(CURRENT_YEAR, month_num, d2)
            else:
                open_d = date(CURRENT_YEAR, month_num, d1)
                close_d = date(CURRENT_YEAR, month_num, d2)
            return open_d, close_d

    return None, None


def determine_status(open_d: Optional[date], close_d: Optional[date]) -> IPOStatus:
    today = date.today()
    if not open_d or not close_d:
        return IPOStatus.UPCOMING
    if today < open_d:
        return IPOStatus.UPCOMING
    elif open_d <= today <= close_d:
        return IPOStatus.OPEN
    else:
        return IPOStatus.CLOSED


def symbol_from_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", name.upper())[:12]


def scrape_ipowatch_all() -> dict:
    """Scrape ipowatch.in for mainboard + SME open and upcoming IPOs."""
    result = {"mainboard": [], "sme": []}
    try:
        with httpx.Client(follow_redirects=True, timeout=20) as c:
            r = c.get("https://ipowatch.in/upcoming-ipo/", headers=HEADERS)
            if r.status_code != 200:
                logger.warning(f"[ipowatch] upcoming-ipo status {r.status_code}")
                return result

            soup = BeautifulSoup(r.text, "lxml")
            tables = soup.find_all("table")

            # Table 1 → Mainboard (columns: Company | Date | Size | Price Band | Apply)
            # Table 2 → SME (columns: IPO | Date | Size | Price Band | Platform | Apply)
            for tbl_idx, tbl_key in enumerate(["mainboard", "sme"]):
                if tbl_idx >= len(tables):
                    break
                rows = tables[tbl_idx].find_all("tr")
                for row in rows[1:]:  # skip header
                    cols = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cols) < 3 or not cols[0].strip():
                        continue
                    name = cols[0].strip()
                    date_str = cols[1].strip()
                    size_str = cols[2].strip() if len(cols) > 2 else ""
                    price_str = cols[3].strip() if len(cols) > 3 else ""
                    platform = cols[4].strip() if len(cols) > 4 else ("NSE/BSE" if tbl_key == "mainboard" else "SME")

                    open_d, close_d = parse_ipo_dates(date_str)
                    max_p = parse_price(price_str)
                    min_p = parse_min_price(price_str)
                    size_cr = parse_issue_size(size_str)
                    status = determine_status(open_d, close_d)

                    result[tbl_key].append({
                        "company_name": name,
                        "symbol": symbol_from_name(name),
                        "open_date": open_d,
                        "close_date": close_d,
                        "min_price": min_p,
                        "max_price": max_p,
                        "issue_price": max_p,
                        "total_issue_size_cr": size_cr,
                        "issue_type": IssueType.MAINBOARD if tbl_key == "mainboard" else IssueType.SME,
                        "status": status,
                    })

        logger.info(f"[ipowatch] Mainboard: {len(result['mainboard'])}, SME: {len(result['sme'])}")
    except Exception as e:
        logger.error(f"[ipowatch] Scrape error: {e}")
        import traceback; traceback.print_exc()
    return result


def scrape_gmp_from_ipowatch() -> list:
    """
    Scrape GMP data from ipowatch.in/ipo-gmp-grey-market-premium/
    Page uses JS rendering — fallback: scrape main page for GMP column if present.
    """
    gmp_list = []
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as c:
            r = c.get("https://ipowatch.in/ipo-gmp-grey-market-premium/", headers=HEADERS)
            soup = BeautifulSoup(r.text, "lxml")
            # Try to find any table
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = [td.get_text(strip=True) for td in row.find_all("td")]
                    if len(cols) >= 3:
                        name = cols[0]
                        gmp_raw = cols[1] if len(cols) > 1 else "0"
                        gmp_val = parse_price(gmp_raw) or 0.0
                        if gmp_val > 0:
                            gmp_list.append({"company_name": name, "gmp": gmp_val})
    except Exception as e:
        logger.warning(f"[GMP Scrape] {e}")
    logger.info(f"[GMP] Scraped {len(gmp_list)} GMP records from ipowatch")
    return gmp_list


def name_match(a: str, b: str) -> bool:
    stop = {"limited", "ltd", "private", "pvt", "inc", "the", "of", "and", "enterprises", "ipo"}
    a_words = set(re.sub(r"[^a-z0-9]", " ", a.lower()).split()) - stop
    b_words = set(re.sub(r"[^a-z0-9]", " ", b.lower()).split()) - stop
    common = a_words & b_words
    return len(common) >= 1 and len(a_words) > 0


def upsert_ipos(db, source, all_ipos: list) -> int:
    now = datetime.now(timezone.utc)
    count = 0
    for rec in all_ipos:
        name = rec["company_name"]
        symbol = rec["symbol"]

        # Try matching by symbol first, then by name
        existing = db.query(IPO).filter(IPO.symbol == symbol).first()
        if not existing:
            existing = db.query(IPO).filter(IPO.company_name.ilike(f"%{name[:15]}%")).first()

        if existing:
            # Update mutable fields
            existing.status = rec["status"]
            if rec.get("max_price"): existing.max_price = rec["max_price"]
            if rec.get("min_price"): existing.min_price = rec["min_price"]
            if rec.get("issue_price"): existing.issue_price = rec["issue_price"]
            if rec.get("open_date"): existing.open_date = rec["open_date"]
            if rec.get("close_date"): existing.close_date = rec["close_date"]
            if rec.get("total_issue_size_cr"): existing.total_issue_size_cr = rec["total_issue_size_cr"]
            logger.info(f"  [UPDATE] {name} → {rec['status'].value}")
        else:
            new_ipo = IPO(
                symbol=symbol,
                company_name=name,
                issue_type=rec["issue_type"],
                status=rec["status"],
                min_price=rec.get("min_price"),
                max_price=rec.get("max_price"),
                issue_price=rec.get("issue_price"),
                total_issue_size_cr=rec.get("total_issue_size_cr"),
                open_date=rec.get("open_date"),
                close_date=rec.get("close_date"),
                primary_source_id=source.id,
            )
            db.add(new_ipo)
            logger.info(f"  [INSERT] {name} ({rec['status'].value})")
        count += 1
    return count


def update_gmp_in_db(db, source, gmp_list: list):
    now = datetime.now(timezone.utc)
    all_ipos = db.query(IPO).all()
    updated = 0
    for ipo in all_ipos:
        for g in gmp_list:
            if name_match(ipo.company_name, g["company_name"]) and g["gmp"] > 0:
                issue_p = ipo.max_price or ipo.issue_price or 0
                gmp_pct = round((g["gmp"] / issue_p) * 100, 2) if issue_p else 0.0
                db.add(GMPHistory(
                    ipo_id=ipo.id, source_id=source.id,
                    gmp_price=g["gmp"], gmp_percent=gmp_pct,
                    estimated_listing_price=(issue_p + g["gmp"]),
                    observation_time=now,
                ))
                updated += 1
                break
    return updated


def run_realtime_update():
    """Main function: scrape + update DB."""
    db = SessionLocal()
    try:
        source = db.query(DataSource).filter(DataSource.code == "LIVE_EXCHANGE").first()
        if not source:
            source = DataSource(code="LIVE_EXCHANGE", name="NSE/BSE Live Exchange Data via ipowatch.in")
            db.add(source)
            db.flush()

        logger.info("[RealTime Scraper] Fetching IPO data from ipowatch.in...")
        scraped = scrape_ipowatch_all()
        gmp_data = scrape_gmp_from_ipowatch()

        all_ipos = scraped["mainboard"] + scraped["sme"]
        if not all_ipos:
            logger.warning("[RealTime Scraper] No data scraped. Keeping existing DB data.")
            return False

        n_upserted = upsert_ipos(db, source, all_ipos)
        n_gmp = update_gmp_in_db(db, source, gmp_data)
        db.commit()

        logger.info(f"[RealTime Scraper] Done. Upserted: {n_upserted} IPOs, GMP updated: {n_gmp}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"[RealTime Scraper] Error: {e}")
        import traceback; traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 60)
    print("  REAL-TIME IPO SCRAPER — ipowatch.in")
    print("=" * 60)
    ok = run_realtime_update()
    print(f"\n{'[SUCCESS]' if ok else '[WARN] No data scraped.'} Done.")
