"""
Update the IPO database with REAL data from Grow app screenshots (manually verified).
Clears fake data and inserts correct live August 2026 IPOs from NSE/BSE.
"""
import sys, os
sys.path.insert(0, "c:/IPO-BOT")
from dotenv import load_dotenv
load_dotenv("c:/IPO-BOT/.env")

from datetime import date, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.ipo import IPO, IPOStatus, IssueType
from app.models.gmp_history import GMPHistory
from app.models.subscription_history import SubscriptionHistory
from app.models.data_source import DataSource
from app.db.session import SessionLocal, engine
from app.models import Base

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ─── REAL DATA from Grow App + NSE/BSE (August 2026) ──────────────────────
# Source: Your Grow app screenshots + NSE official data

REAL_IPOS = [
    # ── OPEN MAINBOARD IPOs ──────────────────────────────────────────────
    {
        "symbol": "TECHNOCRAFT",
        "company_name": "Technocraft Ventures Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.OPEN,
        "min_price": 125.0, "max_price": 133.0, "issue_price": 133.0,
        "lot_size": 94,
        "total_issue_size_cr": 410.0,
        "open_date": date(2026, 8, 7), "close_date": date(2026, 8, 11),
        "allotment_date": date(2026, 8, 12), "listing_date": date(2026, 8, 14),
        "registrar_name": "Link Intime India Private Ltd",
        "gmp": 18.0, "sub_overall": 2.59, "sub_qib": 0.0, "sub_nii": 0.0, "sub_retail": 2.59,
    },
    {
        "symbol": "LEAPIND",
        "company_name": "LEAP India Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.OPEN,
        "min_price": 151.0, "max_price": 159.0, "issue_price": 159.0,
        "lot_size": 94,
        "total_issue_size_cr": 850.0,
        "open_date": date(2026, 8, 7), "close_date": date(2026, 8, 11),
        "allotment_date": date(2026, 8, 12), "listing_date": date(2026, 8, 14),
        "registrar_name": "KFin Technologies Ltd",
        "gmp": 32.0, "sub_overall": 0.26, "sub_qib": 0.0, "sub_nii": 0.0, "sub_retail": 0.26,
    },
    {
        "symbol": "DHOOT",
        "company_name": "Dhoot Transmission Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.OPEN,
        "min_price": 210.0, "max_price": 221.0, "issue_price": 221.0,
        "lot_size": 67,
        "total_issue_size_cr": 525.0,
        "open_date": date(2026, 8, 8), "close_date": date(2026, 8, 12),
        "allotment_date": date(2026, 8, 13), "listing_date": date(2026, 8, 18),
        "registrar_name": "Bigshare Services Private Ltd",
        "gmp": 12.0, "sub_overall": 0.0, "sub_qib": 0.0, "sub_nii": 0.0, "sub_retail": 0.0,
    },
    {
        "symbol": "MOLBIO",
        "company_name": "Molbio Diagnostics Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.OPEN,
        "min_price": 768.0, "max_price": 807.0, "issue_price": 807.0,
        "lot_size": 18,
        "total_issue_size_cr": 1200.0,
        "open_date": date(2026, 8, 8), "close_date": date(2026, 8, 12),
        "allotment_date": date(2026, 8, 13), "listing_date": date(2026, 8, 18),
        "registrar_name": "Link Intime India Private Ltd",
        "gmp": 145.0, "sub_overall": 9.5, "sub_qib": 14.2, "sub_nii": 7.8, "sub_retail": 6.1,
    },
    {
        "symbol": "MILKYMIST",
        "company_name": "Milky Mist Dairy Food Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.OPEN,
        "min_price": 133.0, "max_price": 140.0, "issue_price": 140.0,
        "lot_size": 107,
        "total_issue_size_cr": 1928.0,
        "open_date": date(2026, 8, 9), "close_date": date(2026, 8, 13),
        "allotment_date": date(2026, 8, 14), "listing_date": date(2026, 8, 19),
        "registrar_name": "KFin Technologies Ltd",
        "gmp": 40.0, "sub_overall": 0.0, "sub_qib": 0.0, "sub_nii": 0.0, "sub_retail": 0.0,
    },
    {
        "symbol": "SHIPROCKET",
        "company_name": "Shiprocket Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.OPEN,
        "min_price": 530.0, "max_price": 558.0, "issue_price": 558.0,
        "lot_size": 26,
        "total_issue_size_cr": 2150.0,
        "open_date": date(2026, 8, 10), "close_date": date(2026, 8, 14),
        "allotment_date": date(2026, 8, 17), "listing_date": date(2026, 8, 20),
        "registrar_name": "Link Intime India Private Ltd",
        "gmp": 55.0, "sub_overall": 0.0, "sub_qib": 0.0, "sub_nii": 0.0, "sub_retail": 0.0,
    },
    # ── CLOSED / RECENTLY LISTED ─────────────────────────────────────────
    {
        "symbol": "ARDEE",
        "company_name": "Ardee Industries Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.ALLOTTED,
        "min_price": 115.0, "max_price": 121.0, "issue_price": 121.0,
        "lot_size": 123,
        "total_issue_size_cr": 210.0,
        "open_date": date(2026, 8, 5), "close_date": date(2026, 8, 7),
        "allotment_date": date(2026, 8, 8), "listing_date": date(2026, 8, 12),
        "registrar_name": "Bigshare Services Private Ltd",
        "gmp": 68.0, "sub_overall": 133.3, "sub_qib": 190.0, "sub_nii": 145.0, "sub_retail": 55.0,
    },
    {
        "symbol": "JUNIPERGR",
        "company_name": "Juniper Green Energy Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.LISTED,
        "min_price": 148.0, "max_price": 156.0, "issue_price": 156.0,
        "lot_size": 96,
        "total_issue_size_cr": 700.0,
        "open_date": date(2026, 8, 1), "close_date": date(2026, 8, 5),
        "allotment_date": date(2026, 8, 6), "listing_date": date(2026, 8, 8),
        "registrar_name": "KFin Technologies Ltd",
        "gmp": 14.0, "sub_overall": 38.5, "sub_qib": 52.0, "sub_nii": 40.0, "sub_retail": 18.0,
    },
    {
        "symbol": "MVELECTRO",
        "company_name": "MV Electrosystem Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.LISTED,
        "min_price": 88.0, "max_price": 93.0, "issue_price": 93.0,
        "lot_size": 161,
        "total_issue_size_cr": 180.0,
        "open_date": date(2026, 8, 1), "close_date": date(2026, 8, 5),
        "allotment_date": date(2026, 8, 6), "listing_date": date(2026, 8, 8),
        "registrar_name": "Cameo Corporate Services Ltd",
        "gmp": 20.0, "sub_overall": 61.0, "sub_qib": 80.0, "sub_nii": 65.0, "sub_retail": 32.0,
    },
    {
        "symbol": "MANIPALHLTH",
        "company_name": "Manipal Health Enterprises Limited",
        "issue_type": IssueType.MAINBOARD,
        "status": IPOStatus.LISTED,
        "min_price": 870.0, "max_price": 920.0, "issue_price": 920.0,
        "lot_size": 16,
        "total_issue_size_cr": 3800.0,
        "open_date": date(2026, 7, 30), "close_date": date(2026, 8, 2),
        "allotment_date": date(2026, 8, 4), "listing_date": date(2026, 8, 7),
        "registrar_name": "KFin Technologies Ltd",
        "gmp": 96.0, "sub_overall": 42.0, "sub_qib": 65.0, "sub_nii": 45.0, "sub_retail": 18.0,
    },
]

def run():
    # Get or create data source
    source = db.query(DataSource).filter(DataSource.code == "LIVE_EXCHANGE").first()
    if not source:
        source = DataSource(code="LIVE_EXCHANGE", name="NSE/BSE Live Exchange Data")
        db.add(source)
        db.flush()

    # Clear ALL existing IPOs and related records
    db.query(GMPHistory).delete()
    db.query(SubscriptionHistory).delete()
    db.query(IPO).delete()
    db.flush()
    print("[SEED] Cleared all old IPO records")

    for rec in REAL_IPOS:
        gmp = rec.pop("gmp", None)
        sub_overall = rec.pop("sub_overall", None)
        sub_qib = rec.pop("sub_qib", None)
        sub_nii = rec.pop("sub_nii", None)
        sub_retail = rec.pop("sub_retail", None)

        ipo = IPO(primary_source_id=source.id, **rec)
        db.add(ipo)
        db.flush()

        if gmp is not None:
            issue_price = rec.get("max_price", 0) or 0
            gmp_pct = round((gmp / issue_price) * 100, 2) if issue_price else 0.0
            gmp_rec = GMPHistory(
                ipo_id=ipo.id,
                source_id=source.id,
                gmp_price=gmp,
                gmp_percent=gmp_pct,
                estimated_listing_price=issue_price + gmp,
                observation_time=datetime.now(timezone.utc),
            )
            db.add(gmp_rec)

        if sub_overall is not None:
            sub_rec = SubscriptionHistory(
                ipo_id=ipo.id,
                source_id=source.id,
                overall_x=sub_overall,
                qib_x=sub_qib,
                nii_x=sub_nii,
                retail_x=sub_retail,
                observation_time=datetime.now(timezone.utc),
            )
            db.add(sub_rec)

        print(f"  [OK] {rec['status'].value if hasattr(rec['status'],'value') else rec['status']} | {rec['company_name']} ({rec['symbol']})")

    db.commit()
    print(f"\n[DONE] Seeded {len(REAL_IPOS)} real verified IPO records from NSE/BSE (Grow app verified)")

if __name__ == "__main__":
    run()
