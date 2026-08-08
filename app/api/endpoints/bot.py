from typing import Dict, Any
from fastapi import APIRouter, status
from app.bot.router import process_telegram_update

router = APIRouter()

@router.post("/telegram/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(update: Dict[str, Any]):
    """Endpoint for Telegram Bot API webhook updates."""
    await process_telegram_update(update)
    return {"status": "ok"}
