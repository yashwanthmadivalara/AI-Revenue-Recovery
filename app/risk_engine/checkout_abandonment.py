from typing import Tuple, Dict, Any
from app.models.event_models import RiskSeverity


class CheckoutAbandonmentEvaluator:
    """Evaluates checkout abandonment events based on cart value, items, and visitor engagement."""

    @staticmethod
    def evaluate(amount: float, metadata: Dict[str, Any]) -> Tuple[RiskSeverity, str, float]:
        """
        Returns:
            Tuple of (Severity, Reason, Recommended Discount Pct)
        """
        cart_items_count = metadata.get("cart_items_count", 1)
        time_spent_seconds = metadata.get("time_spent_seconds", 120)
        has_promo_applied = metadata.get("has_promo_applied", False)

        # High cart value (> $1000)
        if amount >= 1000:
            severity = RiskSeverity.HIGH
            discount_pct = 5.0 if not has_promo_applied else 0.0
            reason = "High-value cart abandoned at checkout step. Priority recovery with dynamic discount incentive."
        elif amount >= 250:
            severity = RiskSeverity.MEDIUM
            discount_pct = 10.0 if not has_promo_applied else 0.0
            reason = "Mid-value checkout abandonment. Standard automated email/SMS recovery sequence."
        else:
            severity = RiskSeverity.LOW
            discount_pct = 0.0
            reason = "Low-value cart abandonment. Single email notification."

        return severity, reason, discount_pct
