import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.providers.mock_provider import MockIPOProvider
from app.providers.upstox_provider import UpstoxIPOProvider
from app.providers.base import ProviderFetchError
from app.services.ipo_sync_service import IPOSyncService
from app.models import IPO, SubscriptionHistory, APIRequest, WorkflowHealth

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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_provider_parse_and_validate():
    """Verify that malformed records are filtered out without throwing or corrupting valid records."""
    provider = MockIPOProvider()
    raw_data = [
        # Valid record
        {
            "symbol": "VALID_IPO",
            "company_name": "Valid Company Ltd",
            "issue_type": "MAINBOARD",
            "status": "OPEN",
            "min_price": 100.0,
            "max_price": 105.0
        },
        # Malformed record (negative price)
        {
            "symbol": "INVALID_PRICE",
            "company_name": "Invalid Price Ltd",
            "min_price": -50.0
        },
        # Missing required symbol
        {
            "company_name": "No Symbol Ltd"
        }
    ]

    dtos, errors = provider.parse_and_validate(raw_data)
    assert len(dtos) == 1, "Only valid record should be accepted"
    assert dtos[0].symbol == "VALID_IPO"
    assert len(errors) == 2, "2 malformed records should generate warning logs"

@pytest.mark.asyncio
async def test_sync_service_execution(db_session):
    """Verify IPOSyncService creates IPOs, subscriptions, SLA logs, and workflow health records."""
    provider = MockIPOProvider()
    sync_service = IPOSyncService(db_session)

    result = await sync_service.sync_provider(provider)

    assert result.status == "SUCCESS"
    assert result.ipos_processed == 2
    assert result.ipos_created == 2
    assert result.subscription_records_created == 1

    # Verify IPO inserted
    swiggy = db_session.scalars(select(IPO).where(IPO.symbol == "MOCK_SWIGGY")).first()
    assert swiggy is not None
    assert swiggy.company_name == "Swiggy Limited Mock"

    # Verify Subscription snapshot inserted
    sub = db_session.scalars(select(SubscriptionHistory).where(SubscriptionHistory.ipo_id == swiggy.id)).first()
    assert sub is not None
    assert float(sub.overall_x) == 3.59

    # Verify APIRequest & WorkflowHealth logged
    api_logs = db_session.scalars(select(APIRequest)).all()
    assert len(api_logs) >= 1

    wf_logs = db_session.scalars(select(WorkflowHealth)).all()
    assert len(wf_logs) >= 1

@pytest.mark.asyncio
async def test_sync_service_idempotency_and_update(db_session):
    """Verify re-running sync updates existing records instead of creating duplicate IPOs."""
    provider = MockIPOProvider()
    sync_service = IPOSyncService(db_session)

    # First sync
    res1 = await sync_service.sync_provider(provider)
    assert res1.ipos_created == 2

    # Update payload for second sync
    updated_payload = {
        "status": "success",
        "data": [
            {
                "symbol": "MOCK_SWIGGY",
                "company_name": "Swiggy Limited Updated Name",
                "issue_type": "MAINBOARD",
                "status": "OPEN",
                "min_price": 371.0,
                "max_price": 395.0,  # Price updated
                "lot_size": 38
            }
        ]
    }
    updated_provider = MockIPOProvider(mock_response=updated_payload)

    # Second sync
    res2 = await sync_service.sync_provider(updated_provider)
    assert res2.ipos_created == 0, "No new IPOs should be created"
    assert res2.ipos_updated == 1, "1 existing IPO should be updated"

    # Verify updated field
    swiggy = db_session.scalars(select(IPO).where(IPO.symbol == "MOCK_SWIGGY")).first()
    assert float(swiggy.max_price) == 395.0
    assert swiggy.company_name == "Swiggy Limited Updated Name"

@pytest.mark.asyncio
async def test_provider_retry_on_network_failure():
    """Verify that network failures trigger retry logic and reraise ProviderFetchError on persistent failure."""
    failing_provider = MockIPOProvider(should_fail=True)
    
    with pytest.raises(ProviderFetchError):
        await failing_provider.fetch_with_retry()

def test_ingestion_api_endpoint(client):
    """Test POST /ingest/ipos endpoint."""
    response = client.post("/ingest/ipos?provider_code=MOCK_PROVIDER")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_code"] == "MOCK_PROVIDER"
    assert data["status"] == "SUCCESS"
    assert data["ipos_processed"] == 2

@pytest.mark.asyncio
async def test_upstox_provider_controlled_test():
    """Controlled real/mocked API test for UpstoxIPOProvider."""
    provider = UpstoxIPOProvider()
    
    mock_upstox_resp = {
        "status": "success",
        "data": [
            {
                "symbol": "UPSTOX_TEST",
                "company_name": "Upstox Test IPO Ltd",
                "issue_type": "MAINBOARD",
                "status": "UPCOMING"
            }
        ]
    }

    with patch.object(provider, "_do_fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_upstox_resp
        res = await provider.fetch_with_retry()
        assert res["status_code"] == 200
        dtos, errors = provider.parse_and_validate(res["raw_data"]["data"])
        assert len(dtos) == 1
        assert dtos[0].symbol == "UPSTOX_TEST"
