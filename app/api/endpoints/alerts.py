from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.alert_service import SmartAlertService

router = APIRouter()

@router.post("/alerts/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_smart_alerts(
    chat_id: str = Query("123456789", description="Target Telegram chat_id or admin channel"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Triggers programmatic evaluation of all smart alert triggers across active IPOs 
    (GMP surge, GMP drop, trend reversal, dates, subscription milestones) 
    with automatic idempotency deduplication.
    """
    alert_service = SmartAlertService(db)
    return await alert_service.evaluate_and_dispatch(target_chat_id=chat_id)
