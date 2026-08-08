import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.ipo import IssueType, IPOStatus
from app.schemas.gmp import GMPResponse
from app.schemas.subscription import SubscriptionResponse

class IPOResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    bse_code: Optional[str] = None
    company_name: str
    issue_type: IssueType
    status: IPOStatus
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    issue_price: Optional[float] = None
    lot_size: Optional[int] = None
    total_issue_size_cr: Optional[float] = None
    fresh_issue_cr: Optional[float] = None
    offer_for_sale_cr: Optional[float] = None
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    allotment_date: Optional[date] = None
    listing_date: Optional[date] = None
    registrar_name: Optional[str] = None
    registrar_url: Optional[str] = None
    rhp_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IPOListResponse(BaseModel):
    total: int
    page: int
    limit: int
    ipos: List[IPOResponse]

    model_config = ConfigDict(from_attributes=True)

class IPOSummaryResponse(BaseModel):
    ipo: IPOResponse
    latest_gmp: Optional[GMPResponse] = None
    latest_subscription: Optional[SubscriptionResponse] = None
    estimated_return_percent: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
