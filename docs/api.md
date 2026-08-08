# Indian IPO Intelligence Platform — REST API Specification

## Executive Summary
This document provides the technical specification and API reference for the **FastAPI Backend Services** of the Indian IPO Intelligence Platform.

The backend strictly implements a **Clean Architecture** separating Routes, Schemas, Repositories, Services, and External API Clients.

---

## 1. Architectural Layers Overview

```
+-------------------------------------------------------------+
|                      API ROUTERS                            |
|        app/api/endpoints/health.py | ipos.py                |
+-------------------------------------------------------------+
                               │
                               ▼
+-------------------------------------------------------------+
|                     SERVICES LAYER                          |
|                 app/services/ipo_service.py                 |
+-------------------------------------------------------------+
                               │
                               ▼
+-------------------------------------------------------------+
|                   REPOSITORIES LAYER                        |
|   app/repositories/ ipo_repo.py | gmp_repo.py | sub_repo.py  |
+-------------------------------------------------------------+
                               │
                               ▼
+-------------------------------------------------------------+
|                     DATABASE & MODELS                       |
|           SQLAlchemy 2.0 ORM (app/models/*)                 |
+-------------------------------------------------------------+
```

---

## 2. API Endpoints Reference

### 2.1 Health Check
#### `GET /health`
* **Description**: Returns real-time health status of the application and PostgreSQL database connection.
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "status": "ok",
  "database": "healthy",
  "timestamp": "2026-08-08T23:45:00Z",
  "version": "1.0.0"
}
```

---

### 2.2 List IPOs (Paginated)
#### `GET /ipos`
* **Description**: Retrieves a paginated list of IPOs with optional filtering.
* **Query Parameters**:
  * `status` *(optional)*: Filter by status (`UPCOMING`, `OPEN`, `CLOSED`, `ALLOTTED`, `LISTED`, `WITHDRAWN`).
  * `issue_type` *(optional)*: Filter by category (`MAINBOARD`, `SME`).
  * `page` *(optional, default 1)*: Page number (`ge=1`).
  * `limit` *(optional, default 20)*: Page size (`1 <= limit <= 100`).
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "total": 2,
  "page": 1,
  "limit": 20,
  "ipos": [
    {
      "id": "24085991-4e16-43f4-9cc0-98963dbi14e0d",
      "symbol": "SWIGGY",
      "bse_code": "544280",
      "company_name": "Swiggy Limited",
      "issue_type": "MAINBOARD",
      "status": "OPEN",
      "min_price": 371.0,
      "max_price": 390.0,
      "issue_price": 390.0,
      "lot_size": 38,
      "total_issue_size_cr": 11327.43,
      "open_date": "2026-08-07",
      "close_date": "2026-08-09",
      "allotment_date": "2026-08-12",
      "listing_date": "2026-08-15"
    }
  ]
}
```

---

### 2.3 List Open IPOs
#### `GET /ipos/open`
* **Description**: Retrieves all IPOs currently open for bidding.
* **Status Code**: `200 OK`
* **Response Body**: `List[IPOResponse]`

---

### 2.4 List Upcoming IPOs
#### `GET /ipos/upcoming`
* **Description**: Retrieves all announced/upcoming IPOs.
* **Status Code**: `200 OK`
* **Response Body**: `List[IPOResponse]`

---

### 2.5 Get IPO Detail
#### `GET /ipos/{ipo_id}`
* **Description**: Retrieves full details of a specific IPO by **UUID** or **Stock Symbol**.
* **Path Parameters**: `ipo_id` (e.g. `SWIGGY` or `24085991-4e16-43f4-9cc0-98963dbi14e0d`)
* **Status Codes**:
  * `200 OK`: Success
  * `404 Not Found`: IPO identifier does not exist.
* **Error Response Body (404)**:
```json
{
  "detail": "IPO with identifier 'UNKNOWN' was not found.",
  "error_code": "IPO_NOT_FOUND"
}
```

---

### 2.6 Get Latest GMP Snapshot
#### `GET /ipos/{ipo_id}/gmp`
* **Description**: Retrieves the most recent Grey Market Premium (GMP) observation for an IPO.
* **Path Parameters**: `ipo_id` (UUID or Symbol)
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "ipo_id": "24085991-4e16-43f4-9cc0-98963dbi14e0d",
  "source_id": "c1d2e3f4-5678-90ab-cdef-1234567890ab",
  "source_code": "APIFY_GMP",
  "gmp_price": 22.0,
  "gmp_percent": 5.64,
  "estimated_listing_price": 412.0,
  "subject_to_sauda": 550.0,
  "observation_time": "2026-08-08T22:30:00Z"
}
```

---

### 2.7 Get GMP Time-Series History
#### `GET /ipos/{ipo_id}/gmp/history`
* **Description**: Retrieves the immutable append-only historical observations of GMP over time.
* **Query Parameters**: `limit` *(default 50)*
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "ipo_id": "24085991-4e16-43f4-9cc0-98963dbi14e0d",
  "symbol": "SWIGGY",
  "count": 4,
  "history": [ ... ]
}
```

---

### 2.8 Get Subscription Rates & History
#### `GET /ipos/{ipo_id}/subscription`
* **Description**: Retrieves category-wise subscription rates (QIB, NII, Retail, Employee, Overall) and historical snapshots.
* **Query Parameters**: `limit` *(default 50)*
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "ipo_id": "24085991-4e16-43f4-9cc0-98963dbi14e0d",
  "symbol": "SWIGGY",
  "count": 2,
  "latest": {
    "qib_x": 6.02,
    "nii_x": 4.15,
    "b_nii_x": 4.5,
    "s_nii_x": 3.45,
    "retail_x": 1.14,
    "employee_x": 1.65,
    "overall_x": 3.59,
    "observation_time": "2026-08-08T22:30:00Z"
  },
  "history": [ ... ]
}
```

---

### 2.9 Get Consolidated IPO Summary
#### `GET /ipos/{ipo_id}/summary`
* **Description**: Returns master IPO data, latest GMP snapshot, latest subscription snapshot, and calculated return percentage in a single payload.
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "ipo": { ... },
  "latest_gmp": { ... },
  "latest_subscription": { ... },
  "estimated_return_percent": 5.64
}
```

---

## 3. Global Error Handling & Exception Architecture

All unhandled internal exceptions are caught by global exception handlers to prevent exposing internal stack traces:

* **HTTP 404 (IPO Not Found)**:
  `{"detail": "IPO with identifier 'XYZ' was not found.", "error_code": "IPO_NOT_FOUND"}`
* **HTTP 422 (Validation Error)**:
  Standard FastAPI Pydantic field validation errors.
* **HTTP 500 (Internal Server Error)**:
  `{"detail": "An internal server error occurred. Please try again later.", "error_code": "INTERNAL_SERVER_ERROR"}`

---

## 4. Test Suite Execution

Run automated unit and integration tests:

```bash
python -m pytest tests/
```

Result: **20 Passed (10 Database Tests + 10 API Integration Tests)**.
