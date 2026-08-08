from fastapi import APIRouter
from app.api.endpoints import health, ipos, ingestion, bot, alerts

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(ipos.router, tags=["IPOs"])
api_router.include_router(ingestion.router, tags=["Ingestion"])
api_router.include_router(bot.router, tags=["Telegram Bot"])
api_router.include_router(alerts.router, tags=["Smart Alerts"])
