from typing import Tuple, Dict, Any
from app.models.event_models import RiskSeverity


class MandateExpiryEvaluator:
    """Evaluates recurring e-mandates (UPI AutoPay, NACH, SEPA, Credit Card Expiry)."""

    @staticmethod
    def evaluate(amount: float, metadata: Dict[str, Any]) -> Tuple[RiskSeverity, str]:
        days_until_expiry = metadata.get("days_until_expiry", 0)
        mandate_type = metadata.get("mandate_type", "e-mandate")

        if days_until_expiry <= 0:
            severity = RiskSeverity.HIGH
            reason = f"Recurring {mandate_type} has expired! Next billing cycle will automatically fail unless renewed."
        elif days_until_expiry <= 7:
            severity = RiskSeverity.MEDIUM
            reason = f"Recurring {mandate_type} expires in {days_until_expiry} days. Proactive renewal link dispatch."
        else:
            severity = RiskSeverity.LOW
            reason = f"Recurring {mandate_type} scheduled to expire in {days_until_expiry} days."

        return severity, reason
