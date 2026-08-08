import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db

@pytest.fixture
def client(db_engine):
    """Provide a TestClient with clean isolated database session."""
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

def test_full_e2e_pipeline(client):
    """
    Full End-to-End Pipeline Verification:
    HTTP API Request -> FastAPI Router -> Pydantic Validation -> Database Persistence -> Retrieval API
    """
    # 1. Trigger Ingestion via API
    ingest_res = client.post("/ingest/ipos?provider_code=MOCK_PROVIDER")
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["provider_code"] == "MOCK_PROVIDER"
    assert ingest_data["status"] == "SUCCESS"
    assert ingest_data["ipos_created"] == 2
    assert ingest_data["subscription_records_created"] == 1

    # 2. Retrieve Ingested IPO Detail via API
    detail_res = client.get("/ipos/MOCK_SWIGGY")
    assert detail_res.status_code == 200
    ipo_detail = detail_res.json()
    assert ipo_detail["symbol"] == "MOCK_SWIGGY"
    assert ipo_detail["company_name"] == "Swiggy Limited Mock"
    assert ipo_detail["issue_type"] == "MAINBOARD"
    assert ipo_detail["status"] == "OPEN"
    assert ipo_detail["min_price"] == 371.0
    assert ipo_detail["max_price"] == 390.0

    # 3. Retrieve Subscription History via API
    sub_res = client.get("/ipos/MOCK_SWIGGY/subscription")
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["symbol"] == "MOCK_SWIGGY"
    assert sub_data["count"] == 1
    assert sub_data["latest"]["overall_x"] == 3.59
    assert sub_data["latest"]["qib_x"] == 6.02

    # 4. Verify Health Status after Ingestion
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["database"] == "healthy"
