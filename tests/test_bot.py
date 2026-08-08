import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.bot.router import process_telegram_update
from app.bot.config import bot_settings
from app.bot.client import TelegramAPIClient, BackendAPIClient
from app.bot import handlers

@pytest.fixture
def client(db_engine, seeded_db):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    
    # Override handlers.backend_client to use in-memory ASGI app
    test_backend_client = BackendAPIClient(app=app, base_url="http://test")
    handlers.backend_client = test_backend_client

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def create_update(command_text: str, chat_id: str = "123456789") -> dict:
    return {
        "update_id": 10001,
        "message": {
            "message_id": 55,
            "from": {"id": 123456789, "first_name": "TestUser"},
            "chat": {"id": chat_id, "type": "private"},
            "text": command_text
        }
    }

@pytest.mark.asyncio
async def test_bot_start_command():
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/start")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "Welcome to the Indian IPO Intelligence Agent" in text_sent

@pytest.mark.asyncio
async def test_bot_help_command():
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/help")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "Grey Market Premium (GMP) is an informal" in text_sent, "Must include mandatory GMP disclaimer"

@pytest.mark.asyncio
async def test_bot_open_command(client):
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/open")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "SWIGGY" in text_sent

@pytest.mark.asyncio
async def test_bot_gmp_command(client):
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/gmp SWIGGY")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "GMP Analysis: Swiggy Limited" in text_sent
        assert "Disclaimer" in text_sent

@pytest.mark.asyncio
async def test_bot_details_command(client):
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/details SWIGGY")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "Swiggy Limited" in text_sent
        assert "Link Intime" in text_sent

@pytest.mark.asyncio
async def test_bot_history_command(client):
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/history SWIGGY")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "GMP History: SWIGGY" in text_sent

@pytest.mark.asyncio
async def test_bot_subscription_command(client):
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/subscription SWIGGY")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "Subscription Status: SWIGGY" in text_sent
        assert "3.59x" in text_sent

@pytest.mark.asyncio
async def test_bot_unknown_symbol_graceful_error(client):
    """Verify non-existent symbol returns friendly message without exposing internal errors."""
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/details UNKNOWN_SYMBOL")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "not found" in text_sent
        assert "Traceback" not in text_sent

@pytest.mark.asyncio
async def test_bot_test_mode_protection():
    """Verify test mode blocks broadcasts to non-admin chat IDs."""
    client = TelegramAPIClient()
    bot_settings.TEST_MODE = True
    bot_settings.ADMIN_CHAT_IDS = ["123456789"]

    # Allowed admin chat
    res_admin = await client.send_message("123456789", "Hello Admin")
    
    # Blocked public chat
    res_public = await client.send_message("999999999", "Hello Public User")
    assert res_public["result"]["message_id"] == 99999

def test_telegram_webhook_endpoint(client):
    """Test POST /telegram/webhook API endpoint."""
    payload = create_update("/start")
    res = client.post("/telegram/webhook", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
