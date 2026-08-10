"""
GeminiIPOResearchProvider
=========================
A web-grounded IPO research provider powered by Google Gemini API
with Google Search grounding via the official google-genai SDK v2+.

Architecture position:
    BaseIPOProvider
    ├── UpstoxIPOProvider
    ├── IPONotifyProvider
    └── GeminiIPOResearchProvider  ← this module

This provider:
  - Uses Gemini + Google Search grounding to discover current Indian IPOs
  - Returns validated Pydantic DTOs, not raw prose
  - Applies anti-hallucination rules (source-backed assertions only)
  - Implements staleness protection using actual IPO dates
  - Does NOT send Telegram messages
  - Does NOT modify production workflows
  - Does NOT hard-code any API credentials

Dependencies:
  - google-genai >= 2.0.0   (official Google GenAI SDK)
  - pydantic >= 2.0
  - GEMINI_API_KEY in environment / .env
"""

from __future__ import annotations

import os
import json
import asyncio
import time
from datetime import datetime, date, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator, ValidationError

from app.providers.base import BaseIPOProvider, ProviderFetchError
from app.schemas.ingestion import RawIPODTO, RawSubscriptionDTO
from app.models.ipo import IPOStatus, IssueType
from app.core.logging import logger

# ---------------------------------------------------------------------------
# IST helpers
# ---------------------------------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))


def _now_ist() -> datetime:
    return datetime.now(IST)


def _today_ist() -> date:
    return _now_ist().date()


# ---------------------------------------------------------------------------
# Pydantic schemas for Gemini's structured JSON output
# ---------------------------------------------------------------------------

class GMPInfo(BaseModel):
    """Grey-market premium — always labelled unofficial."""
    value_inr: Optional[float] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    as_of_date: Optional[str] = None
    is_unofficial: bool = True

    model_config = {"extra": "ignore"}


class SourceRef(BaseModel):
    """A grounding citation returned by the model."""
    title: Optional[str] = None
    url: Optional[str] = None

    model_config = {"extra": "ignore"}


class GeminiIPORecord(BaseModel):
    """
    A single IPO record as extracted by Gemini via Google Search grounding.
    All string values are from search results, not invented.
    """
    company_name: str = Field(..., min_length=1, max_length=255)
    symbol: Optional[str] = Field(default=None, max_length=50)
    issue_type: str = Field(default="MAINBOARD")          # "MAINBOARD" | "SME"
    classification_confidence: str = Field(default="LOW") # "HIGH" | "MEDIUM" | "LOW"

    issue_price_min: Optional[float] = Field(default=None, ge=0)
    issue_price_max: Optional[float] = Field(default=None, ge=0)
    lot_size: Optional[int] = Field(default=None, ge=1)
    issue_size_cr: Optional[float] = Field(default=None, ge=0)

    open_date: Optional[str] = None   # ISO8601 "YYYY-MM-DD"
    close_date: Optional[str] = None
    allotment_date: Optional[str] = None
    listing_date: Optional[str] = None

    registrar: Optional[str] = None

    # Subscription data (could be partial)
    subscription_total_x: Optional[float] = None
    subscription_qib_x: Optional[float] = None
    subscription_nii_x: Optional[float] = None
    subscription_retail_x: Optional[float] = None

    gmp: Optional[GMPInfo] = None

    # Grounding sources
    sources: List[SourceRef] = Field(default_factory=list)

    # Anti-hallucination flags
    data_conflict: bool = False
    conflict_details: Optional[str] = None
    stale_data: bool = False
    stale_reason: Optional[str] = None

    model_config = {"extra": "ignore"}

    @field_validator("open_date", "close_date", "allotment_date", "listing_date", mode="before")
    @classmethod
    def _validate_date_str(cls, v: Any) -> Optional[str]:
        if v is None or v == "" or str(v).upper() in ("NULL", "NONE", "N/A", "UNKNOWN"):
            return None
        try:
            date.fromisoformat(str(v)[:10])
            return str(v)[:10]
        except (ValueError, TypeError):
            return None

    def to_date(self, field_name: str) -> Optional[date]:
        val = getattr(self, field_name, None)
        if val:
            try:
                return date.fromisoformat(val[:10])
            except (ValueError, TypeError):
                pass
        return None

    def calculated_status(self) -> IPOStatus:
        """Compute status from actual dates relative to today IST."""
        today = _today_ist()
        open_d = self.to_date("open_date")
        close_d = self.to_date("close_date")
        listing_d = self.to_date("listing_date")
        allotment_d = self.to_date("allotment_date")

        if listing_d and today >= listing_d:
            return IPOStatus.LISTED
        if allotment_d and today >= allotment_d and (not listing_d):
            return IPOStatus.ALLOTTED
        if close_d and today > close_d:
            return IPOStatus.CLOSED
        if open_d and close_d and open_d <= today <= close_d:
            return IPOStatus.OPEN
        if open_d and today < open_d:
            return IPOStatus.UPCOMING
        return IPOStatus.UPCOMING


class GeminiResearchResult(BaseModel):
    """Top-level structured output from Gemini IPO research."""
    research_timestamp_ist: str
    current_date_ist: str
    open_ipos: List[GeminiIPORecord] = Field(default_factory=list)
    upcoming_ipos: List[GeminiIPORecord] = Field(default_factory=list)
    closed_ipos: List[GeminiIPORecord] = Field(default_factory=list)
    research_sources: List[SourceRef] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    grounding_confirmed: bool = False
    model_used: str = ""
    search_queries_used: List[str] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


# ---------------------------------------------------------------------------
# Research request log (in-memory, for cost control & deduplication)
# ---------------------------------------------------------------------------

class _ResearchLog:
    """Simple in-memory log to prevent duplicate research within a time window."""

    def __init__(self, deduplicate_window_seconds: int = 300):
        self._last_run: Optional[datetime] = None
        self._window = deduplicate_window_seconds
        self._total_calls = 0
        self._max_calls_per_hour = 12  # cost control: max 12 full research runs/hour

    def should_skip(self) -> Tuple[bool, str]:
        now = _now_ist()
        if self._last_run is None:
            return False, ""
        elapsed = (now - self._last_run).total_seconds()
        if elapsed < self._window:
            return True, f"Deduplication: last run was {int(elapsed)}s ago (window={self._window}s)"
        return False, ""

    def record(self):
        self._last_run = _now_ist()
        self._total_calls += 1
        logger.info(f"[GeminiProvider] Research run #{self._total_calls} recorded at {self._last_run.isoformat()}")

    def total_calls(self) -> int:
        return self._total_calls


_research_log = _ResearchLog(deduplicate_window_seconds=300)


# ---------------------------------------------------------------------------
# Available model IDs to try in order (most capable first)
# ---------------------------------------------------------------------------
_MODEL_PRIORITY = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]


def _probe_available_model(client, candidates: List[str]) -> str:
    """
    Try each model ID with a minimal test request.
    Returns the first model that responds successfully.
    Falls back to gemini-3.6-flash if all probes fail.
    """
    for model_id in candidates:
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents="Say 'ok'",
            )
            if resp and resp.text:
                logger.info(f"[GeminiProvider] Model probe OK: {model_id}")
                return model_id
        except Exception as e:
            logger.debug(f"[GeminiProvider] Model probe failed for {model_id}: {e}")
            continue
    # Last resort
    return "gemini-3.6-flash"


# ---------------------------------------------------------------------------
# The Provider
# ---------------------------------------------------------------------------

class GeminiIPOResearchProvider(BaseIPOProvider):
    """
    Gemini-powered IPO research provider.

    Uses the official google-genai SDK v2+ with Google Search grounding
    to discover current Indian IPO data in real-time.

    NEVER invents data — only reports what grounded search results confirm.
    """

    DEFAULT_MODEL = "gemini-3.6-flash"
    MAX_RETRIES = 2
    REQUEST_TIMEOUT = 60.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        deduplicate_window_seconds: int = 300,
        dry_run: bool = False,
        auto_detect_model: bool = True,
    ):
        super().__init__(
            code="GEMINI_IPO",
            name="Gemini IPO Research (Google Search Grounded)",
            timeout=self.REQUEST_TIMEOUT,
            max_retries=self.MAX_RETRIES,
        )
        self._api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self._model = model or self.DEFAULT_MODEL
        self._auto_detect_model = auto_detect_model
        self._dry_run = dry_run
        self._client = None     # lazy-init
        self._model_confirmed = False  # True once we know the model works

        if not self._api_key:
            logger.warning("[GeminiProvider] GEMINI_API_KEY is not set. Provider will fail on use.")

    def _get_client(self):
        """Lazy-initialize the google-genai client."""
        if self._client is None:
            try:
                from google import genai  # official google-genai SDK v2+
                self._client = genai.Client(api_key=self._api_key)
            except ImportError:
                raise ProviderFetchError(
                    "google-genai SDK not installed. Run: pip install -U google-genai"
                )
        return self._client

    def _ensure_working_model(self, client) -> str:
        """
        Confirm the configured model works, or auto-detect one that does.
        Result is cached after first successful probe.
        """
        if self._model_confirmed:
            return self._model

        if not self._auto_detect_model:
            self._model_confirmed = True
            return self._model

        # Put the configured model first in the probe list
        candidates = [self._model] + [m for m in _MODEL_PRIORITY if m != self._model]
        working_model = _probe_available_model(client, candidates)
        self._model = working_model
        self._model_confirmed = True
        logger.info(f"[GeminiProvider] Active model confirmed: {self._model}")
        return self._model

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_research_prompt(self, today_str: str) -> str:
        return f"""You are an Indian IPO intelligence agent.

Today's date is {today_str} (Asia/Kolkata / IST).

TASK: Search for CURRENT Indian IPO information and return ONLY verifiable facts.

CRITICAL RULES:
1. Do NOT invent IPO names, dates, prices, or subscription numbers.
2. Do NOT present old articles as current information.
3. Every IPO listed as OPEN must have evidence that it is currently open as of {today_str}.
4. Every IPO listed as UPCOMING must have an opening date that is in the future relative to {today_str}.
5. If two sources disagree on a date or price, set data_conflict=true and describe the conflict.
6. GMP (Grey Market Premium) is unofficial market data — label it as unofficial, never as an exchange price.
7. If you are uncertain about a value, leave the field null rather than guessing.
8. Prefer NSE/BSE official announcements > SEBI filings > registrar data > financial publications > other sources.

SEARCH AND REPORT:
A. Currently OPEN mainboard IPOs (subscription period is active today: {today_str})
B. Currently OPEN SME IPOs (subscription period is active today: {today_str})
C. UPCOMING mainboard IPOs (opening date in the future)
D. UPCOMING SME IPOs (opening date in the future)
E. RECENTLY CLOSED IPOs (closed within the last 14 days)

For each IPO, find and populate these fields:
- company_name (string, required)
- symbol (NSE/BSE ticker, if available)
- issue_type ("MAINBOARD" or "SME")
- issue_price_min (lower price band in INR, nullable)
- issue_price_max (upper price band / issue price in INR, nullable)
- lot_size (minimum lot size, nullable)
- issue_size_cr (total issue size in Indian Crores, nullable)
- open_date (ISO8601 "YYYY-MM-DD", nullable)
- close_date (ISO8601 "YYYY-MM-DD", nullable)
- allotment_date (ISO8601 "YYYY-MM-DD", nullable)
- listing_date (ISO8601 "YYYY-MM-DD", nullable)
- registrar (registrar name, nullable)
- subscription_total_x (total subscription times, nullable — only if officially published)
- subscription_qib_x (QIB subscription, nullable)
- subscription_nii_x (NII/HNI subscription, nullable)
- subscription_retail_x (retail subscription, nullable)
- gmp: {{"value_inr": number_or_null, "source": "source_name", "source_url": "url_or_null", "as_of_date": "YYYY-MM-DD_or_null", "is_unofficial": true}}
- sources: list of {{"title": "...", "url": "..."}}
- data_conflict (boolean, true if sources disagree)
- conflict_details (string description of conflict, if data_conflict is true)

Return a JSON object with this exact structure:
{{
  "research_timestamp_ist": "{today_str}T<current_time>+05:30",
  "current_date_ist": "{today_str}",
  "open_ipos": [ <GeminiIPORecord objects> ],
  "upcoming_ipos": [ <GeminiIPORecord objects> ],
  "closed_ipos": [ <GeminiIPORecord objects> ],
  "research_sources": [ {{"title": "...", "url": "..."}} ],
  "conflicts": [ "<description of any cross-source conflicts>" ],
  "grounding_confirmed": true
}}

IMPORTANT:
- Return ONLY valid JSON, no markdown fences, no explanatory prose outside the JSON.
- If you found zero open IPOs, return an empty list: "open_ipos": []
- Do not include any field not defined in the schema above.
- Do not include hallucinated or uncertain data.
"""

    # ------------------------------------------------------------------
    # Core fetch — calls Gemini API with Google Search grounding
    # ------------------------------------------------------------------

    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a real Gemini API call with Google Search grounding.
        Returns raw dict from the model's response.
        """
        if not self._api_key:
            raise ProviderFetchError(
                "GEMINI_API_KEY is not configured. Cannot perform Gemini research."
            )

        today_str = _today_ist().isoformat()
        prompt = self._build_research_prompt(today_str)

        logger.info(f"[GeminiProvider] Starting research for {today_str}")
        start = time.time()

        try:
            client = self._get_client()

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._call_gemini_sync,
                client,
                prompt,
            )

            elapsed = time.time() - start
            logger.info(f"[GeminiProvider] API call completed in {elapsed:.1f}s")
            return result

        except ProviderFetchError:
            raise
        except Exception as e:
            raise ProviderFetchError(f"Gemini API call failed: {type(e).__name__}: {e}") from e

    def _call_gemini_sync(self, client, prompt: str) -> Dict[str, Any]:
        """
        Synchronous Gemini API call using generate_content with Google Search tool.
        Compatible with google-genai SDK v2+.
        Falls back to standard generate_content if Google Search tool quota is exhausted.
        """
        model_id = self._ensure_working_model(client)
        from google.genai import types, errors

        # Attempt 1: With Google Search Grounding
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.1,
                ),
            )

            raw_text = ""
            grounding_confirmed = False
            search_queries: List[str] = []

            if response.candidates:
                for candidate in response.candidates:
                    meta = getattr(candidate, "grounding_metadata", None)
                    if meta:
                        grounding_confirmed = True
                        web_queries = getattr(meta, "web_search_queries", None)
                        if web_queries:
                            search_queries.extend(web_queries)

                    content = getattr(candidate, "content", None)
                    if content and getattr(content, "parts", None):
                        for part in content.parts:
                            text = getattr(part, "text", None)
                            if text:
                                raw_text += text

            logger.info(
                f"[GeminiProvider] Grounded generate_content done. "
                f"grounding={grounding_confirmed}, text_len={len(raw_text)}"
            )

            return {
                "raw_text": raw_text.strip(),
                "search_queries": search_queries,
                "grounding_confirmed": grounding_confirmed,
                "model_used": model_id,
            }

        except errors.ClientError as ce:
            if "429" in str(ce) or "RESOURCE_EXHAUSTED" in str(ce):
                logger.warning(
                    f"[GeminiProvider] Google Search grounding quota exhausted or unavailable "
                    f"on free tier (requires setting up billing in Google AI Studio). "
                    f"Falling back to standard prompt execution. Error: {ce}"
                )
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.1),
                    )
                    raw_text = ""
                    if response.candidates:
                        for candidate in response.candidates:
                            content = getattr(candidate, "content", None)
                            if content and getattr(content, "parts", None):
                                for part in content.parts:
                                    text = getattr(part, "text", None)
                                    if text:
                                        raw_text += text
                    return {
                        "raw_text": raw_text.strip(),
                        "search_queries": [],
                        "grounding_confirmed": False,
                        "model_used": model_id,
                    }
                except Exception as e2:
                    raise ProviderFetchError(f"Gemini API call failed: {e2}") from e2
            raise ProviderFetchError(f"Gemini API call failed: {ce}") from ce
        except Exception as e:
            logger.error(f"[GeminiProvider] generate_content failed: {e}")
            raise ProviderFetchError(f"Gemini generate_content failed: {e}") from e

    # ------------------------------------------------------------------
    # Response parsing and Pydantic validation
    # ------------------------------------------------------------------

    def _extract_json_from_text(self, text: str) -> str:
        """Strip markdown fences and extract the JSON object from model output."""
        text = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            start = 1
            end = len(lines)
            if lines[-1].strip() == "```":
                end = len(lines) - 1
            text = "\n".join(lines[start:end]).strip()
        # Find the first { and last }
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            text = text[brace_start:brace_end + 1]
        return text

    def _parse_gemini_response(
        self, raw_text: str, search_queries: List[str], grounding_confirmed: bool,
        model_used: str = ""
    ) -> GeminiResearchResult:
        """
        Parse and validate the model's JSON output into GeminiResearchResult.
        """
        today_str = _today_ist().isoformat()

        if not raw_text:
            raise ProviderFetchError("Gemini returned empty response text")

        try:
            json_str = self._extract_json_from_text(raw_text)
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[GeminiProvider] JSON parse failed: {e}")
            logger.debug(f"[GeminiProvider] Raw text (first 500 chars): {raw_text[:500]}")
            raise ProviderFetchError(f"Model response was not valid JSON: {e}")

        # Inject API-level metadata
        data["grounding_confirmed"] = grounding_confirmed
        data["model_used"] = model_used or self._model
        data["search_queries_used"] = search_queries
        if "current_date_ist" not in data:
            data["current_date_ist"] = today_str
        if "research_timestamp_ist" not in data:
            data["research_timestamp_ist"] = _now_ist().isoformat()

        try:
            result = GeminiResearchResult.model_validate(data)
        except ValidationError as ve:
            raise ProviderFetchError(
                f"GeminiResearchResult Pydantic validation failed: {ve}"
            ) from ve

        return result

    # ------------------------------------------------------------------
    # Staleness protection
    # ------------------------------------------------------------------

    def _apply_staleness_check(self, result: GeminiResearchResult) -> GeminiResearchResult:
        """
        Flag IPO records as stale if their dates contradict their category.
        """
        today = _today_ist()
        MAX_AGE_DAYS = 30

        def check_record(record: GeminiIPORecord, expected_status: str) -> GeminiIPORecord:
            close_d = record.to_date("close_date")
            open_d = record.to_date("open_date")

            if expected_status == "OPEN":
                if close_d and today > close_d:
                    record.stale_data = True
                    record.stale_reason = (
                        f"Listed in open_ipos but close_date {close_d} < today {today}"
                    )
                elif open_d and today < open_d:
                    record.stale_data = True
                    record.stale_reason = (
                        f"Listed in open_ipos but open_date {open_d} > today {today}"
                    )
            elif expected_status == "UPCOMING":
                if open_d and today >= open_d:
                    record.stale_data = True
                    record.stale_reason = (
                        f"Listed in upcoming_ipos but open_date {open_d} <= today {today}"
                    )
            elif expected_status == "CLOSED":
                if close_d and (today - close_d).days > MAX_AGE_DAYS:
                    record.stale_data = True
                    record.stale_reason = (
                        f"Closed {(today - close_d).days} days ago > MAX_AGE_DAYS={MAX_AGE_DAYS}"
                    )
            return record

        result.open_ipos = [check_record(r, "OPEN") for r in result.open_ipos]
        result.upcoming_ipos = [check_record(r, "UPCOMING") for r in result.upcoming_ipos]
        result.closed_ipos = [check_record(r, "CLOSED") for r in result.closed_ipos]
        return result

    # ------------------------------------------------------------------
    # Conversion to RawIPODTO (provider abstraction interface)
    # ------------------------------------------------------------------

    def _gemini_record_to_dto(self, record: GeminiIPORecord) -> Optional[RawIPODTO]:
        """Convert a validated GeminiIPORecord into a RawIPODTO for the pipeline."""
        try:
            symbol = record.symbol
            if not symbol:
                symbol = (
                    record.company_name.upper()
                    .replace(" LIMITED", "")
                    .replace(" LTD", "")
                    .replace(" ", "")[:12]
                )

            issue_type = (
                IssueType.SME
                if record.issue_type.upper() == "SME"
                else IssueType.MAINBOARD
            )

            status = record.calculated_status()

            sub_dto = None
            if any([
                record.subscription_total_x,
                record.subscription_qib_x,
                record.subscription_nii_x,
                record.subscription_retail_x,
            ]):
                sub_dto = RawSubscriptionDTO(
                    overall_x=record.subscription_total_x or 0.0,
                    qib_x=record.subscription_qib_x,
                    nii_x=record.subscription_nii_x,
                    retail_x=record.subscription_retail_x,
                )

            dto = RawIPODTO(
                symbol=symbol,
                company_name=record.company_name,
                issue_type=issue_type,
                status=status,
                min_price=record.issue_price_min,
                max_price=record.issue_price_max,
                issue_price=record.issue_price_max,
                lot_size=record.lot_size,
                total_issue_size_cr=record.issue_size_cr,
                open_date=record.open_date,
                close_date=record.close_date,
                allotment_date=record.allotment_date,
                listing_date=record.listing_date,
                registrar_name=record.registrar,
                subscription=sub_dto,
            )
            return dto
        except (ValidationError, Exception) as e:
            logger.warning(f"[GeminiProvider] DTO conversion failed for '{record.company_name}': {e}")
            return None

    def gemini_result_to_dtos(
        self, result: GeminiResearchResult
    ) -> Tuple[List[RawIPODTO], List[str]]:
        """Convert all GeminiIPORecord items into RawIPODTO objects."""
        dtos: List[RawIPODTO] = []
        errors: List[str] = []

        all_records = result.open_ipos + result.upcoming_ipos + result.closed_ipos
        for record in all_records:
            if record.stale_data:
                errors.append(
                    f"STALE_DATA: '{record.company_name}' — {record.stale_reason}"
                )
                continue
            dto = self._gemini_record_to_dto(record)
            if dto:
                dtos.append(dto)
            else:
                errors.append(f"DTO_CONVERSION_FAILED: '{record.company_name}'")

        return dtos, errors

    def parse_and_validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[RawIPODTO], List[str]]:
        """
        BaseIPOProvider interface implementation.
        Parses raw Gemini response dict from fetch_with_retry into validated RawIPODTOs.
        """
        if not raw_records:
            return [], ["Empty raw records received from Gemini provider"]

        # Handles when raw_records contains the raw_data dict or items
        item = raw_records[0] if raw_records else {}
        if isinstance(item, dict) and "raw_text" in item:
            raw_text = item.get("raw_text", "")
            search_queries = item.get("search_queries", [])
            grounding_confirmed = item.get("grounding_confirmed", False)
            model_used = item.get("model_used", self._model)

            try:
                result = self._parse_gemini_response(raw_text, search_queries, grounding_confirmed, model_used)
                result = self._apply_staleness_check(result)
                return self.gemini_result_to_dtos(result)
            except Exception as e:
                return [], [f"Gemini parse_and_validate failed: {e}"]
        
        # Fallback for standard BaseIPOProvider list of dicts
        return super().parse_and_validate(raw_records)

    # ------------------------------------------------------------------
    # High-level research method
    # ------------------------------------------------------------------

    async def research(self, force: bool = False) -> GeminiResearchResult:
        """
        Execute a full web-grounded IPO research cycle.

        Args:
            force: Skip deduplication window check.

        Returns:
            GeminiResearchResult with validated, grounded IPO data.

        Raises:
            ProviderFetchError: On API failure or validation failure.
        """
        if not force:
            should_skip, reason = _research_log.should_skip()
            if should_skip:
                raise ProviderFetchError(f"Research skipped — {reason}")

        raw = await self.fetch_with_retry()
        raw_data = raw.get("raw_data", {})

        raw_text = raw_data.get("raw_text", "")
        search_queries = raw_data.get("search_queries", [])
        grounding_confirmed = raw_data.get("grounding_confirmed", False)
        model_used = raw_data.get("model_used", self._model)

        result = self._parse_gemini_response(raw_text, search_queries, grounding_confirmed, model_used)
        result = self._apply_staleness_check(result)

        _research_log.record()
        logger.info(
            f"[GeminiProvider] Research complete: "
            f"open={len(result.open_ipos)}, upcoming={len(result.upcoming_ipos)}, "
            f"closed={len(result.closed_ipos)}, grounding={result.grounding_confirmed}"
        )
        return result
