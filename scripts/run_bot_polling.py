import sys
import os
import asyncio
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bot.config import bot_settings
from app.bot.router import process_telegram_update
from app.core.logging import logger

async def start_telegram_polling():
    token = bot_settings.TELEGRAM_BOT_TOKEN
    base_url = f"https://api.telegram.org/bot{token}"
    offset = 0

    logger.info(f"Starting live Telegram polling daemon for @bharathipobot...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Delete webhook if set so polling works smoothly
        try:
            await client.post(f"{base_url}/deleteWebhook")
        except Exception:
            pass

        while True:
            try:
                res = await client.get(f"{base_url}/getUpdates", params={"offset": offset, "timeout": 15})
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for update in updates:
                        offset = update["update_id"] + 1
                        asyncio.create_task(process_telegram_update(update))
            except Exception as e:
                logger.error(f"Polling loop error: {e}")
                await asyncio.sleep(3)

            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(start_telegram_polling())
