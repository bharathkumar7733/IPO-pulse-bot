# Architecture Decision Records (ADRs) — Indian IPO Intelligence Platform

## ADR Index
* **ADR-001**: Hybrid Orchestration Architecture (n8n + FastAPI)
* **ADR-002**: Upstox API v2 as Primary Data Source for Master & Subscription Data
* **ADR-003**: Multi-Tier Managed Gateway Strategy for Grey Market Premium (GMP)
* **ADR-004**: PostgreSQL as Central Relational Store
* **ADR-005**: Programmatic Workflow Management via n8n MCP Server
* **ADR-006**: LLM-Powered Financial RHP Summarization & Risk Sentiment Analysis

---

## ADR-001: Hybrid Orchestration Architecture (n8n + FastAPI)

### Context
We need a system that handles scheduled background fetching, event-driven Telegram notifications, business logic processing, database persistence, and automated AI workflow management.

### Decision
We adopt a **Hybrid Architecture**:
* **FastAPI** handles domain models, database ORM, API endpoints, data normalization, deduplication, and high-performance Telegram webhook responses.
* **n8n** handles scheduled cron triggers, multi-step pipeline orchestration, retry loops, and visual workflow monitoring.

### Rationale
Pure n8n workflows can become complex when dealing with database migrations, complex data transformations, and custom async code. Pure FastAPI lacks visual scheduling, dead-letter monitoring, and rapid workflow adjustments. Combining both gives maximum reliability and maintainability.

### Consequences
* Requires both FastAPI Python runtime and n8n instance.
* FastAPI acts as the single source of truth for business logic and data schema.

---

## ADR-002: Upstox API v2 as Primary Master & Subscription Source

### Context
Direct web scraping of exchange websites (NSE/BSE) is subject to IP blocking, Cloudflare WAF bot challenges, dynamic session cookie requirements, and TOS violations.

### Decision
We select **Upstox API v2 (`GET /v2/ipos`)** as our primary provider for IPO master data, price bands, lot sizes, timeline dates, and live subscription figures.

### Rationale
* **Official Broker API**: Fully compliant, documented, stable REST endpoint.
* **High SLA & Speed**: Cloud-backed JSON responses without scraping overhead.
* **Cost Efficiency**: Provided free for registered developer applications.

### Consequences
* Fallback pipeline required for instances where Upstox API key is rate limited or unavailable.

---

## ADR-003: Multi-Tier Managed Gateway Strategy for Grey Market Premium (GMP)

### Context
Grey Market Premium (GMP) is an informal, unorganized market sentiment indicator. There are no official NSE/BSE APIs for GMP. Single-source scrapers break frequently when websites update their DOM layout.

### Decision
We implement a **Multi-Tier Managed Aggregator Pipeline**:
* **Primary**: Managed Aggregator API Gateway (Apify / RapidAPI IPO Wallah) backed by InvestorGain.
* **Secondary Fallback**: Direct fallback HTML parser for InvestorGain with proxy rotation.

### Rationale
Managed gateways maintain scrapers and selector updates automatically, ensuring 99.9% uptime for GMP feeds without requiring manual code fixes every time a website layout changes.

### Consequences
* Minor monthly SaaS cost ($5 - $15/month for managed gateway API).
* Mandatory regulatory disclaimers must be attached to all GMP outputs.

---

## ADR-004: PostgreSQL as Central Relational Store

### Context
IPO data consists of structured entities (IPOs, subscription snapshots over time, daily GMP snapshots, user watchlists, alert logs) requiring relational integrity, time-series indexing, and JSONB preference querying.

### Decision
We select **PostgreSQL 15+** with SQLAlchemy 2.0 (AsyncPG driver) as the central relational database.

### Rationale
* Strong relational constraints (foreign keys, unique constraints on symbols/dates).
* Native JSONB support for storing user notification preferences.
* ACID compliance guarantees zero duplicate alert dispatches.

### Consequences
* Requires running a PostgreSQL database instance (local Docker or managed cloud DB like Supabase/Neon).

---

## ADR-005: Programmatic Workflow Management via n8n MCP Server

### Context
The Antigravity AI agent needs to programmatically inspect, design, validate, build, test, and maintain n8n workflows without manual UI drag-and-drop.

### Decision
We connect Antigravity to n8n using the **n8n MCP Server** protocol (v1.1.0) via SSE transport.

### Rationale
Provides 34 native MCP tools (`create_workflow_from_code`, `validate_workflow`, `search_nodes`, `get_node_types`, `update_workflow`), allowing Antigravity to build, validate, and update n8n workflows with guaranteed structural validity.

### Consequences
* Workspace credentials stored in `.agents/mcp_config.json` must be kept out of version control via `.gitignore`.

---

## ADR-006: LLM-Powered Financial RHP Summarization & Risk Sentiment Analysis

### Context
Investors often struggle to digest 300+ page Red Herring Prospectus (RHP) documents to understand company financials, risks, and valuations.

### Decision
We integrate **Google Gemini API** via FastAPI to automatically process RHP highlights and generate concise 3-bullet summaries, financial risk flags, and an overall sentiment score (-1.0 to +1.0).

### Rationale
Delivers high-value insights to Telegram users beyond raw numbers, giving competitive advantage to the platform.

### Consequences
* LLM API rate limits and token costs must be managed with caching.
