import os
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import httpx

from app.providers.base import BaseIPOProvider, ProviderFetchError
from app.schemas.ingestion import RawIPODTO, RawSubscriptionDTO
from app.models.ipo import IPOStatus, IssueType
from app.core.logging import logger

class IPONotifyProvider(BaseIPOProvider):
    """
    Official Provider implementation for IPO Notify (https://iponotify.me/api/ipo).
    Fetches, paginates, validates, and normalizes Indian IPO master & subscription data.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://iponotify.me/api/ipo",
        timeout: float = 10.0,
        max_retries: int = 3
    ):
        super().__init__(code="IPO_NOTIFY", name="IPO Notify Primary Gateway", timeout=timeout, max_retries=max_retries)
        self.api_key = api_key or os.getenv("IPO_NOTIFY_API_KEY")
        self.base_url = base_url.rstrip("/")

    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Executes GET request to IPO Notify API endpoints with X-API-KEY authentication."""
        endpoint_status = (status or "open").lower()
        if endpoint_status not in ["open", "upcoming", "closed"]:
            endpoint_status = "open"

        url = f"{self.base_url}/{endpoint_status}"
        headers = {}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        params = {"limit": 20}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(url, headers=headers, params=params)
            res.raise_for_status()
            return res.json()

    def parse_and_validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[RawIPODTO], List[str]]:
        """
        Normalizes raw IPO Notify JSON payload items into validated RawIPODTO instances.
        Determines exact IPO status based on dates and API status field.
        """
        validated_dtos: List[RawIPODTO] = []
        errors: List[str] = []

        for idx, item in enumerate(raw_records):
            try:
                # Symbol fallback: use upper(searchId) if symbol is missing/null
                raw_sym = item.get("symbol")
                if not raw_sym and item.get("searchId"):
                    raw_sym = item.get("searchId", "").replace("-ipo", "").upper()
                
                if not raw_sym:
                    errors.append(f"Record [{idx}]: Missing symbol and searchId skipped")
                    continue

                # Issue size normalization: bytes/rupees to Crores (divide by 10^7)
                issue_size_raw = item.get("issueSize")
                size_cr = None
                if issue_size_raw and isinstance(issue_size_raw, (int, float)):
                    size_cr = round(float(issue_size_raw) / 10_000_000, 2)

                # Classification: SME if isSme is True
                is_sme = bool(item.get("isSme", False))
                issue_type = IssueType.SME if is_sme else IssueType.MAINBOARD

                # Status Normalization
                raw_status = (item.get("status") or "").upper()
                if raw_status in ["OPEN", "ACTIVE"]:
                    status_enum = IPOStatus.OPEN
                elif raw_status == "UPCOMING":
                    status_enum = IPOStatus.UPCOMING
                elif raw_status == "CLOSED":
                    status_enum = IPOStatus.CLOSED
                elif raw_status == "LISTED":
                    status_enum = IPOStatus.LISTED
                else:
                    status_enum = IPOStatus.OPEN

                # Extract Subscription DTO if present
                sub_dto = None
                sub_rates = item.get("subscriptionRates") or []
                if sub_rates and isinstance(sub_rates, list):
                    qib_val = None
                    nii_val = None
                    retail_val = None
                    total_val = None
                    for cat in sub_rates:
                        c_name = (cat.get("category") or "").upper()
                        val = cat.get("subscriptionRate")
                        if val is not None:
                            val_f = float(val)
                            if c_name == "QIB":
                                qib_val = val_f
                            elif c_name == "NII":
                                nii_val = val_f
                            elif c_name == "RETAIL":
                                retail_val = val_f
                            elif c_name == "TOTAL":
                                total_val = val_f

                    if total_val is not None:
                        sub_dto = RawSubscriptionDTO(
                            qib_x=qib_val,
                            nii_x=nii_val,
                            retail_x=retail_val,
                            overall_x=total_val
                        )

                listing_data = item.get("listing") or {}

                dto = RawIPODTO(
                    symbol=raw_sym,
                    company_name=item.get("companyName") or f"{raw_sym} Limited",
                    company_short_name=item.get("companyShortName"),
                    issue_type=issue_type,
                    status=status_enum,
                    min_price=float(item["minPrice"]) if item.get("minPrice") is not None else None,
                    max_price=float(item["maxPrice"]) if item.get("maxPrice") is not None else None,
                    issue_price=float(item["issuePrice"]) if item.get("issuePrice") is not None else None,
                    lot_size=int(item["lotSize"]) if item.get("lotSize") is not None else None,
                    total_issue_size_cr=size_cr,
                    open_date=item.get("startDate"),
                    close_date=item.get("endDate"),
                    allotment_date=item.get("allotmentDate"),
                    registrar_name=item.get("registrar"),
                    bse_scrip_code=listing_data.get("bseScripCode"),
                    nse_scrip_code=listing_data.get("nseScripCode"),
                    subscription=sub_dto
                )
                validated_dtos.append(dto)

            except Exception as e:
                err_msg = f"Record [{idx}] Symbol '{item.get('symbol', 'UNKNOWN')}': Validation error -> {str(e)}"
                logger.warning(f"Provider [{self.code}] malformed record skipped: {err_msg}")
                errors.append(err_msg)

        return validated_dtos, errors
