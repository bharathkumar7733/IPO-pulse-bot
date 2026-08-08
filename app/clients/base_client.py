import httpx
from typing import Dict, Any, Optional
from app.core.logging import logger

class BaseHTTPClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"Sending GET request to {url}")
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
