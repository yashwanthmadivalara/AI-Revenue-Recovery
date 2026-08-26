import uuid
import logging
from datetime import datetime
from app.schemas.events import IngestionEvent, RiskDetectionResult
from app.models.event_models import RiskType, RiskSeverity
from app.risk_engine.soft_decline import SoftDeclineEvaluator
from app.risk_engine.checkout_abandonment import CheckoutAbandonmentEvaluator
from app.risk_engine.invoice_aging import InvoiceAgingEvaluator
from app.risk_engine.mandate_expiry import MandateExpiryEvaluator

logger = logging.getLogger(__name__)


class RiskDetector:
    """
    Central Risk Detection Engine:
    Classifies raw ingestion events into concrete Risk Events with severity and risk typology.
    """

    @classmethod
    def evaluate_event(cls, event: IngestionEvent) -> RiskDetectionResult:
        event_id = f"risk_{uuid.uuid4().hex[:12]}"
        event_type = event.event_type.lower()
        amount = event.amount

        # 1. Soft Decline / Payment Failure
        if "payment_failed" in event_type or "failed" in event_type or event.decline_code:
            is_soft, severity, reason = SoftDeclineEvaluator.evaluate(event.decline_code or "generic", amount)
            risk_type = RiskType.SOFT_DECLINE if is_soft else RiskType.SOFT_DECLINE  # categorized as payment failure
            payload = {
                "reason": reason,
                "is_soft_decline": is_soft,
                "decline_code": event.decline_code,
                "source_metadata": event.metadata
            }

        # 2. Abandoned Checkout
        elif "abandoned" in event_type or "checkout" in event_type or "cart_exit" in event_type:
            risk_type = RiskType.ABANDONED_CHECKOUT
            severity, reason, discount_pct = CheckoutAbandonmentEvaluator.evaluate(amount, event.metadata)
            payload = {
                "reason": reason,
                "recommended_discount_pct": discount_pct,
                "source_metadata": event.metadata
            }

        # 3. Overdue Invoice / B2B Aging
        elif "invoice" in event_type or "aged" in event_type or event.days_overdue is not None:
            risk_type = RiskType.OVERDUE_INVOICE
            days = event.days_overdue if event.days_overdue is not None else 30
            severity, reason, needs_voice = InvoiceAgingEvaluator.evaluate(days, amount)
            payload = {
                "reason": reason,
                "days_overdue": days,
                "requires_voice": needs_voice,
                "source_metadata": event.metadata
            }

        # 4. Expired Mandate / AutoPay
        elif "mandate" in event_type or "autopay" in event_type or "subscription.halted" in event_type:
            risk_type = RiskType.EXPIRED_MANDATE
            severity, reason = MandateExpiryEvaluator.evaluate(amount, event.metadata)
            payload = {
                "reason": reason,
                "source_metadata": event.metadata
            }

        # 5. Fallback unclassified
        else:
            risk_type = RiskType.UNKNOWN
            severity = RiskSeverity.MEDIUM
            payload = {
                "reason": "Unclassified event ingested",
                "source_metadata": event.metadata
            }

        result = RiskDetectionResult(
            event_id=event_id,
            source=event.source,
            event_type=event.event_type,
            risk_type=risk_type,
            severity=severity,
            amount=amount,
            currency=event.currency,
            customer_id=event.customer_id,
            detected_at=datetime.utcnow(),
            raw_payload=payload
        )

        logger.info(f"Detected Risk [{risk_type}] Severity [{severity}] Amount [{amount} {event.currency}] for customer [{event.customer_id}]")
        return result
