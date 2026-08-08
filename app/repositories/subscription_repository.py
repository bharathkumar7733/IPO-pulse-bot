import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.subscription_history import SubscriptionHistory

class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_subscription(self, ipo_id: uuid.UUID) -> Optional[SubscriptionHistory]:
        """Fetch latest subscription observation record for an IPO."""
        query = (
            select(SubscriptionHistory)
            .options(joinedload(SubscriptionHistory.source))
            .where(SubscriptionHistory.ipo_id == ipo_id)
            .order_by(SubscriptionHistory.observation_time.desc())
            .limit(1)
        )
        return self.db.scalars(query).first()

    def get_subscription_history(self, ipo_id: uuid.UUID, limit: int = 50) -> List[SubscriptionHistory]:
        """Fetch historical subscription observation records for an IPO."""
        query = (
            select(SubscriptionHistory)
            .options(joinedload(SubscriptionHistory.source))
            .where(SubscriptionHistory.ipo_id == ipo_id)
            .order_by(SubscriptionHistory.observation_time.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())
