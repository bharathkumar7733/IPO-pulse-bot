import pytest
import os
from unittest.mock import patch, AsyncMock
import httpx

from app.providers.ipo_notify_provider import IPONotifyProvider
from app.providers.base import ProviderFetchError
from app.models.ipo import IPOStatus, IssueType

SAMPLE_SUCCESS_PAYLOAD = {
    "metadata": {"count": 1, "totalCount": 1, "limit": 10},
    "ipos": [
        {
            "searchId": "swiggy-limited-ipo",
            "companyName": "Swiggy Limited",
            "companyShortName": "Swiggy",
            "isSme": False,
            "symbol": "SWIGGY",
            "issueType": "Book Building",
            "lotSize": 38,
            "minPrice": 371,
            "maxPrice": 390,
            "issuePrice": 390,
            "issueSize": 113274300000,
            "registrar": "Link Intime India Private Ltd",
            "startDate": "2024-11-06",
            "endDate": "2024-11-08",
            "status": "OPEN",
            "subscriptionRates": [
                {"category": "QIB", "subscriptionRate": 6.02},
                {"category": "NII", "subscriptionRate": 4.15},
                {"category": "RETAIL", "subscriptionRate": 1.14},
                {"category": "TOTAL", "subscriptionRate": 3.59}
            ]
        }
    ]
}

def test_parse_and_validate_success():
    """Verify IPONotifyProvider parses valid JSON into RawIPODTO clean instances."""
    provider = IPONotifyProvider(api_key="test_key")
    dtos, errors = provider.parse_and_validate(SAMPLE_SUCCESS_PAYLOAD["ipos"])

    assert len(dtos) == 1
    assert len(errors) == 0

    dto = dtos[0]
    assert dto.symbol == "SWIGGY"
    assert dto.company_name == "Swiggy Limited"
    assert dto.issue_type == IssueType.MAINBOARD
    assert dto.status == IPOStatus.OPEN
    assert dto.min_price == 371.0
    assert dto.max_price == 390.0
    assert dto.lot_size == 38
    assert dto.total_issue_size_cr == 11327.43
    assert dto.subscription is not None
    assert dto.subscription.overall_x == 3.59
    assert dto.subscription.qib_x == 6.02

def test_symbol_fallback_to_search_id():
    """Verify symbol falls back to searchId if symbol field is missing."""
    raw = [
        {
            "searchId": "abril-paper-tech-ipo",
            "companyName": "Abril Paper Tech Ltd",
            "isSme": True,
            "symbol": None,
            "minPrice": 61,
            "maxPrice": 61
        }
    ]
    provider = IPONotifyProvider(api_key="test_key")
    dtos, errors = provider.parse_and_validate(raw)

    assert len(dtos) == 1
    assert dtos[0].symbol == "ABRIL-PAPER-TECH"
    assert dtos[0].issue_type == IssueType.SME

@pytest.mark.asyncio
async def test_authentication_failure():
    """Verify 401/403 HTTP error raises ProviderFetchError."""
    provider = IPONotifyProvider(api_key="invalid_key")
    dummy_req = httpx.Request("GET", "https://iponotify.me/api/ipo/open")
    
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_resp = httpx.Response(status_code=401, json={"error": "Unauthorized API key"}, request=dummy_req)
        mock_get.return_value = mock_resp
        
        with pytest.raises(ProviderFetchError) as exc_info:
            await provider.fetch_with_retry()
        assert "HTTP 401" in str(exc_info.value)

@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Verify 429 rate limit triggers ProviderFetchError."""
    provider = IPONotifyProvider(api_key="test_key")
    dummy_req = httpx.Request("GET", "https://iponotify.me/api/ipo/open")
    
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_resp = httpx.Response(status_code=429, json={"error": "Too Many Requests"}, request=dummy_req)
        mock_get.return_value = mock_resp
        
        with pytest.raises(ProviderFetchError):
            await provider.fetch_with_retry()

@pytest.mark.asyncio
async def test_timeout_handling():
    """Verify timeout exception triggers ProviderFetchError."""
    provider = IPONotifyProvider(api_key="test_key")
    
    with patch.object(httpx.AsyncClient, "get", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(ProviderFetchError):
            await provider.fetch_with_retry()

def test_malformed_and_empty_records():
    """Verify malformed records are skipped cleanly while preserving valid items."""
    raw = [
        {"invalid": "data_no_symbol_or_search_id"},
        {
            "searchId": "valid-ipo",
            "companyName": "Valid IPO Ltd",
            "minPrice": 100,
            "maxPrice": 105
        }
    ]
    provider = IPONotifyProvider()
    dtos, errors = provider.parse_and_validate(raw)

    assert len(dtos) == 1
    assert dtos[0].symbol == "VALID"
    assert len(errors) == 1
    assert "Record [0]" in errors[0]

def test_empty_response():
    """Verify empty response array returns zero DTOs without errors."""
    provider = IPONotifyProvider()
    dtos, errors = provider.parse_and_validate([])
    assert len(dtos) == 0
    assert len(errors) == 0
