from typing import Dict, Any, Optional, List
import httpx
from app.providers.base import BaseIPOProvider

class UpstoxIPOProvider(BaseIPOProvider):
    """Upstox API v2 official IPO Data Provider implementation."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.upstox.com/v2"):
        super().__init__(code="UPSTOX_API", name="Upstox Developer API v2")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/ipos"
        params = {}
        if status:
            params["status"] = status.lower()

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(url, params=params, headers=headers)
            res.raise_for_status()
            return res.json()
