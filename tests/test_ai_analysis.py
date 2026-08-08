import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.services.ai_service import AIService
from app.bot.router import process_telegram_update
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
    
    test_backend_client = BackendAPIClient(app=app, base_url="http://test")
    handlers.backend_client = test_backend_client

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def create_update(command_text: str, chat_id: str = "123456789") -> dict:
    return {
        "update_id": 20001,
        "message": {
            "message_id": 99,
            "from": {"id": 123456789, "first_name": "TestUser"},
            "chat": {"id": chat_id, "type": "private"},
            "text": command_text
        }
    }

def test_ai_service_factual_grounding(db_session, seeded_db):
    """Verify AIService builds structured facts from PostgreSQL and derives grounded insights without number fabrication."""
    ai_service = AIService(db_session)
    res = ai_service.generate_analysis("SWIGGY")

    assert res.symbol == "SWIGGY"
    assert res.company_name == "Swiggy Limited"
    assert res.current_gmp == 22.0
    assert res.overall_subscription == 3.59
    assert len(res.positive_signals) > 0
    assert len(res.risks) > 0
    assert "Swiggy Limited" in res.overall_assessment
    assert "Informational analysis only" in res.formatted_markdown

@pytest.mark.asyncio
async def test_bot_analysis_command(client):
    """Test /analysis SWIGGY bot command."""
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        update = create_update("/analysis SWIGGY")
        await process_telegram_update(update)

        mock_send.assert_called_once()
        text_sent = mock_send.call_args[0][1]
        assert "SWIGGY IPO Analysis" in text_sent
        assert "GMP: ₹22.0" in text_sent
        assert "GMP Trend: Rising" in text_sent
        assert "Subscription: 3.59x" in text_sent
        assert "Positive signals" in text_sent
        assert "Risks" in text_sent
        assert "Overall assessment" in text_sent
        assert "Informational analysis only" in text_sent

def test_get_ai_analysis_rest_endpoint(client):
    """Test GET /ipos/SWIGGY/analysis REST endpoint."""
    res = client.get("/ipos/SWIGGY/analysis")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "SWIGGY"
    assert data["current_gmp"] == 22.0
    assert data["overall_subscription"] == 3.59
    assert isinstance(data["positive_signals"], list)
    assert isinstance(data["risks"], list)
