import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    ipo_id: uuid.UUID
    source_id: uuid.UUID
    source_code: Optional[str] = None
    qib_x: Optional[float] = None
    nii_x: Optional[float] = None
    b_nii_x: Optional[float] = None
    s_nii_x: Optional[float] = None
    retail_x: Optional[float] = None
    employee_x: Optional[float] = None
    overall_x: float
    observation_time: datetime

    model_config = ConfigDict(from_attributes=True)

class SubscriptionHistoryListResponse(BaseModel):
    ipo_id: uuid.UUID
    symbol: str
    count: int
    latest: Optional[SubscriptionResponse] = None
    history: list[SubscriptionResponse]

    model_config = ConfigDict(from_attributes=True)
