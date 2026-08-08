from typing import Dict, Any, Optional
from app.clients.base_client import BaseHTTPClient

class UpstoxIPOClient(BaseHTTPClient):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://api.upstox.com/v2")
        self.api_key = api_key

    async def fetch_ipos(self, status: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if status:
            params["status"] = status
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return await self.get("ipos", params=params, headers=headers)

    async def fetch_ipo_details(self, ipo_id: str) -> Dict[str, Any]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return await self.get(f"ipos/{ipo_id}", headers=headers)
