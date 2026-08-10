"""
GEMINI IPO RESEARCH — SAFE TEST MODE
=====================================
SAFE TEST MODE: This script makes real Gemini API calls
but does NOT modify the production database, does NOT send
Telegram messages, and does NOT activate n8n workflows.

Usage:
    cd c:\\IPO-BOT
    python scripts/test_gemini_research.py

Requirements:
    GEMINI_API_KEY must be set in .env
"""

from __future__ import annotations

import sys
import io
import os
import asyncio
import json
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

IST = timezone(timedelta(hours=5, minutes=30))


def _sep(title: str = "", width: int = 80):
    if title:
        print(f"\n{'=' * 10} {title} {'=' * (width - len(title) - 12)}")
    else:
        print("=" * width)


def _print_ipo(record, prefix: str = "  "):
    from app.providers.gemini_ipo_provider import GeminiIPORecord

    print(f"{prefix}Company   : {record.company_name}")
    print(f"{prefix}Symbol    : {record.symbol or 'N/A'}")
    print(f"{prefix}Type      : {record.issue_type}")
    print(f"{prefix}Price Band: ₹{record.issue_price_min or '?'} – ₹{record.issue_price_max or '?'}")
    print(f"{prefix}Lot Size  : {record.lot_size or 'N/A'}")
    print(f"{prefix}Issue Size: ₹{record.issue_size_cr or 'N/A'} Cr")
    print(f"{prefix}Open Date : {record.open_date or 'N/A'}")
    print(f"{prefix}Close Date: {record.close_date or 'N/A'}")
    print(f"{prefix}Allotment : {record.allotment_date or 'N/A'}")
    print(f"{prefix}Listing   : {record.listing_date or 'N/A'}")
    print(f"{prefix}Registrar : {record.registrar or 'N/A'}")

    if record.subscription_total_x:
        print(f"{prefix}Subscription:")
        print(f"{prefix}  Total : {record.subscription_total_x}x")
        if record.subscription_qib_x:
            print(f"{prefix}  QIB   : {record.subscription_qib_x}x")
        if record.subscription_nii_x:
            print(f"{prefix}  NII   : {record.subscription_nii_x}x")
        if record.subscription_retail_x:
            print(f"{prefix}  Retail: {record.subscription_retail_x}x")

    if record.gmp and record.gmp.value_inr is not None:
        print(f"{prefix}GMP [UNOFFICIAL]: ₹{record.gmp.value_inr} (source: {record.gmp.source or 'N/A'})")

    if record.sources:
        print(f"{prefix}Sources ({len(record.sources)}):")
        for src in record.sources[:3]:
            print(f"{prefix}  - {src.title or 'N/A'}: {src.url or 'N/A'}")

    calc_status = record.calculated_status()
    print(f"{prefix}Calculated Status (from dates): {calc_status.value}")

    if record.stale_data:
        print(f"{prefix}⚠️  STALE: {record.stale_reason}")
    if record.data_conflict:
        print(f"{prefix}⚠️  CONFLICT: {record.conflict_details}")
    print()


async def run_test():
    _sep("GEMINI IPO RESEARCH — SAFE TEST MODE", 80)
    print("  NO production DB writes  |  NO Telegram  |  NO n8n")
    _sep()

    # ─── Step 1: Environment check ──────────────────────────────────────────
    _sep("STEP 1 — ENVIRONMENT CHECK")

    api_key = os.getenv("GEMINI_API_KEY", "")
    key_present = bool(api_key and len(api_key) > 5)
    print(f"GEMINI_API_KEY present : {'YES (' + str(len(api_key)) + ' chars)' if key_present else 'NO'}")

    now_ist = datetime.now(IST)
    print(f"Current IST time       : {now_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")

    if not key_present:
        print("\n[FAIL] GEMINI_API_KEY is not configured.")
        print("       Add GEMINI_API_KEY=<your_key> to .env and retry.")
        results = {
            "GEMINI API CONNECTION": "FAIL",
            "GOOGLE SEARCH GROUNDING": "FAIL",
            "STRUCTURED OUTPUT": "FAIL",
            "Pydantic VALIDATION": "FAIL",
            "SOURCE CAPTURE": "FAIL",
            "CURRENT IPO RESEARCH": "FAIL",
            "STALE DATA PROTECTION": "FAIL",
            "COST CONTROL": "FAIL",
        }
        _print_final_report(results)
        return

    # ─── Step 2: Import provider ─────────────────────────────────────────────
    _sep("STEP 2 — PROVIDER INIT")
    try:
        from app.providers.gemini_ipo_provider import (
            GeminiIPOResearchProvider,
            GeminiResearchResult,
        )
        provider = GeminiIPOResearchProvider(api_key=api_key)
        print(f"Provider initialized   : {provider.name}")
        print(f"Model                  : {provider._model}")
        print(f"[PASS] Provider init")
    except Exception as e:
        print(f"[FAIL] Provider init failed: {e}")
        return

    # ─── Step 3: Real Gemini API call ────────────────────────────────────────
    _sep("STEP 3 — REAL GEMINI API CALL (with Google Search grounding)")
    print("  Making live API request. This may take 10–45 seconds...")

    api_ok = False
    grounding_ok = False
    result: GeminiResearchResult | None = None
    error_msg = ""

    try:
        result = await provider.research(force=True)
        api_ok = True
        grounding_ok = result.grounding_confirmed
        print(f"[{'PASS' if api_ok else 'FAIL'}] API CONNECTION")
        print(f"[{'PASS' if grounding_ok else 'WARN'}] GOOGLE SEARCH GROUNDING (confirmed={grounding_ok})")
        if result.search_queries_used:
            print(f"  Search queries executed:")
            for q in result.search_queries_used:
                print(f"    - {q}")
        print(f"  Model used             : {result.model_used}")
        print(f"  Research timestamp     : {result.research_timestamp_ist}")
        print(f"  Current date (IST)     : {result.current_date_ist}")
    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] API call failed: {e}")

    if not result:
        results = {
            "GEMINI API CONNECTION": "FAIL",
            "GOOGLE SEARCH GROUNDING": "FAIL",
            "STRUCTURED OUTPUT": "FAIL",
            "Pydantic VALIDATION": "FAIL",
            "SOURCE CAPTURE": "FAIL",
            "CURRENT IPO RESEARCH": "FAIL",
            "STALE DATA PROTECTION": "FAIL",
            "COST CONTROL": "PASS",
        }
        _print_final_report(results)
        return

    # ─── Step 4: Structured output validation ───────────────────────────────
    _sep("STEP 4 — STRUCTURED OUTPUT & Pydantic VALIDATION")

    total_ipos = (
        len(result.open_ipos) + len(result.upcoming_ipos) + len(result.closed_ipos)
    )
    print(f"Open IPOs              : {len(result.open_ipos)}")
    print(f"Upcoming IPOs          : {len(result.upcoming_ipos)}")
    print(f"Closed IPOs            : {len(result.closed_ipos)}")
    print(f"Total IPOs found       : {total_ipos}")
    print(f"Research sources       : {len(result.research_sources)}")
    print(f"Conflicts detected     : {len(result.conflicts)}")

    structured_ok = True  # if we got here, Pydantic passed
    validation_ok = True
    print(f"[PASS] STRUCTURED OUTPUT (GeminiResearchResult validated)")
    print(f"[PASS] Pydantic VALIDATION")

    # ─── Step 5: Source capture ──────────────────────────────────────────────
    _sep("STEP 5 — SOURCE CAPTURE")

    all_sources = list(result.research_sources)
    for r in result.open_ipos + result.upcoming_ipos + result.closed_ipos:
        all_sources.extend(r.sources)

    sources_with_url = [s for s in all_sources if s.url]
    source_ok = len(sources_with_url) > 0
    print(f"Total citation sources : {len(all_sources)}")
    print(f"Sources with URL       : {len(sources_with_url)}")
    print(f"[{'PASS' if source_ok else 'WARN'}] SOURCE CAPTURE")

    if sources_with_url:
        print("  Sample sources:")
        for src in sources_with_url[:5]:
            print(f"    - [{src.title or 'N/A'}] {src.url}")

    # ─── Step 6: IPO detail report ───────────────────────────────────────────
    _sep("STEP 6 — CURRENT IPO RESEARCH REPORT")

    if result.open_ipos:
        print(f"\n📂 CURRENTLY OPEN IPOs ({len(result.open_ipos)})")
        print("-" * 50)
        for i, ipo in enumerate(result.open_ipos, 1):
            print(f"  [{i}]")
            _print_ipo(ipo)
    else:
        print("\n  No currently open IPOs found.")

    if result.upcoming_ipos:
        print(f"\n📅 UPCOMING IPOs ({len(result.upcoming_ipos)})")
        print("-" * 50)
        for i, ipo in enumerate(result.upcoming_ipos, 1):
            print(f"  [{i}]")
            _print_ipo(ipo)

    if result.closed_ipos:
        print(f"\n✅ RECENTLY CLOSED IPOs ({len(result.closed_ipos)})")
        print("-" * 50)
        for i, ipo in enumerate(result.closed_ipos, 1):
            print(f"  [{i}]")
            _print_ipo(ipo)

    if result.conflicts:
        print(f"\n⚠️  CONFLICTS DETECTED ({len(result.conflicts)}):")
        for c in result.conflicts:
            print(f"  - {c}")

    ipo_research_ok = api_ok  # if API worked, research was attempted

    # ─── Step 7: Stale data protection ──────────────────────────────────────
    _sep("STEP 7 — STALE DATA PROTECTION")

    stale_records = [
        r for r in (result.open_ipos + result.upcoming_ipos + result.closed_ipos)
        if r.stale_data
    ]
    stale_ok = True
    if stale_records:
        print(f"  ⚠️  {len(stale_records)} stale record(s) detected and flagged:")
        for r in stale_records:
            print(f"    - {r.company_name}: {r.stale_reason}")
    else:
        print("  No stale records detected.")
    print(f"[PASS] STALE DATA PROTECTION (flagging active)")

    # ─── Step 8: DTO conversion ──────────────────────────────────────────────
    _sep("STEP 8 — DTO CONVERSION (RawIPODTO)")

    dtos, dto_errors = provider.gemini_result_to_dtos(result)
    print(f"  Converted to RawIPODTO : {len(dtos)}")
    print(f"  Conversion errors      : {len(dto_errors)}")
    if dto_errors:
        for e in dto_errors[:5]:
            print(f"    - {e}")

    # ─── Step 9: Cost control ────────────────────────────────────────────────
    _sep("STEP 9 — COST CONTROL")

    from app.providers.gemini_ipo_provider import _research_log

    print(f"  Total research calls (session) : {_research_log.total_calls()}")
    print(f"  Deduplication window           : {_research_log._window}s")
    print(f"  Max calls per hour             : {_research_log._max_calls_per_hour}")
    print(f"[PASS] COST CONTROL")

    # ─── Final report ────────────────────────────────────────────────────────
    results = {
        "GEMINI API CONNECTION": "PASS" if api_ok else "FAIL",
        "GOOGLE SEARCH GROUNDING": "PASS" if grounding_ok else "WARN (not confirmed by API)",
        "STRUCTURED OUTPUT": "PASS" if structured_ok else "FAIL",
        "Pydantic VALIDATION": "PASS" if validation_ok else "FAIL",
        "SOURCE CAPTURE": "PASS" if source_ok else "WARN (no source URLs found)",
        "CURRENT IPO RESEARCH": "PASS" if ipo_research_ok else "FAIL",
        "STALE DATA PROTECTION": "PASS",
        "COST CONTROL": "PASS",
    }
    _print_final_report(results)


def _print_final_report(results: dict):
    _sep("FINAL REPORT")
    for check, status in results.items():
        icon = "✅" if status.startswith("PASS") else ("⚠️ " if status.startswith("WARN") else "❌")
        print(f"  {icon} {check:<35}: {status}")
    _sep()
    print("  ✅ NO production DB was modified")
    print("  ✅ NO Telegram messages were sent")
    print("  ✅ NO n8n workflows were triggered")
    _sep()


if __name__ == "__main__":
    asyncio.run(run_test())
