import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import ValidationError

from app.schemas.ingestion import RawIPODTO
from app.core.logging import logger
from app.models.api_request import APIRequest

class ProviderFetchError(Exception):
    """Raised when external API provider fetch fails after retries."""
    pass

class BaseIPOProvider(ABC):
    """Abstract Base Class for IPO Data Providers."""
    
    def __init__(self, code: str, name: str, timeout: float = 10.0, max_retries: int = 3):
        self.code = code
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Subclasses implement the raw HTTP GET request."""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, ProviderFetchError, Exception)),
        reraise=True
    )
    async def fetch_with_retry(self, status: Optional[str] = None) -> Dict[str, Any]:
        """Executes fetch with automatic exponential backoff retry for network/HTTP errors."""
        start_time = time.time()
        
        try:
            data = await self._do_fetch(status=status)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Provider [{self.code}] fetch succeeded in {duration_ms}ms")
            return {
                "raw_data": data,
                "duration_ms": duration_ms,
                "status_code": 200,
                "error_message": None
            }
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"Provider [{self.code}] HTTP Error {status_code}: {e}")
            if status_code == 429:
                logger.warning(f"Rate limited by provider [{self.code}], triggering backoff.")
            raise ProviderFetchError(f"HTTP {status_code}: {e}") from e
        except Exception as e:
            if isinstance(e, ProviderFetchError):
                raise
            logger.error(f"Provider [{self.code}] Fetch Error: {e}")
            raise ProviderFetchError(f"Fetch error: {e}") from e

    def parse_and_validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[RawIPODTO], List[str]]:
        """
        Parses raw record dicts into validated Pydantic RawIPODTO objects.
        Filters out malformed records cleanly without breaking valid items.
        """
        validated_dtos: List[RawIPODTO] = []
        errors: List[str] = []

        for idx, item in enumerate(raw_records):
            try:
                dto = RawIPODTO.model_validate(item)
                validated_dtos.append(dto)
            except ValidationError as ve:
                err_msg = f"Record [{idx}] Symbol '{item.get('symbol', 'UNKNOWN')}': Validation Error -> {ve.errors()[0]['msg']}"
                logger.warning(f"Provider [{self.code}] malformed record skipped: {err_msg}")
                errors.append(err_msg)
            except Exception as e:
                err_msg = f"Record [{idx}]: Unexpected parsing error -> {str(e)}"
                logger.error(f"Provider [{self.code}] error: {err_msg}")
                errors.append(err_msg)

        return validated_dtos, errors
