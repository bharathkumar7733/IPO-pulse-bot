import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid
from sqlalchemy import String, Text, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base, UTCDateTime

if TYPE_CHECKING:
    from app.models.ipo import IPO
    from app.models.data_source import DataSource

class NotificationType(str, enum.Enum):
    GMP_SURGE = "GMP_SURGE"                  # GMP increased by >= +10
    GMP_DROP = "GMP_DROP"                    # GMP decreased by <= -10
    GMP_TREND_REVERSAL = "GMP_TREND_REVERSAL"# Trend reversed (e.g. FALLING -> RISING)
    IPO_OPENED = "IPO_OPENED"                # Bidding opened today
    IPO_CLOSING_SOON = "IPO_CLOSING_SOON"    # Bidding closes today
    IPO_LISTING_TOMORROW = "IPO_LISTING_TOMORROW" # Listing tomorrow
    SUBSCRIPTION_MILESTONE = "SUBSCRIPTION_MILESTONE" # Crossed 1x, 5x, 10x, 25x, 50x, 100x
    STALE_DATA_ALERT = "STALE_DATA_ALERT"    # Data source hasn't updated in 24h
    API_FAILURE_ALERT = "API_FAILURE_ALERT"  # API provider failure
    GMP_SPIKE = "GMP_SPIKE"
    SUBSCRIPTION_HIGH = "SUBSCRIPTION_HIGH"
    ALLOTMENT_OUT = "ALLOTMENT_OUT"
    DAILY_DIGEST = "DAILY_DIGEST"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class Notification(Base):
    __tablename__ = "notifications"

    ipo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ipos.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    telegram_chat_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False, name="notification_type_enum"),
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, native_enum=False, name="notification_status_enum"),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    ipo: Mapped[Optional["IPO"]] = relationship("IPO", back_populates="notifications")

    __table_args__ = (
        Index("idx_notif_status_type", "status", "notification_type"),
        Index("idx_notif_chat_created", "telegram_chat_id", "created_at"),
    )
