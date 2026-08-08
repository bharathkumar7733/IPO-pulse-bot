from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlalchemy import String, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base, UTCDateTime

if TYPE_CHECKING:
    from app.models.data_source import DataSource

class APIRequest(Base):
    """
    Log of API requests made to external data sources for reliability and rate limit monitoring.
    """
    __tablename__ = "api_requests"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), default="GET", nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    request_timestamp: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    source: Mapped["DataSource"] = relationship("DataSource", back_populates="api_requests")

    __table_args__ = (
        Index("idx_api_req_source_status", "source_id", "status_code"),
        Index("idx_api_req_timestamp", request_timestamp.desc()),
    )
