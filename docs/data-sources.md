# Indian IPO Data Sources Evaluation & Sourcing Architecture

## Executive Summary
Building a production-grade **Indian IPO Intelligence Platform** requires a resilient, multi-tiered data acquisition strategy. IPO data in India is fragmented across official exchange portals, SEBI regulatory filings, registrar allotment gateways, broker APIs, and informal grey market aggregators.

This document presents a comprehensive evaluation of candidate data sources across official, market, and GMP categories, followed by a recommended primary and fallback sourcing architecture.

---

## 1. Required Data Fields Specification

| Field Category | Required Data Points | Precision / Format | Update Frequency Required |
| :--- | :--- | :--- | :--- |
| **IPO Master Data** | Company Name, Symbol/BSE Code, Issue Type (Mainboard vs SME), Industry/Sector, Lead Managers | String / Enum | Daily |
| **Status** | Status (`Upcoming`, `Open`, `Closed`, `Allotted`, `Listed`, `Withdrawn`) | Enum | Real-time / Hourly |
| **Pricing & Valuation** | Min Price, Max Price, Final Cut-off Price, Face Value, P/E Ratio | Decimal (INR) | Daily during announcement |
| **Issue Structure** | Minimum Lot Size (Shares), Total Issue Size (₹ Crores), Fresh Issue (₹ Cr), Offer For Sale / OFS (₹ Cr) | Integer / Decimal | Once on RHP filing |
| **Event Timeline** | Opening Date, Closing Date, Basis of Allotment Date, Refund Initiation Date, Credit to Demat Date, Listing Date | Date (`YYYY-MM-DD`) | Daily check |
| **Live Subscription** | QIB Subscription (x-times), NII / bNII / sNII (x-times), Retail (x-times), Employee Quota (x-times), Overall Subscription (x-times) | Decimal (2 decimal places) | Hourly during bidding (10 AM - 5 PM IST) |
| **Grey Market Premium (GMP)** | Absolute GMP (₹), Percentage GMP (%), Estimated Listing Price (₹), Subject to Sauda Rate (₹) | Decimal / Percentage | Every 2-4 hours |
| **Historical GMP** | Time-series array of daily GMP from announcement to listing date | Array of `{date, gmp, percentage}` | Daily EOD snapshot |
| **Allotment Sourcing** | Registrar Name (Link Intime, KFintech, Bigshare, etc.), Allotment Check Web URL / Endpoint | String / URL | On Allotment Date |

---

## 2. Source Classification & Candidate Evaluation

### Category A: Official & Primary Regulatory Sources

#### A1. National Stock Exchange (NSE) & Bombay Stock Exchange (BSE) Official Portals
* **Description**: Official stock exchange public issue portals (`nseindia.com/market-data/all-upcoming-issues-ipo` and `bseindia.com/publicissue.html`).
* **API Availability**: No official public JSON API for consumer use. Private internal APIs used by web portals require dynamic cookie/session management. Commercial data feeds available via licensed vendors (TrueData, Accord Fintech).
* **Pricing**: Web access free; Authorized Data Vendor feeds cost ₹15,000 - ₹50,000/month.
* **Rate Limits**: Strict IP rate limiting and Akamai/Cloudflare WAF bot protection.
* **Reliability**: 99.99% for exchange portal uptime.
* **Update Frequency**: Real-time bid details updated every 15-30 minutes during market hours.
* **Data Fields**: Master data, price band, lot size, live category-wise subscription, official listing price.
* **Historical Data**: Excellent historical archives of all listed issues.
* **Authentication**: Cookie session / User-Agent spoofing required for direct web endpoint; API key for commercial vendors.
* **Terms / Licensing**: Commercial automated scraping violates Terms of Service. Authorized vendor agreement required for commercial redistribution.
* **Failure Risk**: High risk of IP blocks if directly scraped without authorization.

#### A2. Securities and Exchange Board of India (SEBI) Filings Portal
* **Description**: SEBI official repository for Draft Red Herring Prospectus (DRHP) and Red Herring Prospectus (RHP) filings.
* **API Availability**: No REST API. Document repository (PDF files).
* **Pricing**: Free public access.
* **Reliability**: 99.9% uptime.
* **Data Fields**: Comprehensive prospectus details, financial statements, risk factors, object of the issue.
* **Terms / Licensing**: Public domain regulatory documents.
* **Failure Risk**: PDF parsing complexity requires OCR / LLM extraction.

#### A3. IPO Registrars (Link Intime, KFintech, Bigshare Services, Skyline, Cameo)
* **Description**: Primary registrar platforms responsible for processing applications and publishing allotment status.
* **API Availability**: No public REST APIs. Form-based submission portals (`linkintime.co.in`, `kfintech.com`).
* **Pricing**: Free.
* **Update Frequency**: Allotment status updated once on allotment date (typically late evening).
* **Data Fields**: PAN/Application/DP-ID allotment status check, shares allotted, refund status.
* **Terms / Licensing**: Intended for end-user manual verification. CAPTCHAs frequently deployed.
* **Failure Risk**: Server overload on allotment nights leads to high latency and timeouts.

---

### Category B: Market-Data & Broker APIs

#### B1. Upstox API v2 (`GET /v2/ipos`, `GET /v2/ipos/{id}`)
* **Description**: Official developer API provided by Upstox securities broker.
* **API Availability**: Native REST API with JSON response format.
* **Pricing**: Free for registered developer accounts.
* **Rate Limits**: 20 requests/second.
* **Reliability**: High (99.9% SLA backed by cloud infrastructure).
* **Update Frequency**: Real-time / Hourly updates for open and upcoming issues.
* **Data Fields**: Comprehensive master data, price band, lot size, issue size, timeline dates, live subscription metrics, RHP PDF links.
* **Historical Data**: Good coverage of recent past issues (Closed & Listed).
* **Authentication**: OAuth 2.0 / Access Token header (`Authorization: Bearer <token>`).
* **Terms / Licensing**: Fully compliant developer API for building financial tools.
* **Failure Risk**: Low. Broker API key revocation risk if abused.

#### B2. Authorized Market Data Vendors (TrueData / Accord Fintech / Global Datafeeds)
* **Description**: SEBI/Exchange-authorized market data feed aggregators.
* **API Availability**: WebSocket & REST APIs.
* **Pricing**: Paid commercial subscription ($100 - $500/month).
* **Reliability**: Extremely High (Institutional Grade).
* **Data Fields**: Full market depth, live subscription, historical corporate actions.
* **Terms / Licensing**: Fully legal commercial license.
* **Failure Risk**: Extremely Low.

---

### Category C: Grey Market Premium (GMP) Sources

> **IMPORTANT REGULATORY NOTE**: Grey Market Premium (GMP) represents an informal, unorganized, and unregulated over-the-counter sentiment indicator. Neither SEBI, NSE, nor BSE track or endorse GMP. All GMP data must be treated as indicative market sentiment and flagged appropriately in the platform.

#### C1. InvestorGain (`investorgain.com`)
* **Description**: Primary benchmark aggregator in India for daily live and historical GMP, Subject to Sauda rates, and estimated listing prices.
* **API Availability**: No official API. Managed API wrappers available via Parse.bot / RapidAPI.
* **Pricing**: Direct web browsing free; API wrappers cost $0 - $20/month.
* **Rate Limits**: 30-60 requests/minute via wrapper APIs.
* **Reliability**: Medium-High (Updated multiple times daily by market tracking team).
* **Update Frequency**: Updated 3-6 times daily as grey market rates fluctuate.
* **Data Fields**: Absolute GMP (₹), Percentage GMP (%), Subject to Sauda rate, Lot size, Estimated listing price, Daily historical GMP trend.
* **Historical Data**: Excellent historical GMP time-series records per IPO.
* **Terms / Licensing**: Unofficial data aggregation.
* **Failure Risk**: Medium. Website layout changes can temporarily disrupt direct scrapers.

#### C2. Chittorgarh (`chittorgarh.com`)
* **Description**: Veteran financial portal aggregating IPO subscription, GMP, reviews, and timelines.
* **API Availability**: No public API.
* **Pricing**: Web browsing free.
* **Reliability**: High (Industry standard reference).
* **Update Frequency**: Daily EOD and intraday subscription updates.
* **Data Fields**: GMP, Subscription breakdown, Lead manager performance, Financial ratios.
* **Failure Risk**: High for web scraping due to Anti-bot headers and Cloudflare protection.

#### C3. Commercial Managed Scraper Gateways (Apify Indian IPO Tracker / RapidAPI IPO Wallah)
* **Description**: Managed serverless actors and middleware gateways that aggregate and sanitize GMP & IPO data from InvestorGain, Chittorgarh, and IPOWatch into structured JSON endpoints.
* **API Availability**: REST API (JSON).
* **Pricing**: $5 - $30/month based on usage volume.
* **Rate Limits**: 100-500 requests/minute.
* **Reliability**: High (Managed proxies and automatic selector updates).
* **Update Frequency**: Hourly sync.
* **Authentication**: API Key (`X-RapidAPI-Key` or Bearer Token).
* **Failure Risk**: Low to Medium.

---

## 3. Comparative Evaluation Matrix

| Source Candidate | Category | API Available? | Data Accuracy | GMP Support | Reliability | Cost | Legal/Terms Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Upstox API v2** | Broker API | **Yes (Official)** | 100% | No | Very High | Free | **Zero Risk** |
| **NSE / BSE Direct** | Primary Exchange | No (Internal) | 100% | No | High | Free / High | Medium-High (Scraping) |
| **InvestorGain (via Gateway)** | GMP Aggregator | **Yes (Wrapper)** | ~90% (Informal) | **Yes (Primary)**| High | Low | Low |
| **Apify IPO Aggregator** | Managed Scraper | **Yes (REST)** | ~92% | **Yes** | High | Low ($5/mo) | Low |
| **Chittorgarh Direct** | Web Portal | No | ~95% | **Yes** | Medium | Free | High (Cloudflare) |
| **Link Intime / KFintech** | Registrar | No | 100% (Allotment) | No | Medium | Free | Low (Public portal) |

---

## 4. Recommended Sourcing Architecture

To ensure **high reliability, zero downtime, and audit compliance**, we establish a **Primary + Secondary Sourcing Pipeline**:

```
+-----------------------------------------------------------------------------------+
|                            PRIMARY SOURCE LAYER                                   |
|                                                                                   |
|   1. Upstox API v2 -> Master Data, Price Band, Lot Size, Dates, Live Subscription |
|   2. Apify / RapidAPI Gateway -> Multi-source GMP Data & Daily Trends             |
+-----------------------------------------------------------------------------------+
                                       |
                                (Failover Trigger)
                                       v
+-----------------------------------------------------------------------------------+
|                            FALLBACK SOURCE LAYER                                  |
|                                                                                   |
|   1. Direct Exchange JSON Endpoints / Scraper -> Master Data & Subscription Backup |
|   2. Parse.bot / InvestorGain Direct Parser -> Backup GMP Sourcing                 |
|   3. Registrar Direct Portal Handlers -> Allotment URL Routing                    |
+-----------------------------------------------------------------------------------+
```

### Primary Pipeline
1. **Official & Financial Data**: **Upstox API v2**. Handles IPO discovery, price band, lot size, issue size, timeline dates, and subscription numbers.
2. **GMP & Market Sentiment**: **Managed Aggregator API (Apify / RapidAPI IPO Wallah)** backed by **InvestorGain**. Provides live GMP, percentage return estimates, and historical GMP time-series.
3. **Allotment Processing**: Direct deep-linking to **Link Intime / KFintech / Bigshare** official search portals.

### Fallback Pipeline (Circuit Breaker Triggered)
1. **Fallback Master & Subscription**: Secondary cache + direct NSE/BSE public feed parser.
2. **Fallback GMP**: Direct fallback HTML parser for InvestorGain with IP rotation.

---

## 5. Anti-Patterns & Prohibited Practices

1. **PROHIBITED**: Direct web scraping of NSE/BSE main portals without rate limiting or IP rotation.
2. **PROHIBITED**: Hardcoding single-source scrapers for GMP without circuit breaker fallbacks.
3. **PROHIBITED**: Storing or displaying GMP as guaranteed returns (Must display mandatory regulatory disclaimer).
4. **PROHIBITED**: Fabricating unverified API endpoints or inventing response formats.
