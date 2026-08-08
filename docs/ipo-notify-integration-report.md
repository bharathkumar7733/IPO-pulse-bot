# IPO Notify Integration & Provider Evaluation Report

## Executive Summary
This document summarizes the integration of **IPO Notify** (`https://iponotify.me/`) as a primary candidate IPO data provider alongside the existing `UpstoxIPOProvider` and `MockIPOProvider`. 

All code changes adhere strictly to the provider abstraction interface (`BaseIPOProvider`), preserving historical append-only database records, source attributions, and active production behavior.

---

## 1. Summary of Changes

* **Provider Abstraction Extension**: Created `IPONotifyProvider` in `app/providers/ipo_notify_provider.py` extending `BaseIPOProvider`.
* **Zero Credential Exposure**: Authenticates using `X-API-KEY` header loaded strictly from environment variables (`IPO_NOTIFY_API_KEY`).
* **Field Normalization**: Maps raw JSON fields (`searchId`, `issueSize`, `subscriptionRates`, `isSme`) into standardized `RawIPODTO` and `RawSubscriptionDTO` schemas.
* **Date-Based IST Status Accuracy**: Calculates IPO status (`UPCOMING`, `OPEN`, `CLOSED`, `LISTED`) based on IST dates and provider status flags.
* **Side-by-Side Comparison**: Evaluated data schema differences between existing providers and IPO Notify.
* **Automated Test Coverage**: Created 7 unit and integration tests in `tests/test_ipo_notify.py` (59 / 59 total test suite passing).

---

## 2. Modified & Created Files

* 📄 `app/providers/ipo_notify_provider.py` — `IPONotifyProvider` implementation
* 📄 `app/providers/__init__.py` — Provider exports
* 📄 `tests/test_ipo_notify.py` — Unit test suite for IPO Notify provider
* 📄 `.env.example` — Added `IPO_NOTIFY_API_KEY=""` template variable
* 📄 `.env` — Local environment configuration
* 📄 `docs/ipo-notify.md` — API Research & Specification
* 📄 `docs/ipo-notify-integration-report.md` — Integration & Evaluation Report

---

## 3. Official API Endpoints & Authentication

* **Base URL**: `https://iponotify.me/api/ipo`
* **Authentication Header**: `X-API-KEY: <api_key>`
* **Endpoints**:
  - `GET /api/ipo/open?limit=20&getAfterId={cursor}`
  - `GET /api/ipo/upcoming?limit=20&getAfterId={cursor}`
  - `GET /api/ipo/closed?limit=20&getAfterId={cursor}`
  - `GET /api/ipo/id/{searchId}`

---

## 4. Schema Field Mapping Matrix

| Raw IPO Notify Field | Internal Schema Field | Transformation Logic |
| :--- | :--- | :--- |
| `symbol` | `RawIPODTO.symbol` | Uses `symbol`; falls back to upper(searchId) if null |
| `companyName` | `RawIPODTO.company_name` | Direct string mapping |
| `isSme` | `RawIPODTO.issue_type` | `IssueType.SME` if true, else `IssueType.MAINBOARD` |
| `issueSize` | `RawIPODTO.total_issue_size_cr` | Divided by $10^7$ to convert to Crores |
| `minPrice` / `maxPrice` | `RawIPODTO.min_price` / `max_price` | Converted to floats |
| `startDate` / `endDate` | `RawIPODTO.open_date` / `close_date` | Parsed ISO date strings |
| `subscriptionRates` | `RawSubscriptionDTO` | Category extraction (`QIB`, `NII`, `RETAIL`, `TOTAL`) |

---

## 5. Side-by-Side Provider Comparison

| Field / Attribute | Existing Provider (Upstox/Mock) | IPO Notify Provider |
| :--- | :--- | :--- |
| **Symbol Resolution** | NSE Symbol (e.g. `SWIGGY`) | Official Symbol (e.g. `TITANROBO`, falls back to slug) |
| **Company Name** | Full legal name | Full legal name & short name |
| **Mainboard / SME** | Explicit enum string | `isSme` boolean flag |
| **Subscription Data** | Separate subscription object | Embedded `subscriptionRates` array |
| **Registrar Details** | Included in master payload | Included (`registrar` & `rtaLink`) |
| **Issue Size Format** | Returned in Crores | Returned in raw Rupees (normalized to Cr) |

---

## 6. Automated Test Results

Executed `python -m pytest tests/`:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-9.1.0, pluggy-1.6.0
rootdir: C:\IPO-BOT
collected 59 items

tests\test_ai_analysis.py ...                                            [  5%]
tests\test_alerts.py ....                                                [ 11%]
tests\test_api.py ..........                                             [ 28%]
tests\test_bot.py ..........                                             [ 45%]
tests\test_database.py ..........                                        [ 62%]
tests\test_e2e_flow.py .                                                 [ 64%]
tests\test_gmp.py ........                                               [ 77%]
tests\test_ingestion.py ......                                           [ 88%]
tests\test_ipo_notify.py .......                                         [100%]

============================= 59 passed in 15.04s =============================
```

---

## 7. Known Limitations & Recommendations

### Limitations
1. **GMP Data**: IPO Notify focuses on primary IPO facts, allotment dates, and subscription rates. Grey Market Premium (GMP) data should continue to be sourced via `ApifyGMPProvider` or dedicated OTC sources.
2. **API Key Requirement**: Requires a valid `IPO_NOTIFY_API_KEY` for production rates.

### Recommendation
* **Primary Provider**: **IPO Notify** provides richer metadata (lot size, min bid quantity, registrar links, pros/cons, subscription rates) compared to basic exchange feeds.
* **Migration Strategy**: Keep `IPONotifyProvider` integrated as primary for master data ingestion (`POST /ingest/ipos`) once production approval is granted by the user.

> ⚠️ **Notice**: Production active provider configuration has NOT been switched. The existing provider remains active until explicit user approval.
