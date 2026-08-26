from typing import Tuple
from app.models.event_models import RiskSeverity

# Common soft decline codes across Stripe, Adyen, Razorpay
SOFT_DECLINE_CODES = {
    "insufficient_funds",
    "card_velocity_exceeded",
    "try_again_later",
    "processing_error",
    "issuer_unavailable",
    "temporary_hold",
    "exceeded_pin_retry",
    "timeout",
    "gateway_timeout",
    "network_error",
    "do_not_honor"  # Often soft when transient
}

HARD_DECLINE_CODES = {
    "stolen_card",
    "lost_card",
    "fraudulent",
    "card_expired",
    "invalid_account_number",
    "pickup_card",
    "restricted_card",
    "account_closed"
}


class SoftDeclineEvaluator:
    """Evaluates payment failure codes to distinguish recoverable soft declines from hard declines."""

    @staticmethod
    def evaluate(decline_code: str, amount: float) -> Tuple[bool, RiskSeverity, str]:
        normalized_code = (decline_code or "generic").lower().replace(" ", "_")

        # Check soft decline
        if any(soft in normalized_code for soft in SOFT_DECLINE_CODES):
            if amount > 1000:
                severity = RiskSeverity.HIGH
            elif amount > 200:
                severity = RiskSeverity.MEDIUM
            else:
                severity = RiskSeverity.LOW
            return True, severity, f"Soft decline detected ({normalized_code}): Eligible for smart gateway retry sequencing."

        # Check hard decline
        if any(hard in normalized_code for hard in HARD_DECLINE_CODES):
            return False, RiskSeverity.CRITICAL, f"Hard decline detected ({normalized_code}): Direct card retry will fail. Requires customer payment method update."

        # Default fallback
        severity = RiskSeverity.MEDIUM if amount > 250 else RiskSeverity.LOW
        return True, severity, f"Unclassified decline code ({normalized_code}): Treated as potential soft decline with fallback outreach."
