import enum
from datetime import date
from typing import List, Optional, TYPE_CHECKING
import uuid
from sqlalchemy import String, Integer, Numeric, Date, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

if TYPE_CHECKING:
    from app.models.data_source import DataSource
    from app.models.gmp_history import GMPHistory
    from app.models.subscription_history import SubscriptionHistory
    from app.models.notification import Notification

class IssueType(str, enum.Enum):
    MAINBOARD = "MAINBOARD"
    SME = "SME"

class IPOStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ALLOTTED = "ALLOTTED"
    LISTED = "LISTED"
    WITHDRAWN = "WITHDRAWN"

class IPO(Base):
    __tablename__ = "ipos"

    symbol: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    bse_code: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_type: Mapped[IssueType] = mapped_column(
        Enum(IssueType, native_enum=True, name="issue_type_enum"),
        default=IssueType.MAINBOARD,
        nullable=False,
        index=True
    )
    status: Mapped[IPOStatus] = mapped_column(
        Enum(IPOStatus, native_enum=True, name="ipo_status_enum"),
        default=IPOStatus.UPCOMING,
        nullable=False,
        index=True
    )
    
    min_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    issue_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    lot_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    total_issue_size_cr: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    fresh_issue_cr: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    offer_for_sale_cr: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    open_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    allotment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    listing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    
    registrar_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    registrar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rhp_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    primary_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    primary_source: Mapped[Optional["DataSource"]] = relationship("DataSource", back_populates="primary_ipos")
    gmp_history: Mapped[List["GMPHistory"]] = relationship("GMPHistory", back_populates="ipo", cascade="all, delete-orphan")
    subscription_history: Mapped[List["SubscriptionHistory"]] = relationship("SubscriptionHistory", back_populates="ipo", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="ipo", cascade="all, delete-orphan")
