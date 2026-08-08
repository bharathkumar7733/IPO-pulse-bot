import enum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base_class import Base

if TYPE_CHECKING:
    from app.models.ipo import IPO
    from app.models.gmp_history import GMPHistory
    from app.models.subscription_history import SubscriptionHistory
    from app.models.api_request import APIRequest

class SourceType(str, enum.Enum):
    OFFICIAL = "OFFICIAL"
    MARKET_DATA = "MARKET_DATA"
    UNOFFICIAL_GMP = "UNOFFICIAL_GMP"
    REGISTRAR = "REGISTRAR"

class DataSource(Base):
    __tablename__ = "data_sources"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=True, name="source_type_enum"),
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    config_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relationships
    primary_ipos: Mapped[List["IPO"]] = relationship("IPO", back_populates="primary_source")
    gmp_records: Mapped[List["GMPHistory"]] = relationship("GMPHistory", back_populates="source")
    subscription_records: Mapped[List["SubscriptionHistory"]] = relationship("SubscriptionHistory", back_populates="source")
    api_requests: Mapped[List["APIRequest"]] = relationship("APIRequest", back_populates="source")
