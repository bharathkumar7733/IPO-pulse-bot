from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ingestion import SyncResult
from app.services.ipo_sync_service import IPOSyncService
from app.services.gmp_service import GMPService
from app.providers.gemini_ipo_provider import GeminiIPOResearchProvider
from app.providers.ipo_notify_provider import IPONotifyProvider
from app.providers.upstox_provider import UpstoxIPOProvider
from app.providers.mock_provider import MockIPOProvider
from app.providers.gmp_provider import ApifyGMPProvider, MockGMPProvider

router = APIRouter()

@router.post("/ingest/ipos", response_model=SyncResult, status_code=status.HTTP_200_OK)
async def trigger_ipo_ingestion(
    provider_code: str = Query("GEMINI_IPO", description="Provider code to sync (GEMINI_IPO, IPO_NOTIFY, UPSTOX_API, or MOCK_PROVIDER)"),
    ipo_status: Optional[str] = Query(None, alias="status", description="Status filter (e.g. open, upcoming)"),
    db: Session = Depends(get_db)
):
    """
    Safely triggers programmatic synchronization of IPO master and subscription data 
    from the specified provider into PostgreSQL/SQLite.
    """
    p_code = provider_code.upper()
    if p_code == "GEMINI_IPO":
        provider = GeminiIPOResearchProvider()
    elif p_code == "IPO_NOTIFY":
        provider = IPONotifyProvider()
    elif p_code == "MOCK_PROVIDER":
        provider = MockIPOProvider()
    else:
        provider = UpstoxIPOProvider()

    sync_service = IPOSyncService(db)
    return await sync_service.sync_provider(provider=provider, status_filter=ipo_status)

@router.post("/ingest/gmp", response_model=SyncResult, status_code=status.HTTP_200_OK)
async def trigger_gmp_ingestion(
    provider_code: str = Query("APIFY_GMP", description="GMP Provider code to sync (APIFY_GMP or MOCK_GMP)"),
    db: Session = Depends(get_db)
):
    """
    Safely triggers programmatic synchronization of Grey Market Premium (GMP) data 
    into append-only time-series PostgreSQL records.
    """
    if provider_code.upper() == "MOCK_GMP":
        provider = MockGMPProvider()
    else:
        provider = ApifyGMPProvider()

    gmp_service = GMPService(db)
    return await gmp_service.sync_gmp(provider=provider)
