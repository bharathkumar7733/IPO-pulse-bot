# Grounded AI Financial Prospectus & Risk Sentiment Layer

## Executive Summary
This document defines the technical design, structured data pipeline, grounded prompt engineering, and strict anti-hallucination guardrails for the **AI Financial Prospectus & Risk Sentiment Layer**.

The AI layer processes verified structured facts directly from PostgreSQL (master details, GMP time-series, subscription multipliers) and generates structured analysis cards without inventing financial numbers.

---

## 1. Grounded Data Context Injection Pipeline

```
+-------------------------------------------------------+
| PostgreSQL Master & Time-Series Database              |
| (IPO details, GMP trend, Subscription multipliers)    |
+-------------------------------------------------------+
                           │
             Structured Fact Extraction
                           │
                           ▼
+-------------------------------------------------------+
| AIService.build_structured_context(identifier)        |
+-------------------------------------------------------+
                           │
      Grounded Synthesis & Safety Guardrails
                           │
                           ▼
+-------------------------------------------------------+
| Formatted AI Output Card                              |
| /analysis <symbol>                                    |
+-------------------------------------------------------+
```

---

## 2. Mandatory Output Template

Every `/analysis <symbol>` output follows the strict pattern:

```text
📊 <SYMBOL> IPO Analysis

GMP: ₹<current_gmp>
GMP Trend: <gmp_trend>
Subscription: <overall_subscription>x

Positive signals:
• ...
• ...

Risks:
• ...
• ...

Overall assessment:
...

⚠️ Informational analysis only.
```

---

## 3. Strict Financial Safety & Anti-Hallucination Guardrails

1. **Zero Financial Number Invention**: All monetary values (GMP, price bands, issue size) and multipliers (subscription x) are extracted directly from verified database records.
2. **Grounded Positive Signals**: Synthesized only from confirmed positive metrics (e.g. positive GMP, `RISING` trend, $\ge 1.0\times$ subscription demand, high fresh issue ratio).
3. **Grounded Risk Factors**: Synthesized from factual risk indicators (e.g. `FALLING` trend, high OFS ratio where proceeds flow to selling shareholders, low subscription).
4. **Mandatory Disclaimer**: Every AI analysis output terminates with `⚠️ Informational analysis only.`

---

## 4. API & Telegram Integration

* **REST API Endpoint**: `GET /ipos/{ipo_id}/analysis`
* **Telegram Command**: `/analysis <symbol>`
* **Automated Unit Tests**: `tests/test_ai_analysis.py` (52 / 52 total test suite passing)
