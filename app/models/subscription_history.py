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

class SubscriptionHistory(Base):
    """
    Append-only historical subscription observation records (category-wise x-times).
    Allows storing observations from multiple data providers over time.
    """
    __tablename__ = "subscription_history"

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

    qib_x: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    nii_x: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    b_nii_x: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    s_nii_x: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    retail_x: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    employee_x: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    overall_x: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    observation_time: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    ipo: Mapped["IPO"] = relationship("IPO", back_populates="subscription_history")
    source: Mapped["DataSource"] = relationship("DataSource", back_populates="subscription_records")

    __table_args__ = (
        Index("idx_sub_ipo_time", "ipo_id", observation_time.desc()),
        Index("idx_sub_source_time", "source_id", observation_time.desc()),
        UniqueConstraint("ipo_id", "source_id", "observation_time", name="uq_sub_ipo_source_obs_time"),
    )
