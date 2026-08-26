from typing import Tuple
from app.models.event_models import RiskSeverity


class InvoiceAgingEvaluator:
    """Evaluates overdue B2B receivables across 30, 60, and 90+ day aging brackets."""

    @staticmethod
    def evaluate(days_overdue: int, amount: float) -> Tuple[RiskSeverity, str, bool]:
        """
        Returns:
            Tuple of (Severity, Reason, Requires Escalation / Voice outreach)
        """
        if days_overdue >= 90:
            severity = RiskSeverity.CRITICAL
            reason = f"Invoice is {days_overdue} days delinquent (>90 days). High bad-debt write-off risk. Immediate AI Voice outreach or human collections required."
            requires_voice_or_escalation = True
        elif days_overdue >= 60:
            severity = RiskSeverity.HIGH
            reason = f"Invoice is {days_overdue} days delinquent (60-89 days). Medium bad-debt risk. Multilingual AI Voice call with Promise-to-Pay negotiation."
            requires_voice_or_escalation = True
        elif days_overdue >= 30:
            severity = RiskSeverity.MEDIUM
            reason = f"Invoice is {days_overdue} days overdue (30-59 days). Formal accounts receivable dunning notice & payment link."
            requires_voice_or_escalation = False
        else:
            severity = RiskSeverity.LOW
            reason = f"Invoice is {days_overdue} days past due (<30 days). Friendly automated reminder."
            requires_voice_or_escalation = False

        # Additional escalation if large amount (> $10,000)
        if amount >= 10000:
            severity = RiskSeverity.CRITICAL

        return severity, reason, requires_voice_or_escalation
