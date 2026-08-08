import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.providers.gmp_provider import BaseGMPProvider
from app.schemas.ingestion import SyncResult
from app.schemas.gmp import GMPAnalysisResponse, GMPTrend
from app.repositories.ipo_repository import IPORepository
from app.repositories.gmp_repository import GMPRepository
from app.models import (
    DataSource, SourceType,
    IPO,
    GMPHistory,
    APIRequest,
    WorkflowHealth, HealthStatus
)
from app.core.exceptions import IPONotFoundException
from app.core.logging import logger

class GMPService:
    """Service to handle fetching, validating, persisting, and analyzing Grey Market Premium (GMP) time-series."""

    def __init__(self, db: Session):
        self.db = db
        self.ipo_repo = IPORepository(db)
        self.gmp_repo = GMPRepository(db)

    def _get_or_create_source(self, provider: BaseGMPProvider) -> DataSource:
        source = self.db.scalars(select(DataSource).where(DataSource.code == provider.code)).first()
        if not source:
            source = DataSource(
                code=provider.code,
                name=provider.name,
                source_type=SourceType.UNOFFICIAL_GMP,
                is_active=True,
                priority=1
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source

    async def sync_gmp(self, provider: BaseGMPProvider) -> SyncResult:
        """Fetches, validates, and stores append-only GMP observations."""
        start_time = time.time()
        source = self._get_or_create_source(provider)

        gmp_processed = 0
        gmp_created = 0
        errors: List[str] = []

        try:
            fetch_res = await provider.fetch_with_retry()
            raw_payload = fetch_res["raw_data"]
            duration_ms = fetch_res["duration_ms"]

            # Log SLA metrics
            api_log = APIRequest(
                source_id=source.id,
                endpoint="/gmp",
                http_method="GET",
                status_code=fetch_res["status_code"],
                response_time_ms=duration_ms,
                request_timestamp=datetime.now(timezone.utc)
            )
            self.db.add(api_log)

            raw_list = raw_payload.get("data", []) if isinstance(raw_payload, dict) else raw_payload
            if not isinstance(raw_list, list):
                raw_list = [raw_payload]

            dtos, val_errors = provider.parse_and_validate_gmp(raw_list)
            errors.extend(val_errors)
            gmp_processed = len(dtos)

            obs_time_now = datetime.now(timezone.utc)

            for dto in dtos:
                try:
                    target_ipo = self.ipo_repo.get_by_id_or_symbol(dto.symbol)
                    if not target_ipo:
                        # Auto-create stub IPO if not found to prevent dropping GMP data
                        target_ipo = IPO(
                            symbol=dto.symbol,
                            company_name=dto.company_name or f"{dto.symbol} Limited",
                            primary_source_id=source.id
                        )
                        self.db.add(target_ipo)
                        self.db.flush()

                    obs_time = dto.observation_time or obs_time_now

                    # Duplicate Check:
                    # 1. Exact observation_time match, OR
                    # 2. Latest observation for same IPO & source has identical gmp_price within last 15 minutes
                    existing_obs = None
                    if dto.observation_time:
                        existing_obs = self.db.scalars(
                            select(GMPHistory).where(
                                GMPHistory.ipo_id == target_ipo.id,
                                GMPHistory.source_id == source.id,
                                GMPHistory.observation_time == obs_time
                            )
                        ).first()
                    else:
                        latest_obs = self.gmp_repo.get_latest_gmp(target_ipo.id)
                        if latest_obs and latest_obs.source_id == source.id:
                            time_diff = abs((obs_time - latest_obs.observation_time).total_seconds())
                            if float(latest_obs.gmp_price) == dto.gmp_price and time_diff < 900:  # 15 mins
                                existing_obs = latest_obs

                    if existing_obs:
                        logger.info(f"Duplicate GMP observation for '{dto.symbol}' skipped.")
                        continue

                    gmp_record = GMPHistory(
                        ipo_id=target_ipo.id,
                        source_id=source.id,
                        gmp_price=dto.gmp_price,
                        gmp_percent=dto.gmp_percent,
                        estimated_listing_price=dto.estimated_listing_price,
                        subject_to_sauda=dto.subject_to_sauda,
                        observation_time=obs_time
                    )
                    self.db.add(gmp_record)
                    gmp_created += 1

                except Exception as ex:
                    err_msg = f"Failed to persist GMP for '{dto.symbol}': {str(ex)}"
                    logger.error(err_msg)
                    errors.append(err_msg)

            self.db.commit()
            sync_status = "SUCCESS" if not errors else ("PARTIAL_SUCCESS" if gmp_created > 0 else "FAILED")

        except Exception as e:
            self.db.rollback()
            sync_status = "FAILED"
            error_msg = f"GMP Sync failed for provider [{provider.code}]: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        total_duration = int((time.time() - start_time) * 1000)

        # Log Workflow Telemetry
        wf_health = WorkflowHealth(
            workflow_name=f"SYNC_GMP_{provider.code}",
            status=HealthStatus.SUCCESS if sync_status in ["SUCCESS", "PARTIAL_SUCCESS"] else HealthStatus.FAILURE,
            metrics={"processed": gmp_processed, "gmp_created": gmp_created, "errors_count": len(errors)},
            error_log="\n".join(errors) if errors else None,
            last_heartbeat=datetime.now(timezone.utc)
        )
        self.db.add(wf_health)
        self.db.commit()

        return SyncResult(
            provider_code=provider.code,
            status=sync_status,
            ipos_processed=gmp_processed,
            ipos_created=0,
            ipos_updated=0,
            subscription_records_created=gmp_created,
            errors=errors,
            duration_ms=total_duration
        )

    def analyze_gmp(self, identifier: str) -> GMPAnalysisResponse:
        """Calculates current, previous, absolute change, percentage change, 24h change, and trend state."""
        ipo = self.ipo_repo.get_by_id_or_symbol(identifier)
        if not ipo:
            raise IPONotFoundException(identifier)

        records = self.gmp_repo.get_gmp_history(ipo.id, limit=100)
        if not records:
            return GMPAnalysisResponse(
                ipo_id=ipo.id,
                symbol=ipo.symbol,
                company_name=ipo.company_name,
                trend=GMPTrend.UNKNOWN
            )

        latest = records[0]
        curr_price = float(latest.gmp_price)
        gmp_pct = float(latest.gmp_percent) if latest.gmp_percent is not None else None

        prev_price = None
        abs_change = None
        pct_change = None
        trend = GMPTrend.UNKNOWN

        if len(records) > 1:
            previous = records[1]
            prev_price = float(previous.gmp_price)
            abs_change = round(curr_price - prev_price, 2)
            
            if prev_price > 0:
                pct_change = round((abs_change / prev_price) * 100, 2)

            if abs_change > 0:
                trend = GMPTrend.RISING
            elif abs_change < 0:
                trend = GMPTrend.FALLING
            else:
                trend = GMPTrend.STABLE

        # Calculate 24-hour change relative to current observation time
        h24_change = None
        target_24h_time = latest.observation_time - timedelta(hours=24)
        
        best_candidate = None
        min_diff = timedelta(days=365)
        for r in records[1:]:
            diff = abs(r.observation_time - target_24h_time)
            if diff < min_diff:
                min_diff = diff
                best_candidate = r

        if best_candidate and best_candidate.id != latest.id:
            h24_change = round(curr_price - float(best_candidate.gmp_price), 2)

        return GMPAnalysisResponse(
            ipo_id=ipo.id,
            symbol=ipo.symbol,
            company_name=ipo.company_name,
            current_gmp=curr_price,
            gmp_percent=gmp_pct,
            previous_gmp=prev_price,
            absolute_change=abs_change,
            percentage_change=pct_change,
            twenty_four_hour_change=h24_change,
            trend=trend,
            latest_observation_time=latest.observation_time,
            source_code=latest.source.code if latest.source else None
        )
