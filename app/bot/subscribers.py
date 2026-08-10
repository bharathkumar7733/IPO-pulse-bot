import os
import json
from typing import Set
from app.core.logging import logger

SUBSCRIBERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "subscribers.json")

def load_subscribers() -> Set[str]:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    try:
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except Exception as e:
        logger.error(f"Failed to load subscribers.json: {e}")
        return set()

def save_subscriber(chat_id: str):
    if not chat_id or chat_id == "123456789":
        return
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.add(chat_id)
        try:
            with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
                json.dump(list(subscribers), f)
            logger.info(f"[Subscribers] Added new subscriber chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Failed to save subscriber chat_id {chat_id}: {e}")
