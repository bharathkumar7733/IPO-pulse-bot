"""
Sync Real Current IPO Data using Gemini IPO Research Engine into SQLite DB.
Performs real Gemini API call, parses validated Pydantic RawIPODTOs,
and upserts records into ipo_agent.db for live bot testing.
"""
import sys
import os
import asyncio
import io
from datetime import datetime, timezone

sys.path.insert(0, "c:/IPO-BOT")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.db.session import engine, SessionLocal
from app.models.base_class import Base
from app.providers.gemini_ipo_provider import GeminiIPOResearchProvider
from app.repositories.ipo_repository import IPORepository
from app.models.ipo import IPO, IPOStatus, IssueType

async def main():
    print("=" * 80)
    print("   SYNCING REAL CURRENT IPO DATA VIA GEMINI RESEARCH ENGINE INTO DB")
    print("=" * 80)

    # 1. Create tables
    Base.metadata.create_all(bind=engine)
    print("1. DB tables verified.")

    # 2. Run Gemini research
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY is missing.")
        return

    provider = GeminiIPOResearchProvider(api_key=api_key)
    print("2. Calling Gemini Research Engine...")

    try:
        result = await provider.research(force=True)
        print(f"   [PASS] Gemini Research complete (Model: {result.model_used})")
        print(f"   Open: {len(result.open_ipos)}, Upcoming: {len(result.upcoming_ipos)}, Closed: {result.closed_ipos}")

        dtos, errors = provider.gemini_result_to_dtos(result)
        print(f"   Converted RawIPODTOs: {len(dtos)}, Errors: {len(errors)}")

        # 3. Upsert into database
        db = SessionLocal()
        repo = IPORepository(db)
        created_count = 0
        updated_count = 0

        for dto in dtos:
            existing = repo.get_by_id_or_symbol(dto.symbol)
            if existing:
                for field, val in dto.model_dump(exclude={"subscription"}).items():
                    if val is not None and getattr(existing, field) != val:
                        setattr(existing, field, val)
                existing.updated_at = datetime.now(timezone.utc)
                updated_count += 1
            else:
                new_ipo = IPO(
                    symbol=dto.symbol,
                    company_name=dto.company_name,
                    issue_type=dto.issue_type,
                    status=dto.status,
                    min_price=dto.min_price,
                    max_price=dto.max_price,
                    issue_price=dto.issue_price,
                    lot_size=dto.lot_size,
                    total_issue_size_cr=dto.total_issue_size_cr,
                    open_date=dto.open_date,
                    close_date=dto.close_date,
                    allotment_date=dto.allotment_date,
                    listing_date=dto.listing_date,
                    registrar_name=dto.registrar_name,
                )
                db.add(new_ipo)
                created_count += 1

        db.commit()
        print(f"3. DB Upsert complete: Created {created_count}, Updated {updated_count}")

        # 4. Display stored IPOs
        all_ipos = db.query(IPO).all()
        print("\n" + "=" * 80)
        print(f"      DATABASE SUMMARY: {len(all_ipos)} TOTAL IPOs STORED IN LOCAL DB")
        print("=" * 80)

        for status_type in [IPOStatus.OPEN, IPOStatus.UPCOMING, IPOStatus.CLOSED, IPOStatus.LISTED]:
            matching = [i for i in all_ipos if i.status == status_type]
            print(f"\n📌 {status_type.value} ({len(matching)} records):")
            for ipo in matching:
                print(f"  • [{ipo.issue_type.value}] Symbol: {ipo.symbol:<15} | Company: {ipo.company_name:<40} | Price: ₹{ipo.min_price or 0:.0f}-₹{ipo.max_price or 0:.0f} | Lot: {ipo.lot_size or 'N/A'} | Open: {ipo.open_date} | Close: {ipo.close_date}")

        db.close()

    except Exception as e:
        print(f"[FAIL] Gemini Sync Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
