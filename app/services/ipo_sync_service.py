import time
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.providers.base import BaseIPOProvider, ProviderFetchError
from app.schemas.ingestion import SyncResult, RawIPODTO
from app.repositories.ipo_repository import IPORepository
from app.models import (
    DataSource, SourceType,
    IPO,
    SubscriptionHistory,
    APIRequest,
    WorkflowHealth, HealthStatus
)
from app.core.logging import logger

class IPOSyncService:
    """Service to handle fetching, validating, upserting, and auditing IPO data ingestion."""

    def __init__(self, db: Session):
        self.db = db
        self.ipo_repo = IPORepository(db)

    def _get_or_create_source(self, provider: BaseIPOProvider) -> DataSource:
        source = self.db.scalars(select(DataSource).where(DataSource.code == provider.code)).first()
        if not source:
            source = DataSource(
                code=provider.code,
                name=provider.name,
                source_type=SourceType.OFFICIAL if "UPSTOX" in provider.code else SourceType.MARKET_DATA,
                is_active=True,
                priority=1
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source

    async def sync_provider(self, provider: BaseIPOProvider, status_filter: Optional[str] = None) -> SyncResult:
        start_time = time.time()
        source = self._get_or_create_source(provider)

        ipos_processed = 0
        ipos_created = 0
        ipos_updated = 0
        sub_created = 0
        errors: List[str] = []

        try:
            # 1. Fetch raw data with retry & backoff
            fetch_res = await provider.fetch_with_retry(status=status_filter)
            raw_payload = fetch_res["raw_data"]
            duration_ms = fetch_res["duration_ms"]

            # Log API SLA request
            api_log = APIRequest(
                source_id=source.id,
                endpoint=f"/ipos?status={status_filter or 'all'}",
                http_method="GET",
                status_code=fetch_res["status_code"],
                response_time_ms=duration_ms,
                request_timestamp=datetime.now(timezone.utc)
            )
            self.db.add(api_log)

            # Extract data list from payload
            raw_list = raw_payload.get("data", []) if isinstance(raw_payload, dict) else raw_payload
            if not isinstance(raw_list, list):
                raw_list = [raw_payload]

            # 2. Parse & Validate via Pydantic
            dtos, val_errors = provider.parse_and_validate(raw_list)
            errors.extend(val_errors)
            ipos_processed = len(dtos)

            # 3. Normalize & Upsert into Database
            for dto in dtos:
                try:
                    existing_ipo = self.ipo_repo.get_by_id_or_symbol(dto.symbol)
                    
                    if existing_ipo:
                        # Stale data check & update fields
                        updated = False
                        for field, val in dto.model_dump(exclude={"subscription"}).items():
                            if val is not None and getattr(existing_ipo, field) != val:
                                setattr(existing_ipo, field, val)
                                updated = True
                        
                        if updated:
                            existing_ipo.updated_at = datetime.now(timezone.utc)
                            ipos_updated += 1
                        target_ipo = existing_ipo
                    else:
                        # Insert new IPO
                        ipo_data = dto.model_dump(exclude={"subscription"})
                        ipo_data["primary_source_id"] = source.id
                        target_ipo = IPO(**ipo_data)
                        self.db.add(target_ipo)
                        self.db.flush()
                        ipos_created += 1

                    # 4. Process Subscription Snapshot if present
                    if dto.subscription:
                        sub_data = dto.subscription.model_dump()
                        sub_obs = SubscriptionHistory(
                            ipo_id=target_ipo.id,
                            source_id=source.id,
                            observation_time=datetime.now(timezone.utc),
                            **sub_data
                        )
                        self.db.add(sub_obs)
                        sub_created += 1

                except Exception as ex:
                    err_msg = f"Failed to upsert IPO '{dto.symbol}': {str(ex)}"
                    logger.error(err_msg)
                    errors.append(err_msg)

            self.db.commit()
            sync_status = "SUCCESS" if not errors else ("PARTIAL_SUCCESS" if ipos_processed > 0 else "FAILED")

        except Exception as e:
            self.db.rollback()
            sync_status = "FAILED"
            error_msg = f"Sync failed for provider [{provider.code}]: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        total_duration = int((time.time() - start_time) * 1000)

        # Log Workflow Telemetry
        wf_health = WorkflowHealth(
            workflow_name=f"SYNC_{provider.code}",
            status=HealthStatus.SUCCESS if sync_status in ["SUCCESS", "PARTIAL_SUCCESS"] else HealthStatus.FAILURE,
            metrics={
                "processed": ipos_processed,
                "created": ipos_created,
                "updated": ipos_updated,
                "subscriptions": sub_created,
                "errors_count": len(errors)
            },
            error_log="\n".join(errors) if errors else None,
            last_heartbeat=datetime.now(timezone.utc)
        )
        self.db.add(wf_health)
        self.db.commit()

        return SyncResult(
            provider_code=provider.code,
            status=sync_status,
            ipos_processed=ipos_processed,
            ipos_created=ipos_created,
            ipos_updated=ipos_updated,
            subscription_records_created=sub_created,
            errors=errors,
            duration_ms=total_duration
        )
