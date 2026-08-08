from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid
from sqlalchemy import Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base, UTCDateTime

if TYPE_CHECKING:
    from app.models.ipo import IPO
    from app.models.data_source import DataSource

class GMPHistory(Base):
    """
    Append-only historical Grey Market Premium (GMP) observations.
    CRITICAL REQUIREMENT: Records in this table are immutable time-series observations 
    and must NEVER be overwritten or updated.
    """
    __tablename__ = "gmp_history"

    ipo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ipos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    gmp_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    gmp_percent: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_listing_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    subject_to_sauda: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    observation_time: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationships
    ipo: Mapped["IPO"] = relationship("IPO", back_populates="gmp_history")
    source: Mapped["DataSource"] = relationship("DataSource", back_populates="gmp_records")

    __table_args__ = (
        Index("idx_gmp_ipo_time", "ipo_id", observation_time.desc()),
        Index("idx_gmp_source_time", "source_id", observation_time.desc()),
        UniqueConstraint("ipo_id", "source_id", "observation_time", name="uq_gmp_ipo_source_obs_time"),
    )
