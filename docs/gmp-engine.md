# Grey Market Premium (GMP) Tracking & Trend Analysis Engine

## Executive Summary
This document defines the technical design, calculations, validation rules, and append-only time-series architecture of the **GMP Tracking Engine** for the Indian IPO Intelligence Platform.

---

## 1. Core Principles & Constraints

1. **Append-Only Immutability**: Historical GMP observation records in `gmp_history` are **NEVER overwritten or deleted**. Every sync execution appends a new observation with an explicit UTC timestamp.
2. **Provider Attribution**: Every observation is associated with its source provider (`source_id` referencing `data_sources.id`).
3. **Data Sanitization**: Null prices, missing symbols, and negative GMP values are filtered out safely before reaching PostgreSQL.
4. **Duplicate Safeguard**: Identical observation timestamps for the same IPO and source are skipped to prevent duplicate noise.

---

## 2. Calculated Metrics & Delta Formulas

Given a time-series array of observations for an IPO ordered by `observation_time DESC`:

* `current_gmp`: $P_{\text{current}} = \text{observations}[0].\text{gmp\_price}$
* `previous_gmp`: $P_{\text{previous}} = \text{observations}[1].\text{gmp\_price}$ (if count $\ge 2$)
* `absolute_change`: $\Delta P = P_{\text{current}} - P_{\text{previous}}$
* `percentage_change`: $\Delta P\% = \left(\frac{P_{\text{current}} - P_{\text{previous}}}{P_{\text{previous}}}\right) \times 100$
* `twenty_four_hour_change`: $\Delta P_{24\text{h}} = P_{\text{current}} - P_{24\text{h\_ago}}$
* `trend` State:
  $$\text{Trend} = \begin{cases} 
  \mathbf{RISING} & \text{if } \Delta P > 0 \\ 
  \mathbf{FALLING} & \text{if } \Delta P < 0 \\ 
  \mathbf{STABLE} & \text{if } \Delta P = 0 \\ 
  \mathbf{UNKNOWN} & \text{if } P_{\text{previous}} \text{ is None} 
  \end{cases}$$

---

## 3. API Endpoints for GMP Engine

| Endpoint | Method | Response Model | Description |
| :--- | :--- | :--- | :--- |
| `/ipos/{ipo_id}/gmp` | `GET` | `GMPResponse` | Most recent single GMP snapshot |
| `/ipos/{ipo_id}/gmp/analysis` | `GET` | `GMPAnalysisResponse` | Current GMP, previous GMP, deltas, 24h change, and `trend` state |
| `/ipos/{ipo_id}/gmp/history` | `GET` | `GMPHistoryListResponse` | Full append-only time-series history |
| `/ingest/gmp` | `POST` | `SyncResult` | Triggers programmatic sync from provider (`APIFY_GMP` / `MOCK_GMP`) |

---

## 4. Test Verification Summary

Automated tests in `tests/test_gmp.py` verify:
* Null/Missing GMP filtering without DB corruption (`test_gmp_validation_and_null_handling`).
* Append-only history preservation across multiple sync runs (`test_gmp_append_only_and_source_attribution`).
* Trend state calculations (`RISING`, `FALLING`, `STABLE`, `UNKNOWN`) (`test_gmp_trend_calculations`).
* Endpoint delivery via `POST /ingest/gmp` and `GET /ipos/{ipo_id}/gmp/analysis` (`test_gmp_ingest_and_analysis_endpoints`).
