from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import httpx
from pydantic import ValidationError

from app.providers.base import BaseIPOProvider
from app.schemas.gmp import RawGMPDTO
from app.core.logging import logger

class BaseGMPProvider(BaseIPOProvider, ABC):
    """Abstract Base Class for Grey Market Premium (GMP) Providers."""

    def parse_and_validate_gmp(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[RawGMPDTO], List[str]]:
        """Parses and validates raw GMP dictionaries into RawGMPDTO objects."""
        dtos: List[RawGMPDTO] = []
        errors: List[str] = []

        for idx, item in enumerate(raw_records):
            try:
                # Handle null/missing gmp_price gracefully
                if item.get("gmp_price") is None:
                    errors.append(f"Record [{idx}] Symbol '{item.get('symbol', 'UNKNOWN')}': Missing or Null GMP price skipped")
                    continue
                
                dto = RawGMPDTO.model_validate(item)
                dtos.append(dto)
            except ValidationError as ve:
                err_msg = f"Record [{idx}] Symbol '{item.get('symbol', 'UNKNOWN')}': Validation Error -> {ve.errors()[0]['msg']}"
                logger.warning(f"GMP Provider [{self.code}] malformed record skipped: {err_msg}")
                errors.append(err_msg)
            except Exception as e:
                err_msg = f"Record [{idx}]: Unexpected parsing error -> {str(e)}"
                logger.error(f"GMP Provider [{self.code}] error: {err_msg}")
                errors.append(err_msg)

        return dtos, errors

class ApifyGMPProvider(BaseGMPProvider):
    """Apify / InvestorGain Managed Scraper Gateway GMP Provider."""

    def __init__(self, api_key: Optional[str] = None, actor_url: Optional[str] = None):
        super().__init__(code="APIFY_GMP", name="Apify Indian IPO Tracker Gateway")
        self.api_key = api_key
        self.actor_url = actor_url or "https://api.apify.com/v2/acts/indian-ipo-tracker/runs/last/dataset/items"

    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(self.actor_url, headers=headers)
            res.raise_for_status()
            return {"data": res.json()}

class MockGMPProvider(BaseGMPProvider):
    """Mock GMP Data Provider for testing, simulations, and edge case validation."""

    def __init__(self, mock_records: Optional[List[Dict[str, Any]]] = None, should_fail: bool = False):
        super().__init__(code="MOCK_GMP", name="Mock GMP Data Provider")
        self.should_fail = should_fail
        self.mock_records = mock_records or [
            {
                "symbol": "SWIGGY",
                "company_name": "Swiggy Limited",
                "gmp_price": 28.00,
                "gmp_percent": 7.18,
                "estimated_listing_price": 418.00,
                "subject_to_sauda": 600.00
            },
            {
                "symbol": "HYUNDAI",
                "company_name": "Hyundai Motor India Limited",
                "gmp_price": 45.00,
                "gmp_percent": 2.30,
                "estimated_listing_price": 2005.00
            },
            # Edge case 1: Null GMP price
            {
                "symbol": "NULL_GMP_IPO",
                "gmp_price": None
            },
            # Edge case 2: Negative/Malformed price
            {
                "symbol": "BAD_GMP_IPO",
                "gmp_price": -10.00
            }
        ]

    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        if self.should_fail:
            raise Exception("Simulated GMP provider fetch failure")
        return {"data": self.mock_records}
