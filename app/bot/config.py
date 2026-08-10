import os
from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_CHAT_IDS: list[str] = [
        id_str.strip()
        for id_str in os.getenv("ADMIN_CHAT_IDS", "").split(",")
        if id_str.strip()
    ]
    TEST_MODE: bool = os.getenv("BOT_TEST_MODE", "false").lower() == "true"
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


bot_settings = BotSettings()
