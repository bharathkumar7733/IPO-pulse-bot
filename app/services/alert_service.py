from datetime import datetime, timezone, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import IPO, GMPHistory, SubscriptionHistory, Notification, NotificationType, NotificationStatus, APIRequest
from app.services.gmp_service import GMPService
from app.bot.config import bot_settings
from app.bot.client import TelegramAPIClient
from app.core.logging import logger

SUBSCRIPTION_MILESTONES = [1.0, 5.0, 10.0, 25.0, 50.0, 100.0]

class SmartAlertService:
    """Service for evaluating smart triggers and dispatching deduplicated Telegram alerts."""

    def __init__(self, db: Session):
        self.db = db
        self.gmp_service = GMPService(db)
        self.telegram_client = TelegramAPIClient()

    def _is_alert_sent(self, idempotency_key: str) -> bool:
        """Check if an alert with this idempotency key was already dispatched."""
        existing = self.db.scalars(
            select(Notification).where(Notification.idempotency_key == idempotency_key)
        ).first()
        return existing is not None

    async def evaluate_and_dispatch(self, target_chat_id: str = "123456789") -> List[Dict[str, Any]]:
        """Evaluates all smart alert triggers across active IPOs and dispatches new deduplicated alerts."""
        ipos = self.db.scalars(select(IPO)).all()
        dispatched_alerts = []
        today_date = date.today()
        tomorrow_date = today_date + timedelta(days=1)

        for ipo in ipos:
            # 1. Evaluate Date-Based Alerts (IPO Opened, Closing Soon, Listing Tomorrow)
            if ipo.open_date == today_date:
                key = f"IPO_OPENED:{ipo.symbol}:{today_date.isoformat()}"
                if not self._is_alert_sent(key):
                    title = f"🔔 IPO OPENED TODAY: {ipo.company_name} ({ipo.symbol})"
                    msg = (
                        f"🔔 *IPO Opened For Bidding Today!*\n\n"
                        f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                        f"• Price Band: ₹{ipo.min_price} - ₹{ipo.max_price}\n"
                        f"• Lot Size: {ipo.lot_size} Shares\n"
                        f"• Close Date: {ipo.close_date}\n\n"
                        f"Use `/details {ipo.symbol}` for prospectus info."
                    )
                    await self._record_and_send(ipo.id, target_chat_id, NotificationType.IPO_OPENED, title, msg, key)
                    dispatched_alerts.append({"type": "IPO_OPENED", "symbol": ipo.symbol, "title": title})

            if ipo.close_date == today_date:
                key = f"IPO_CLOSING_SOON:{ipo.symbol}:{today_date.isoformat()}"
                if not self._is_alert_sent(key):
                    title = f"⏳ CLOSING TODAY: {ipo.company_name} ({ipo.symbol})"
                    msg = (
                        f"⏳ *Bidding Closes Today!*\n\n"
                        f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                        f"Final cutoff window is closing today ({ipo.close_date}).\n\n"
                        f"Use `/subscription {ipo.symbol}` to check live demand rates."
                    )
                    await self._record_and_send(ipo.id, target_chat_id, NotificationType.IPO_CLOSING_SOON, title, msg, key)
                    dispatched_alerts.append({"type": "IPO_CLOSING_SOON", "symbol": ipo.symbol, "title": title})

            if ipo.listing_date == tomorrow_date:
                key = f"IPO_LISTING_TOMORROW:{ipo.symbol}:{tomorrow_date.isoformat()}"
                if not self._is_alert_sent(key):
                    title = f"🎯 LISTING TOMORROW: {ipo.company_name} ({ipo.symbol})"
                    msg = (
                        f"🎯 *Exchange Listing Tomorrow!*\n\n"
                        f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                        f"Listing Date: {ipo.listing_date}\n"
                        f"Issue Price: ₹{ipo.issue_price or ipo.max_price}\n\n"
                        f"Use `/gmp {ipo.symbol}` for latest grey market listing estimate."
                    )
                    await self._record_and_send(ipo.id, target_chat_id, NotificationType.IPO_LISTING_TOMORROW, title, msg, key)
                    dispatched_alerts.append({"type": "IPO_LISTING_TOMORROW", "symbol": ipo.symbol, "title": title})

            # 2. Evaluate GMP Surge (+₹10), Drop (-₹10), & Trend Reversals
            try:
                gmp_analysis = self.gmp_service.analyze_gmp(ipo.symbol)
                if gmp_analysis and gmp_analysis.current_gmp is not None:
                    abs_change = gmp_analysis.absolute_change or 0.0
                    obs_time_str = gmp_analysis.latest_observation_time.isoformat() if gmp_analysis.latest_observation_time else "NOW"

                    # GMP Surge (+₹10)
                    if abs_change >= 10.0:
                        key = f"GMP_SURGE:{ipo.symbol}:{obs_time_str}"
                        if not self._is_alert_sent(key):
                            title = f"🚀 GMP SURGE: {ipo.symbol} +₹{abs_change}"
                            msg = (
                                f"🚀 *GMP SURGE ALERT: +₹{abs_change}*\n\n"
                                f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                                f"• Current GMP: ₹{gmp_analysis.current_gmp} ({gmp_analysis.gmp_percent}%)\n"
                                f"• Previous GMP: ₹{gmp_analysis.previous_gmp}\n"
                                f"• Surge Delta: +₹{abs_change} (+{gmp_analysis.percentage_change}%)\n"
                                f"• Current Trend: 🟢 RISING\n\n"
                                f"⚠️ _GMP is informal and unregulated._"
                            )
                            await self._record_and_send(ipo.id, target_chat_id, NotificationType.GMP_SURGE, title, msg, key)
                            dispatched_alerts.append({"type": "GMP_SURGE", "symbol": ipo.symbol, "title": title})

                    # GMP Drop (-₹10)
                    if abs_change <= -10.0:
                        key = f"GMP_DROP:{ipo.symbol}:{obs_time_str}"
                        if not self._is_alert_sent(key):
                            title = f"🔻 GMP DROP: {ipo.symbol} ₹{abs_change}"
                            msg = (
                                f"🔻 *GMP DROP ALERT: ₹{abs_change}*\n\n"
                                f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                                f"• Current GMP: ₹{gmp_analysis.current_gmp} ({gmp_analysis.gmp_percent}%)\n"
                                f"• Previous GMP: ₹{gmp_analysis.previous_gmp}\n"
                                f"• Drop Delta: ₹{abs_change} ({gmp_analysis.percentage_change}%)\n"
                                f"• Current Trend: 🔴 FALLING\n\n"
                                f"⚠️ _GMP is informal and unregulated._"
                            )
                            await self._record_and_send(ipo.id, target_chat_id, NotificationType.GMP_DROP, title, msg, key)
                            dispatched_alerts.append({"type": "GMP_DROP", "symbol": ipo.symbol, "title": title})

                    # Trend Reversal Check
                    gmp_history = self.db.scalars(
                        select(GMPHistory).where(GMPHistory.ipo_id == ipo.id).order_by(GMPHistory.observation_time.desc())
                    ).all()
                    if len(gmp_history) >= 3:
                        prev_delta = float(gmp_history[1].gmp_price) - float(gmp_history[2].gmp_price)
                        curr_delta = float(gmp_history[0].gmp_price) - float(gmp_history[1].gmp_price)
                        
                        if (prev_delta < 0 < curr_delta) or (prev_delta > 0 > curr_delta):
                            new_trend = "RISING 🟢" if curr_delta > 0 else "FALLING 🔴"
                            key = f"GMP_REVERSAL:{ipo.symbol}:{gmp_analysis.trend}:{obs_time_str}"
                            if not self._is_alert_sent(key):
                                title = f"🔄 TREND REVERSAL: {ipo.symbol} is now {gmp_analysis.trend}"
                                msg = (
                                    f"🔄 *GMP TREND REVERSAL ALERT*\n\n"
                                    f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                                    f"• New Trend: *{new_trend}*\n"
                                    f"• Current GMP: ₹{gmp_analysis.current_gmp}\n"
                                    f"• Delta: ₹{curr_delta:+.2f}\n\n"
                                    f"⚠️ _GMP is informal and unregulated._"
                                )
                                await self._record_and_send(ipo.id, target_chat_id, NotificationType.GMP_TREND_REVERSAL, title, msg, key)
                                dispatched_alerts.append({"type": "GMP_TREND_REVERSAL", "symbol": ipo.symbol, "title": title})
            except Exception as e:
                logger.error(f"Error evaluating GMP alerts for {ipo.symbol}: {e}")

            # 3. Evaluate Subscription Milestones (1x, 5x, 10x, 25x, 50x, 100x)
            try:
                sub_history = self.db.scalars(
                    select(SubscriptionHistory).where(SubscriptionHistory.ipo_id == ipo.id).order_by(SubscriptionHistory.observation_time.desc())
                ).first()
                if sub_history and sub_history.overall_x is not None:
                    overall = float(sub_history.overall_x)
                    for milestone in SUBSCRIPTION_MILESTONES:
                        if overall >= milestone:
                            key = f"SUBSCRIPTION_MILESTONE:{ipo.symbol}:{int(milestone)}X"
                            if not self._is_alert_sent(key):
                                title = f"🔥 SUBSCRIPTION MILESTONE: {ipo.symbol} crossed {int(milestone)}x!"
                                msg = (
                                    f"🔥 *SUBSCRIPTION MILESTONE PASSED!*\n\n"
                                    f"🏢 *{ipo.company_name}* (`{ipo.symbol}`)\n"
                                    f"• Overall Demand: *{overall:.2f}x* (Crossed {int(milestone)}x)\n"
                                    f"• QIB: {sub_history.qib_x or 'N/A'}x | NII: {sub_history.nii_x or 'N/A'}x | Retail: {sub_history.retail_x or 'N/A'}x\n\n"
                                    f"Use `/subscription {ipo.symbol}` for breakdown."
                                )
                                await self._record_and_send(ipo.id, target_chat_id, NotificationType.SUBSCRIPTION_MILESTONE, title, msg, key)
                                dispatched_alerts.append({"type": "SUBSCRIPTION_MILESTONE", "symbol": ipo.symbol, "title": title})
            except Exception as e:
                logger.error(f"Error evaluating subscription alerts for {ipo.symbol}: {e}")

        # 4. Evaluate Stale Data Warning Alert
        latest_gmp = self.db.scalars(select(GMPHistory).order_by(GMPHistory.observation_time.desc())).first()
        if latest_gmp and latest_gmp.observation_time:
            if latest_gmp.observation_time < datetime.now(timezone.utc) - timedelta(hours=24):
                stale_key = f"STALE_DATA_ALERT:{today_date.isoformat()}"
                if not self._is_alert_sent(stale_key):
                    title = "⚠️ STALE DATA WARNING: No GMP updates in 24h"
                    msg = "⚠️ *STALE DATA WARNING*: Data feeds have not ingested new GMP observations in over 24 hours."
                    await self._record_and_send(None, target_chat_id, NotificationType.STALE_DATA_ALERT, title, msg, stale_key)
                    dispatched_alerts.append({"type": "STALE_DATA_ALERT", "symbol": "SYSTEM", "title": title})

        return dispatched_alerts

    async def _record_and_send(
        self,
        ipo_id: Optional[Any],
        chat_id: str,
        notif_type: NotificationType,
        title: str,
        message: str,
        idempotency_key: str
    ):
        """Persists notification record to PostgreSQL with idempotency_key and dispatches to Telegram."""
        notif = Notification(
            ipo_id=ipo_id,
            telegram_chat_id=chat_id,
            notification_type=notif_type,
            title=title,
            message=message,
            idempotency_key=idempotency_key,
            status=NotificationStatus.PENDING
        )
        self.db.add(notif)
        self.db.commit()

        # Send via Telegram API
        send_res = await self.telegram_client.send_message(chat_id, message)
        if send_res.get("ok"):
            notif.status = NotificationStatus.SENT
            notif.sent_at = datetime.now(timezone.utc)
        else:
            notif.status = NotificationStatus.FAILED
            notif.error_message = send_res.get("error", "Failed to deliver Telegram message")
        
        self.db.commit()
