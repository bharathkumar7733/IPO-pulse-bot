from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.ipo_service import IPOService
from app.services.gmp_service import GMPService
from app.services.ai_service import AIService, AIAnalysisResponse
from app.schemas.ipo import IPOResponse, IPOListResponse, IPOSummaryResponse
from app.schemas.gmp import GMPResponse, GMPHistoryListResponse, GMPAnalysisResponse
from app.schemas.subscription import SubscriptionHistoryListResponse
from app.models.ipo import IPOStatus, IssueType

router = APIRouter()

@router.get("/ipos", response_model=IPOListResponse, status_code=status.HTTP_200_OK)
def get_ipos(
    ipo_status: Optional[IPOStatus] = Query(None, alias="status", description="Filter by IPO status"),
    issue_type: Optional[IssueType] = Query(None, description="Filter by issue type (MAINBOARD or SME)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Retrieve a paginated list of IPOs with optional filtering by status and issue type."""
    service = IPOService(db)
    return service.list_ipos(status=ipo_status, issue_type=issue_type, page=page, limit=limit)

@router.get("/ipos/open", response_model=List[IPOResponse], status_code=status.HTTP_200_OK)
def get_open_ipos(db: Session = Depends(get_db)):
    """Retrieve all currently OPEN IPOs."""
    service = IPOService(db)
    return service.list_open_ipos()

@router.get("/ipos/upcoming", response_model=List[IPOResponse], status_code=status.HTTP_200_OK)
def get_upcoming_ipos(db: Session = Depends(get_db)):
    """Retrieve all UPCOMING IPOs."""
    service = IPOService(db)
    return service.list_upcoming_ipos()

@router.get("/ipos/{ipo_id}", response_model=IPOResponse, status_code=status.HTTP_200_OK)
def get_ipo_detail(ipo_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed information for a specific IPO by UUID or Stock Symbol."""
    service = IPOService(db)
    return service.get_ipo_detail(ipo_id)

@router.get("/ipos/{ipo_id}/gmp", response_model=GMPResponse, status_code=status.HTTP_200_OK)
def get_latest_gmp(ipo_id: str, db: Session = Depends(get_db)):
    """Retrieve the latest Grey Market Premium (GMP) snapshot for a specific IPO."""
    service = IPOService(db)
    return service.get_gmp_latest(ipo_id)

@router.get("/ipos/{ipo_id}/gmp/analysis", response_model=GMPAnalysisResponse, status_code=status.HTTP_200_OK)
def get_gmp_analysis(ipo_id: str, db: Session = Depends(get_db)):
    """Retrieve GMP trend analysis including deltas, 24h change, and trend state."""
    service = GMPService(db)
    return service.analyze_gmp(ipo_id)

@router.get("/ipos/{ipo_id}/analysis", response_model=AIAnalysisResponse, status_code=status.HTTP_200_OK)
def get_ai_analysis(ipo_id: str, db: Session = Depends(get_db)):
    """Retrieve grounded AI analysis including positive signals, risk factors, and overall synthesis without number fabrication."""
    ai_service = AIService(db)
    return ai_service.generate_analysis(ipo_id)

@router.get("/ipos/{ipo_id}/gmp/history", response_model=GMPHistoryListResponse, status_code=status.HTTP_200_OK)
def get_gmp_history(
    ipo_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum historical records to return"),
    db: Session = Depends(get_db)
):
    """Retrieve historical append-only time-series of GMP observations for an IPO."""
    service = IPOService(db)
    return service.get_gmp_history(ipo_id, limit=limit)

@router.get("/ipos/{ipo_id}/subscription", response_model=SubscriptionHistoryListResponse, status_code=status.HTTP_200_OK)
def get_subscription_history(
    ipo_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum historical records to return"),
    db: Session = Depends(get_db)
):
    """Retrieve category-wise live & historical subscription data for an IPO."""
    service = IPOService(db)
    return service.get_subscription_history(ipo_id, limit=limit)

@router.get("/ipos/{ipo_id}/summary", response_model=IPOSummaryResponse, status_code=status.HTTP_200_OK)
def get_ipo_summary(ipo_id: str, db: Session = Depends(get_db)):
    """Retrieve consolidated summary including master details, latest GMP, and subscription rates."""
    service = IPOService(db)
    return service.get_ipo_summary(ipo_id)
