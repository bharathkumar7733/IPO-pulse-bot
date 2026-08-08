from typing import Dict, Any
from app.bot import handlers
from app.core.logging import logger

async def process_telegram_update(update: Dict[str, Any]):
    """Dispatches incoming Telegram update object to the corresponding command handler."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = str(message.get("chat", {}).get("id"))
    text = (message.get("text") or "").strip()

    if not text.startswith("/"):
        return

    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    if "@" in command:
        command = command.split("@")[0]

    arg = parts[1].strip() if len(parts) > 1 else None

    logger.info(f"Received Telegram command '{command}' from chat_id {chat_id} (arg: {arg})")

    if command == "/start":
        await handlers.handle_start(chat_id)
    elif command == "/help":
        await handlers.handle_help(chat_id)
    elif command == "/ipo":
        await handlers.handle_ipo(chat_id)
    elif command == "/open":
        await handlers.handle_open(chat_id)
    elif command == "/upcoming":
        await handlers.handle_upcoming(chat_id)
    elif command == "/gmp":
        await handlers.handle_gmp(chat_id, arg)
    elif command == "/details":
        await handlers.handle_details(chat_id, arg)
    elif command == "/analysis":
        await handlers.handle_analysis(chat_id, arg)
    elif command == "/history":
        await handlers.handle_history(chat_id, arg)
    elif command == "/subscription":
        await handlers.handle_subscription(chat_id, arg)
    else:
        logger.warning(f"Unknown command '{command}' received.")
