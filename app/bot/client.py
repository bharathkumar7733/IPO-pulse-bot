import httpx
from typing import Dict, Any, Optional, List
from app.bot.config import bot_settings
from app.core.logging import logger

class BackendAPIClient:
    """Client for calling backend FastAPI endpoints rather than external raw providers."""

    def __init__(self, base_url: Optional[str] = None, app: Optional[Any] = None):
        self.base_url = (base_url or bot_settings.BACKEND_URL).rstrip("/")
        self.app = app

    def _get_client(self, timeout: float = 10.0) -> httpx.AsyncClient:
        if self.app:
            transport = httpx.ASGITransport(app=self.app)
            return httpx.AsyncClient(transport=transport, base_url=self.base_url, timeout=timeout)
        return httpx.AsyncClient(timeout=timeout)

    async def get_health(self) -> Dict[str, Any]:
        async with self._get_client(timeout=5.0) as client:
            res = await client.get(f"{self.base_url}/health")
            res.raise_for_status()
            return res.json()

    async def get_ipos(self, status: Optional[str] = None, issue_type: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        params = {"limit": limit}
        if status:
            params["status"] = status
        if issue_type:
            params["issue_type"] = issue_type

        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos", params=params)
            res.raise_for_status()
            return res.json()

    async def get_open_ipos(self) -> List[Dict[str, Any]]:
        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos/open")
            res.raise_for_status()
            return res.json()

    async def get_upcoming_ipos(self) -> List[Dict[str, Any]]:
        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos/upcoming")
            res.raise_for_status()
            return res.json()

    async def get_ipo_detail(self, identifier: str) -> Dict[str, Any]:
        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos/{identifier}")
            res.raise_for_status()
            return res.json()

    async def get_gmp_analysis(self, identifier: str) -> Dict[str, Any]:
        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos/{identifier}/gmp/analysis")
            res.raise_for_status()
            return res.json()

    async def get_ai_analysis(self, identifier: str) -> Dict[str, Any]:
        async with self._get_client(timeout=15.0) as client:
            res = await client.get(f"{self.base_url}/ipos/{identifier}/analysis")
            res.raise_for_status()
            return res.json()

    async def get_gmp_history(self, identifier: str) -> Dict[str, Any]:
        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos/{identifier}/gmp/history")
            res.raise_for_status()
            return res.json()

    async def get_subscription(self, identifier: str) -> Dict[str, Any]:
        async with self._get_client(timeout=10.0) as client:
            res = await client.get(f"{self.base_url}/ipos/{identifier}/subscription")
            res.raise_for_status()
            return res.json()

class TelegramAPIClient:
    """Client for Telegram Bot API calls."""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or bot_settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        # Test mode filter: if Test Mode is active and chat_id is not in ADMIN_CHAT_IDS, log & skip send to avoid spamming
        if bot_settings.TEST_MODE and str(chat_id) not in bot_settings.ADMIN_CHAT_IDS:
            logger.info(f"[TEST MODE ACTIVE] Blocked broadcast to public chat_id '{chat_id}'. Only admins allowed.")
            return {"ok": True, "result": {"message_id": 99999, "text": "Test mode blocked message to non-admin"}}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                return res.json()
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
                return {"ok": False, "error": str(e)}
