import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text, select, func

from app.api.deps import get_db
from app.models import IPO, GMPHistory, SubscriptionHistory, Notification, APIRequest, WorkflowHealth
from app.schemas.health import HealthCheckResponse
from app.core.logging import logger

router = APIRouter()
START_TIME = time.time()

@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
def get_health(db: Session = Depends(get_db)):
    """Enhanced production health check returning database status, table row counts, uptime, and stale-data detection."""
    try:
        # DB ping
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Gather table metrics
    ipo_count = db.scalar(select(func.count(IPO.id))) or 0
    gmp_count = db.scalar(select(func.count(GMPHistory.id))) or 0
    sub_count = db.scalar(select(func.count(SubscriptionHistory.id))) or 0
    notif_count = db.scalar(select(func.count(Notification.id))) or 0

    # Stale Data Check: verify if latest GMP observation is older than 24 hours
    latest_gmp = db.scalars(select(GMPHistory).order_by(GMPHistory.observation_time.desc())).first()
    stale_warning = False
    if latest_gmp and latest_gmp.observation_time:
        stale_threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        if latest_gmp.observation_time < stale_threshold:
            stale_warning = True

    uptime_seconds = int(time.time() - START_TIME)

    return HealthCheckResponse(
        status="ok" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        stale_data_warning=stale_warning,
        table_counts={
            "ipos": ipo_count,
            "gmp_history": gmp_count,
            "subscription_history": sub_count,
            "notifications": notif_count
        }
    )
