import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.api.deps import get_db

@pytest.fixture
def client(db_engine, seeded_db):
    """Provide a TestClient with overridden database session pointing to db_engine."""
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

def test_get_health(client):
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "database" in data
    assert "timestamp" in data

def test_get_ipos_paginated(client):
    """Test GET /ipos endpoint."""
    response = client.get("/ipos?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "ipos" in data
    assert len(data["ipos"]) >= 2

def test_get_open_ipos(client):
    """Test GET /ipos/open endpoint."""
    response = client.get("/ipos/open")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(ipo["symbol"] == "SWIGGY" for ipo in data)

def test_get_upcoming_ipos(client):
    """Test GET /ipos/upcoming endpoint."""
    response = client.get("/ipos/upcoming")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_ipo_detail_by_symbol(client):
    """Test GET /ipos/{ipo_id} using stock symbol."""
    response = client.get("/ipos/SWIGGY")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SWIGGY"
    assert data["company_name"] == "Swiggy Limited"

def test_get_ipo_not_found(client):
    """Test GET /ipos/{ipo_id} with non-existent symbol returns 404."""
    response = client.get("/ipos/NONEXISTENT_IPO_SYMBOL")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "IPO_NOT_FOUND"

def test_get_ipo_gmp(client):
    """Test GET /ipos/{ipo_id}/gmp endpoint."""
    response = client.get("/ipos/SWIGGY/gmp")
    assert response.status_code == 200
    data = response.json()
    assert "gmp_price" in data
    assert float(data["gmp_price"]) > 0

def test_get_ipo_gmp_history(client):
    """Test GET /ipos/{ipo_id}/gmp/history endpoint."""
    response = client.get("/ipos/SWIGGY/gmp/history")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SWIGGY"
    assert data["count"] >= 4
    assert len(data["history"]) >= 4

def test_get_ipo_subscription(client):
    """Test GET /ipos/{ipo_id}/subscription endpoint."""
    response = client.get("/ipos/SWIGGY/subscription")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SWIGGY"
    assert "latest" in data
    assert data["latest"]["overall_x"] is not None

def test_get_ipo_summary(client):
    """Test GET /ipos/{ipo_id}/summary endpoint."""
    response = client.get("/ipos/SWIGGY/summary")
    assert response.status_code == 200
    data = response.json()
    assert "ipo" in data
    assert "latest_gmp" in data
    assert "latest_subscription" in data
    assert data["ipo"]["symbol"] == "SWIGGY"
