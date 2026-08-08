from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    version: str
    uptime_seconds: Optional[int] = None
    stale_data_warning: Optional[bool] = False
    table_counts: Optional[Dict[str, int]] = None
