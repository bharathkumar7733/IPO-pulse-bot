# IPO Notify API Integration & Research Specification

## Executive Summary
This document provides the complete API specification, authentication method, endpoints, pagination parameters, response JSON schemas, and field mapping for **IPO Notify** (`https://iponotify.me/`).

---

## 1. API Overview & Authentication

* **Base URL**: `https://iponotify.me/api/ipo`
* **Authentication Method**: API Key passed via HTTP Request Header:
  ```http
  X-API-KEY: <your_ipo_notify_api_key>
  ```
* **Response Format**: `application/json`

---

## 2. API Endpoints Reference

| Purpose | Method | Endpoint URL | Query Parameters |
| :--- | :--- | :--- | :--- |
| **Open IPOs** | `GET` | `https://iponotify.me/api/ipo/open` | `limit` (integer), `getAfterId` (string cursor) |
| **Upcoming IPOs** | `GET` | `https://iponotify.me/api/ipo/upcoming` | `limit` (integer), `getAfterId` (string cursor) |
| **Closed IPOs** | `GET` | `https://iponotify.me/api/ipo/closed` | `limit` (integer), `getAfterId` (string cursor) |
| **Single IPO Details** | `GET` | `https://iponotify.me/api/ipo/id/{searchId}` | None |

---

## 3. Cursor-Based Pagination

* **Cursor Field**: `getAfterId`
* **Mechanism**: To fetch the next page of results, pass the `searchId` of the last record from the previous response.
* **Example**:
  ```http
  GET /api/ipo/open?limit=10&getAfterId=tata-tech-ipo
  ```

---

## 4. Response JSON Schema & Field Mapping

| IPO Notify API Field | Type | Description | Application Schema (`RawIPODTO`) Mapping |
| :--- | :--- | :--- | :--- |
| `symbol` | `string \| null` | Stock exchange symbol (e.g. `TITANROBO`) | `symbol` (falls back to uppercase `searchId` if null) |
| `companyName` | `string` | Full corporate company name | `company_name` |
| `companyShortName` | `string` | Abbreviated name | `company_short_name` |
| `isSme` | `boolean` | Mainboard vs SME classification | `issue_type` (`SME` if true, else `MAINBOARD`) |
| `issueType` | `string` | Issue type (Book Building / Fixed Price) | `bidding_type` |
| `lotSize` | `integer` | Minimum lot size quantity | `lot_size` |
| `minPrice` | `float` | Minimum price band boundary | `min_price` |
| `maxPrice` | `float` | Maximum price band boundary | `max_price` |
| `issuePrice` | `float \| null` | Final cutoff / allotment price | `issue_price` |
| `issueSize` | `number` | Total issue size in ₹ (e.g. `285000000`) | `total_issue_size_cr` (divided by $10^7$) |
| `registrar` | `string \| null` | Registrar name | `registrar_name` |
| `startDate` | `string` | Bidding start date (`YYYY-MM-DD`) | `open_date` |
| `endDate` | `string` | Bidding end date (`YYYY-MM-DD`) | `close_date` |
| `allotmentDate` | `string` | Allotment finalization date | `allotment_date` |
| `listing.listedOn` | `list[str]` | Stock exchanges (`NSE`, `BSE`) | `exchanges` |
| `listing.bseScripCode` | `string` | BSE Scrip Code | `bse_scrip_code` |
| `listing.nseScripCode` | `string` | NSE Symbol | `nse_scrip_code` |
| `subscriptionRates` | `list[dict]` | Live subscription rates by category | Normalized into `RawSubscriptionDTO` (`QIB`, `NII`, `RETAIL`, `TOTAL`) |

---

## 5. Feature & Capability Assessment

* **Open / Upcoming / Closed Support**: Fully supported via dedicated endpoint parameters.
* **Subscription Data**: Included in `subscriptionRates` array.
* **GMP Data**: Not returned directly in standard IPO listing payload (handled via dedicated GMP provider layer `BaseGMPProvider`).
* **Rate Limits**: Governed by API plan headers; handled via exponential backoff retries.
