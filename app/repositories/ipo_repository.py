import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.ipo import IPO, IPOStatus, IssueType

class IPORepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id_or_symbol(self, identifier: str) -> Optional[IPO]:
        """Fetch IPO by UUID string/object or stock symbol (case-insensitive)."""
        try:
            val_uuid = uuid.UUID(identifier)
            query = select(IPO).where(IPO.id == val_uuid)
            res = self.db.scalars(query).first()
            if res:
                return res
        except ValueError:
            pass

        # Fallback to symbol lookup
        query = select(IPO).where(func.upper(IPO.symbol) == identifier.upper())
        return self.db.scalars(query).first()

    def list_ipos(
        self,
        status: Optional[IPOStatus] = None,
        issue_type: Optional[IssueType] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[IPO], int]:
        """Get paginated list of IPOs with optional filters."""
        query = select(IPO)
        if status:
            query = query.where(IPO.status == status)
        if issue_type:
            query = query.where(IPO.issue_type == issue_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # Offset pagination
        offset = (page - 1) * limit
        query = query.order_by(IPO.created_at.desc()).offset(offset).limit(limit)
        ipos = self.db.scalars(query).all()

        return list(ipos), total

    def list_open(self) -> List[IPO]:
        """Get all currently OPEN IPOs."""
        query = select(IPO).where(IPO.status == IPOStatus.OPEN).order_by(IPO.close_date.asc())
        return list(self.db.scalars(query).all())

    def list_upcoming(self) -> List[IPO]:
        """Get all UPCOMING IPOs."""
        query = select(IPO).where(IPO.status == IPOStatus.UPCOMING).order_by(IPO.open_date.asc())
        return list(self.db.scalars(query).all())
