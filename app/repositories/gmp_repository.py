import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.gmp_history import GMPHistory

class GMPRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_gmp(self, ipo_id: uuid.UUID) -> Optional[GMPHistory]:
        """Fetch latest GMP observation record for an IPO."""
        query = (
            select(GMPHistory)
            .options(joinedload(GMPHistory.source))
            .where(GMPHistory.ipo_id == ipo_id)
            .order_by(GMPHistory.observation_time.desc())
            .limit(1)
        )
        return self.db.scalars(query).first()

    def get_gmp_history(self, ipo_id: uuid.UUID, limit: int = 50) -> List[GMPHistory]:
        """Fetch historical append-only time-series of GMP records for an IPO."""
        query = (
            select(GMPHistory)
            .options(joinedload(GMPHistory.source))
            .where(GMPHistory.ipo_id == ipo_id)
            .order_by(GMPHistory.observation_time.desc())
            .limit(limit)
        )
        return list(self.db.scalars(query).all())
