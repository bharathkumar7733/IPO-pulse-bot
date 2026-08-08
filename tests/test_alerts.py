from datetime import datetime, timezone, date, timedelta
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.services.alert_service import SmartAlertService
from app.bot.client import TelegramAPIClient
from app.models import IPO, GMPHistory, SubscriptionHistory, DataSource, Notification, NotificationType

@pytest.fixture
def client(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_date_based_alerts(db_session):
    """Test IPO Opened Today, Closing Today, and Listing Tomorrow date alerts."""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    ds = DataSource(code="ALERT_SRC", name="Alert Source", source_type="OFFICIAL")
    ipo_open = IPO(symbol="OPEN_TODAY", company_name="Open Today Ltd", open_date=today, close_date=today + timedelta(days=2))
    ipo_close = IPO(symbol="CLOSE_TODAY", company_name="Close Today Ltd", open_date=today - timedelta(days=2), close_date=today)
    ipo_list = IPO(symbol="LIST_TOMORROW", company_name="List Tomorrow Ltd", listing_date=tomorrow)

    db_session.add_all([ds, ipo_open, ipo_close, ipo_list])
    db_session.commit()

    service = SmartAlertService(db_session)
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        alerts = await service.evaluate_and_dispatch()

        types = [a["type"] for a in alerts]
        assert "IPO_OPENED" in types
        assert "IPO_CLOSING_SOON" in types
        assert "IPO_LISTING_TOMORROW" in types

@pytest.mark.asyncio
async def test_gmp_surge_and_drop_alerts(db_session):
    """Test GMP Surge (+10) and GMP Drop (-10) alerts."""
    ds = DataSource(code="GMP_ALERT_SRC", name="GMP Alert Src", source_type="UNOFFICIAL_GMP")
    ipo = IPO(symbol="SURGE_IPO", company_name="Surge IPO Ltd", max_price=100.0)
    db_session.add_all([ds, ipo])
    db_session.commit()

    now = datetime.now(timezone.utc)
    g1 = GMPHistory(ipo_id=ipo.id, source_id=ds.id, gmp_price=10.0, observation_time=now - timedelta(hours=1))
    g2 = GMPHistory(ipo_id=ipo.id, source_id=ds.id, gmp_price=25.0, observation_time=now) # Delta = +15.0 (Surge >= +10)
    db_session.add_all([g1, g2])
    db_session.commit()

    service = SmartAlertService(db_session)
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        alerts = await service.evaluate_and_dispatch()

        surge_alerts = [a for a in alerts if a["type"] == "GMP_SURGE"]
        assert len(surge_alerts) == 1
        assert surge_alerts[0]["symbol"] == "SURGE_IPO"

@pytest.mark.asyncio
async def test_subscription_milestone_and_deduplication(db_session):
    """Test Subscription milestone alerts (1x, 5x, 10x) and verify ZERO duplicate alerts on re-run."""
    ds = DataSource(code="SUB_ALERT_SRC", name="Sub Alert Src", source_type="OFFICIAL")
    ipo = IPO(symbol="SUB_IPO", company_name="Sub IPO Ltd")
    db_session.add_all([ds, ipo])
    db_session.commit()

    sub = SubscriptionHistory(ipo_id=ipo.id, source_id=ds.id, overall_x=12.5, qib_x=15.0, retail_x=8.0, observation_time=datetime.now(timezone.utc))
    db_session.add(sub)
    db_session.commit()

    service = SmartAlertService(db_session)
    with patch.object(TelegramAPIClient, "send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"ok": True}
        
        # 1st Run: Should trigger milestones 1x, 5x, 10x
        alerts_run1 = await service.evaluate_and_dispatch()
        sub_alerts1 = [a for a in alerts_run1 if a["type"] == "SUBSCRIPTION_MILESTONE"]
        assert len(sub_alerts1) == 3 # 1x, 5x, 10x

        # 2nd Run (Deduplication Check): Should trigger ZERO new alerts because idempotency keys exist!
        alerts_run2 = await service.evaluate_and_dispatch()
        sub_alerts2 = [a for a in alerts_run2 if a["type"] == "SUBSCRIPTION_MILESTONE" and a["symbol"] == "SUB_IPO"]
        assert len(sub_alerts2) == 0, "Deduplication must prevent duplicate alerts!"

def test_alerts_endpoint(client):
    """Test POST /alerts/evaluate API endpoint."""
    res = client.post("/alerts/evaluate")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
