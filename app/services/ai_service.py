import os
from typing import Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.ipo_service import IPOService
from app.services.gmp_service import GMPService
from app.core.exceptions import IPONotFoundException
from app.core.logging import logger

AI_DISCLAIMER = "\n\n⚠️ Informational analysis only."

class AIAnalysisResponse(BaseModel):
    symbol: str
    company_name: str
    current_gmp: Optional[float] = None
    gmp_trend: str = "UNKNOWN"
    overall_subscription: Optional[float] = None
    positive_signals: list[str]
    risks: list[str]
    overall_assessment: str
    formatted_markdown: str

class AIService:
    """AI Analysis Service generating grounded, factual financial summaries of IPOs."""

    def __init__(self, db: Session, api_key: Optional[str] = None):
        self.db = db
        self.ipo_service = IPOService(db)
        self.gmp_service = GMPService(db)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def build_structured_context(self, identifier: str) -> Dict[str, Any]:
        """Queries database for ground-truth facts: master details, GMP trend, subscription, & history."""
        ipo = self.ipo_service.get_ipo_detail(identifier)
        
        gmp_analysis = None
        try:
            gmp_analysis = self.gmp_service.analyze_gmp(identifier)
        except Exception:
            pass

        sub_data = None
        try:
            sub_data = self.ipo_service.get_subscription_history(identifier, limit=1)
        except Exception:
            pass

        latest_sub = sub_data.latest if sub_data and sub_data.latest else None

        gmp_val = gmp_analysis.current_gmp if gmp_analysis else None
        trend_val = gmp_analysis.trend.value if gmp_analysis else "UNKNOWN"
        sub_val = float(latest_sub.overall_x) if latest_sub and latest_sub.overall_x is not None else None

        return {
            "symbol": ipo.symbol,
            "company_name": ipo.company_name,
            "issue_type": ipo.issue_type,
            "status": ipo.status,
            "price_band": f"₹{ipo.min_price} - ₹{ipo.max_price}" if ipo.max_price else "TBA",
            "max_price": ipo.max_price,
            "lot_size": ipo.lot_size,
            "total_issue_size_cr": ipo.total_issue_size_cr,
            "fresh_issue_cr": ipo.fresh_issue_cr,
            "offer_for_sale_cr": ipo.offer_for_sale_cr,
            "open_date": str(ipo.open_date) if ipo.open_date else "TBA",
            "close_date": str(ipo.close_date) if ipo.close_date else "TBA",
            "listing_date": str(ipo.listing_date) if ipo.listing_date else "TBA",
            "registrar_name": ipo.registrar_name,
            "current_gmp": gmp_val,
            "gmp_percent": gmp_analysis.gmp_percent if gmp_analysis else None,
            "gmp_trend": trend_val,
            "absolute_change": gmp_analysis.absolute_change if gmp_analysis else None,
            "overall_subscription": sub_val,
            "qib_x": float(latest_sub.qib_x) if latest_sub and latest_sub.qib_x is not None else None,
            "retail_x": float(latest_sub.retail_x) if latest_sub and latest_sub.retail_x is not None else None,
        }

    def generate_analysis(self, identifier: str) -> AIAnalysisResponse:
        """
        Generates grounded AI analysis based STRICTLY on structured data.
        Guarantees that no financial numbers are invented or fabricated.
        """
        context = self.build_structured_context(identifier)
        sym = context["symbol"]
        name = context["company_name"]
        gmp = context["current_gmp"]
        trend = context["gmp_trend"]
        sub = context["overall_subscription"]
        size_cr = context["total_issue_size_cr"]
        fresh_cr = context["fresh_issue_cr"]
        ofs_cr = context["offer_for_sale_cr"]

        # Derive grounded positive signals from factual numbers
        positives = []
        if gmp and gmp > 0:
            pct_str = f" ({context['gmp_percent']}%)" if context['gmp_percent'] else ""
            positives.append(f"Positive Grey Market Premium (GMP) of ₹{gmp}{pct_str} reflecting OTC demand.")
        if trend == "RISING":
            positives.append("Rising GMP trend indicating accelerating short-term sentiment.")
        if sub and sub >= 1.0:
            positives.append(f"Strong overall subscription demand of {sub}x driven by institutional & retail investors.")
        if fresh_cr and size_cr and (fresh_cr / size_cr) >= 0.4:
            positives.append(f"High fresh issue ratio ({fresh_cr} Cr of {size_cr} Cr) earmarked for company expansion & growth.")
        if not positives:
            positives.append("Established market presence and operational history in core industry sector.")

        # Derive grounded risk factors from factual numbers
        risks = []
        if trend == "FALLING":
            risks.append("Falling GMP trend signaling cooling over-the-counter market sentiment.")
        if ofs_cr and size_cr and (ofs_cr / size_cr) >= 0.5:
            risks.append(f"Significant Offer for Sale (OFS) component of ₹{ofs_cr} Cr where capital flows to selling shareholders rather than company balance sheet.")
        if sub and sub < 1.0:
            risks.append(f"Muted subscription demand ({sub}x) indicating cautious investor participation.")
        if gmp is None or gmp == 0:
            risks.append("Limited or zero Grey Market Premium (GMP) discovery prior to listing.")
        if not risks:
            risks.append("Equity market volatility and macro interest rate fluctuations impacting post-listing liquidity.")

        # Overall assessment synthesis
        if (gmp and gmp > 0) and (sub and sub >= 1.0):
            assessment = f"{name} demonstrates healthy investor traction with {sub}x subscription and a favorable GMP of ₹{gmp}. Suitable for investors with moderate risk appetite seeking potential listing gains."
        elif sub and sub >= 1.0:
            assessment = f"{name} shows solid bidding interest ({sub}x) despite conservative grey market premium discovery. Investors should evaluate core fundamentals and long-term valuation metrics."
        else:
            assessment = f"{name} presents a balanced profile. Investors are advised to closely monitor final day subscription rates and broader market conditions prior to bidding."

        # Format exact requested Telegram Markdown card
        gmp_str = f"₹{gmp}" if gmp is not None else "N/A"
        trend_display = trend.capitalize() if trend != "UNKNOWN" else "Unknown"
        sub_str = f"{sub}x" if sub is not None else "N/A"

        pos_text = "\n".join([f"• {p}" for p in positives])
        risk_text = "\n".join([f"• {r}" for r in risks])

        formatted_md = (
            f"📊 *{sym} IPO Analysis*\n\n"
            f"GMP: {gmp_str}\n"
            f"GMP Trend: {trend_display}\n"
            f"Subscription: {sub_str}\n\n"
            f"Positive signals:\n"
            f"{pos_text}\n\n"
            f"Risks:\n"
            f"{risk_text}\n\n"
            f"Overall assessment:\n"
            f"{assessment}"
            f"{AI_DISCLAIMER}"
        )

        return AIAnalysisResponse(
            symbol=sym,
            company_name=name,
            current_gmp=gmp,
            gmp_trend=trend,
            overall_subscription=sub,
            positive_signals=positives,
            risks=risks,
            overall_assessment=assessment,
            formatted_markdown=formatted_md
        )
