"""
Sync Real Current IPO Data from IPO Notify Provider into SQLite DB.
Creates DB tables if missing, fetches open, upcoming, closed IPOs,
and populates ipo_agent.db with authentic live market records.
"""
import sys
import os
import asyncio
import io

sys.path.insert(0, "c:/IPO-BOT")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.session import engine, SessionLocal
from app.models.base_class import Base
from app.providers.ipo_notify_provider import IPONotifyProvider
from app.services.ipo_sync_service import IPOSyncService
from app.models.ipo import IPO, IPOStatus, IssueType
from app.models.gmp_history import GMPHistory

async def main():
    print("=" * 80)
    print("      INITIALIZING DATABASE & SYNCING LIVE CURRENT IPO DATA")
    print("=" * 80)

    # 1. Create tables
    print("\n1. Creating database tables if missing...")
    Base.metadata.create_all(bind=engine)
    print("   [PASS] DB tables ready.")

    # 2. Sync from IPO Notify Provider
    print("\n2. Executing IPOSyncService with IPONotifyProvider...")
    provider = IPONotifyProvider()

    db = SessionLocal()
    try:
        sync_service = IPOSyncService(db=db)

        # Sync open, upcoming, closed
        result_open = await sync_service.sync_provider(provider=provider, status_filter="open")
        print(f"   [OPEN SYNC] Processed: {result_open.ipos_processed}, Created: {result_open.ipos_created}, Updated: {result_open.ipos_updated}")
        if result_open.errors:
            print(f"   Errors: {result_open.errors}")

        result_upcoming = await sync_service.sync_provider(provider=provider, status_filter="upcoming")
        print(f"   [UPCOMING SYNC] Processed: {result_upcoming.ipos_processed}, Created: {result_upcoming.ipos_created}, Updated: {result_upcoming.ipos_updated}")

        result_closed = await sync_service.sync_provider(provider=provider, status_filter="closed")
        print(f"   [CLOSED SYNC] Processed: {result_closed.ipos_processed}, Created: {result_closed.ipos_created}, Updated: {result_closed.ipos_updated}")

        # 3. Print stored IPOs
        all_ipos = db.query(IPO).all()
        print("\n" + "=" * 80)
        print(f"      DATABASE SUMMARY: {len(all_ipos)} TOTAL IPOs STORED IN LOCAL DB")
        print("=" * 80)

        for status_type in [IPOStatus.OPEN, IPOStatus.UPCOMING, IPOStatus.CLOSED, IPOStatus.LISTED]:
            matching = [i for i in all_ipos if i.status == status_type]
            print(f"\n📌 {status_type.value} ({len(matching)} records):")
            for ipo in matching:
                gmp_records = db.query(GMPHistory).filter(GMPHistory.ipo_id == ipo.id).all()
                latest_gmp = gmp_records[-1].gmp_value if gmp_records else None
                print(f"  • [{ipo.issue_type.value}] {ipo.symbol:<15} | {ipo.company_name:<40} | Price: ₹{ipo.min_price or 0:.0f}-₹{ipo.max_price or 0:.0f} | Lot: {ipo.lot_size or 'N/A'} | Open: {ipo.open_date} | Close: {ipo.close_date} | GMP: ₹{latest_gmp if latest_gmp is not None else 'N/A'}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
