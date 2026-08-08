import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class GMPTrend(str, Enum):
    RISING = "RISING"
    FALLING = "FALLING"
    STABLE = "STABLE"
    UNKNOWN = "UNKNOWN"

class RawGMPDTO(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    company_name: Optional[str] = None
    gmp_price: float = Field(..., ge=0.0)
    gmp_percent: Optional[float] = None
    estimated_listing_price: Optional[float] = None
    subject_to_sauda: Optional[float] = None
    observation_time: Optional[datetime] = None

    model_config = ConfigDict(extra="ignore")

class GMPResponse(BaseModel):
    id: uuid.UUID
    ipo_id: uuid.UUID
    source_id: uuid.UUID
    source_code: Optional[str] = None
    gmp_price: float
    gmp_percent: Optional[float] = None
    estimated_listing_price: Optional[float] = None
    subject_to_sauda: Optional[float] = None
    observation_time: datetime

    model_config = ConfigDict(from_attributes=True)

class GMPHistoryListResponse(BaseModel):
    ipo_id: uuid.UUID
    symbol: str
    count: int
    history: List[GMPResponse]

    model_config = ConfigDict(from_attributes=True)

class GMPAnalysisResponse(BaseModel):
    ipo_id: uuid.UUID
    symbol: str
    company_name: str
    current_gmp: Optional[float] = None
    gmp_percent: Optional[float] = None
    previous_gmp: Optional[float] = None
    absolute_change: Optional[float] = None
    percentage_change: Optional[float] = None
    twenty_four_hour_change: Optional[float] = None
    trend: GMPTrend = GMPTrend.UNKNOWN
    latest_observation_time: Optional[datetime] = None
    source_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
