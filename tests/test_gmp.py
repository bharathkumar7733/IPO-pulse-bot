from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db
from app.providers.gmp_provider import MockGMPProvider, ApifyGMPProvider
from app.providers.base import ProviderFetchError
from app.services.gmp_service import GMPService
from app.schemas.gmp import GMPTrend
from app.models import IPO, GMPHistory, DataSource

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
async def test_01_gmp_fetched_correctly():
    """1. Verify GMP is fetched correctly from provider."""
    provider = MockGMPProvider()
    res = await provider.fetch_with_retry()
    assert res["status_code"] == 200
    assert "data" in res["raw_data"]
    assert len(res["raw_data"]["data"]) > 0

@pytest.mark.asyncio
async def test_02_gmp_stored_in_db(db_session):
    """2. Verify GMP is stored in PostgreSQL gmp_history table."""
    provider = MockGMPProvider()
    gmp_service = GMPService(db_session)
    res = await gmp_service.sync_gmp(provider)
    assert res.subscription_records_created >= 2

    swiggy = db_session.scalars(select(IPO).where(IPO.symbol == "SWIGGY")).one()
    latest_gmp = db_session.scalars(
        select(GMPHistory).where(GMPHistory.ipo_id == swiggy.id).order_by(GMPHistory.observation_time.desc())
    ).first()
    assert latest_gmp is not None
    assert float(latest_gmp.gmp_price) == 28.00

@pytest.mark.asyncio
async def test_03_history_preserved_append_only(db_session):
    """3. Verify history is preserved and records are NEVER overwritten."""
    provider = MockGMPProvider()
    gmp_service = GMPService(db_session)
    await gmp_service.sync_gmp(provider)

    swiggy = db_session.scalars(select(IPO).where(IPO.symbol == "SWIGGY")).one()
    count_before = len(swiggy.gmp_history)

    # Sync a second time at a later timestamp
    new_obs_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    new_data = [
        {"symbol": "SWIGGY", "gmp_price": 32.00, "observation_time": new_obs_time}
    ]
    p2 = MockGMPProvider(mock_records=new_data)
    await gmp_service.sync_gmp(p2)

    updated_swiggy = db_session.scalars(select(IPO).where(IPO.symbol == "SWIGGY")).one()
    assert len(updated_swiggy.gmp_history) == count_before + 1, "History must append without overwriting"

@pytest.mark.asyncio
async def test_04_previous_gmp_and_change_calculations(db_session):
    """4, 5, 6, 7. Verify previous GMP is identified, absolute change, percentage change & trend work."""
    ds = DataSource(code="GMP_TEST_SRC", name="Test Src", source_type="UNOFFICIAL_GMP")
    ipo = IPO(symbol="CALC_IPO", company_name="Calc IPO Ltd", max_price=100.0)
    db_session.add_all([ds, ipo])
    db_session.commit()

    gmp_service = GMPService(db_session)

    t1 = datetime.now(timezone.utc) - timedelta(hours=2)
    t2 = datetime.now(timezone.utc)

    # Prev = 20.00, Current = 25.00 -> Abs Change = 5.00, Pct Change = 25.00%, Trend = RISING
    g1 = GMPHistory(ipo_id=ipo.id, source_id=ds.id, gmp_price=20.00, observation_time=t1)
    g2 = GMPHistory(ipo_id=ipo.id, source_id=ds.id, gmp_price=25.00, observation_time=t2)
    db_session.add_all([g1, g2])
    db_session.commit()

    analysis = gmp_service.analyze_gmp("CALC_IPO")
    assert analysis.current_gmp == 25.00
    assert analysis.previous_gmp == 20.00
    assert analysis.absolute_change == 5.00
    assert analysis.percentage_change == 25.00
    assert analysis.trend == GMPTrend.RISING

@pytest.mark.asyncio
async def test_08_duplicate_observations_handled(db_session):
    """8. Verify duplicate observations (same IPO, source, timestamp) are handled safely."""
    provider = MockGMPProvider()
    gmp_service = GMPService(db_session)

    # Sync first time
    res1 = await gmp_service.sync_gmp(provider)
    first_created = res1.subscription_records_created

    # Sync exact same payload again with same timestamps
    res2 = await gmp_service.sync_gmp(provider)
    assert res2.subscription_records_created == 0, "Duplicate timestamp observations must be skipped"

@pytest.mark.asyncio
async def test_09_missing_gmp_does_not_crash(db_session):
    """9. Verify missing or null GMP values do not crash system."""
    provider = MockGMPProvider()
    raw = [
        {"symbol": "NULL_TEST", "gmp_price": None},
        {"symbol": "VALID_TEST", "gmp_price": 10.0}
    ]
    dtos, errors = provider.parse_and_validate_gmp(raw)
    assert len(dtos) == 1
    assert dtos[0].symbol == "VALID_TEST"
    assert len(errors) == 1

@pytest.mark.asyncio
async def test_10_provider_failure_handled():
    """10. Verify provider failure is handled gracefully with retry and exception handling."""
    failing_provider = MockGMPProvider(should_fail=True)
    with pytest.raises(ProviderFetchError):
        await failing_provider.fetch_with_retry()

@pytest.mark.asyncio
async def test_11_real_gmp_data_controlled_test(db_session):
    """11. Verify real approved GMP data ingestion using Apify/InvestorGain schema structure."""
    real_gmp_payload = {
        "status": "success",
        "data": [
            {
                "symbol": "SWIGGY",
                "company_name": "Swiggy Limited",
                "gmp_price": 31.50,
                "gmp_percent": 8.08,
                "estimated_listing_price": 421.50,
                "subject_to_sauda": 550.00,
                "observation_time": (datetime.now(timezone.utc)).isoformat()
            },
            {
                "symbol": "NIVA_BUPA",
                "company_name": "Niva Bupa Health Insurance Ltd",
                "gmp_price": 3.00,
                "gmp_percent": 4.05,
                "estimated_listing_price": 77.00
            }
        ]
    }

    apify_provider = ApifyGMPProvider()
    gmp_service = GMPService(db_session)

    with patch.object(apify_provider, "_do_fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = real_gmp_payload
        result = await gmp_service.sync_gmp(apify_provider)

        assert result.provider_code == "APIFY_GMP"
        assert result.status in ["SUCCESS", "PARTIAL_SUCCESS"]
        assert result.subscription_records_created >= 2

    # Verify Swiggy updated GMP analysis
    analysis = gmp_service.analyze_gmp("SWIGGY")
    assert analysis.current_gmp == 31.50
    assert analysis.source_code == "APIFY_GMP"
