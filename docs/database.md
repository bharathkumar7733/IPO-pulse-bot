# Database Schema Specification & Data Foundation

## Executive Summary
This document defines the **PostgreSQL Relational Schema & Data Foundation** for the **Indian IPO Intelligence Agent**. It details the entity relationships, indexing strategies, audit mechanisms, append-only time-series rules, multi-source attribution, and migration architecture.

The database foundation is built using **SQLAlchemy 2.0 ORM** and version-controlled via **Alembic migrations**.

---

## 1. Core Schema Architecture & Principles

### A. UUID Primary Keys
All tables utilize globally unique 128-bit **UUID (v4)** primary keys to prevent ID enumeration, enable client-side UUID pre-generation, and support multi-region database replication.

### B. Timezone-Aware Timestamps
All date/time attributes (`created_at`, `updated_at`, `observation_time`, `sent_at`, `request_timestamp`, `last_heartbeat`) strictly use **UTC Timestamps with Time Zone (`TIMESTAMPTZ` / `UTCDateTime`)** to prevent timezone ambiguity across Indian Standard Time (IST) and server UTC runtimes.

### C. Append-Only Time-Series Guarantee (Immutable GMP & Subscription Records)
* **Rule**: Records in `gmp_history` and `subscription_history` represent point-in-time market observations.
* **Enforcement**: Records are strictly **append-only**. Historical observations are **NEVER overwritten or updated**.
* **Benefit**: Preserves full historical audit trails for GMP fluctuations, price movements, and subscription surges over the IPO lifecycle.

### D. Multi-Provider Data Attribution
* **Rule**: Multiple data providers (e.g., `UPSTOX_API`, `APIFY_GMP`, `INVESTOR_GAIN`, `NSE_DIRECT`) can concurrently supply observations for the same IPO.
* **Enforcement**: Every observation record carries a mandatory foreign key `source_id` referencing `data_sources.id`.

---

## 2. Table Specifications & Entity Relationships

```
+----------------+       1:N       +----------------------+
|  data_sources  | <-------------- |        ipos          |
+----------------+                 +----------------------+
  │         │                        │             │
  │ 1:N     │ 1:N                1:N │         1:N │
  ▼         ▼                        ▼             ▼
+---------------+                +---------------+ |
|  gmp_history  |                | subscription_ | |
+---------------+                |   history     | |
                                 +---------------+ |
  │                                                │
  │ 1:N                                        1:N │
  ▼                                                ▼
+---------------+                        +---------------+
| api_requests  |                        | notifications |
+---------------+                        +---------------+
```

---

### 2.1 `data_sources` Table
Stores registered primary, market, unofficial, and registrar data providers.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Code identifier (e.g., `UPSTOX_API`, `APIFY_GMP`) |
| `name` | VARCHAR(100) | NOT NULL | Human-readable name |
| `source_type` | ENUM | NOT NULL, INDEX | `OFFICIAL`, `MARKET_DATA`, `UNOFFICIAL_GMP`, `REGISTRAR` |
| `is_active` | BOOLEAN | NOT NULL (default true) | Active status flag |
| `priority` | INTEGER | NOT NULL (default 1) | Failover priority rank (1 = Primary) |
| `config_metadata` | JSONB / JSON | NULLABLE | Provider API configuration & metadata |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp (UTC) |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp (UTC) |

---

### 2.2 `ipos` Table
Master repository for Mainboard and SME Initial Public Offerings.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `symbol` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Stock symbol identifier (e.g., `SWIGGY`, `HYUNDAI`) |
| `bse_code` | VARCHAR(20) | NULLABLE, INDEX | BSE Security Code |
| `company_name` | VARCHAR(255) | NOT NULL | Full corporate name |
| `issue_type` | ENUM | NOT NULL, INDEX | `MAINBOARD` or `SME` |
| `status` | ENUM | NOT NULL, INDEX | `UPCOMING`, `OPEN`, `CLOSED`, `ALLOTTED`, `LISTED`, `WITHDRAWN` |
| `min_price` | NUMERIC(12, 2) | NULLABLE | Minimum price band (₹) |
| `max_price` | NUMERIC(12, 2) | NULLABLE | Maximum price band (₹) |
| `issue_price` | NUMERIC(12, 2) | NULLABLE | Final cut-off / issue price (₹) |
| `lot_size` | INTEGER | NULLABLE | Shares per lot |
| `total_issue_size_cr`| NUMERIC(12, 2) | NULLABLE | Total size (₹ Crores) |
| `fresh_issue_cr` | NUMERIC(12, 2) | NULLABLE | Fresh Issue portion (₹ Cr) |
| `offer_for_sale_cr` | NUMERIC(12, 2) | NULLABLE | Offer For Sale portion (₹ Cr) |
| `open_date` | DATE | NULLABLE, INDEX | Bidding start date |
| `close_date` | DATE | NULLABLE, INDEX | Bidding end date |
| `allotment_date` | DATE | NULLABLE, INDEX | Basis of allotment date |
| `listing_date` | DATE | NULLABLE, INDEX | Exchange listing date |
| `registrar_name` | VARCHAR(150) | NULLABLE | Registrar (Link Intime, KFintech, etc.) |
| `registrar_url` | VARCHAR(500) | NULLABLE | Registrar allotment URL |
| `rhp_url` | VARCHAR(500) | NULLABLE | Prospectus PDF link |
| `primary_source_id` | UUID | FK -> `data_sources.id` | Source attribution for master record |
| `created_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |

---

### 2.3 `gmp_history` Table (Append-Only Time-Series)
Stores immutable historical observations of Grey Market Premium rates.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `ipo_id` | UUID | FK -> `ipos.id` (CASCADE), INDEX | Target IPO |
| `source_id` | UUID | FK -> `data_sources.id` (CASCADE), INDEX | Provider attribution |
| `gmp_price` | NUMERIC(12, 2) | NOT NULL | Absolute GMP (₹) |
| `gmp_percent` | NUMERIC(8, 2) | NULLABLE | Percentage return over max price (%) |
| `estimated_listing_price` | NUMERIC(12, 2) | NULLABLE | Estimated listing price (₹) |
| `subject_to_sauda` | NUMERIC(12, 2) | NULLABLE | Subject to Sauda rate (₹) |
| `observation_time` | TIMESTAMPTZ | NOT NULL, INDEX | Observation timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Record update timestamp |

* **Unique Constraint**: `uq_gmp_ipo_source_obs_time` on `(ipo_id, source_id, observation_time)`
* **Indexes**: `idx_gmp_ipo_time` (`ipo_id`, `observation_time DESC`), `idx_gmp_source_time` (`source_id`, `observation_time DESC`)

---

### 2.4 `subscription_history` Table (Append-Only Time-Series)
Stores category-wise subscription multipliers over time.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `ipo_id` | UUID | FK -> `ipos.id` (CASCADE), INDEX | Target IPO |
| `source_id` | UUID | FK -> `data_sources.id` (CASCADE), INDEX | Provider attribution |
| `qib_x` | NUMERIC(10, 2) | NULLABLE | QIB category subscription (x-times) |
| `nii_x` | NUMERIC(10, 2) | NULLABLE | NII category subscription (x-times) |
| `b_nii_x` | NUMERIC(10, 2) | NULLABLE | Big NII (>10L) subscription (x-times) |
| `s_nii_x` | NUMERIC(10, 2) | NULLABLE | Small NII (2L-10L) subscription (x-times) |
| `retail_x` | NUMERIC(10, 2) | NULLABLE | Retail category subscription (x-times) |
| `employee_x` | NUMERIC(10, 2) | NULLABLE | Employee quota subscription (x-times) |
| `overall_x` | NUMERIC(10, 2) | NOT NULL | Overall subscription multiplier (x-times) |
| `observation_time` | TIMESTAMPTZ | NOT NULL, INDEX | Observation timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |

* **Unique Constraint**: `uq_sub_ipo_source_obs_time` on `(ipo_id, source_id, observation_time)`
* **Indexes**: `idx_sub_ipo_time` (`ipo_id`, `observation_time DESC`), `idx_sub_source_time` (`source_id`, `observation_time DESC`)

---

### 2.5 `notifications` Table
Tracks alert generation, broadcast logs, and Telegram message dispatch statuses.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `ipo_id` | UUID | FK -> `ipos.id` (SET NULL), INDEX | Associated IPO |
| `telegram_chat_id` | VARCHAR(100) | NOT NULL, INDEX | Target Telegram Chat / Channel ID |
| `notification_type` | ENUM | NOT NULL, INDEX | `GMP_SPIKE`, `SUBSCRIPTION_HIGH`, `ALLOTMENT_OUT`, `DAILY_DIGEST`, `IPO_OPENING` |
| `title` | VARCHAR(255) | NOT NULL | Notification headline |
| `message` | TEXT | NOT NULL | Formatted message body |
| `status` | ENUM | NOT NULL, INDEX | `PENDING`, `SENT`, `FAILED` |
| `sent_at` | TIMESTAMPTZ | NULLABLE | Dispatch timestamp |
| `error_message` | TEXT | NULLABLE | Error stack trace if failed |
| `source_id` | UUID | FK -> `data_sources.id` (SET NULL) | Data source that triggered alert |
| `created_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |

* **Indexes**: `idx_notif_status_type` (`status`, `notification_type`), `idx_notif_chat_created` (`telegram_chat_id`, `created_at`)

---

### 2.6 `api_requests` Table
Monitors external API latency, response status codes, and service availability SLAs.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `source_id` | UUID | FK -> `data_sources.id` (CASCADE), INDEX | Target data source |
| `endpoint` | VARCHAR(500) | NOT NULL | API endpoint URL |
| `http_method` | VARCHAR(10) | NOT NULL | `GET`, `POST`, etc. |
| `status_code` | INTEGER | NOT NULL, INDEX | HTTP Status Code (200, 429, 500) |
| `response_time_ms`| INTEGER | NOT NULL | Latency in milliseconds |
| `error_message` | TEXT | NULLABLE | Failure description |
| `request_timestamp`| TIMESTAMPTZ| NOT NULL, INDEX | Request timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |

---

### 2.7 `workflow_health` Table
Stores execution health telemetry for n8n automated workflows and cron jobs.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Primary Key |
| `workflow_name` | VARCHAR(100) | NOT NULL, INDEX | Workflow name (e.g., `WF-01: Ingestion Sync Cron`) |
| `n8n_execution_id` | VARCHAR(100) | NULLABLE, INDEX | n8n execution ID |
| `status` | ENUM | NOT NULL, INDEX | `SUCCESS`, `WARNING`, `FAILURE`, `RUNNING` |
| `metrics` | JSONB / JSON | NULLABLE | Records processed, execution duration |
| `error_log` | TEXT | NULLABLE | Error stack trace |
| `last_heartbeat` | TIMESTAMPTZ | NOT NULL, INDEX | Heartbeat timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | UTC Timestamp |

---

## 3. Database Migrations & Validation

Migrations are managed via **Alembic**:

```bash
# Apply migrations to database
python -m alembic upgrade head
```

Initial Migration File: `migrations/versions/0001_initial_schema.py`

### Automated Test Suite
The database foundation has been validated with `pytest`:

```bash
python -m pytest tests/
```

**Test Coverage**:
* `test_schema_creation_and_seed`: Validates creation and seeding across all 7 tables.
* `test_gmp_append_only_history`: Validates that new GMP observations append to time-series without overwriting previous readings.
* `test_multi_source_data_attribution`: Validates storing multi-provider observations for the same IPO.
* `test_uuid_and_timezone_timestamps`: Validates UUID primary key generation and timezone-aware UTC timestamps.
