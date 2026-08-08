import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Enum, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base_class import Base, UTCDateTime

class HealthStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"

class WorkflowHealth(Base):
    """
    Health check and execution telemetry log for n8n workflows and scheduled automation jobs.
    """
    __tablename__ = "workflow_health"

    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    n8n_execution_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, native_enum=True, name="health_status_enum"),
        default=HealthStatus.SUCCESS,
        nullable=False,
        index=True
    )
    
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    last_heartbeat: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("idx_wf_name_status", "workflow_name", "status"),
        Index("idx_wf_heartbeat", last_heartbeat.desc()),
    )
