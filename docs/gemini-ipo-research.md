# Gemini IPO Research Engine

## Overview

The Gemini IPO Research Provider is a web-grounded IPO data acquisition engine powered by the **Google Gemini API** with **Google Search grounding**. It discovers current Indian IPO information in real-time by searching the live web — not from a fixed dataset or internal knowledge alone.

It sits alongside the existing providers in the provider abstraction layer:

```
BaseIPOProvider
├── UpstoxIPOProvider
├── IPONotifyProvider
└── GeminiIPOResearchProvider   ← this component
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | **Yes** | Your Google AI Studio API key |
| `GEMINI_MODEL` | No | Override model (default: `gemini-2.5-flash`) |

Set in `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

> [!CAUTION]
> Never hard-code the API key. Never log it. Never send it to Telegram. Never commit it to Git.

### Obtaining an API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Add it to `.env`

---

## Model Used

**Default**: `gemini-2.5-flash`

This model supports:
- Google Search grounding (live web retrieval)
- Structured JSON output
- Long context for multi-source research

To override the model, pass `model=` to the provider constructor:

```python
provider = GeminiIPOResearchProvider(api_key=key, model="gemini-2.5-pro")
```

---

## Google Search Grounding

Grounding is activated using the official `google_search` tool via the Interactions API:

```python
interaction = client.interactions.create(
    model="gemini-2.5-flash",
    input=prompt,
    tools=[{"type": "google_search"}],
)
```

When grounding is active:
- Gemini automatically issues Google Search queries
- The model cites URL sources in its response
- The `grounding_confirmed` flag is set in `GeminiResearchResult`
- All executed search queries are logged

> [!IMPORTANT]
> If `grounding_confirmed` is `False` in the result, the model returned information from its training data only. This reduces reliability for current IPO data.

---

## Research Methodology

The research cycle:

1. **Prompt construction** — A structured prompt is built with today's IST date embedded. The prompt instructs the model to only report verifiable, current data.

2. **Web-grounded search** — Gemini executes Google Search queries such as:
   - `"India IPO open August 2026"`
   - `"NSE BSE IPO subscription live today"`
   - `"upcoming mainboard SME IPO India"`

3. **Structured extraction** — The model is required to return a JSON object matching the `GeminiResearchResult` schema.

4. **Pydantic validation** — The JSON is validated against the schema. Invalid responses trigger one retry. If both attempts fail, the research run is marked `FAILED`.

5. **Staleness check** — Each IPO record's dates are checked against the current IST date. Records with inconsistent dates are flagged `STALE_DATA`.

6. **DTO conversion** — Valid records are converted to `RawIPODTO` for the standard pipeline.

---

## Source Hierarchy

The prompt instructs Gemini to prefer sources in this order:

| Priority | Source |
|---|---|
| 1 | NSE / BSE official exchange pages |
| 2 | SEBI / company official filings |
| 3 | Registrar information (Link Intime, KFin, Bigshare, etc.) |
| 4 | Reputable financial publications (Moneycontrol, Economic Times, Livemint) |
| 5 | Established IPO data platforms (Chittorgarh, IPO Watch) |
| 6 | Other sources (only when necessary) |

> [!NOTE]
> GMP (Grey Market Premium) data is always sourced from unofficial grey-market platforms. It is clearly labelled as unofficial in the `GMPInfo.is_unofficial = True` field and must never be presented as an exchange-official price.

---

## JSON Schema

### `GeminiResearchResult`

```json
{
  "research_timestamp_ist": "2026-08-09T10:30:00+05:30",
  "current_date_ist": "2026-08-09",
  "open_ipos": [ <GeminiIPORecord> ],
  "upcoming_ipos": [ <GeminiIPORecord> ],
  "closed_ipos": [ <GeminiIPORecord> ],
  "research_sources": [ <SourceRef> ],
  "conflicts": [ "description string" ],
  "grounding_confirmed": true,
  "model_used": "gemini-2.5-flash",
  "search_queries_used": [ "India IPO open August 2026" ]
}
```

### `GeminiIPORecord`

```json
{
  "company_name": "Alpha Corp Limited",
  "symbol": "ALPHACORP",
  "issue_type": "MAINBOARD",
  "classification_confidence": "HIGH",
  "issue_price_min": 200.0,
  "issue_price_max": 210.0,
  "lot_size": 71,
  "issue_size_cr": 1200.0,
  "open_date": "2026-08-09",
  "close_date": "2026-08-12",
  "allotment_date": "2026-08-14",
  "listing_date": "2026-08-18",
  "registrar": "Link Intime India",
  "subscription_total_x": 8.2,
  "subscription_qib_x": 12.5,
  "subscription_nii_x": 6.3,
  "subscription_retail_x": 3.8,
  "gmp": {
    "value_inr": 45.0,
    "source": "ipogmp.com",
    "source_url": "https://ipogmp.com/alpha",
    "as_of_date": "2026-08-09",
    "is_unofficial": true
  },
  "sources": [
    { "title": "NSE IPO Page", "url": "https://nseindia.com/ipo/alpha" }
  ],
  "data_conflict": false,
  "conflict_details": null,
  "stale_data": false,
  "stale_reason": null
}
```

### `SourceRef`

```json
{ "title": "NSE India", "url": "https://nseindia.com" }
```

---

## Pydantic Validation

All model output is validated through strict Pydantic models:

- `GeminiResearchResult` — top-level result
- `GeminiIPORecord` — per-IPO record
- `GMPInfo` — grey-market premium data
- `SourceRef` — citation reference

If validation fails:
1. **Retry once** with correction
2. If still invalid → raise `ProviderFetchError`
3. Invalid data is **never written to PostgreSQL**

Date fields use a custom validator that accepts ISO 8601 strings and rejects strings like `"NULL"`, `"N/A"`, `"UNKNOWN"`.

---

## Retry Logic

| Scenario | Behavior |
|---|---|
| Network timeout | Retried by `BaseIPOProvider.fetch_with_retry` (3 attempts, exponential backoff) |
| Gemini API error | Retried by `fetch_with_retry` |
| Invalid JSON output | Retried once with a correction prompt (internal to provider) |
| `GEMINI_API_KEY` missing | Immediately raises `ProviderFetchError` — no retries |

---

## Stale Data Detection

After every research cycle, `_apply_staleness_check()` validates each record:

| Record Category | Stale Condition |
|---|---|
| `open_ipos` | `close_date < today` OR `open_date > today` |
| `upcoming_ipos` | `open_date <= today` |
| `closed_ipos` | `close_date < today - 30 days` |

Stale records are:
- Flagged with `stale_data = True` and `stale_reason` describing the conflict
- **Excluded from DTO conversion** (`gemini_result_to_dtos()`)
- Logged as errors in the sync result

---

## Cost Control Strategy

| Control | Setting |
|---|---|
| Deduplication window | 5 minutes (300 seconds) |
| Max calls per hour | 12 |
| Retry limit | 2 attempts per research run |
| Search query logging | All queries logged at INFO level |

The `_ResearchLog` class tracks the last run timestamp. Calling `research()` within the deduplication window returns a `ProviderFetchError` unless `force=True` is passed.

> [!TIP]
> Use `force=True` only for explicit test/debug runs. Normal production use should rely on the deduplication window.

---

## Limitations

1. **Grounding is not guaranteed** — If Google Search returns no results for a query, `grounding_confirmed` may be `False`.
2. **GMP data may be delayed** — Grey-market data is scraped from unofficial sources; it lags real-time by hours.
3. **SME IPO coverage** — SME IPOs are smaller and may not appear in mainstream financial press; coverage may be less complete than mainboard IPOs.
4. **Subscription data timing** — Real-time subscription figures are only available after day 1 of the subscription period.
5. **Not a financial data API** — This provider is for research and intelligence, not trading infrastructure. All figures must be verified before use in financial decisions.
6. **Billing** — Each Google Search executed by the model incurs a billable event. Multiple queries per prompt are possible and each is billed separately.

---

## Safe Test Mode

To run a test without modifying production:

```powershell
cd c:\IPO-BOT
python scripts/test_gemini_research.py
```

This will:
- ✅ Call the real Gemini API
- ✅ Use Google Search grounding
- ✅ Validate the response
- ✅ Print a structured report
- ❌ NOT write to PostgreSQL
- ❌ NOT send Telegram messages
- ❌ NOT activate n8n workflows

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   GeminiIPOResearchProvider                      │
│                                                                  │
│  1. _build_research_prompt(today_IST)                           │
│        ↓                                                         │
│  2. client.interactions.create(model, prompt,                   │
│           tools=[{"type": "google_search"}])                    │
│        ↓                                                         │
│  3. Google Search queries executed automatically                 │
│     (e.g. "India open IPO August 2026")                        │
│        ↓                                                         │
│  4. Model synthesizes grounded response → raw JSON text         │
│        ↓                                                         │
│  5. _parse_gemini_response() → Pydantic validation              │
│        ↓                                                         │
│  6. _apply_staleness_check() → flag inconsistent records        │
│        ↓                                                         │
│  7. GeminiResearchResult returned                                │
│        ↓                                                         │
│  8. gemini_result_to_dtos() → RawIPODTO[] for pipeline          │
└─────────────────────────────────────────────────────────────────┘
         ↓
┌────────────────────┐
│   IPOSyncService   │  (same pipeline as other providers)
│   → PostgreSQL DB  │
└────────────────────┘
```

---

## Files

| File | Purpose |
|---|---|
| `app/providers/gemini_ipo_provider.py` | Provider implementation |
| `app/providers/__init__.py` | Exports `GeminiIPOResearchProvider` |
| `scripts/test_gemini_research.py` | Safe test mode runner |
| `tests/test_gemini_provider.py` | Unit tests (all mocked) |
| `docs/gemini-ipo-research.md` | This document |
