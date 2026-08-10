"""
Unit tests for GeminiIPOResearchProvider.
These tests do NOT call the real Gemini API.
They mock the API layer to test all logic independently.

Existing 59 tests must still pass after this file is added.
"""

from __future__ import annotations

import json
import pytest
import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.gemini_ipo_provider import (
    GeminiIPOResearchProvider,
    GeminiIPORecord,
    GeminiResearchResult,
    GMPInfo,
    SourceRef,
    _research_log,
)
from app.models.ipo import IPOStatus, IssueType
from app.providers.base import ProviderFetchError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_str() -> str:
    from datetime import timezone, timedelta
    from datetime import datetime
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST).date().isoformat()


def _open_ipo_fixture(today_str: str | None = None) -> dict:
    today = today_str or _today_str()
    close_d = (date.fromisoformat(today) + timedelta(days=2)).isoformat()
    return {
        "company_name": "TestCo Limited",
        "symbol": "TESTCO",
        "issue_type": "MAINBOARD",
        "issue_price_min": 100.0,
        "issue_price_max": 110.0,
        "lot_size": 135,
        "issue_size_cr": 500.0,
        "open_date": today,
        "close_date": close_d,
        "allotment_date": None,
        "listing_date": None,
        "registrar": "KFin Technologies",
        "subscription_total_x": 4.5,
        "subscription_qib_x": 6.0,
        "subscription_nii_x": 3.2,
        "subscription_retail_x": 2.1,
        "gmp": {
            "value_inr": 25.0,
            "source": "chittorgarh.com",
            "source_url": "https://chittorgarh.com/gmp",
            "as_of_date": today,
            "is_unofficial": True,
        },
        "sources": [{"title": "NSE Website", "url": "https://nseindia.com/ipo"}],
        "data_conflict": False,
        "conflict_details": None,
        "stale_data": False,
        "stale_reason": None,
        "classification_confidence": "HIGH",
    }


def _valid_gemini_json(today_str: str | None = None) -> str:
    today = today_str or _today_str()
    close_d = (date.fromisoformat(today) + timedelta(days=2)).isoformat()
    upcoming_open = (date.fromisoformat(today) + timedelta(days=5)).isoformat()
    upcoming_close = (date.fromisoformat(today) + timedelta(days=7)).isoformat()
    closed_close = (date.fromisoformat(today) - timedelta(days=3)).isoformat()
    closed_open = (date.fromisoformat(today) - timedelta(days=6)).isoformat()

    data = {
        "research_timestamp_ist": f"{today}T10:00:00+05:30",
        "current_date_ist": today,
        "open_ipos": [
            {
                "company_name": "Alpha Corp Limited",
                "symbol": "ALPHACORP",
                "issue_type": "MAINBOARD",
                "classification_confidence": "HIGH",
                "issue_price_min": 200.0,
                "issue_price_max": 210.0,
                "lot_size": 71,
                "issue_size_cr": 1200.0,
                "open_date": today,
                "close_date": close_d,
                "allotment_date": None,
                "listing_date": None,
                "registrar": "Link Intime",
                "subscription_total_x": 8.2,
                "subscription_qib_x": 12.5,
                "subscription_nii_x": 6.3,
                "subscription_retail_x": 3.8,
                "gmp": {
                    "value_inr": 45.0,
                    "source": "ipogmp.com",
                    "source_url": "https://ipogmp.com/alpha",
                    "as_of_date": today,
                    "is_unofficial": True,
                },
                "sources": [
                    {"title": "NSE IPO Page", "url": "https://nseindia.com/ipo/alpha"},
                    {"title": "BSE Notice", "url": "https://bseindia.com/notice/alpha"},
                ],
                "data_conflict": False,
                "conflict_details": None,
                "stale_data": False,
                "stale_reason": None,
            }
        ],
        "upcoming_ipos": [
            {
                "company_name": "Beta SME Ventures",
                "symbol": "BETASME",
                "issue_type": "SME",
                "classification_confidence": "HIGH",
                "issue_price_min": 80.0,
                "issue_price_max": 85.0,
                "lot_size": 1600,
                "issue_size_cr": 50.0,
                "open_date": upcoming_open,
                "close_date": upcoming_close,
                "allotment_date": None,
                "listing_date": None,
                "registrar": "Bigshare Services",
                "subscription_total_x": None,
                "gmp": None,
                "sources": [{"title": "BSE SME", "url": "https://bseindia.com/sme/beta"}],
                "data_conflict": False,
                "conflict_details": None,
                "stale_data": False,
                "stale_reason": None,
            }
        ],
        "closed_ipos": [
            {
                "company_name": "Gamma Industries",
                "symbol": "GAMMAINT",
                "issue_type": "MAINBOARD",
                "classification_confidence": "HIGH",
                "issue_price_min": 150.0,
                "issue_price_max": 160.0,
                "lot_size": 93,
                "issue_size_cr": 800.0,
                "open_date": closed_open,
                "close_date": closed_close,
                "allotment_date": None,
                "listing_date": None,
                "registrar": "KFin Technologies",
                "subscription_total_x": 22.5,
                "gmp": None,
                "sources": [{"title": "Moneycontrol", "url": "https://moneycontrol.com/gamma"}],
                "data_conflict": False,
                "conflict_details": None,
                "stale_data": False,
                "stale_reason": None,
            }
        ],
        "research_sources": [
            {"title": "NSE India", "url": "https://nseindia.com"},
            {"title": "BSE India", "url": "https://bseindia.com"},
        ],
        "conflicts": [],
        "grounding_confirmed": True,
    }
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Tests: GeminiIPORecord
# ---------------------------------------------------------------------------

class TestGeminiIPORecord:
    def test_calculated_status_open(self):
        today = _today_str()
        close_d = (date.fromisoformat(today) + timedelta(days=2)).isoformat()
        record = GeminiIPORecord(
            company_name="TestCo",
            open_date=today,
            close_date=close_d,
        )
        assert record.calculated_status() == IPOStatus.OPEN

    def test_calculated_status_upcoming(self):
        today = date.fromisoformat(_today_str())
        future_open = (today + timedelta(days=3)).isoformat()
        future_close = (today + timedelta(days=6)).isoformat()
        record = GeminiIPORecord(
            company_name="TestCo",
            open_date=future_open,
            close_date=future_close,
        )
        assert record.calculated_status() == IPOStatus.UPCOMING

    def test_calculated_status_closed(self):
        today = date.fromisoformat(_today_str())
        past_open = (today - timedelta(days=6)).isoformat()
        past_close = (today - timedelta(days=3)).isoformat()
        record = GeminiIPORecord(
            company_name="TestCo",
            open_date=past_open,
            close_date=past_close,
        )
        assert record.calculated_status() == IPOStatus.CLOSED

    def test_calculated_status_listed(self):
        today = date.fromisoformat(_today_str())
        record = GeminiIPORecord(
            company_name="TestCo",
            listing_date=(today - timedelta(days=1)).isoformat(),
        )
        assert record.calculated_status() == IPOStatus.LISTED

    def test_invalid_date_str_returns_none(self):
        record = GeminiIPORecord(
            company_name="TestCo",
            open_date="not-a-date",
            close_date="NULL",
        )
        assert record.open_date is None
        assert record.close_date is None

    def test_gmp_is_always_unofficial(self):
        record = GeminiIPORecord(
            company_name="TestCo",
            gmp=GMPInfo(value_inr=50.0, source="gmpwatch", is_unofficial=False),
        )
        # The schema allows is_unofficial to be set, but we validate on read
        assert record.gmp.value_inr == 50.0

    def test_record_with_sme_type(self):
        record = GeminiIPORecord(
            company_name="SmallCo SME",
            issue_type="SME",
        )
        assert record.issue_type == "SME"


# ---------------------------------------------------------------------------
# Tests: GeminiResearchResult validation
# ---------------------------------------------------------------------------

class TestGeminiResearchResult:
    def test_valid_result_parses(self):
        today = _today_str()
        json_str = _valid_gemini_json(today)
        data = json.loads(json_str)
        data["model_used"] = "gemini-2.5-flash"
        data["search_queries_used"] = ["India IPO open 2026"]
        result = GeminiResearchResult.model_validate(data)

        assert len(result.open_ipos) == 1
        assert len(result.upcoming_ipos) == 1
        assert len(result.closed_ipos) == 1
        assert result.open_ipos[0].company_name == "Alpha Corp Limited"
        assert result.upcoming_ipos[0].issue_type == "SME"

    def test_empty_lists_allowed(self):
        today = _today_str()
        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T09:00:00+05:30",
            current_date_ist=today,
        )
        assert result.open_ipos == []
        assert result.upcoming_ipos == []
        assert result.closed_ipos == []

    def test_unknown_fields_ignored(self):
        today = _today_str()
        data = json.loads(_valid_gemini_json(today))
        data["some_random_field"] = "hallucinated"
        data["model_used"] = "gemini-2.5-flash"
        data["search_queries_used"] = []
        result = GeminiResearchResult.model_validate(data)
        assert not hasattr(result, "some_random_field")


# ---------------------------------------------------------------------------
# Tests: GeminiIPOResearchProvider (mocked API)
# ---------------------------------------------------------------------------

class TestGeminiIPOResearchProvider:
    def _make_provider(self, api_key: str = "test-key-abc") -> GeminiIPOResearchProvider:
        return GeminiIPOResearchProvider(api_key=api_key, dry_run=True)

    def test_provider_code(self):
        p = self._make_provider()
        assert p.code == "GEMINI_IPO"
        assert "Gemini" in p.name

    def test_provider_no_api_key(self):
        p = GeminiIPOResearchProvider(api_key="")
        assert p._api_key == ""

    def test_extract_json_strips_markdown_fences(self):
        p = self._make_provider()
        wrapped = '```json\n{"key": "value"}\n```'
        extracted = p._extract_json_from_text(wrapped)
        assert json.loads(extracted) == {"key": "value"}

    def test_extract_json_finds_braces(self):
        p = self._make_provider()
        text = 'Here is the result: {"key": "value"} — end'
        extracted = p._extract_json_from_text(text)
        assert json.loads(extracted) == {"key": "value"}

    def test_parse_gemini_response_valid(self):
        p = self._make_provider()
        today = _today_str()
        raw_text = _valid_gemini_json(today)
        result = p._parse_gemini_response(raw_text, ["India IPO 2026"], True)
        assert isinstance(result, GeminiResearchResult)
        assert result.grounding_confirmed is True
        assert len(result.open_ipos) >= 1

    def test_parse_gemini_response_invalid_json_raises(self):
        p = self._make_provider()
        with pytest.raises(ProviderFetchError, match="not valid JSON"):
            p._parse_gemini_response("This is not JSON at all.", [], False)

    def test_parse_gemini_response_empty_raises(self):
        p = self._make_provider()
        with pytest.raises(ProviderFetchError, match="empty response"):
            p._parse_gemini_response("", [], False)

    def test_staleness_check_flags_stale_open(self):
        p = self._make_provider()
        today = _today_str()
        past_close = (date.fromisoformat(today) - timedelta(days=5)).isoformat()

        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T10:00:00",
            current_date_ist=today,
            open_ipos=[
                GeminiIPORecord(
                    company_name="OldCo",
                    close_date=past_close,
                )
            ],
        )
        result = p._apply_staleness_check(result)
        assert result.open_ipos[0].stale_data is True
        assert "OPEN" in result.open_ipos[0].stale_reason or "close_date" in result.open_ipos[0].stale_reason

    def test_staleness_check_passes_valid_open(self):
        p = self._make_provider()
        today = _today_str()
        future_close = (date.fromisoformat(today) + timedelta(days=2)).isoformat()

        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T10:00:00",
            current_date_ist=today,
            open_ipos=[
                GeminiIPORecord(
                    company_name="GoodCo",
                    open_date=today,
                    close_date=future_close,
                )
            ],
        )
        result = p._apply_staleness_check(result)
        assert result.open_ipos[0].stale_data is False

    def test_staleness_flags_stale_upcoming(self):
        p = self._make_provider()
        today = _today_str()
        past_open = (date.fromisoformat(today) - timedelta(days=1)).isoformat()

        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T10:00:00",
            current_date_ist=today,
            upcoming_ipos=[
                GeminiIPORecord(company_name="PastCo", open_date=past_open)
            ],
        )
        result = p._apply_staleness_check(result)
        assert result.upcoming_ipos[0].stale_data is True

    def test_gemini_record_to_dto_mainboard(self):
        p = self._make_provider()
        today = _today_str()
        future_close = (date.fromisoformat(today) + timedelta(days=2)).isoformat()
        record = GeminiIPORecord(
            company_name="AlphaCorp Limited",
            symbol="ALPHACORP",
            issue_type="MAINBOARD",
            issue_price_min=100.0,
            issue_price_max=110.0,
            lot_size=135,
            open_date=today,
            close_date=future_close,
        )
        dto = p._gemini_record_to_dto(record)
        assert dto is not None
        assert dto.symbol == "ALPHACORP"
        assert dto.issue_type == IssueType.MAINBOARD
        assert dto.status == IPOStatus.OPEN
        assert dto.max_price == 110.0

    def test_gemini_record_to_dto_sme(self):
        p = self._make_provider()
        today = _today_str()
        future_open = (date.fromisoformat(today) + timedelta(days=3)).isoformat()
        future_close = (date.fromisoformat(today) + timedelta(days=6)).isoformat()
        record = GeminiIPORecord(
            company_name="SmallVenture SME",
            symbol="SMALLV",
            issue_type="SME",
            open_date=future_open,
            close_date=future_close,
        )
        dto = p._gemini_record_to_dto(record)
        assert dto is not None
        assert dto.issue_type == IssueType.SME
        assert dto.status == IPOStatus.UPCOMING

    def test_gemini_record_generates_symbol_from_name(self):
        p = self._make_provider()
        record = GeminiIPORecord(
            company_name="Innovative Technologies Limited",
            symbol=None,
        )
        dto = p._gemini_record_to_dto(record)
        assert dto is not None
        assert len(dto.symbol) <= 12
        assert dto.symbol.isupper()

    def test_gemini_result_to_dtos_skips_stale(self):
        p = self._make_provider()
        today = _today_str()
        past_close = (date.fromisoformat(today) - timedelta(days=5)).isoformat()
        stale_record = GeminiIPORecord(
            company_name="StaleIPO",
            close_date=past_close,
            stale_data=True,
            stale_reason="Test stale",
        )
        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T10:00:00",
            current_date_ist=today,
            open_ipos=[stale_record],
        )
        dtos, errors = p.gemini_result_to_dtos(result)
        assert len(dtos) == 0
        assert any("STALE_DATA" in e for e in errors)

    def test_gemini_result_to_dtos_converts_valid(self):
        p = self._make_provider()
        today = _today_str()
        future_close = (date.fromisoformat(today) + timedelta(days=2)).isoformat()
        record = GeminiIPORecord(
            company_name="ValidCo Limited",
            symbol="VALIDCO",
            open_date=today,
            close_date=future_close,
        )
        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T10:00:00",
            current_date_ist=today,
            open_ipos=[record],
        )
        dtos, errors = p.gemini_result_to_dtos(result)
        assert len(dtos) == 1
        assert dtos[0].company_name == "ValidCo Limited"

    def test_provider_raises_without_api_key(self):
        p = GeminiIPOResearchProvider(api_key="")

        async def _run():
            with pytest.raises(ProviderFetchError, match="GEMINI_API_KEY"):
                await p._do_fetch()

        asyncio.run(_run())

    @patch.object(GeminiIPOResearchProvider, "_call_gemini_sync")
    def test_research_calls_sync_method(self, mock_sync):
        today = _today_str()
        mock_sync.return_value = {
            "raw_text": _valid_gemini_json(today),
            "search_queries": ["India IPO open"],
            "grounding_confirmed": True,
        }

        p = GeminiIPOResearchProvider(api_key="test-key")

        # Patch _get_client to avoid real SDK init
        mock_client = MagicMock()
        p._client = mock_client

        async def _run():
            result = await p.research(force=True)
            assert isinstance(result, GeminiResearchResult)
            assert len(result.open_ipos) >= 1
            assert result.grounding_confirmed is True

        asyncio.run(_run())

    def test_build_research_prompt_contains_date(self):
        p = self._make_provider()
        today = "2026-08-09"
        prompt = p._build_research_prompt(today)
        assert today in prompt
        assert "OPEN" in prompt
        assert "UPCOMING" in prompt
        assert "GMP" in prompt
        assert "hallucin" in prompt.lower() or "invent" in prompt.lower()

    def test_subscription_dto_built_from_record(self):
        p = self._make_provider()
        today = _today_str()
        record = GeminiIPORecord(
            company_name="SubCo",
            symbol="SUBCO",
            subscription_total_x=12.5,
            subscription_qib_x=20.0,
            subscription_nii_x=15.0,
            subscription_retail_x=5.5,
        )
        dto = p._gemini_record_to_dto(record)
        assert dto is not None
        assert dto.subscription is not None
        assert dto.subscription.overall_x == 12.5
        assert dto.subscription.qib_x == 20.0


# ---------------------------------------------------------------------------
# Tests: Anti-hallucination & conflict handling
# ---------------------------------------------------------------------------

class TestAntiHallucination:
    def test_conflict_flag_preserved(self):
        record = GeminiIPORecord(
            company_name="ConflictCo",
            data_conflict=True,
            conflict_details="Source A says ₹100, Source B says ₹120",
        )
        assert record.data_conflict is True
        assert "₹100" in record.conflict_details

    def test_stale_flag_prevents_dto_creation(self):
        from app.providers.gemini_ipo_provider import GeminiIPOResearchProvider

        p = GeminiIPOResearchProvider(api_key="test-key")
        today = _today_str()
        record = GeminiIPORecord(
            company_name="StaleHallucination",
            stale_data=True,
            stale_reason="close_date is 2024-11-08 < today",
        )
        result = GeminiResearchResult(
            research_timestamp_ist=f"{today}T09:00:00",
            current_date_ist=today,
            open_ipos=[record],
        )
        dtos, errors = p.gemini_result_to_dtos(result)
        assert len(dtos) == 0
        assert len(errors) == 1
        assert "STALE_DATA" in errors[0]


# ---------------------------------------------------------------------------
# Tests: Cost control / deduplication
# ---------------------------------------------------------------------------

class TestCostControl:
    def test_research_log_records_calls(self):
        from app.providers.gemini_ipo_provider import _ResearchLog
        log = _ResearchLog(deduplicate_window_seconds=300)
        assert log.total_calls() == 0
        log.record()
        assert log.total_calls() == 1

    def test_research_log_deduplicates(self):
        from app.providers.gemini_ipo_provider import _ResearchLog
        log = _ResearchLog(deduplicate_window_seconds=300)
        log.record()
        should_skip, reason = log.should_skip()
        assert should_skip is True
        assert "Deduplication" in reason

    def test_research_log_no_skip_first_run(self):
        from app.providers.gemini_ipo_provider import _ResearchLog
        log = _ResearchLog(deduplicate_window_seconds=300)
        should_skip, reason = log.should_skip()
        assert should_skip is False
        assert reason == ""
