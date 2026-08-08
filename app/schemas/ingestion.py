from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.ipo import IssueType, IPOStatus

class RawSubscriptionDTO(BaseModel):
    qib_x: Optional[float] = None
    nii_x: Optional[float] = None
    b_nii_x: Optional[float] = None
    s_nii_x: Optional[float] = None
    retail_x: Optional[float] = None
    employee_x: Optional[float] = None
    overall_x: float = Field(default=0.0, ge=0.0)

    model_config = ConfigDict(extra="ignore")

class RawIPODTO(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    company_name: str = Field(..., min_length=1, max_length=255)
    bse_code: Optional[str] = None
    issue_type: IssueType = Field(default=IssueType.MAINBOARD)
    status: IPOStatus = Field(default=IPOStatus.UPCOMING)
    min_price: Optional[float] = Field(default=None, ge=0.0)
    max_price: Optional[float] = Field(default=None, ge=0.0)
    issue_price: Optional[float] = Field(default=None, ge=0.0)
    lot_size: Optional[int] = Field(default=None, ge=1)
    total_issue_size_cr: Optional[float] = Field(default=None, ge=0.0)
    fresh_issue_cr: Optional[float] = Field(default=None, ge=0.0)
    offer_for_sale_cr: Optional[float] = Field(default=None, ge=0.0)
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    allotment_date: Optional[date] = None
    listing_date: Optional[date] = None
    registrar_name: Optional[str] = None
    registrar_url: Optional[str] = None
    rhp_url: Optional[str] = None
    subscription: Optional[RawSubscriptionDTO] = None

    model_config = ConfigDict(extra="ignore")

class SyncResult(BaseModel):
    provider_code: str
    status: str
    ipos_processed: int
    ipos_created: int
    ipos_updated: int
    subscription_records_created: int
    errors: List[str] = Field(default_factory=list)
    duration_ms: int

    model_config = ConfigDict(from_attributes=True)
